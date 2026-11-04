"""Star-schema export: grain, keys, metric consistency, file formats and DAX references."""
import re
import tempfile
import unittest
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

import export_powerbi as ex
from analysis import fit_candidates

ROOT = Path(__file__).resolve().parents[1]
FAMILIES = ["Normal", "Gamma", "Beta", "Uniform", "Log-Normal"]
CREATED = "2026-01-01T00:00:00Z"


def datasets():
    rng = np.random.default_rng(7)
    return [{"dataset_name": "Gamma sample", "values": rng.gamma(3., 2., 400), "source": "synthetic"},
            {"dataset_name": "Normal sample", "values": rng.normal(10, 2, 300), "source": "synthetic"},
            {"dataset_name": "Constant", "values": np.full(50, 4.)},
            {"dataset_name": "Too short", "values": [1., 2., 3.]}]


class StarSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.items = datasets()
        cls.tables = ex.build_star_schema(cls.items, FAMILIES, seed=3, created_utc=CREATED)
        cls.fact, cls.dim_ds = cls.tables["fact_fit"], cls.tables["dim_dataset"]

    def test_tables_have_declared_columns(self):
        for name, columns in ex.TABLES.items():
            self.assertEqual(list(self.tables[name].columns), list(columns), name)

    def test_grain_and_foreign_keys(self):
        self.assertEqual(len(self.fact), 2 * len(FAMILIES))
        self.assertFalse(self.fact.duplicated(["run_id", "dataset_id", "distribution_id"]).any())
        self.assertTrue(self.fact["dataset_id"].isin(self.dim_ds["dataset_id"]).all())
        self.assertTrue(self.fact["distribution_id"].isin(self.tables["dim_distribution"]["distribution_id"]).all())
        self.assertTrue(self.fact["run_id"].isin(self.tables["dim_run"]["run_id"]).all())
        self.assertEqual(len(self.tables["dim_distribution"]), 14)
        self.assertTrue(self.tables["dim_distribution"]["distribution_id"].is_unique)

    def test_metrics_match_fit_candidates(self):
        item = self.items[0]
        fit = fit_candidates(item["values"], FAMILIES, seed=3)
        ids = ex.distribution_ids()
        rows = self.fact[self.fact["dataset_id"] == "gamma_sample"].set_index("distribution_id")
        for result in fit["results"]:
            row = rows.loc[ids[result["Distribution"]]]
            params = result["Parameters"]
            self.assertAlmostEqual(row["loc"], params[-2])
            self.assertAlmostEqual(row["scale"], params[-1])
            self.assertEqual(row["parameter_count"], len(params))
            self.assertAlmostEqual(row["aic"], result["AIC"])
            self.assertAlmostEqual(row["bic"], result["BIC"])
            self.assertAlmostEqual(row["ks_statistic"], result["KS Stat"])
            self.assertAlmostEqual(row["heldout_nll"], result["Held-out NLL"])
            # AIC = 2k - 2 logL on the training split.
            self.assertAlmostEqual(row["aic"], 2 * len(params) - 2 * row["log_likelihood"])
        best = rows[rows["is_best_fit"]].index.tolist()
        self.assertEqual(best, [ids[fit["results"][0]["Distribution"]]])

    def test_ranks_deltas_and_weights_are_consistent_within_each_dataset(self):
        for _, group in self.fact.groupby("dataset_id"):
            self.assertEqual(group["rank_heldout_nll"].min(), 1)
            self.assertEqual(int(group["is_best_fit"].sum()), 1)
            self.assertAlmostEqual(group["delta_aic"].min(), 0.)
            self.assertAlmostEqual(group["delta_bic"].min(), 0.)
            self.assertAlmostEqual(group["akaike_weight"].sum(), 1.)
            self.assertTrue((group["delta_aic"] >= 0).all())
            ordered = group.sort_values("rank_heldout_nll")
            self.assertTrue(ordered["heldout_nll"].dropna().is_monotonic_increasing)
            self.assertEqual(group["rank_aic"].idxmin(), group["aic"].idxmin())

    def test_ks_pass_follows_p_value_and_alpha(self):
        self.assertTrue(((self.fact["ks_p_value"] >= ex.KS_ALPHA) == self.fact["ks_pass"]).all())
        strict = ex.build_star_schema(self.items[:2], FAMILIES, seed=3, created_utc=CREATED, ks_alpha=1e-12)
        self.assertGreaterEqual(strict["fact_fit"]["ks_pass"].sum(), self.fact["ks_pass"].sum())

    def test_unfittable_datasets_are_recorded_not_dropped(self):
        status = self.dim_ds.set_index("dataset_id")
        self.assertEqual(status.loc["gamma_sample", "analysis_status"], "fitted")
        for key in ("constant", "too_short"):
            self.assertEqual(status.loc[key, "analysis_status"], "skipped")
            self.assertTrue(status.loc[key, "skip_reason"])
            self.assertNotIn(key, set(self.fact["dataset_id"]))

    def test_failed_fit_rows_keep_reason_and_null_metrics(self):
        values = np.random.default_rng(1).normal(size=200)
        row = ex._fit_rows("r", "d", {"data": values, "train_indices": np.arange(150), "held_indices": np.arange(150, 200),
                                      "results": [], "errors": {"Normal": "ValueError: boom"}},
                           ex.distribution_ids(), .05)
        self.assertEqual(row.loc[0, "fit_status"], "failed")
        self.assertEqual(row.loc[0, "failure_reason"], "ValueError: boom")
        self.assertTrue(pd.isna(row.loc[0, "aic"]))
        self.assertTrue(pd.isna(row.loc[0, "rank_heldout_nll"]))

    def test_unknown_candidate_and_duplicate_ids_are_rejected(self):
        with self.assertRaises(ValueError):
            ex.build_star_schema(self.items[:1], ["Nope"])
        with self.assertRaises(ValueError):
            ex.build_star_schema([self.items[0], self.items[0]], FAMILIES)

    def test_export_is_deterministic(self):
        again = ex.build_star_schema(self.items, FAMILIES, seed=3, created_utc=CREATED)
        pd.testing.assert_frame_equal(again["fact_fit"], self.fact)
        self.assertEqual(again["dim_run"]["run_id"][0], self.tables["dim_run"]["run_id"][0])

    def test_outlier_filtering_is_recorded(self):
        values = np.append(np.random.default_rng(2).normal(0, 1, 300), [500., 600.])
        tables = ex.build_star_schema([{"dataset_name": "o", "values": values}], ["Normal"],
                                      outlier_method="IQR", created_utc=CREATED)
        row = tables["dim_dataset"].iloc[0]
        self.assertGreaterEqual(row["removed_observations"], 2)
        self.assertEqual(row["source_observations"] - row["removed_observations"], row["prepared_observations"])
        self.assertEqual(tables["dim_run"].loc[0, "outlier_method"], "IQR")


class FileTests(unittest.TestCase):
    def test_csv_and_parquet_agree_and_parquet_types_are_explicit(self):
        tables = ex.build_star_schema(datasets()[:2], FAMILIES, seed=3, created_utc=CREATED)
        with tempfile.TemporaryDirectory() as tmp:
            paths = ex.write_star_schema(tables, tmp)
            self.assertEqual(len(paths), 8)
            for name, columns in ex.TABLES.items():
                table = pq.read_table(Path(tmp, "parquet", f"{name}.parquet"))
                self.assertEqual(table.column_names, list(columns))
                kinds = {"string": "string", "double": "double", "int64": "int64", "bool": "bool"}
                self.assertEqual([str(f.type) for f in table.schema], [kinds[k] for k in columns.values()])
                from_csv = pd.read_csv(Path(tmp, "csv", f"{name}.csv"))
                self.assertEqual(len(from_csv), len(tables[name]))
                from_parquet = table.to_pandas()
                for column in ("dataset_id", "distribution_id", "dataset_name", "distribution_name", "run_id"):
                    if column in from_csv:
                        self.assertEqual(from_csv[column].astype(str).tolist(), from_parquet[column].astype(str).tolist())
            fact = pq.read_table(Path(tmp, "parquet", "fact_fit.parquet")).to_pandas()
            csv = pd.read_csv(Path(tmp, "csv", "fact_fit.csv"))
            np.testing.assert_allclose(fact["aic"].astype(float), csv["aic"], rtol=1e-12)
            self.assertEqual(fact["shape_2"].isna().tolist(), csv["shape_2"].isna().tolist())

    def test_unsupported_format_is_rejected(self):
        with self.assertRaises(ValueError):
            ex.write_star_schema({}, "unused", ("xlsx",))

    def test_cli_exports_numeric_csv_columns(self):
        rng = np.random.default_rng(5)
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp, "sales.csv")
            pd.DataFrame({"region": ["a"] * 120, "amount": rng.gamma(2., 3., 120),
                          "units": rng.normal(50, 5, 120)}).to_csv(source, index=False)
            out = Path(tmp, "out")
            ex.main([str(source), "--out", str(out), "--format", "csv", "--created-utc", CREATED])
            fact = pd.read_csv(out / "csv" / "fact_fit.csv")
            self.assertEqual(sorted(fact["dataset_id"].unique()), ["sales_amount", "sales_units"])
            self.assertFalse((out / "parquet").exists())
            self.assertTrue((out / "reference_measures.csv").exists())
            with self.assertRaises(ValueError):
                ex.load_csv_datasets(source, ["region"])


class SampleExportTests(unittest.TestCase):
    """The committed sample export must stay in step with the schema and the DAX."""
    folder = ROOT / "powerbi" / "sample_export"

    def test_committed_sample_matches_schema_and_covers_public_datasets(self):
        for name, columns in ex.TABLES.items():
            for fmt in ("csv", "parquet"):
                path = self.folder / fmt / f"{name}.{fmt}"
                frame = pd.read_csv(path) if fmt == "csv" else pq.read_table(path).to_pandas()
                self.assertEqual(list(frame.columns), list(columns), path.name)
        fact = pd.read_csv(self.folder / "csv" / "fact_fit.csv")
        self.assertEqual(fact["dataset_id"].nunique(), 12)
        self.assertEqual(len(fact), 12 * 14)
        self.assertTrue((fact.groupby("dataset_id")["is_best_fit"].sum() == 1).all())

    def test_sample_inputs_regenerate_the_committed_fact_table_keys(self):
        items = ex.load_sample_datasets(ROOT / "powerbi" / "sample_data")
        self.assertEqual(len(items), 12)
        self.assertTrue(all(len(i["values"]) >= 30 for i in items))

    def test_reference_measures_are_consistent_with_the_fact_table(self):
        tables = {name: pd.read_csv(self.folder / "csv" / f"{name}.csv") for name in ex.TABLES}
        reference = ex.reference_measures(tables)
        self.assertAlmostEqual(reference["best_fit_share"].sum(), 1.)
        fact = tables["fact_fit"]
        self.assertAlmostEqual((reference["ks_pass_rate"] * reference["datasets_fitted"]).sum() / len(fact),
                               fact["ks_pass"].mean())
        committed = pd.read_csv(self.folder.parent / "sample_export" / "reference_measures.csv")
        pd.testing.assert_frame_equal(committed, reference, check_exact=False, rtol=1e-9)

    def test_dax_only_references_existing_tables_and_columns(self):
        dax = (ROOT / "powerbi" / "measures.dax").read_text()
        code = re.sub(r"//[^\n]*", "", dax)
        for table, column in re.findall(r"\b(fact_fit|dim_dataset|dim_distribution|dim_run)\[(\w+)\]", code):
            self.assertIn(column, ex.TABLES[table], f"{table}[{column}] is not in the export schema")
        measures = re.findall(r"^([A-Z][\w ]+?) =\s*$", dax, re.M)
        self.assertGreaterEqual(len(measures), 10)
        for referenced in set(re.findall(r"(?<![\w\]])\[([A-Z][\w ]+)\]", code)):
            self.assertIn(referenced, measures, f"[{referenced}] is not defined")
        for required in ("Best Fit Share", "AIC Delta", "KS Pass Rate"):
            self.assertIn(required, measures)


if __name__ == "__main__":
    unittest.main()
