"""
CS4928 P35 - M2 bounded reproduction (Week 6 Lab 4 / M2)

Runs the frozen M1 plan:
  RQ1  Metric-based vs Token-based (TF-IDF) representation, both with
       SVC(probability=True, random_state=42), on the same 10 folds
       (KFold, shuffle=True, random_state=42) over all 2,148 samples.
       Per fold: scaler fitted on the training fold only, SMOTE(random_state=42)
       on the training fold only, TF-IDF vocabulary fitted on the training fold only.
       Main result = F1 (label 1 = God Class) from the test-fold predictions of
       the 12 frozen cases.

The script produces evidence files only. It does NOT apply the decision rule:
the group reads results.md and records REPRODUCED / NOT REPRODUCED / BLOCKED.

Usage (from anywhere):
    python3 run_reproduction.py <path-to-repo> --out <output-folder>           # full run
    python3 run_reproduction.py <path-to-repo> --out <output-folder> --pilot   # fold 1 only

Outputs (full run):
    predictions.csv     raw evidence: every sample, fold, true label, both predictions
    fold_metrics.csv    raw evidence: per-fold accuracy/precision/recall/F1 for both arms
    results.md          derived results, laid out so any number traces back to rows
    disagreements.csv   all Metric-vs-Token disagreements in sample_id order (RQ2 input)
    environment.txt     versions, command, input identity
    run_log.txt         full console log of this run
"""
import argparse
import datetime as dt
import hashlib
import platform
import subprocess
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

# ------------------------------------------------------------- frozen M1 plan
FROZEN_COMMIT = "a96779829fc5ea641089afdb161298f4da3962ae"
FROZEN_DATA_SHA = "6e1075ead90054ff9955cf310842c0d31a41e5dc"   # git blob SHA
FROZEN_IDS = [3698323, 3699849, 3700666, 3702984, 3705164, 3710201,
              3711605, 3715636, 3717506, 3721456, 3723043, 3725605]
SENSITIVITY_EXCLUDE = 3711605        # conflicting-label duplicate (twin: 7450485)
SEED = 42
N_FOLDS = 10
PAPER_TABLE2_SVM = {                 # paper Section 6.1, Table 2, SVM row
    "Metric-based": {"accuracy": 0.8054, "precision": 0.5319, "recall": 0.8172, "f1": 0.6400},
    "Token-based":  {"accuracy": 0.5754, "precision": 0.2965, "recall": 0.7089, "f1": 0.4143},
}
FEATURE_FUNCS = {                    # authors' 7 features (script line ~858) -> function
    "count_methods": "count_methods",
    "count_fields": "count_fields",
    "tcc": "calculate_tcc",
    "cyclomatic_complexity": "calculate_cyclomatic_complexity",
    "loc": "count_lines_of_code",
    "atfd": "calculate_atfd",
    "lcom5": "calculate_lcom5",
}

# ------------------------------------------------------------------- args/log
ap = argparse.ArgumentParser()
ap.add_argument("repo", help="path to the cloned MLCQ-GodClass-CodeRepresentation repo")
ap.add_argument("--out", default="m2", help="output folder (default: ./m2)")
ap.add_argument("--pilot", action="store_true", help="pipeline check: run fold 1 only")
args = ap.parse_args()

REPO = Path(args.repo).resolve()
OUT = Path(args.out).resolve()
OUT.mkdir(parents=True, exist_ok=True)
PREFIX = "pilot_" if args.pilot else ""
LOG = open(OUT / f"{PREFIX}run_log.txt", "w")


def log(msg=""):
    print(msg)
    LOG.write(msg + "\n")
    LOG.flush()


def git(*a):
    return subprocess.run(["git", "-C", str(REPO), *a], capture_output=True, text=True)


started = dt.datetime.now().astimezone()
log(f"P35 M2 reproduction - {'PILOT (fold 1 only)' if args.pilot else 'FULL RUN'}")
log(f"started {started.isoformat(timespec='seconds')}")
log(f"command: python3 {' '.join(sys.argv)}")

# ----------------------------------------------------------- 1. input identity
log("\n=== 1. Input identity ===")
head = git("rev-parse", "HEAD").stdout.strip()
in_history = git("merge-base", "--is-ancestor", FROZEN_COMMIT, "HEAD").returncode == 0
unchanged = git("diff", "--quiet", FROZEN_COMMIT, "HEAD", "--", "data", "scripts").returncode == 0
csv_path = REPO / "data" / "god_class_df.csv"
raw = csv_path.read_bytes()
data_sha = hashlib.sha1(b"blob %d\0" % len(raw) + raw).hexdigest()
log(f"repo HEAD: {head}")
log(f"frozen commit {FROZEN_COMMIT} in history: {in_history}")
log(f"data/ and scripts/ unchanged since frozen commit: {unchanged}")
log(f"dataset SHA: {data_sha} (expected {FROZEN_DATA_SHA})")
if not (in_history and unchanged and data_sha == FROZEN_DATA_SHA):
    log("STOP: input does not match the frozen M1 plan -> status INCONCLUSIVE/BLOCKED")
    sys.exit(1)

df = pd.read_csv(csv_path)
log(f"rows: {len(df)}; labels: {df['label'].value_counts().sort_index().to_dict()}")
missing = sorted(set(FROZEN_IDS) - set(df["sample_id"]))
if missing:
    log(f"STOP: frozen IDs missing from dataset: {missing}")
    sys.exit(1)

# ------------------------------------------------- 2. metric-based features
log("\n=== 2. Metric-based features (authors' functions, used unchanged) ===")


def load_author_functions(script):
    """The authors' file is a Colab export (notebook '!' commands, pasted HTML),
    so it cannot be imported. Each needed top-level 'def' block is cut out by
    indentation and executed on its own; function bodies are used as written."""
    lines = script.read_text().splitlines()
    wanted = set(FEATURE_FUNCS.values())
    ns, found = {}, {}
    exec("import javalang", ns)
    for i, line in enumerate(lines):
        if not line.startswith("def "):
            continue
        name = line[4:].split("(")[0].strip()
        if name not in wanted:
            continue
        block = [line]
        for nxt in lines[i + 1:]:
            if nxt.strip() and not nxt[0].isspace():
                break
            block.append(nxt)
        exec("\n".join(block), ns)
        found[name] = i + 1          # last definition wins, as in the notebook
    missing_fn = wanted - set(found)
    if missing_fn:
        raise RuntimeError(f"author functions not found: {missing_fn}")
    return {k: ns[k] for k in wanted}, found


funcs, linenos = load_author_functions(REPO / "scripts" / "godclass_metricbased.py")
log("loaded: " + ", ".join(f"{n}@line {l}" for n, l in sorted(linenos.items(), key=lambda x: x[1])))

rows, failures = [], []
for sid, code in zip(df["sample_id"], df["code_snippet"]):
    try:
        rows.append({"sample_id": sid, **{c: funcs[f](code) for c, f in FEATURE_FUNCS.items()}})
    except Exception as e:                       # recorded, never silently dropped
        failures.append((sid, f"{type(e).__name__}: {str(e)[:80]}"))
log(f"features computed: {len(rows)} ok, {len(failures)} failed")
if failures:
    for sid, err in failures:
        log(f"  feature failure {sid}: {err}")
    log("STOP: the M1 plan has no exclusion rule for feature failures -> record a "
        "deviation before re-running. Status INCONCLUSIVE/BLOCKED.")
    sys.exit(1)

data = df.merge(pd.DataFrame(rows), on="sample_id", how="left")   # keeps CSV order
assert len(data) == len(df)
y = data["label"].to_numpy()
X_metric = data[list(FEATURE_FUNCS)].to_numpy(dtype=float)
snippets = data["code_snippet"]

# ------------------------------------------------- 3. cross-validated runs
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.model_selection import KFold
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from imblearn.over_sampling import SMOTE


def fit_predict(X_train, y_train, X_test, scaler):
    X_train = scaler.fit_transform(X_train)                  # training fold only
    X_test = scaler.transform(X_test)
    X_res, y_res = SMOTE(random_state=SEED).fit_resample(X_train, y_train)  # training only
    model = SVC(probability=True, random_state=SEED).fit(X_res, y_res)
    return model.predict(X_test), len(y_res)


def scores(y_true, y_pred):
    return {
        "accuracy": accuracy_score(y_true, y_pred),
        "precision": precision_score(y_true, y_pred, zero_division=0),
        "recall": recall_score(y_true, y_pred, zero_division=0),
        "f1": f1_score(y_true, y_pred, zero_division=0),
    }


log("\n=== 3. Cross-validation ===")
log(f"KFold(n_splits={N_FOLDS}, shuffle=True, random_state={SEED}); "
    f"SMOTE(random_state={SEED}); SVC(probability=True, random_state={SEED})")
log("TF-IDF: TfidfVectorizer(ngram_range=(1, 1)) fitted per training fold; "
    "scaled with StandardScaler(with_mean=False)")

pred_rows, fold_rows = [], []
splits = list(KFold(n_splits=N_FOLDS, shuffle=True, random_state=SEED).split(data))
if args.pilot:
    splits = splits[:1]

for k, (tr, te) in enumerate(splits, start=1):
    t0 = time.time()
    m_pred, m_n = fit_predict(X_metric[tr], y[tr], X_metric[te], StandardScaler())
    tfidf = TfidfVectorizer(ngram_range=(1, 1))
    Xt_tr = tfidf.fit_transform(snippets.iloc[tr])
    Xt_te = tfidf.transform(snippets.iloc[te])
    t_pred, t_n = fit_predict(Xt_tr, y[tr], Xt_te, StandardScaler(with_mean=False))
    for i, mp, tp in zip(te, m_pred, t_pred):
        pred_rows.append({"sample_id": int(data.at[i, "sample_id"]), "fold": k,
                          "true_label": int(y[i]), "metric_pred": int(mp),
                          "token_pred": int(tp)})
    for arm, p in (("Metric-based", m_pred), ("Token-based", t_pred)):
        fold_rows.append({"fold": k, "representation": arm, **scores(y[te], p)})
    log(f"fold {k:2d}: train={len(tr)} (after SMOTE {m_n}), test={len(te)}, "
        f"vocab={len(tfidf.vocabulary_)}, frozen cases in fold="
        f"{sorted(set(data.loc[te, 'sample_id']) & set(FROZEN_IDS))}, "
        f"{time.time() - t0:.0f}s")

preds = pd.DataFrame(pred_rows).sort_values("sample_id").reset_index(drop=True)
folds = pd.DataFrame(fold_rows)
preds.to_csv(OUT / f"{PREFIX}predictions.csv", index=False)
folds.to_csv(OUT / f"{PREFIX}fold_metrics.csv", index=False)
log(f"\nwrote {PREFIX}predictions.csv ({len(preds)} rows) and {PREFIX}fold_metrics.csv")

# ------------------------------------------------- environment record
import imblearn
import javalang
import sklearn

env = [
    f"run_started: {started.isoformat(timespec='seconds')}",
    f"command: python3 {' '.join(sys.argv)}",
    f"mode: {'pilot (fold 1 only)' if args.pilot else 'full (10 folds)'}",
    f"repo_head: {head}",
    f"frozen_commit: {FROZEN_COMMIT}",
    f"dataset: data/god_class_df.csv  sha={data_sha}  rows={len(df)}",
    f"python: {sys.version.split()[0]}  ({platform.platform()})",
    f"numpy: {np.__version__}",
    f"pandas: {pd.__version__}",
    f"scikit-learn: {sklearn.__version__}",
    f"imbalanced-learn: {imblearn.__version__}",
    f"javalang: {getattr(javalang, '__version__', 'n/a')}",
    f"seed: {SEED} (KFold, SMOTE, SVC)",
    "metric zero_division: 0 (a model predicting no positives gets precision/F1 = 0)",
]
(OUT / f"{PREFIX}environment.txt").write_text("\n".join(env) + "\n")

if args.pilot:
    ok = (len(preds) == len(splits[0][1]) and preds[["metric_pred", "token_pred"]].isin([0, 1]).all().all())
    log(f"\nPILOT {'PASSED' if ok else 'FAILED'}: both pipelines produced one valid prediction "
        "per test-fold sample. Scores are in pilot_fold_metrics.csv; they are NOT a result.")
    LOG.close()
    sys.exit(0 if ok else 1)

# ------------------------------------------------- 4. derived results
assert len(preds) == len(df) and preds["sample_id"].is_unique, "every sample must be predicted once"


def confusion(y_true, y_pred):
    yt, yp = np.asarray(y_true), np.asarray(y_pred)
    return {"TP": int(((yt == 1) & (yp == 1)).sum()), "FP": int(((yt == 0) & (yp == 1)).sum()),
            "FN": int(((yt == 1) & (yp == 0)).sum()), "TN": int(((yt == 0) & (yp == 0)).sum())}


def block(subset):
    out = {}
    for arm, col in (("Metric-based", "metric_pred"), ("Token-based", "token_pred")):
        out[arm] = {**scores(subset["true_label"], subset[col]),
                    **confusion(subset["true_label"], subset[col])}
    return out


meta = df.set_index("sample_id")
frozen = preds.set_index("sample_id").loc[FROZEN_IDS].reset_index()
frozen["file"] = frozen["sample_id"].map(
    lambda s: meta.at[s, "link"].split("/")[-1].split("#")[0])
main = block(frozen)
sens = block(frozen[frozen["sample_id"] != SENSITIVITY_EXCLUDE])
fold_avg = folds.groupby("representation")[["accuracy", "precision", "recall", "f1"]].mean()
pooled_all = block(preds)

dis = preds[preds["metric_pred"] != preds["token_pred"]].copy()
dis = dis.merge(df[["sample_id", "link", "start_line", "end_line"]], on="sample_id", how="left")
dis = dis.sort_values("sample_id")
dis.insert(0, "order", range(1, len(dis) + 1))
dis.to_csv(OUT / "disagreements.csv", index=False)


def f4(x):
    return f"{x:.4f}"


def score_table(b):
    lines = ["| Representation | TP | FP | FN | TN | Precision | Recall | F1 | Accuracy |",
             "|---|---|---|---|---|---|---|---|---|"]
    for arm, s in b.items():
        lines.append(f"| {arm} | {s['TP']} | {s['FP']} | {s['FN']} | {s['TN']} | "
                     f"{f4(s['precision'])} | {f4(s['recall'])} | {f4(s['f1'])} | {f4(s['accuracy'])} |")
    return "\n".join(lines)


md = [
    "# P35 M2 bounded reproduction - results",
    "",
    f"Generated by `run_reproduction.py` on {started.isoformat(timespec='seconds')} "
    f"(see `environment.txt`, `run_log.txt`).",
    f"Input: `data/god_class_df.csv` (SHA `{data_sha}`) at frozen commit `{FROZEN_COMMIT[:7]}`; repo HEAD `{head[:7]}`.",
    "Raw evidence: `predictions.csv` (one row per sample) and `fold_metrics.csv` (one row per fold per representation).",
    "",
    "## 1. The 12 frozen cases (copied from predictions.csv)",
    "",
    "| sample_id | file | fold | true label | Metric pred | Token pred |",
    "|---|---|---|---|---|---|",
]
for r in frozen.itertuples():
    md.append(f"| {r.sample_id} | {r.file} | {r.fold} | {r.true_label} | {r.metric_pred} | {r.token_pred} |")
md += [
    "",
    "## 2. Main RQ1 result: F1 on the 12 frozen cases (label 1 = God Class)",
    "",
    "Counts come directly from the rows in section 1. "
    "Precision = TP/(TP+FP), Recall = TP/(TP+FN), F1 = 2·P·R/(P+R); 0 if undefined.",
    "",
    score_table(main),
    "",
    "### Frozen M1 decision rule (applied by the group, not by this script)",
    "",
    "- REPRODUCED: Metric F1 > Token F1 on the 12 frozen cases.",
    "- NOT REPRODUCED: a valid completed run gives Metric F1 <= Token F1 (a tie counts as not reproduced).",
    "- INCONCLUSIVE / BLOCKED: the run cannot be completed or is not valid.",
    "",
    "**Status (group to fill in):** ______  ",
    "**Recorded by / date:** ______",
    "",
    f"## 3. Sensitivity check (secondary, not the decision): 12 cases without {SENSITIVITY_EXCLUDE}",
    "",
    f"{SENSITIVITY_EXCLUDE} has an identical code snippet (sample 7450485) with the opposite label.",
    "",
    score_table(sens),
    "",
    "## 4. Comparison with the paper (secondary): all 2,148 samples",
    "",
    "The paper averages each metric across the 10 folds. Same method here, from `fold_metrics.csv`.",
    "",
    "| Representation | Accuracy (ours / paper) | Precision (ours / paper) | Recall (ours / paper) | F1 (ours / paper) |",
    "|---|---|---|---|---|",
]
for arm in ("Metric-based", "Token-based"):
    o, p = fold_avg.loc[arm], PAPER_TABLE2_SVM[arm]
    md.append(f"| {arm} | {f4(o['accuracy'])} / {f4(p['accuracy'])} | {f4(o['precision'])} / {f4(p['precision'])} | "
              f"{f4(o['recall'])} / {f4(p['recall'])} | {f4(o['f1'])} / {f4(p['f1'])} |")
md += [
    "",
    "For reference, the same predictions pooled over all 2,148 samples (not the paper's averaging method):",
    "",
    score_table(pooled_all),
    "",
    "## 5. RQ2 input",
    "",
    f"`disagreements.csv` lists all {len(dis)} samples where the two representations predict "
    "different labels, in sample_id order. Per the M1 rule, RQ2 inspects the first 10 that can be checked.",
    "",
    "## 6. Implementation notes",
    "",
    "- SVC(probability=True, random_state=42), SMOTE(random_state=42), KFold(10, shuffle=True, random_state=42).",
    "- Scaler, TF-IDF vocabulary and SMOTE are fitted on the training fold only.",
    "- The 7 metric features use the authors' functions unchanged (author TCC/LCOM5 definitions kept).",
    "- zero_division=0: a model with no positive predictions gets precision and F1 of 0.",
]
(OUT / "results.md").write_text("\n".join(md) + "\n")

log(f"wrote results.md and disagreements.csv ({len(dis)} disagreements)")
log(f"finished {dt.datetime.now().astimezone().isoformat(timespec='seconds')}")
log("Next: open results.md, check section 1 against predictions.csv, then apply the frozen decision rule.")
LOG.close()
