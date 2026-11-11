"""Streamed random samples from CSV files that are too big to load in one go."""
import json

import numpy as np
import pytest

import analysis
import compare_distributions as compare


ROWS = 60_000


@pytest.fixture
def big_csv(tmp_path):
    """A 60,000-row file with a Gamma column, a few blanks and one text value."""
    values = np.random.default_rng(5).gamma(2, 2, ROWS)
    lines = ["Time,Value"]
    for i, value in enumerate(values):
        if i == 17:
            lines.append("0,")                 # blank
        elif i == 18:
            lines.append("0,not-a-number")     # text
        elif i == 19:
            lines.append("0,inf")              # not finite
        else:
            lines.append(f"{i},{float(value)!r}")
    path = tmp_path / "large.csv"
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path, values


def test_sample_keeps_original_rows_and_counts_the_whole_file(big_csv):
    path, values = big_csv
    result = analysis.reservoir_sample_column(path, "Value", 500, seed=3, chunksize=1_000)
    assert result["rows_scanned"] == ROWS
    assert result["rows_skipped"] == 3
    assert result["chunks"] == 60
    assert result["sample_size"] == 500
    assert len(result["values"]) == 500
    # Each sampled value is the exact value from the row it came from, in file order.
    assert np.all(np.diff(result["row_numbers"]) > 0)
    assert np.array_equal(result["values"], values[result["row_numbers"]])
    assert not {17, 18, 19} & set(result["row_numbers"].tolist())


def test_same_seed_repeats_and_chunk_size_does_not_change_the_sample(big_csv):
    path, _ = big_csv
    first = analysis.reservoir_sample_column(path, "Value", 300, seed=9, chunksize=1_000)
    again = analysis.reservoir_sample_column(path, "Value", 300, seed=9, chunksize=1_000)
    other_seed = analysis.reservoir_sample_column(path, "Value", 300, seed=10, chunksize=1_000)
    assert np.array_equal(first["row_numbers"], again["row_numbers"])
    assert not np.array_equal(first["row_numbers"], other_seed["row_numbers"])
    # Chunk size must not matter: the same seed gives the same sample at every piece size.
    for chunksize in (1, 7, 999, 50_000, ROWS + 1):
        other = analysis.reservoir_sample_column(path, "Value", 300, seed=9, chunksize=chunksize)
        assert np.array_equal(other["row_numbers"], first["row_numbers"]), chunksize


def test_sample_mean_is_close_to_the_whole_column(big_csv):
    path, values = big_csv
    result = analysis.reservoir_sample_column(path, "Value", 4_000, seed=1, chunksize=7_000)
    # Standard error of a 4,000-row mean is about 0.03 here; allow ten of them.
    finite = np.delete(values, [17, 18, 19])
    assert abs(result["values"].mean() - finite.mean()) < 0.3


def test_sample_larger_than_the_file_returns_every_finite_row(tmp_path):
    path = tmp_path / "small.csv"
    path.write_text("Value\n1\n2\nx\n4\n", encoding="utf-8")
    result = analysis.reservoir_sample_column(path, "Value", 100, chunksize=2)
    assert result["values"].tolist() == [1.0, 2.0, 4.0]
    assert result["sample_size"] == 3
    assert result["rows_skipped"] == 1


@pytest.mark.parametrize("column, message", [("Missing", "missing"), ("Value", "no finite")])
def test_bad_inputs_are_explained(tmp_path, column, message):
    path = tmp_path / "bad.csv"
    path.write_text("Value\n,\n", encoding="utf-8")
    with pytest.raises(ValueError, match=message):
        analysis.reservoir_sample_column(path, column, 10)


def test_sample_size_and_chunk_size_must_be_positive(big_csv):
    path, _ = big_csv
    with pytest.raises(ValueError, match="Sample size"):
        analysis.reservoir_sample_column(path, "Value", 0)
    with pytest.raises(ValueError, match="Chunk size"):
        analysis.reservoir_sample_column(path, "Value", 10, chunksize=0)


def test_command_line_fit_streams_the_file_and_records_how_rows_were_chosen(big_csv, tmp_path):
    path, _ = big_csv
    out = tmp_path / "bundle"
    assert compare.main(["fit", "--input", str(path), "--column", "Value", "--sample-size", "400",
                         "--out", str(out)]) == 0
    saved = json.loads((out / "comparison.json").read_text(encoding="utf-8"))
    sampling = saved["analysis"]["settings"]["sampling"]
    assert sampling["rows_scanned"] == ROWS
    assert sampling["sample_size"] == 400
    assert len(saved["analysis"]["source_data"]) == 400
    assert (out / "manifest.json").is_file()


def test_sample_size_cannot_be_combined_with_the_built_in_sample(tmp_path):
    with pytest.raises(SystemExit):
        compare.main(["fit", "--sample", "--sample-size", "10", "--out", str(tmp_path / "x")])
