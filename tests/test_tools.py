"""
Unit tests for Agentic Tools: FertilizerCalculator, MandiPriceTool, and PestDiagnoser.
"""
import unittest
from tools.fertilizer_calc import FertilizerCalculator
from tools.mandi_prices import MandiPriceTool
from tools.pest_diagnoser import PestDiagnoser

class TestAgenticTools(unittest.TestCase):
    def setUp(self):
        self.fert_tool = FertilizerCalculator()
        self.mandi_tool = MandiPriceTool()
        self.pest_tool = PestDiagnoser()

    def test_fertilizer_calculation(self):
        res = self.fert_tool.calculate("wheat", acreage=2.0, soil_health_status="medium")
        self.assertEqual(res["crop"], "Wheat")
        self.assertEqual(res["acreage"], 2.0)
        self.assertGreater(res["commercial_fertilizers"]["Urea_50kg_bags"], 0)
        self.assertGreater(res["commercial_fertilizers"]["DAP_50kg_bags"], 0)

    def test_mandi_msp_lookup(self):
        res = self.mandi_tool.get_msp("wheat")
        self.assertEqual(res["msp"], 2275)

    def test_pest_diagnoser(self):
        matches = self.pest_tool.diagnose("wheat", "bright yellow powdery stripes")
        self.assertGreater(len(matches), 0)
        self.assertIn("Yellow Rust", matches[0]["diagnosis"])

if __name__ == "__main__":
    unittest.main()
