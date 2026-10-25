import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_holdout


class HoldoutInputTests(unittest.TestCase):
    def test_frozen_manifest_validates_without_model_execution(self):
        _, training, holdout, _ = run_holdout.validate_inputs(ROOT)
        self.assertEqual(len(training), 1654)
        self.assertEqual(len(holdout), 494)
        self.assertEqual(training["project_id_data"].nunique(), 319)
        self.assertEqual(holdout["project_id_data"].nunique(), 97)

    def test_positive_class_scores_include_confusion_counts(self):
        result = run_holdout.scores([1, 1, 0, 0], [1, 0, 1, 0])
        self.assertEqual({key: result[key] for key in ("TP", "FP", "FN", "TN")},
                         {"TP": 1, "FP": 1, "FN": 1, "TN": 1})
        self.assertEqual(result["f1"], 0.5)


if __name__ == "__main__":
    unittest.main()
