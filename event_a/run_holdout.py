#!/usr/bin/env python3
"""Run the single preregistered P35 Event A held-out evaluation.

The selection is frozen by EVENT_A_PLAN. This runner refuses to overwrite
predictions.csv so a completed Event A run cannot be silently replaced.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import platform
import subprocess
import sys
import time
import warnings
from pathlib import Path
from urllib.parse import urlsplit

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

FROZEN_DATA_SHA = "6e1075ead90054ff9955cf310842c0d31a41e5dc"
FROZEN_M1_COMMIT = "a96779829fc5ea641089afdb161298f4da3962ae"
EVENT_A_PLAN_COMMIT = "5465e46d55642d9f3423bdc63470fad5b72af184"
SALT = "P35_EVENT_A_V1|"
SEED = 42
FEATURE_FUNCS = {
    "count_methods": "count_methods",
    "count_fields": "count_fields",
    "tcc": "calculate_tcc",
    "cyclomatic_complexity": "calculate_cyclomatic_complexity",
    "loc": "count_lines_of_code",
    "atfd": "calculate_atfd",
    "lcom5": "calculate_lcom5",
}
M2_BASELINES = {
    "bounded": {"Metric-based": 0.6667, "Token-based": 0.6667},
    "full_dataset_cv_mean": {"Metric-based": 0.6379, "Token-based": 0.4135},
}


def git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)


def git_blob_sha1(path: Path) -> str:
    raw = path.read_bytes()
    return hashlib.sha1(f"blob {len(raw)}\0".encode("utf-8") + raw).hexdigest()


def normalize_project(link: str) -> str:
    parsed = urlsplit(str(link).strip())
    if parsed.hostname is None or parsed.hostname.lower() != "github.com":
        raise ValueError(f"not a GitHub URL: {link!r}")
    parts = [part for part in parsed.path.split("/") if part]
    if len(parts) < 2:
        raise ValueError(f"GitHub URL lacks owner/repository: {link!r}")
    return f"{parts[0]}/{parts[1].removesuffix('.git')}".lower()


def selected_for_holdout(project_id: str) -> bool:
    digest = hashlib.sha256(f"{SALT}{project_id}".encode("utf-8")).digest()
    return int.from_bytes(digest, byteorder="big") % 5 == 0


def validate_inputs(repo: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Validate frozen source data and every immutable split assignment."""
    data_path = repo / "data" / "god_class_df.csv"
    manifest_path = repo / "event_a" / "split_manifest.csv"
    cases_path = repo / "event_a" / "heldout_cases.csv"
    if git_blob_sha1(data_path) != FROZEN_DATA_SHA:
        raise RuntimeError("dataset Git blob SHA-1 does not match the M2 frozen input")
    if git(repo, "merge-base", "--is-ancestor", FROZEN_M1_COMMIT, "HEAD").returncode != 0:
        raise RuntimeError("the frozen M1 commit is not in history")
    if git(repo, "diff", "--quiet", FROZEN_M1_COMMIT, "HEAD", "--", "data", "scripts").returncode != 0:
        raise RuntimeError("data/ or scripts/ differs from the frozen M1 input")
    plan = git(repo, "rev-parse", "EVENT_A_PLAN^{}")
    if plan.returncode != 0 or plan.stdout.strip() != EVENT_A_PLAN_COMMIT:
        raise RuntimeError("EVENT_A_PLAN does not resolve to the preregistered preparation commit")

    data = pd.read_csv(data_path)
    manifest = pd.read_csv(manifest_path)
    cases = pd.read_csv(cases_path)
    required = {"sample_id", "project_id", "assignment", "link", "start_line", "end_line", "code_snippet_sha256"}
    if required - set(manifest.columns):
        raise RuntimeError("split manifest is missing required fields")
    if len(data) != 2148 or len(manifest) != 2148 or not manifest["sample_id"].is_unique:
        raise RuntimeError("dataset or manifest does not contain exactly 2,148 unique samples")
    if set(data["sample_id"].astype(int)) != set(manifest["sample_id"].astype(int)):
        raise RuntimeError("manifest IDs do not match the frozen dataset")

    data = data.copy()
    data["sample_id"] = data["sample_id"].astype(int)
    manifest = manifest.copy()
    manifest["sample_id"] = manifest["sample_id"].astype(int)
    manifest["start_line"] = manifest["start_line"].astype(int)
    manifest["end_line"] = manifest["end_line"].astype(int)
    data["project_id"] = data["link"].map(normalize_project)
    data["code_snippet_sha256"] = data["code_snippet"].map(
        lambda snippet: hashlib.sha256(snippet.encode("utf-8")).hexdigest()
    )
    merged = data.merge(
        manifest,
        on="sample_id",
        how="inner",
        suffixes=("_data", "_manifest"),
        validate="one_to_one",
    )
    for field in ("project_id", "link", "start_line", "end_line", "code_snippet_sha256"):
        if not (merged[f"{field}_data"].astype(str) == merged[f"{field}_manifest"].astype(str)).all():
            raise RuntimeError(f"manifest {field} does not match the frozen dataset")

    expected = data[["sample_id", "project_id", "code_snippet"]].copy()
    expected["assignment"] = expected["project_id"].map(
        lambda project: "holdout" if selected_for_holdout(project) else "training"
    )
    heldout_snippets = set(expected.loc[expected["assignment"] == "holdout", "code_snippet"])
    expected.loc[
        (expected["assignment"] == "training") & expected["code_snippet"].isin(heldout_snippets),
        "assignment",
    ] = "excluded"
    assignments = manifest.set_index("sample_id")["assignment"].sort_index()
    expected_assignments = expected.set_index("sample_id")["assignment"].sort_index()
    if not (expected_assignments == assignments).all():
        raise RuntimeError("manifest assignments differ from the preregistered selection rule")
    counts = manifest["assignment"].value_counts().to_dict()
    if counts != {"training": 1654, "holdout": 494}:
        raise RuntimeError(f"unexpected assignment counts: {counts}")

    by_project = manifest.groupby("project_id")["assignment"].agg(set)
    if any("holdout" in values and "training" in values for values in by_project):
        raise RuntimeError("a project appears in both training and holdout")
    source_assignments = data[["sample_id", "code_snippet"]].merge(
        manifest[["sample_id", "assignment"]], on="sample_id", validate="one_to_one"
    )
    by_snippet = source_assignments.groupby("code_snippet")["assignment"].agg(set)
    if any("holdout" in values and "training" in values for values in by_snippet):
        raise RuntimeError("an exact snippet leaks from training to holdout")

    holdout_manifest = manifest.loc[manifest["assignment"] == "holdout"].sort_values("sample_id").reset_index(drop=True)
    cases = cases.sort_values("sample_id").reset_index(drop=True)
    if not cases.equals(holdout_manifest):
        raise RuntimeError("heldout_cases.csv does not exactly match holdout manifest rows")
    merged["assignment"] = merged["assignment"]
    training = merged.loc[merged["assignment"] == "training"].sort_values("sample_id").reset_index(drop=True)
    holdout = merged.loc[merged["assignment"] == "holdout"].sort_values("sample_id").reset_index(drop=True)
    return merged.sort_values("sample_id").reset_index(drop=True), training, holdout, manifest


def load_author_functions(script: Path) -> tuple[dict[str, object], dict[str, int]]:
    """Extract the same seven last-defined functions used by frozen M2."""
    lines = script.read_text().splitlines()
    wanted = set(FEATURE_FUNCS.values())
    namespace: dict[str, object] = {}
    exec("import javalang", namespace)
    found: dict[str, int] = {}
    for index, line in enumerate(lines):
        if not line.startswith("def "):
            continue
        name = line[4:].split("(")[0].strip()
        if name not in wanted:
            continue
        block = [line]
        for next_line in lines[index + 1:]:
            if next_line.strip() and not next_line[0].isspace():
                break
            block.append(next_line)
        exec("\n".join(block), namespace)
        found[name] = index + 1
    if wanted != set(found):
        raise RuntimeError(f"author metric functions missing: {sorted(wanted - set(found))}")
    return {name: namespace[name] for name in wanted}, found


def compute_features(data: pd.DataFrame, functions: dict[str, object]) -> pd.DataFrame:
    rows, failures = [], []
    for sample_id, snippet in zip(data["sample_id"], data["code_snippet"]):
        try:
            rows.append({
                "sample_id": int(sample_id),
                **{column: functions[function](snippet) for column, function in FEATURE_FUNCS.items()},
            })
        except Exception as error:  # M2 fails rather than silently dropping a sample.
            failures.append((int(sample_id), f"{type(error).__name__}: {str(error)[:80]}"))
    if failures:
        raise RuntimeError(f"metric feature extraction failed: {failures}")
    return pd.DataFrame(rows)


def scores(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float | int]:
    from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score

    true = np.asarray(y_true)
    predicted = np.asarray(y_pred)
    return {
        "accuracy": float(accuracy_score(true, predicted)),
        "precision": float(precision_score(true, predicted, zero_division=0)),
        "recall": float(recall_score(true, predicted, zero_division=0)),
        "f1": float(f1_score(true, predicted, zero_division=0)),
        "TP": int(((true == 1) & (predicted == 1)).sum()),
        "FP": int(((true == 0) & (predicted == 1)).sum()),
        "FN": int(((true == 1) & (predicted == 0)).sum()),
        "TN": int(((true == 0) & (predicted == 0)).sum()),
    }


def label_distribution(labels: pd.Series) -> dict[str, float | int]:
    counts = labels.value_counts().sort_index().to_dict()
    total = int(len(labels))
    positives = int(counts.get(1, 0))
    return {"total": total, "negative": int(counts.get(0, 0)), "positive": positives,
            "positive_rate": positives / total}


def metric_table(metrics: dict[str, dict[str, float | int]]) -> str:
    lines = ["| Representation | TP | FP | FN | TN | Precision | Recall | F1 | Accuracy |",
             "|---|---|---|---|---|---|---|---|---|"]
    for name in ("Metric-based", "Token-based"):
        row = metrics[name]
        lines.append(
            f"| {name} | {row['TP']} | {row['FP']} | {row['FN']} | {row['TN']} | "
            f"{row['precision']:.4f} | {row['recall']:.4f} | {row['f1']:.4f} | {row['accuracy']:.4f} |"
        )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the frozen P35 Event A holdout once.")
    parser.add_argument("repo", type=Path, help="repository root")
    parser.add_argument("--out", type=Path, default=Path("event_a"))
    parser.add_argument("--verify-inputs", action="store_true", help="validate inputs without fitting a model")
    args = parser.parse_args()
    repo = args.repo.resolve()
    out = (repo / args.out).resolve() if not args.out.is_absolute() else args.out

    merged, training, holdout, manifest = validate_inputs(repo)
    if args.verify_inputs:
        print("Event A inputs validated; no model was fitted.")
        return
    predictions_path = out / "predictions.csv"
    if predictions_path.exists():
        raise SystemExit(f"refusing to overwrite existing Event A evidence: {predictions_path}")

    started = dt.datetime.now().astimezone()
    out.mkdir(parents=True, exist_ok=True)
    log_path = out / "run_log.txt"
    with log_path.open("w") as log_file:
        def log(message: str = "") -> None:
            print(message)
            log_file.write(message + "\n")
            log_file.flush()

        log("P35 Event A frozen project-disjoint holdout evaluation")
        log(f"started {started.isoformat(timespec='seconds')}")
        log(f"command: {' '.join(sys.argv)}")
        log(f"EVENT_A_PLAN: {EVENT_A_PLAN_COMMIT}")
        log(f"dataset blob SHA-1: {FROZEN_DATA_SHA}")
        log(f"split: training={len(training)}, excluded=0, holdout={len(holdout)}")
        log(f"projects: training={training['project_id_data'].nunique()}, holdout={holdout['project_id_data'].nunique()}")

        functions, lines = load_author_functions(repo / "scripts" / "godclass_metricbased.py")
        log("author metric functions: " + ", ".join(f"{name}@{line}" for name, line in sorted(lines.items(), key=lambda x: x[1])))
        features = compute_features(merged, functions)
        data = merged.merge(features, on="sample_id", how="left", validate="one_to_one")
        train = data.loc[data["assignment"] == "training"].sort_values("sample_id").reset_index(drop=True)
        test = data.loc[data["assignment"] == "holdout"].sort_values("sample_id").reset_index(drop=True)
        y_train = train["label"].to_numpy(dtype=int)
        y_test = test["label"].to_numpy(dtype=int)

        from imblearn.over_sampling import SMOTE
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.preprocessing import StandardScaler
        from sklearn.svm import SVC

        log(f"label distribution training={label_distribution(train['label'])}; holdout={label_distribution(test['label'])}")
        metric_scaler = StandardScaler()
        metric_train = metric_scaler.fit_transform(train[list(FEATURE_FUNCS)])
        metric_test = metric_scaler.transform(test[list(FEATURE_FUNCS)])
        metric_resampled, metric_y_resampled = SMOTE(random_state=SEED).fit_resample(metric_train, y_train)
        metric_model = SVC(probability=True, random_state=SEED).fit(metric_resampled, metric_y_resampled)
        metric_prediction = metric_model.predict(metric_test)
        log(f"metric: fit training={len(train)}, after_SMOTE={len(metric_y_resampled)}, evaluated={len(test)}")

        tfidf = TfidfVectorizer(ngram_range=(1, 1))
        token_train = tfidf.fit_transform(train["code_snippet"])
        token_test = tfidf.transform(test["code_snippet"])
        token_scaler = StandardScaler(with_mean=False)
        token_train = token_scaler.fit_transform(token_train)
        token_test = token_scaler.transform(token_test)
        token_resampled, token_y_resampled = SMOTE(random_state=SEED).fit_resample(token_train, y_train)
        token_model = SVC(probability=True, random_state=SEED).fit(token_resampled, token_y_resampled)
        token_prediction = token_model.predict(token_test)
        log(f"token: fit training={len(train)}, after_SMOTE={len(token_y_resampled)}, vocabulary={len(tfidf.vocabulary_)}, evaluated={len(test)}")

        predictions = test[["sample_id", "project_id_data", "link_data", "start_line_data", "end_line_data", "label"]].copy()
        predictions.columns = ["sample_id", "project_id", "link", "start_line", "end_line", "true_label"]
        predictions["metric_pred"] = metric_prediction.astype(int)
        predictions["token_pred"] = token_prediction.astype(int)
        predictions.to_csv(predictions_path, index=False)
        metrics = {"Metric-based": scores(y_test, metric_prediction), "Token-based": scores(y_test, token_prediction)}

        saved = pd.read_csv(predictions_path).sort_values("sample_id")
        if len(saved) != len(test) or not saved["sample_id"].is_unique:
            raise RuntimeError("saved prediction evidence does not contain one row per holdout sample")
        recomputed = {
            "Metric-based": scores(saved["true_label"].to_numpy(), saved["metric_pred"].to_numpy()),
            "Token-based": scores(saved["true_label"].to_numpy(), saved["token_pred"].to_numpy()),
        }
        if recomputed != metrics:
            raise RuntimeError("metrics recomputed from saved predictions differ from in-memory metrics")

        challenge = metrics["Metric-based"]["f1"] <= metrics["Token-based"]["f1"]
        outcome = "CHALLENGED" if challenge else "SUPPORTED"
        metrics_document = {
            "event": "P35 Event A",
            "event_a_plan_commit": EVENT_A_PLAN_COMMIT,
            "dataset_git_blob_sha1": FROZEN_DATA_SHA,
            "split": {"training_samples": int(len(train)), "excluded_samples": 0, "heldout_samples": int(len(test)),
                      "training_projects": int(train["project_id_data"].nunique()), "heldout_projects": int(test["project_id_data"].nunique())},
            "label_distribution": {"training": label_distribution(train["label"]), "holdout": label_distribution(test["label"])},
            "metrics": metrics,
            "preregistered_challenge_criterion": "Metric positive-class F1 <= Token positive-class F1 on holdout",
            "prediction_outcome": outcome,
            "m2_baselines": M2_BASELINES,
            "saved_prediction_sha256": hashlib.sha256(predictions_path.read_bytes()).hexdigest(),
            "validation": {"input_and_manifest": "passed", "project_disjointness": "passed", "exact_snippet_non_overlap": "passed",
                           "metrics_recomputed_from_saved_predictions": "passed"},
        }
        (out / "metrics.json").write_text(json.dumps(metrics_document, indent=2) + "\n")

        import imblearn
        import javalang
        import sklearn
        environment = [
            f"run_started: {started.isoformat(timespec='seconds')}",
            f"command: {' '.join(sys.argv)}",
            f"repo_head: {git(repo, 'rev-parse', 'HEAD').stdout.strip()}",
            f"event_a_plan_commit: {EVENT_A_PLAN_COMMIT}",
            f"dataset: data/god_class_df.csv sha={FROZEN_DATA_SHA} rows={len(data)}",
            f"python: {sys.version.split()[0]} ({platform.platform()})",
            f"numpy: {np.__version__}", f"pandas: {pd.__version__}", f"scikit-learn: {sklearn.__version__}",
            f"imbalanced-learn: {imblearn.__version__}", f"javalang: {javalang.__version__}",
            "method: frozen M2 SVC(probability=True, random_state=42); SMOTE(random_state=42)",
            "metric scaler: StandardScaler(); token vectorizer: TfidfVectorizer(ngram_range=(1, 1)); token scaler: StandardScaler(with_mean=False)",
        ]
        (out / "environment.txt").write_text("\n".join(environment) + "\n")

        result_lines = [
            "# P35 Event A held-out evaluation", "",
            f"Generated by `run_holdout.py` on {started.isoformat(timespec='seconds')}. Input was frozen by `EVENT_A_PLAN` at `{EVENT_A_PLAN_COMMIT[:7]}`.",
            f"Raw evidence: `predictions.csv` (SHA-256 `{metrics_document['saved_prediction_sha256']}`).", "",
            "## Split and labels", "",
            f"Training: {len(train)} samples from {train['project_id_data'].nunique()} projects; excluded: 0. Holdout: {len(test)} samples from {test['project_id_data'].nunique()} projects.",
            f"Holdout labels: {label_distribution(test['label'])}. The holdout is project-disjoint for Event A training, but not wholly independent of earlier M2 cross-validation.", "",
            "## Event A results", "", metric_table(metrics), "",
            f"**Preregistered outcome: {outcome}.** The challenge criterion was Metric positive-class F1 <= Token positive-class F1; it is {'met' if challenge else 'not met'}.", "",
            "## M2 comparisons", "",
            "The primary M2 bounded result was a tie: Metric F1 0.6667 and Token F1 0.6667, therefore NOT REPRODUCED under its frozen rule.",
            "The secondary M2 full-dataset ten-fold CV mean F1 was Metric 0.6379 and Token 0.4135. These are context baselines, not an independent held-out comparison.", "",
            "## Evidence validation", "",
            "The dataset blob SHA, manifest assignments, project disjointness, and exact-snippet non-overlap were checked before fitting. Metrics were independently recomputed from the saved prediction CSV and matched the reported values.",
            "The scalers, TF-IDF vocabulary, SMOTE, and SVC models were fitted once using training samples only.",
        ]
        (out / "results.md").write_text("\n".join(result_lines) + "\n")
        log(metric_table(metrics))
        log(f"preregistered outcome: {outcome}")
        log(f"finished {dt.datetime.now().astimezone().isoformat(timespec='seconds')}")


if __name__ == "__main__":
    main()
