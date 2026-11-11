"""Seeded checks for mixed failure-mode clustering and early-failure baselines."""
import numpy as np
import pandas as pd
import pytest

import failure_modes as fm


def test_generated_records_are_reproducible_and_include_suspensions():
    first = fm.generate_records(units=300)
    second = fm.generate_records(units=300)
    pd.testing.assert_frame_equal(first, second)
    assert set(first["failed"]) == {0, 1}
    assert (first["time"] > 0).all()
    assert set(first["invented_mode"]) == {"wear", "early"}


def test_clustering_features_are_scaled_and_keep_every_unit():
    records = fm.generate_records(units=200)
    matrix, scaler = fm.clustering_features(records)
    assert matrix.shape == (200, len(fm.CLUSTER_FEATURES))
    assert np.allclose(matrix.mean(axis=0), 0, atol=1e-9)
    assert np.allclose(matrix.std(axis=0), 1, atol=1e-9)
    assert scaler.n_features_in_ == len(fm.CLUSTER_FEATURES)


def test_cluster_count_scans_cover_requested_counts_and_are_seeded():
    records = fm.generate_records(units=300)
    matrix, _ = fm.clustering_features(records)
    kmeans = fm.scan_kmeans(matrix)
    mixture = fm.scan_gaussian_mixture(matrix)
    assert list(kmeans["clusters"]) == list(fm.CANDIDATE_COUNTS)
    assert list(mixture["clusters"]) == list(fm.CANDIDATE_COUNTS)
    assert fm.best_by(kmeans, "silhouette", maximise=True) in fm.CANDIDATE_COUNTS
    assert fm.best_by(mixture, "bic", maximise=False) in fm.CANDIDATE_COUNTS
    again = fm.scan_kmeans(matrix)
    assert np.allclose(kmeans["silhouette"], again["silhouette"])
    assert len(kmeans.loc[0, "labels"]) == 300


def test_weibull_fit_recovers_a_known_shape_in_a_clean_sample():
    rng = np.random.default_rng(1)
    lives = 1000 * rng.weibull(2., 2000)
    records = pd.DataFrame({"time": lives, "failed": 1, "load": .5, "contamination": 1.})
    table = fm.weibull_by_cluster(records, np.zeros(len(records), dtype=int))
    pooled = table.iloc[0]
    assert pooled["group"] == "pooled"
    assert pooled["shape"] == pytest.approx(2., abs=.1)
    assert pooled["scale"] == pytest.approx(1000 * 1.0, rel=.05)


def test_groups_without_failures_are_reported_not_fitted():
    records = pd.DataFrame({"time": [100., 200., 300., 400., 500., 600.],
                            "failed": [1, 1, 1, 0, 0, 0]})
    labels = np.array([0, 0, 0, 1, 1, 1])
    table = fm.weibull_by_cluster(records, labels)
    survivors = table[table["group"] == "cluster 1"].iloc[0]
    assert survivors["failures"] == 0
    assert np.isnan(survivors["shape"])
    assert "No observed failures" in survivors["note"]
    assert table[table["group"] == "cluster 0"].iloc[0]["shape"] > 0


def test_early_labels_drop_suspensions_before_the_cutoff_and_hide_age():
    records = pd.DataFrame({
        "time": [100., 200., 400., 500., 50.],
        "failed": [1, 0, 0, 1, 0],
        "load": [.5, .6, .7, .8, .9],
        "contamination": [1., 2., 3., 4., 5.],
    })
    features, labels = fm.early_failure_dataset(records, early_hours=300.)
    # Row 1 and row 4 were suspended before 300 h, so their status is unknown.
    assert list(labels) == [1, 0, 0]
    assert list(features.columns) == fm.COVARIATES
    assert "time" not in features.columns


def test_baselines_are_out_of_fold_repeatable_and_beat_the_prevalence_reference():
    records = fm.generate_records(units=500)
    features, labels = fm.early_failure_dataset(records)
    first = fm.cross_validated_baselines(features, labels)
    second = fm.cross_validated_baselines(features, labels)
    assert set(first) == {"prevalence only", "logistic regression", "random forest"}
    for name, result in first.items():
        assert len(result["probability"]) == len(labels)
        assert ((result["probability"] >= 0) & (result["probability"] <= 1)).all()
        assert result["confusion"].sum() == len(labels)
        assert np.allclose(result["probability"], second[name]["probability"])
    # Each fold predicts its training prevalence, so AUC is near chance but not exactly .5.
    assert first["prevalence only"]["auc"] == pytest.approx(.5, abs=.05)
    assert first["logistic regression"]["auc"] > .65
    assert first["random forest"]["auc"] > .65
