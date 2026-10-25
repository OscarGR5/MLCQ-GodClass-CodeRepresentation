# P35 Event A preregistration

## Scope and split

Event A evaluates the frozen M2 learning method on a project-disjoint held-out sample from `data/god_class_df.csv`. The source dataset contains 2,148 Java classes from 416 GitHub repositories and has Git blob SHA-1 `6e1075ead90054ff9955cf310842c0d31a41e5dc`, matching the M2 input identity.

`select_holdout.py` derives lowercase `owner/repository` from every GitHub `link`. A project is held out when the unsigned big-endian integer of `SHA-256("P35_EVENT_A_V1|" + project_id)` modulo 5 equals 0. The rule is fixed, deterministic, and does not read labels, M2 predictions, or model performance. Every sample from a held-out project is retained for Event A evaluation. Projects not selected form the candidate training set.

Before training, any candidate-training sample whose exact `code_snippet` occurs in a held-out sample is assigned `excluded`; held-out cases are always retained. The manifest is sorted by `sample_id` to make its output independent of CSV row order.

## Frozen M2 baseline and Event A method

The frozen M2 method compares metric-based SVM with Token/TF-IDF SVM. Metric-based SVM uses the seven authors' metric functions, `StandardScaler()`, training-only `SMOTE(random_state=42)`, and `SVC(probability=True, random_state=42)`. Token/TF-IDF SVM uses `TfidfVectorizer(ngram_range=(1, 1))` with the default scikit-learn tokenizer, `StandardScaler(with_mean=False)`, the same training-only SMOTE configuration, and the same SVC configuration. The existing SVM defaults, decision threshold, and random seed remain frozen.

M2 used `KFold(n_splits=10, shuffle=True, random_state=42)` for cross-validation. Event A replaces only that cross-validation split with `split_manifest.csv`: fit on `training`, omit `excluded`, and evaluate on `holdout`. No hyperparameter tuning, model selection, preprocessing change, seed change, or split revision is permitted after observing Event A results.

The M2 secondary full-dataset CV mean F1 was 0.6379 for Metric and 0.4135 for Token. The primary M2 bounded result was Metric F1 = 0.6667 and Token F1 = 0.6667; under the frozen decision rule, this tie is **NOT REPRODUCED**.

## Pre-registered prediction

"Metric-based SVM will achieve a higher F1-score than token-based SVM on the held-out projects, consistent with the full-dataset M2 results (0.6379 versus 0.4135). However, our primary M2 bounded sample produced a tie (0.6667 versus 0.6667), so the advantage may not transfer."

Operational prediction: Metric-based SVM achieves higher positive-class F1 than Token/TF-IDF SVM on the holdout, although both may perform worse than in M2 CV.

Primary metric: positive-class F1.

Secondary metrics: precision, recall, accuracy and confusion counts.

Challenge criterion:

"Metric-based F1 less than or equal to token-based F1 on the held-out set."

## Git reference reconciliation

The historical GitHub tags `M2_REPRO` and `PRE_EVENT_A` both resolve to `c29bd308d2bee84694ae8f6c193d9ebc5e264834`, one commit after `d10d0c0b3f1de34cf2ba07971d98cea7c18cd6c9`. That follow-up changes only `deviations.md`; it does not alter the frozen dataset, M2 method, raw M2 evidence, or M2 results. Before local references were aligned to the GitHub tags, their former targets were preserved under `LOCAL_M2_REPRO_BEFORE_REMOTE_RECONCILIATION` (`d10d0c0b3f1de34cf2ba07971d98cea7c18cd6c9`) and `LOCAL_PRE_EVENT_A_BEFORE_REMOTE_RECONCILIATION` (`ed32497c40cdba2bb98335ceb12d77edc9fb7729`). The Event A plan is published under the separate `EVENT_A_PLAN` tag; the historical tag names are not used for this plan.

## Validity limits

The dataset was already used for M2 cross-validation. This Event A holdout is project-disjoint for Event A training, but it is not wholly independent of prior M2 investigation. The M2 results informed the preregistered prediction, and the dataset's labels and classes were previously available during M2.

The fixed hash rule can produce an uneven number of classes or samples across projects. Those outcomes will be reported but will not change the split. Exact-string duplicate exclusion prevents direct code leakage across the boundary, but modified, near-duplicate, generated, and shared-library code can still create dependence. GitHub owner/repository normalization also treats renamed or fork-related repositories as separate identifiers when their URLs differ.

## Execution boundary

This directory prepares the split only. No model has been trained, no Event A predictions have been produced, and no performance metrics have been calculated. The next Event A run must use `split_manifest.csv` exactly, fit only on `training`, omit `excluded` samples from fitting, and evaluate only on `holdout` after this plan and manifest are frozen in Git.
