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
- **Likely cause:** [Apple Silicon/macOS vs x86_64/Linux, same library versions]. The Token model uses
  ~55k TF-IDF features, so near-boundary cases are sensitive to floating-point
  differences; the 7-feature Metric model is not affected.
- **Effect:** none on the RQ1 status or the RQ2 sample. Primary results are Tudor's
  run (`m2/`); the re-run is supporting evidence. Threat noted: Token predictions
  are reproducible only up to platform-level numerical differences.
- **Evidence:** `m2/rerun/comparison.txt`, `m2/rerun/predictions.csv`, both `environment.txt` files.



---

## Updates (5 Nov)
- **Pending item resolved:** the second-machine re-run was completed on 18 Oct; see
  "Reproducibility check" above.
- **Re-run cause confirmed:** library versions identical on both machines (scikit-learn,
  numpy, pandas, imbalanced-learn, javalang). Runs differ only in platform: macOS on
  Apple Silicon (arm64, Python 3.14.7) vs Linux x86_64 (Python 3.14.8).

## Event A (25 Oct)
- **Split choice:** "held-out portion" operationalised as a project-disjoint split
  (SHA-256 of owner/repo, mod 5 == 0). Fixed before results; does not read labels.
  494 classes / 97 projects held out; 1,654 classes / 319 projects for training.
- **Method:** frozen M2 method unchanged; only the split differs (one project-disjoint
  split instead of 10-fold CV).
- **Result:** SUPPORTED. Metric F1 0.6337 > Token F1 0.4558. M2 status unchanged
  (NOT REPRODUCED).
- **Threat:** the holdout is unseen by the Event A model, but not by the team: the same
  dataset was used in M2, and M2 results informed the prediction. Only exact duplicate
  snippets were checked (0 crossed the split); near-duplicates may remain.
- **Prediction timing:** preregistered in event_a/plan.md (tag EVENT_A_PLAN, 25 Oct 14:10)
  before execution (14:15); transcribed to the shared tracker afterwards.
- **RQ2 sample unaffected:** the frozen first-10 disagreements come from the reference
  m2/disagreements.csv (Tudor's run); the 2 re-run token flips sit at positions 299 and 361.

## AI use (Event A)
- select_holdout.py / run_holdout.py written by GPT
- Verification of Event A was AI-assisted with Clade: split regenerated (identical manifest),
  run_holdout.py re-run independently (byte-identical predictions), unit tests pass.
  Reviewed by Tudor before merging PR #2


---

## M4: design decision (5 Nov)

### Interim entry replaced
- The interim M4 tracker entries (based on Event A detector reliability) were replaced on 5 Nov by
  the decision based on the RQ2 inspection (`rq2/inspection.md`) and the refactoring in `m4/`.

### RQ2 inspection
- All 10 frozen disagreements inspected; each verdict cross-checked by the other team member.
  Result: 1 clear design problem (case 7, `C`, 3788627), 9 no clear problem, 0 unclear.
- Verdict wording standardised to the frozen M1 phrase ("No clear problem") when moving the
  working doc into the repo; case 1's code-evidence bullets restored from the agreed draft;
  typos and one line-number error (case 7: 998 -> 988) corrected. No verdicts changed.

### Design choices in the refactoring (m4/)
- **Two classes instead of one:** the 3 methods were moved into `TimeUtil` (time conversion) and
  `AudioSessionUtil` (Android audio session), not a single utility class. Upstream ExoPlayer later
  moved them into its general `Util` class; we split them so the two unrelated responsibilities are
  not recombined, and so the pure-Java time logic is testable without Android.
- **Deprecated delegates kept in `C`:** preserves the public API for existing callers. Consequence:
  `C` keeps a `Context` dependency until the delegates are removed (two-step migration).
- **Cosmetic:** the blank line before the final `}` of `after/C.java` was removed (visible in
  `m4/C_before_after.diff`); no effect on behaviour.

### Verification limits (threats)
- `C.java` and `AudioSessionUtil.java` were not compiled: they require the Android SDK.
- `generateAudioSessionIdV21` is verified by reviewing the diff (the delegate forwards the same
  argument to the unchanged, moved method), not by running it.
- The time-conversion test uses a test-only stub `C` holding just `TIME_END_OF_SOURCE` and
  `TIME_UNSET`, copied verbatim from `before/C.java` L48 and L54.
- The refactoring was done on a single-file snapshot, not inside the full ExoPlayer build, so
  ExoPlayer's own callers and test suite were not run.
- The original `msToUs` overflows for very large inputs (e.g. `Long.MAX_VALUE` -> -1000); the
  refactored version reproduces this exactly. Preserved, not fixed, because a refactoring must not
  change behaviour.

### Review
Reviewed by Oscar before merging PR #3

### Detector check(5nov)
- Detector check: run the frozen metric SVM on `m4/after/C.java`. Prediction recorded in
  `m4/README.md` before checking: `C` will still be flagged (164 fields and ~900 LOC unchanged). 
-post running results below:
- Frozen M2 metric SVM, trained on all 2,147 samples except `C` (3788627), scored on the class body
  (L39-end) of before/after `C.java`. Before matches the dataset sample exactly.
- Result: before = 1 (God Class), after = 1; P(God Class) 0.8032 -> 0.8036. Prediction in
  m4/README.md (commit f1fa605, written before the check) **supported**.
- Only LOC changed (908 -> 896); the other 6 features are identical, so the refactoring is invisible
  to the detector. Evidence: m4/detector_check.txt.
- AI use: Claude wrote detector_check.py; Tudor ran it and checked the before-sample sanity line.

### AI use (RQ2 + M4)
- RQ2: Oscar's ChatGPT-assisted notes proposed `C` as the candidate; Claude extracted class
  structures and computed `C`'s feature percentiles.
  All verdicts were made us against the code; Tudor's check corrected one AI claim
  (Android coupling: `C` already depends on `AudioManager` through its constants).
- M4: Claude drafted the code skeletons; Tudor created the files, applied
  the edit to `C.java`, ran the diff and the test, and wrote the README and detector prediction.
