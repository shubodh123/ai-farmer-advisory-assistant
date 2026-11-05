"""
Agentic Tool: APMC Mandi Rates and Minimum Support Price (MSP) Lookup.
Provides government-declared MSP benchmarks and modal market rates across key agricultural mandis.
"""
from typing import Dict, Any, List

MSP_RATES = {
    "wheat": {"msp_per_quintal": 2275, "season": "Rabi 2024-25 / 2025-26", "unit": "Rs / Quintal"},
    "paddy_common": {"msp_per_quintal": 2300, "season": "Kharif 2024-25 / 2025-26", "unit": "Rs / Quintal"},
    "paddy_grade_a": {"msp_per_quintal": 2320, "season": "Kharif 2024-25 / 2025-26", "unit": "Rs / Quintal"},
    "cotton_medium_staple": {"msp_per_quintal": 7121, "season": "Kharif 2024-25", "unit": "Rs / Quintal"},
    "cotton_long_staple": {"msp_per_quintal": 7521, "season": "Kharif 2024-25", "unit": "Rs / Quintal"},
    "mustard": {"msp_per_quintal": 5650, "season": "Rabi 2024-25", "unit": "Rs / Quintal"},
    "sugarcane_frp": {"msp_per_quintal": 340, "season": "Sugar Season 2024-25", "unit": "Rs / Quintal (FRP at 10.25% recovery)"},
    "gram_chana": {"msp_per_quintal": 5440, "season": "Rabi 2024-25", "unit": "Rs / Quintal"}
}

MANDI_BENCHMARKS = [
    {"mandi": "Khanna", "state": "Punjab", "commodity": "Wheat", "modal_price": 2310, "min_price": 2275, "max_price": 2350},
    {"mandi": "Karnal", "state": "Haryana", "commodity": "Wheat", "modal_price": 2300, "min_price": 2275, "max_price": 2340},
    {"mandi": "Gondal", "state": "Gujarat", "commodity": "Cotton", "modal_price": 7450, "min_price": 7100, "max_price": 7800},
    {"mandi": "Warangal", "state": "Telangana", "commodity": "Paddy", "modal_price": 2320, "min_price": 2280, "max_price": 2390},
    {"mandi": "Bharatpur", "state": "Rajasthan", "commodity": "Mustard", "modal_price": 5720, "min_price": 5600, "max_price": 5850},
    {"mandi": "Nashik (Lasalgaon)", "state": "Maharashtra", "commodity": "Onion", "modal_price": 2100, "min_price": 1600, "max_price": 2600},
    {"mandi": "Kolar", "state": "Karnataka", "commodity": "Tomato", "modal_price": 1800, "min_price": 1400, "max_price": 2200}
]

class MandiPriceTool:
    def __init__(self):
        pass

    def get_msp(self, commodity: str) -> Dict[str, Any]:
        comm_lower = commodity.lower().strip()
        for k, v in MSP_RATES.items():
            if comm_lower in k or k in comm_lower:
                return {
                    "commodity": k,
                    "msp": v["msp_per_quintal"],
                    "season": v["season"],
                    "unit": v["unit"],
                    "source": "Commission for Agricultural Costs and Prices (CACP), Ministry of Agriculture"
                }
        return {
            "commodity": commodity,
            "status": "Not declared or non-MSP horticultural produce",
            "reference": "For non-MSP produce like vegetables, market prices fluctuate based on daily supply-demand arrivals on e-NAM."
        }

    def get_mandi_rates(self, commodity: str, state: str = None) -> List[Dict[str, Any]]:
        comm_lower = commodity.lower().strip()
        matched = []
        for m in MANDI_BENCHMARKS:
            if comm_lower in m["commodity"].lower() or m["commodity"].lower() in comm_lower:
                if state is None or state.lower() in m["state"].lower():
                    matched.append(m)
        return matched
