"""
CS4928 P35 - M1 feasibility check (Week 5, before M1_PLAN freeze)

Purpose: show that the released artefact is accessible and that the first
essential step of BOTH representations can execute. It deliberately does NOT
print F1 / accuracy / predictions, so no result is seen before the plan freezes.

Usage (from anywhere):
    python3 m1_feasibility_check.py /path/to/MLCQ-GodClass-CodeRepresentation

Requires: pandas, scikit-learn, imbalanced-learn, javalang
"""
import ast
import hashlib
import subprocess
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

REPO = Path(sys.argv[1]).resolve()
CSV = REPO / "data" / "god_class_df.csv"
SCRIPT = REPO / "scripts" / "godclass_metricbased.py"

EXPECTED_COMMIT = "a96779829fc5ea641089afdb161298f4da3962ae"
EXPECTED_DATA_SHA = "6e1075ead90054ff9955cf310842c0d31a41e5dc"  # git blob SHA
FROZEN_IDS = [3698323, 3699849, 3700666, 3702984, 3705164, 3710201,
              3711605, 3715636, 3717506, 3721456, 3723043, 3725605]
SEED = 42

# The 7 features used by the authors (script line ~858), and the functions
# that compute them. Functions are loaded VERBATIM from the authors' script.
FEATURE_FUNCS = {
    "count_methods": "count_methods",
    "count_fields": "count_fields",
    "tcc": "calculate_tcc",
    "cyclomatic_complexity": "calculate_cyclomatic_complexity",
    "loc": "count_lines_of_code",
    "atfd": "calculate_atfd",
    "lcom5": "calculate_lcom5",
}

results = []  # (check, status, detail)


def record(check, ok, detail):
    status = "PASS" if ok else "FAIL"
    results.append((check, status, detail))
    print(f"[{status}] {check}: {detail}")


def git_blob_sha(path):
    data = path.read_bytes()
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


def load_author_functions():
    """Pull the 7 metric functions out of the Colab export without running it.
    The file as a whole is not valid Python (notebook '!' commands and pasted
    HTML/CSS), so each top-level 'def' block is cut out by indentation and
    executed on its own. The function bodies are used exactly as written."""
    lines = SCRIPT.read_text().splitlines()
    wanted = set(FEATURE_FUNCS.values())
    found, ns = {}, {}
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
        ast.parse("\n".join(block))  # confirm the extracted block is valid Python
        exec("\n".join(block), ns)
        found[name] = i + 1  # last definition wins, as in the notebook
    return {k: ns[k] for k in wanted if k in ns}, found


# ---------------------------------------------------------------- 1. artefact
print("=== 1. Artefact access and version ===")
commit = subprocess.run(["git", "-C", str(REPO), "rev-parse", "HEAD"],
                        capture_output=True, text=True).stdout.strip()
record("Repository commit", commit == EXPECTED_COMMIT, commit)
sha = git_blob_sha(CSV)
record("Dataset SHA (git blob)", sha == EXPECTED_DATA_SHA, sha)

df = pd.read_csv(CSV)
record("Dataset loads", True, f"{df.shape[0]} rows x {df.shape[1]} cols: {list(df.columns)}")
record("Row count = 2,148 (paper)", len(df) == 2148, str(len(df)))
counts = df["label"].value_counts().to_dict()
record("Class balance 1,687 / 461 (paper)",
       counts.get(0) == 1687 and counts.get(1) == 461, str(counts))
record("sample_id unique", df["sample_id"].is_unique,
       f"{df['sample_id'].nunique()} unique of {len(df)}")
record("Code snippet present for all rows",
       df["code_snippet"].notna().all() and (df["code_snippet"].str.strip() != "").all(),
       f"{df['code_snippet'].isna().sum()} missing")
metric_cols = [c for c in FEATURE_FUNCS if c in df.columns]
print(f"NOTE: precomputed metric columns in CSV: {metric_cols or 'none'} "
      "-> the 7 features must be computed from code_snippet.")

# ----------------------------------------------------- 2. frozen sample check
print("\n=== 2. Frozen 12 sample IDs ===")
present = [i for i in FROZEN_IDS if i in set(df["sample_id"])]
record("All 12 frozen IDs present", len(present) == 12, f"{len(present)}/12")
first12 = sorted(df["sample_id"])[:12]
record("Frozen IDs = first 12 by sample_id", first12 == FROZEN_IDS,
       "match" if first12 == FROZEN_IDS else f"first 12 are {first12}")
frozen = df.set_index("sample_id").loc[FROZEN_IDS]
print(frozen.assign(file=frozen["link"].str.split("/").str[-1].str.split("#").str[0])
      [["file", "start_line", "end_line", "label"]].to_string())

# conflicting-label duplicates (known limitation, e.g. 3711605)
dup = df[df.duplicated("code_snippet", keep=False)]
conflict_groups = dup.groupby("code_snippet")["label"].nunique()
conflict_snips = conflict_groups[conflict_groups > 1].index
conflicting = df[df["code_snippet"].isin(conflict_snips)]
print(f"\nDuplicate code snippets: {dup['code_snippet'].nunique()} groups "
      f"({len(dup)} rows); with conflicting labels: {len(conflict_snips)} groups "
      f"({len(conflicting)} rows)")
frozen_conflict = sorted(set(FROZEN_IDS) & set(conflicting["sample_id"]))
for sid in frozen_conflict:
    snip = df.loc[df.sample_id == sid, "code_snippet"].iloc[0]
    twins = df[df.code_snippet == snip][["sample_id", "label"]].values.tolist()
    print(f"  frozen case {sid} has conflicting twins [sample_id, label]: {twins}")

# ------------------------------------------- 3. metric-based feature extraction
print("\n=== 3. Metric-based: compute the 7 features (authors' own functions) ===")
funcs, linenos = load_author_functions()
record("Author metric functions loaded", len(funcs) == 7,
       ", ".join(f"{n}@line {l}" for n, l in sorted(linenos.items(), key=lambda x: x[1])))

feats, failures = [], []
for sid, code in zip(df["sample_id"], df["code_snippet"]):
    row = {"sample_id": sid}
    try:
        for col, fn in FEATURE_FUNCS.items():
            row[col] = funcs[fn](code)
        feats.append(row)
    except Exception as e:  # record, never silently drop
        failures.append((sid, f"{type(e).__name__}: {str(e)[:60]}"))
feat_df = pd.DataFrame(feats)
record("Features computed for all 2,148 samples", not failures,
       f"{len(feat_df)} ok, {len(failures)} failed")
for sid, err in failures[:10]:
    print(f"  failed sample {sid}: {err}")
frozen_fail = [sid for sid, _ in failures if sid in FROZEN_IDS]
record("Features computed for all 12 frozen cases", not frozen_fail,
       f"failed: {frozen_fail or 'none'}")
print(feat_df.set_index("sample_id").loc[[i for i in FROZEN_IDS if i not in frozen_fail]]
      .to_string())

# ----------------------------------------------- 4. one-fold pipeline smoke test
print("\n=== 4. One-fold smoke test (no scores printed) ===")
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import KFold
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from imblearn.over_sampling import SMOTE

data = df.merge(feat_df, on="sample_id", how="inner").reset_index(drop=True)
y = data["label"].values
train_idx, test_idx = next(KFold(n_splits=10, shuffle=True, random_state=SEED).split(data))
print(f"Fold 1: train={len(train_idx)}, test={len(test_idx)} "
      f"(frozen cases in this test fold: "
      f"{sorted(set(data.loc[test_idx, 'sample_id']) & set(FROZEN_IDS))})")

def run_arm(name, X_train, X_test, scaler):
    X_train = scaler.fit_transform(X_train)   # fit on training fold only
    X_test = scaler.transform(X_test)
    Xs, ys = SMOTE(random_state=SEED).fit_resample(X_train, y[train_idx])  # train only
    model = SVC(probability=True, random_state=SEED).fit(Xs, ys)
    pred = model.predict(X_test)
    ok = len(pred) == len(test_idx) and set(np.unique(pred)) <= {0, 1}
    record(f"{name} pipeline runs end to end", ok,
           f"train {X_train.shape} -> after SMOTE {Xs.shape}, "
           f"{len(pred)} test predictions produced (values withheld until M2)")

# Metric-based arm
X_metric = data[list(FEATURE_FUNCS)].values
run_arm("Metric-based (7 features) + SVM",
        X_metric[train_idx], X_metric[test_idx], StandardScaler())

# Token-based arm: TF-IDF, default tokenizer, unigrams; vocabulary from train fold only
tfidf = TfidfVectorizer(ngram_range=(1, 1))
Xt_train = tfidf.fit_transform(data.loc[train_idx, "code_snippet"])
Xt_test = tfidf.transform(data.loc[test_idx, "code_snippet"])
print(f"TF-IDF vocabulary (train fold only): {len(tfidf.vocabulary_)} unigrams")
run_arm("Token-based (TF-IDF) + SVM", Xt_train, Xt_test, StandardScaler(with_mean=False))

# ------------------------------------------------------------------ summary
import sklearn, imblearn, javalang  # noqa
print("\n=== Environment ===")
print(f"python {sys.version.split()[0]} | pandas {pd.__version__} | numpy {np.__version__} | "
      f"scikit-learn {sklearn.__version__} | imbalanced-learn {imblearn.__version__} | "
      f"javalang {getattr(javalang, '__version__', 'n/a')}")

print("\n=== Summary ===")
fails = [r for r in results if r[1] == "FAIL"]
print(f"{len(results) - len(fails)}/{len(results)} checks passed")
for c, s, d in fails:
    print(f"  FAIL - {c}: {d}")
