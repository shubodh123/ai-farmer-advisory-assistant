"""
Agricultural Safety & Groundedness Guardrails:
Prevents hallucinations, toxic chemical misuse, hazardous off-label recommendations,
and verifies strict alignment with ICAR/KVK reference documentation.
"""
import re
from typing import Dict, Any, List, Tuple

HAZARDOUS_TERMS = [
    "bomb", "explosive", "ammonium nitrate bomb", "poison humans",
    "illegal pesticide", "banned endosulfan", "kerosene",
    "suicide", "hazard", "weapon"
]

APPROVED_AGROCHEMICALS = {
    "propiconazole", "tebuconazole", "chlorpyrifos", "dinotefuran",
    "pymetrozine", "cartap hydrochloride", "chlorantraniliprole",
    "tricyclazole", "isoprothiolane", "streptocycline", "copper oxychloride",
    "emamectin benzoate", "profenophos", "flonicamid", "pyriproxyfen",
    "spiromesifen", "imidacloprid", "acetamiprid", "cyantraniliprole",
    "mancozeb", "azoxystrobin", "difenoconazole", "dimethomorph", "cymoxanil",
    "zinc sulphate", "ferrous sulphate", "thiamethoxam", "dimethoate",
    "fipronil", "carbendazim", "spinetoram", "calcium nitrate", "gypsum",
    "trichoderma", "neem oil", "nske"
}

class AgriculturalGuardrails:
    def __init__(self):
        pass

    def check_safety(self, query: str) -> Tuple[bool, str]:
        """
        Scans for prohibited dangerous topics or hazard queries.
        Returns (is_safe, refusal_reason).
        """
        lowered = query.lower()
        for term in HAZARDOUS_TERMS:
            if term in lowered:
                return False, f"⚠️ Query violates agricultural safety policies: detected prohibited or hazardous subject ('{term}')."
        return True, ""

    def calculate_groundedness(self, answer: str, context_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Quantitatively evaluates factual groundedness and entity overlap between
        generated answer and retrieved ICAR chunks.
        """
        if not context_chunks:
            return {
                "groundedness_score": 0.0,
                "is_grounded": False,
                "hallucinated_entities": [],
                "verified_entities": []
            }

        combined_context = " ".join([c.get("text", "") for c in context_chunks]).lower()
        answer_lowered = answer.lower()

        # Extract agrochemical / specific agronomic terms mentioned in answer
        mentioned_chemicals = [chem for chem in APPROVED_AGROCHEMICALS if chem in answer_lowered]

        verified_entities = []
        hallucinated_entities = []

        for chem in mentioned_chemicals:
            if chem in combined_context:
                verified_entities.append(chem)
            else:
                hallucinated_entities.append(chem)

        # Word-level overlap (content words)
        context_words = set(re.findall(r'\b[a-zA-Z]{4,}\b', combined_context))
        answer_words = set(re.findall(r'\b[a-zA-Z]{4,}\b', answer_lowered))

        common_words = answer_words.intersection(context_words)
        lexical_faithfulness = len(common_words) / max(1, len(answer_words))

        # Penalty for ungrounded chemicals
        chem_groundedness = 1.0
        if mentioned_chemicals:
            chem_groundedness = len(verified_entities) / len(mentioned_chemicals)

        final_score = round(0.6 * chem_groundedness + 0.4 * lexical_faithfulness, 3)

        return {
            "groundedness_score": final_score,
            "is_grounded": final_score >= 0.65 and len(hallucinated_entities) == 0,
            "hallucinated_entities": hallucinated_entities,
            "verified_entities": verified_entities,
            "lexical_faithfulness": round(lexical_faithfulness, 3)
        }
