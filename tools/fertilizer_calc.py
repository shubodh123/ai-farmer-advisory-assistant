"""
Agentic Tool: Agricultural Fertilizer & NPK Dosage Calculator.
Calculates exact chemical fertilizer requirements (Urea, DAP, MOP, Zinc Sulphate)
per acre based on crop specifications and ICAR standard formulations.
"""
from typing import Dict, Any

# Standard recommended N-P-K nutrient requirements in kg/acre
CROP_NUTRIENT_REQUIREMENTS = {
    "wheat": {"N": 48.0, "P": 24.0, "K": 16.0, "splits": 3, "zinc_rec": 10.0},
    "paddy": {"N": 48.0, "P": 20.0, "K": 20.0, "splits": 3, "zinc_rec": 10.0},
    "cotton": {"N": 60.0, "P": 30.0, "K": 30.0, "splits": 3, "zinc_rec": 10.0},
    "sugarcane": {"N": 100.0, "P": 40.0, "K": 50.0, "splits": 4, "zinc_rec": 15.0},
    "mustard": {"N": 32.0, "P": 16.0, "K": 12.0, "splits": 2, "zinc_rec": 10.0},
    "tomato": {"N": 60.0, "P": 40.0, "K": 40.0, "splits": 4, "zinc_rec": 5.0},
    "onion": {"N": 40.0, "P": 25.0, "K": 30.0, "splits": 3, "zinc_rec": 5.0}
}

class FertilizerCalculator:
    def __init__(self):
        pass

    def calculate(self, crop_name: str, acreage: float, soil_health_status: str = "medium") -> Dict[str, Any]:
        """
        Calculates required commercial fertilizer quantities in 50 kg bags and kilograms.
        """
        key = crop_name.lower().strip()
        matched_crop = None
        for k in CROP_NUTRIENT_REQUIREMENTS:
            if k in key:
                matched_crop = k
                break

        if not matched_crop:
            matched_crop = "wheat"

        req = CROP_NUTRIENT_REQUIREMENTS[matched_crop]
        multiplier = 1.0
        if soil_health_status == "low":
            multiplier = 1.25  # Increase recommendation by 25%
        elif soil_health_status == "high":
            multiplier = 0.75  # Reduce by 25%

        total_n = req["N"] * acreage * multiplier
        total_p = req["P"] * acreage * multiplier
        total_k = req["K"] * acreage * multiplier

        # 1. Phosphorus is supplied via DAP (18% N, 46% P2O5)
        # DAP kg needed = total_p / 0.46
        dap_kg = total_p / 0.46
        n_from_dap = dap_kg * 0.18

        # 2. Potash is supplied via MOP (60% K2O)
        mop_kg = total_k / 0.60

        # 3. Nitrogen remaining after DAP is supplied via Urea (46% N)
        remaining_n = max(0.0, total_n - n_from_dap)
        urea_kg = remaining_n / 0.46

        # Standard 50kg bags
        dap_bags = round(dap_kg / 50.0, 1)
        mop_bags = round(mop_kg / 50.0, 1)
        urea_bags = round(urea_kg / 50.0, 1)

        basal_urea_kg = round(urea_kg / req["splits"], 1)
        top_dress_urea_kg = round((urea_kg - basal_urea_kg) / (req["splits"] - 1), 1)

        return {
            "crop": matched_crop.capitalize(),
            "acreage": acreage,
            "soil_status": soil_health_status,
            "nutrient_target_kg": {
                "Nitrogen_N": round(total_n, 1),
                "Phosphorus_P": round(total_p, 1),
                "Potash_K": round(total_k, 1)
            },
            "commercial_fertilizers": {
                "DAP_50kg_bags": dap_bags,
                "DAP_total_kg": round(dap_kg, 1),
                "Urea_50kg_bags": urea_bags,
                "Urea_total_kg": round(urea_kg, 1),
                "MOP_50kg_bags": mop_bags,
                "MOP_total_kg": round(mop_kg, 1),
                "Zinc_Sulphate_21_kg": round(req["zinc_rec"] * acreage, 1)
            },
            "application_schedule": {
                "Basal_Application_at_Sowing": f"All DAP ({round(dap_kg, 1)} kg) + All MOP ({round(mop_kg, 1)} kg) + 1/{req['splits']} Urea ({basal_urea_kg} kg)",
                "Top_Dress_Split_1": f"{top_dress_urea_kg} kg Urea at 1st Irrigation / Tillering",
                "Top_Dress_Split_2": f"{top_dress_urea_kg} kg Urea at 2nd Irrigation / Flowering",
                "Caution": "Never mix Zinc Sulphate directly with DAP during basal broadcasting."
            }
        }
