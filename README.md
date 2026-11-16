# P35(G13): Code Representation for ML-Based God Class Detection

 CS4928 project fork (Tudor, Oscar,Nathan,Ivan,Marcus). The original authors README follows below the line

| Stage | Where | Tag |
|---|---|---|
| M1 plan + feasibility | `m1_feasibility_check.py`, `m1_feasibility_output.txt` | `M1_PLAN` |
| M2 bounded reproduction (12 cases, Metric vs Token SVM) | `m2/` (`results.md`, `rerun/`) | `M2_REPRO`, `PRE_EVENT_A` |
| Event A (held-out transfer) | `event_a/` | `EVENT_A_PLAN` |
| RQ2 manual inspection of disagreements | `rq2/inspection.md` | |
| M4 design decision (Move Method on `C`) | `m4/` | `PRE_EVENT_B` |
| Event B (new change pressure) | `event_b/` (run `bash event_b/verify.sh`) | |
| Deviations, threats, AI use | `deviations.md` | |
| Final state | | `FINAL` |

---
# A Study on the Effect of Code Representation Techniques on Machine Learning Results for God Class Code Smell Detection

## Overview

This repository contains all resources related to the research titled **"A Study on the Effect of Code Representation Techniques on Machine Learning Results for God Class Code Smell Detection"**. The project investigates how different representations of source code affect the performance of various machine learning algorithms in detecting the God Class code smell. This includes the use of metric-based, token-based, tree-based, and code embedding techniques.

We provide the final dataset, scripts for metric features extraction, evaluation result visualizations, and an interactive web interface to navigate the evaluation results. The work aims to support reproducibility and future extensions by the research and developer community.

---

## Abstract

In the realm of software development, detecting code smells is a critical task for ensuring good code quality. The God Class code smell, in particular, is often characterized by excessive complexity and a high degree of subjectivity in identifying it, especially concerning coupling and cohesion levels. Automated detection techniques are vital in addressing this subjectivity.

Machine learning algorithms have shown significant potential for improving the objectivity and accuracy of God Class detection, thanks to their ability to identify complex patterns in code. However, the effectiveness of these algorithms is strongly influenced by how the source code is represented for analysis.

This study explores the impact of various code representation techniques—specifically metric-based, token-based, tree-based, and code embeddings—on machine learning performance. The MLCQ dataset was used for this investigation, and several algorithms were tested including Logistic Regression, Support Vector Machines, Decision Trees, Random Forests, Gradient Boosting, XGBoost, and Naïve Bayes.

The results highlight how representation techniques affect detection performance, with the F1-score used as the primary evaluation metric to balance precision and recall. The findings reveal performance improvements over previous studies on the MLCQ dataset and offer practical guidance on code representation and model selection strategies.

---

## Repository Structure


├── data/ # Final labeled dataset (CSV) ├── scripts/ # Metric calculation code ├── visualizations/ # Evaluation bar plots per model and representation ├── docs/ # HTML reports and index for interactive results └── README.md # Project overview and instructions


---

## Contents

- `data/god_class_df.csv`: Final dataset of 2148 samples (1687 nonsmelly, 461 smelly).
- `scripts/godclass_metricbased.py`: Python script used to calculate metric-based features.
- `visualizations/*.png`: Bar plots showing model performance using different code representations.
- `docs/*.html`: Pre-generated evaluation reports and an `index.html` to explore them interactively.

---

## How to Use

1. **Explore the Dataset**  
   Navigate to the `data/` folder to review the labeled dataset used in this study.

2. **Run Metric Extraction (Optional)**  
   If you wish to replicate metric extraction, use the script in `scripts/`.

3. **View Visual Results**  
   Open the plots in the `visualizations/` folder for performance summaries.

4. **Browse the Web Interface**  
    user-friendly interface is available at  
   **[GitHub Pages Web Interface](https://elmohandharoon.github.io/MLCQ-GodClass-CodeRepresentation/)**  
   Alternatively,you can  open `docs/index.html` in browser to view it.

---

