"""
P35 M4 - detector check(to check if the SVM will still predict C as a god class or not after we refactored the class)

Question: does the frozen M2 metric-based SVM still flag ExoPlayer `C` (sample 3788627)
after the Move Method refactoring? Prediction (recorded in m4/README.md, commit f1fa605,
BEFORE this check): yes, because 164 fields and ~900 LOC are unchanged.

Method (frozen M2 metric pipeline, unchanged):
  - 7 features from the authors' own functions (count_methods, count_fields, tcc,
    cyclomatic_complexity, loc, atfd, lcom5)
  - StandardScaler -> SMOTE(random_state=42) -> SVC(probability=True, random_state=42)
  - Trained on all 2,147 dataset samples EXCEPT 3788627, so the model has never seen `C`
    (same principle as M2's test-fold prediction).
  - Scored on the class body (line 39 to end) of m4/before/C.java and m4/after/C.java,
    i.e. the same span as the dataset sample.

Usage (from the repo root):
    python3 m4/detector_check.py . | tee m4/detector_check.txt
"""
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

REPO = Path(sys.argv[1]).resolve()
SAMPLE_ID = 3788627
CLASS_START_LINE = 39          # dataset sample range for C is lines 39-1015
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


def load_author_functions(script):
    """Cut the authors' metric functions out of their Colab export and run them unchanged
    (same extraction as m2/run_reproduction.py)."""
    lines = script.read_text().splitlines()
    wanted = set(FEATURE_FUNCS.values())
    ns = {}
    exec("import javalang", ns)
    for i, line in enumerate(lines):
        if line.startswith("def ") and line[4:].split("(")[0].strip() in wanted:
            block = [line]
            for nxt in lines[i + 1:]:
                if nxt.strip() and not nxt[0].isspace():
                    break
                block.append(nxt)
            exec("\n".join(block), ns)
    return {k: ns[k] for k in wanted}


def features(code, funcs):
    return {col: funcs[fn](code) for col, fn in FEATURE_FUNCS.items()}


def class_body(path):
    return "\n".join(Path(path).read_text().splitlines()[CLASS_START_LINE - 1:])


funcs = load_author_functions(REPO / "scripts" / "godclass_metricbased.py")
df = pd.read_csv(REPO / "data" / "god_class_df.csv")

# Sanity check: before/C.java lines 39-1015 must be the frozen dataset sample.
before_code = class_body(REPO / "m4" / "before" / "C.java")
dataset_code = df.loc[df.sample_id == SAMPLE_ID, "code_snippet"].iloc[0]
same_text = before_code.strip() == dataset_code.strip()
print(f"before/C.java (L{CLASS_START_LINE}-end) identical to dataset sample {SAMPLE_ID}: {same_text}")

# Train the frozen M2 metric pipeline on every sample except C.
train = df[df.sample_id != SAMPLE_ID].reset_index(drop=True)
X = pd.DataFrame([features(c, funcs) for c in train.code_snippet])[list(FEATURE_FUNCS)].to_numpy(float)
y = train.label.to_numpy()

from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from imblearn.over_sampling import SMOTE

scaler = StandardScaler().fit(X)
X_res, y_res = SMOTE(random_state=SEED).fit_resample(scaler.transform(X), y)
model = SVC(probability=True, random_state=SEED).fit(X_res, y_res)
print(f"trained on {len(train)} samples (excluding {SAMPLE_ID}); after SMOTE: {len(y_res)}\n")

rows = []
for name, path in (("before", REPO / "m4" / "before" / "C.java"),
                   ("after", REPO / "m4" / "after" / "C.java")):
    f = features(class_body(path), funcs)
    x = scaler.transform(np.array([[f[c] for c in FEATURE_FUNCS]], dtype=float))
    rows.append({"version": name, **f,
                 "prediction": int(model.predict(x)[0]),
                 "P(God Class)": round(float(model.predict_proba(x)[0, 1]), 4),
                 "decision_value": round(float(model.decision_function(x)[0]), 4)})

out = pd.DataFrame(rows).set_index("version")
print(out.T.to_string())
print("\nprediction: 1 = flagged as God Class, 0 = not flagged")
print("decision_value: distance from the SVM boundary (> 0 means the God Class side)")

import sklearn, imblearn
print(f"\nversions: python {sys.version.split()[0]}, scikit-learn {sklearn.__version__}, "
      f"imbalanced-learn {imblearn.__version__}, numpy {np.__version__}, pandas {pd.__version__}")