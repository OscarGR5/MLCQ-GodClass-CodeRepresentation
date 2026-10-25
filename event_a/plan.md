# P35 Event A preregistration

## Scope and split

Event A evaluates the frozen M2 learning method on a project-disjoint held-out sample from `data/god_class_df.csv`. The source dataset contains 2,148 Java classes from 416 GitHub repositories and has Git blob SHA-1 `6e1075ead90054ff9955cf310842c0d31a41e5dc`, matching the M2 input identity.

`select_holdout.py` derives lowercase `owner/repository` from every GitHub `link`. A project is held out when the unsigned big-endian integer of `SHA-256("P35_EVENT_A_V1|" + project_id)` modulo 5 equals 0. The rule is fixed, deterministic, and does not read labels, M2 predictions, or model performance. Every sample from a held-out project is retained for Event A evaluation. Projects not selected form the candidate training set.

Before training, any candidate-training sample whose exact `code_snippet` occurs in a held-out sample is assigned `excluded`; held-out cases are always retained. The manifest is sorted by `sample_id` to make its output independent of CSV row order.

## Frozen M2 baseline and Event A method

The M2 baseline is the frozen `m2/run_reproduction.py` method: metric-based versus token-based SVM; seven authors' metric functions; TF-IDF unigrams with the default scikit-learn tokenizer; training-only scaling, SMOTE, and TF-IDF fitting; `SVC(probability=True, random_state=42)`; `SMOTE(random_state=42)`; and the existing decision threshold and seed. M2's full-dataset fold-average F1 results were 0.6379 for metric-based SVM and 0.4135 for token-based SVM. Its 12-case bounded sample was tied at 0.6667 each.

For Event A, only the split changes. The representation, preprocessing, SMOTE configuration, SVM configuration, decision threshold, and random seeds remain frozen. No hyperparameter tuning, model selection, or split revision is permitted after inspecting Event A results.

## Pre-registered prediction

"Metric-based SVM will achieve a higher F1-score than token-based SVM on the held-out projects, consistent with the full-dataset M2 results (0.6379 versus 0.4135). However, our primary M2 bounded sample produced a tie (0.6667 versus 0.6667), so the advantage may not transfer."

Primary metric: positive-class F1.

Secondary metrics: precision, recall, accuracy and confusion counts.

Challenge criterion:

"Metric-based F1 less than or equal to token-based F1 on the held-out set."

## Validity limits

The dataset was already used for M2 cross-validation. This Event A holdout is project-disjoint for Event A training, but it is not wholly independent of prior M2 investigation. The M2 results informed the preregistered prediction, and the dataset's labels and classes were previously available during M2.

The fixed hash rule can produce an uneven number of classes or samples across projects. Those outcomes will be reported but will not change the split. Exact-string duplicate exclusion prevents direct code leakage across the boundary, but modified, near-duplicate, generated, and shared-library code can still create dependence. GitHub owner/repository normalization also treats renamed or fork-related repositories as separate identifiers when their URLs differ.

## Execution boundary

This directory prepares the split only. No model has been trained, no Event A predictions have been produced, and no performance metrics have been calculated. The next Event A run must use `split_manifest.csv` exactly, fit only on `training`, omit `excluded` samples from fitting, and evaluate only on `holdout` after this plan and manifest are frozen in Git.
