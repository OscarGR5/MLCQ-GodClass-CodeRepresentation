# P35 - Deviations, threats and AI-use log

Running log for the P35 reproduction. Entries are added, never rewritten: if something
changes, add a new dated entry that refers back to the old one.
Frozen plan: M1 doc (Google Docs, named version "M1_PLAN") + repo tag `M1_PLAN` (commit `1af8ea4`).

Format per entry: **what** changed / was found · **why** · **effect on interpretation** · **evidence**.

---

## Deviations from the original study

### D1 - SMOTE seed fixed to 42 (recorded at M1, 8 Oct)
- **What:** `SMOTE(random_state=42)`.
- **Why:** the paper says a fixed seed was used, but the released script leaves SMOTE unseeded, so runs are not repeatable.
- **Effect:** small run-to-run differences vs the authors are possible; ours is fully repeatable.
- **Evidence:** `m2/run_reproduction.py`, `m2/environment.txt`.

### D2 - SVC random_state fixed to 42 (recorded at M1, 8 Oct)
- **What:** `SVC(probability=True, random_state=42)`; the authors used `SVC(probability=True)` without a seed.
- **Why:** repeatability (`probability=True` uses internal randomness).
- **Effect:** none on the method; makes reruns identical.
- **Evidence:** `m2/run_reproduction.py`.

### D3 - Token-based pipeline rebuilt from the paper (recorded at M1, 8 Oct)
- **What:** the repo contains no token-based code; we rebuilt it from the paper's description (TF-IDF, default scikit-learn tokenizer, unigrams), with the vocabulary fitted on training folds only and `StandardScaler(with_mean=False)`.
- **Why:** the original script is not available.
- **Effect:** our token arm may differ from the authors'.
- **Update 18 Oct:** our full-data fold-averaged Token SVM results closely match Table 2 (F1 0.4135 vs 0.4143; accuracy 0.5777 vs 0.5754), which limits this threat.
- **Evidence:** `m2/results.md` section 4, `m2/fold_metrics.csv`.

### D4 - Authors' script used via function extraction (recorded at feasibility, 8 Oct)
- **What:** the authors' `godclass_metricbased.py` is a Colab export (notebook commands, pasted HTML) and does not run as a Python file. Our scripts cut out the 7 metric functions and run them unchanged.
- **Why:** to use the authors' own metric definitions rather than reimplementing them.
- **Effect:** none on the metric values; the function line numbers are logged.
- **Evidence:** `m1_feasibility_check.py`, `m2/run_log.txt` (section 2).

### D5 - zero_division = 0 (implementation detail, 18 Oct)
- **What:** if a model predicts no God Classes, its precision and F1 are set to 0.
- **Why:** F1 is otherwise undefined; the paper does not specify.
- **Effect:** none in practice: neither model had zero positive predictions on the 12 cases or in any fold.
- **Evidence:** `m2/results.md` sections 2 and 6.

### D6 - M1_PLAN tag added retrospectively (18 Oct)
- **What:** tag `M1_PLAN` was created on 18 Oct, pointing to commit `1af8ea4` (8 Oct), the repo state approved at the Week 5 checkpoint.
- **Why:** the tag was not created on the day.
- **Effect:** none on the method; the tagged commit predates the M1 checkpoint.

---

## Threats to validity

### T1 - Sample 3711605 has a conflicting-label duplicate (found at feasibility, 8 Oct)
- 3711605 (`MavenWrapperDownloader.java`, label 1) has identical code to 7450485 (label 0). It is the only such pair in the 2,148 samples, and 1 of the 5 God Classes in our frozen 12.
- Kept in the sample (removing it would break the selection rule). Pre-declared sensitivity check: F1 without it.
- **Result 18 Oct:** both models missed it (FN); without it, both score F1 0.7273, so the outcome is unchanged (tie).

### T2 - Small bounded sample (declared at M1)
- 12 cases with 5 positives: one prediction moves F1 substantially.
- **Result 18 Oct:** this materialised. The tie (both F1 0.6667) comes from one offsetting false positive each (Metric: 3705164; Token: 3717506).

### T3 - Authors' TCC is not the textbook definition (found at feasibility, 8 Oct)
- Based on shared method calls, divided by the number of methods rather than pairs, so it is not bounded 0-1 (e.g. 13.59 for 3700666). Kept, because we reproduce the authors' method.

### T4 - Authors' "lcom5" behaves partly like a size metric (found 12 Oct)
- Counts ordered method pairs sharing no **local variable** names (not fields), and often equals methods x (methods - 1) (e.g. 3699849: 6 methods -> 30; 3715636: 28 -> 756). Kept as written; relevant when interpreting RQ2.

### T5 - Dependency versions not reported by the authors
- Ours are recorded in `m2/environment.txt`; small numerical differences from the paper may come from versions.

---

## AI use (material only)
- **Feasibility script (8 Oct) and `m2/run_reproduction.py` (18 Oct):** written by Claude. Checked by the group: it follows the frozen M1 method, uses the authors' metric functions unchanged, and verifies the dataset SHA and frozen commit. The 12 rows in `results.md` were checked against `predictions.csv`, and a second machine re-ran the script (see `m2/rerun/`).
- **AI also flagged** the TCC (T3) and lcom5 (T4) behaviour; both were verified against the authors' code and our computed values.

---

## Pending
- Second-machine re-run (Oscar): `m2/rerun/comparison.txt`. 

## Reproducibility check: second-machine re-run (18 Oct)
- **What:** Oscar re-ran `m2/run_reproduction.py` on a second machine (`m2/rerun/`).
- **Result:** all 2,148 Metric-based predictions identical. 2 of 2,148 Token-based
  predictions differ, both in fold 8: 5702079 and 6080166 (Tudor 0, re-run 1).
  Only fold-8 Token metrics change; disagreements 822 -> 820.
- **Decision-relevant outputs unchanged:** all 12 frozen rows identical; 12-case F1
  Metric 0.6667 / Token 0.6667 on both machines. The first 10 disagreements (RQ2
  sample) are unchanged; the two differing cases sit at positions 299 and 361.
- **Likely cause:** [fill in after comparing the two environment.txt files, e.g.
  different scikit-learn/numpy versions or CPU architecture]. The Token model uses
  ~55k TF-IDF features, so near-boundary cases are sensitive to floating-point
  differences; the 7-feature Metric model is not affected.
- **Effect:** none on the RQ1 status or the RQ2 sample. Primary results are Tudor's
  run (`m2/`); the re-run is supporting evidence. Threat noted: Token predictions
  are reproducible only up to platform-level numerical differences.
- **Evidence:** `m2/rerun/comparison.txt`, `m2/rerun/predictions.csv`, both `environment.txt` files.
