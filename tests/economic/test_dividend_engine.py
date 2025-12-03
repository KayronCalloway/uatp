"""
Tests for Capsule Dividend Engine
"""
import unittest
from src.economic.dividend_engine import calculate_dividends


class TestDividendEngine(unittest.TestCase):
    def test_three_level_chain(self):
        """Test dividend distribution across three generations"""
        chain = [
            {"capsule_id": "A", "contributors": ["Alice"], "parent_capsule": None},
            {"capsule_id": "B", "contributors": ["Bob"], "parent_capsule": "A"},
            {"capsule_id": "C", "contributors": ["Charlie"], "parent_capsule": "B"},
        ]

        result = calculate_dividends(chain)

        # Verify allocations
        self.assertAlmostEqual(result["Alice"], 0.875)  # 0.5 (A) + 0.25 (B) + 0.125 (C)
        self.assertAlmostEqual(result["Bob"], 0.75)  # 0.5 (B) + 0.25 (C)
        self.assertAlmostEqual(result["Charlie"], 0.5)  # 0.5 (C)


if __name__ == "__main__":
    unittest.main()
