import unittest

from delivery_metrics import simulate_delivery


class TestDeliveryMetrics(unittest.TestCase):
    def test_simulation_returns_consistent_delivery_counts(self):
        result = simulate_delivery()
        self.assertEqual(
            result["total"],
            result["pending"] + result["on_the_way"] + result["delivered"],
        )
        self.assertGreaterEqual(result["pending"], 10)
        self.assertLessEqual(result["pending"], 20)
        self.assertGreaterEqual(result["average_seconds"], 15)
        self.assertLessEqual(result["average_seconds"], 45)


if __name__ == "__main__":
    unittest.main()
