"""
Agentic Tool: Agricultural Pest & Disease Symptom Diagnoser.
Maps field observations and crop symptoms to probable pathogens and provides immediate first-line response.
"""
from typing import Dict, Any, List

SYMPTOM_DIAGNOSTIC_DB = [
    {
        "crop": "Wheat",
        "symptoms": ["yellow powdery stripes on leaves", "yellow stripes", "yellow powder", "peeli kungi"],
        "diagnosis": "Yellow Rust (Stripe Rust) caused by Puccinia striiformis",
        "severity": "High (Spread rapidly in cool, humid weather)",
        "immediate_action": "Spray Propiconazole 25% EC @ 1 ml/litre (200 ml/acre) immediately in 200 litres water.",
        "precaution": "Do not delay spraying once yellow powdery dust is visible on fingertips."
    },
    {
        "crop": "Wheat",
        "symptoms": ["plants wilting in patches", "severed roots", "underground insect attacking stems", "termites", "dimak"],
        "diagnosis": "Termite Infestation (Microtermes obesi)",
        "severity": "Medium-High",
        "immediate_action": "Apply Chlorpyrifos 20% EC @ 1.5 litres/acre mixed with 20-25 kg dry sand followed by light irrigation.",
        "precaution": "Ensure proper seed treatment before sowing in next cycle."
    },
    {
        "crop": "Cotton",
        "symptoms": ["rosetted flowers", "pink larva inside bolls", "premature boll opening", "stained cotton lint", "gulabi sundi"],
        "diagnosis": "Pink Bollworm (Pectinophora gossypiella)",
        "severity": "Critical",
        "immediate_action": "Install 5-8 pheromone traps per acre; spray Emamectin Benzoate 5% SG @ 5g/10L or Chlorantraniliprole 18.5% SC @ 3ml/10L water.",
        "precaution": "Avoid synthetic pyrethroids which induce resurgence of whiteflies."
    },
    {
        "crop": "Rice/Paddy",
        "symptoms": ["hopper burn", "drying of lower canopy", "circular scorched patches", "tiny insects jumping at water surface"],
        "diagnosis": "Brown Plant Hopper (BPH)",
        "severity": "Severe",
        "immediate_action": "Drain standing field water immediately for 2-3 days; spray Dinotefuran 20% SG @ 80g/acre directed at stem base.",
        "precaution": "Direct spray nozzle towards the base of the plant, not on top leaves."
    },
    {
        "crop": "Tomato",
        "symptoms": ["upward curling of leaves", "puckering", "stunted plants", "tiny white flying flies under leaves"],
        "diagnosis": "Tomato Leaf Curl Virus (ToLCV) transmitted by Whitefly",
        "severity": "High",
        "immediate_action": "Uproot and bury severely infected plants. Install yellow sticky traps (15-20/acre) and spray Imidacloprid 17.8% SL @ 0.3 ml/L.",
        "precaution": "Virus cannot be cured with fungicide; focus strictly on vector (whitefly) control."
    }
]

class PestDiagnoser:
    def __init__(self):
        pass

    def diagnose(self, crop: str, symptom_description: str) -> List[Dict[str, Any]]:
        desc_lower = symptom_description.lower()
        crop_lower = crop.lower()
        matches = []

        for entry in SYMPTOM_DIAGNOSTIC_DB:
            crop_match = (crop_lower in entry["crop"].lower() or entry["crop"].lower() in crop_lower) if crop else True
            symptom_match_count = sum(1 for sym in entry["symptoms"] if any(word in desc_lower for word in sym.split()))
            if crop_match and (symptom_match_count > 0 or any(s in desc_lower for s in entry["symptoms"])):
                res = dict(entry)
                res["confidence"] = min(0.98, 0.5 + (0.15 * symptom_match_count))
                matches.append(res)

        matches.sort(key=lambda x: x.get("confidence", 0), reverse=True)
        return matches
