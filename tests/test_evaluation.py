import unittest
from evaluate import scores

class EvaluationTests(unittest.TestCase):
    def test_known_errors_and_direction_abstention(self):
        result=scores([100,120],[110,110],[90,130])
        self.assertEqual(result['mae'],10)
        self.assertEqual(result['rmse'],10)
        self.assertAlmostEqual(result['mape_percent'],(10/100+10/120)*50)
        self.assertEqual(result['directional_accuracy_percent'],100)
        baseline=scores([100,120],[90,130],[90,130])
        self.assertEqual(baseline['directional_accuracy_percent'],0)

    def test_undefined_variance_and_invalid_samples(self):
        self.assertIsNone(scores([100,100],[100,100],[100,100])['r2'])
        for actual,predicted,previous in [([],[],[]),([0],[1],[1]),([1],[float('nan')],[1]),([1,2],[1],[1])]:
            with self.assertRaises(ValueError):scores(actual,predicted,previous)
