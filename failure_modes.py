"""Find groups of failures that look different, then test early-failure prediction.

Records use the same convention as reliability.py: ``time`` is the age in hours and
``failed`` is 1 for a failure or 0 for a unit still running when it was last checked
(a suspension). The notebook at notebooks/failure_modes.ipynb walks through these
functions. Everything here is seeded, so the same input gives the same numbers.

The generated records are invented for teaching and testing. They are not measurements
from a real process.
"""
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, confusion_matrix, roc_auc_score, silhouette_score
from sklearn.mixture import GaussianMixture
from sklearn.model_selection import StratifiedKFold, cross_val_predict
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from reliability import fit_life_model

SEED = 20261110
EARLY_HOURS = 300.
CLUSTER_FEATURES = ["log_time", "suspended", "load", "contamination"]
COVARIATES = ["load", "contamination"]
CANDIDATE_COUNTS = (2, 3, 4)


def generate_records(units=600, seed=SEED):
    """Invented pump bearings from two failure modes, with suspensions and install-time readings.

    ``wear`` units fail late with a rising hazard (Weibull shape 3). ``early``
    units, about 30%, carry more contamination and fail soon after installation
    (shape 0.7). Each unit is checked at a random age, so some are suspensions.
    """
    rng = np.random.default_rng(seed)
    early = rng.random(units) < .3
    load = rng.uniform(.4, 1., units)
    contamination = rng.lognormal(mean=np.where(early, .6, 0.), sigma=.6)
    shape = np.where(early, .7, 3.)
    scale = np.where(early, 300., 2000.) * (1.2 - .5 * load) * np.exp(-.2 * (contamination - 3.))
    life = scale * rng.weibull(shape)
    checked = rng.uniform(200., 3000., units)
    return pd.DataFrame({
        "unit_id": [f"BRG-{i:03}" for i in range(1, units + 1)],
        "time": np.round(np.minimum(life, checked), 2),
        "failed": (life <= checked).astype(int),
        "load": np.round(load, 3),
        "contamination": np.round(contamination, 3),
        "invented_mode": np.where(early, "early", "wear"),
    })


def clustering_features(records):
    """Scale life, censoring and install-time readings so no column dominates distance."""
    frame = pd.DataFrame({
        "log_time": np.log(records["time"].to_numpy(dtype=float)),
        "suspended": 1 - records["failed"].to_numpy(dtype=int),
        "load": records["load"].to_numpy(dtype=float),
        "contamination": records["contamination"].to_numpy(dtype=float),
    }, columns=CLUSTER_FEATURES)
    scaler = StandardScaler()
    return scaler.fit_transform(frame), scaler


def scan_kmeans(matrix, counts=CANDIDATE_COUNTS, seed=SEED):
    """Silhouette score for each cluster count; higher means tighter, better separated groups."""
    rows = []
    for k in counts:
        model = KMeans(n_clusters=k, n_init=10, random_state=seed).fit(matrix)
        rows.append(dict(clusters=k, silhouette=silhouette_score(matrix, model.labels_),
                         inertia=model.inertia_, labels=model.labels_))
    return pd.DataFrame(rows)


def scan_gaussian_mixture(matrix, counts=CANDIDATE_COUNTS, seed=SEED):
    """BIC for each mixture size; lower is better after penalising extra parameters."""
    rows = []
    for k in counts:
        model = GaussianMixture(n_components=k, covariance_type="full", n_init=5,
                                random_state=seed).fit(matrix)
        rows.append(dict(clusters=k, bic=model.bic(matrix), labels=model.predict(matrix)))
    return pd.DataFrame(rows)


def best_by(scan, column, maximise):
    """Return the cluster count that wins on one column of a scan table."""
    row = scan.loc[scan[column].idxmax() if maximise else scan[column].idxmin()]
    return int(row["clusters"])


def weibull_by_cluster(records, labels):
    """Fit a Weibull to each cluster and to the pooled sample, keeping suspensions in."""
    table = pd.DataFrame({"time": records["time"].to_numpy(dtype=float),
                          "failed": records["failed"].to_numpy(dtype=int)})
    rows = [_weibull_row("pooled", table)]
    for cluster in sorted(np.unique(labels)):
        rows.append(_weibull_row(f"cluster {cluster}", table[labels == cluster].reset_index(drop=True)))
    return pd.DataFrame(rows)


def _weibull_row(name, table):
    row = dict(group=name, units=len(table), failures=int(table["failed"].sum()))
    try:
        fit = fit_life_model(table, "weibull")
    except ValueError as error:
        return {**row, "shape": np.nan, "scale": np.nan, "b10": np.nan, "note": str(error)}
    return {**row, "shape": fit["parameters"]["shape"], "scale": fit["parameters"]["scale"],
            "b10": fit["b10"]["estimate"], "note": ""}


def early_failure_dataset(records, early_hours=EARLY_HOURS):
    """Label failures before ``early_hours`` as early, using only install-time readings.

    A unit suspended before ``early_hours`` could still fail early, so it is left out.
    Units that survived past the cutoff, or failed later, are labelled not early.
    Age and cluster labels are not features: both come from the outcome itself.
    """
    times = records["time"].to_numpy(dtype=float)
    failed = records["failed"].to_numpy(dtype=int).astype(bool)
    known = failed | (times > early_hours)
    labels = (failed & (times <= early_hours))[known].astype(int)
    features = records.loc[known, COVARIATES].reset_index(drop=True)
    return features, pd.Series(labels, name="early_failure")


def baseline_models(seed=SEED):
    """Logistic regression, random forest and a prevalence-only reference."""
    return {
        "prevalence only": DummyClassifier(strategy="prior"),
        "logistic regression": make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000)),
        "random forest": RandomForestClassifier(n_estimators=300, min_samples_leaf=5, random_state=seed),
    }


def cross_validated_baselines(features, labels, seed=SEED, folds=5):
    """Out-of-fold probabilities for each baseline, so every unit is scored by a model that did not see it."""
    cv = StratifiedKFold(n_splits=folds, shuffle=True, random_state=seed)
    results = {}
    for name, model in baseline_models(seed).items():
        probability = cross_val_predict(model, features, labels, cv=cv, method="predict_proba")[:, 1]
        predicted = (probability >= .5).astype(int)
        matrix = confusion_matrix(labels, predicted, labels=[0, 1])
        results[name] = dict(probability=probability, confusion=matrix,
                             auc=roc_auc_score(labels, probability),
                             brier=brier_score_loss(labels, probability))
    return results
