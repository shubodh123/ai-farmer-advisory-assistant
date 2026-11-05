"""
Retriever with Indian-language vocabulary bridging, agronomic synonym expansion,
confidence thresholding, and structured context assembly.
"""
from typing import List, Dict, Any, Tuple
from rag.document_store import DocumentStore

# Bilingual / Transliteration agronomic vocabulary bridge across Indian languages
INDIC_AGRI_SYNONYMS = {
    # Hindi / Hinglish -> English Agronomic Terms
    "gehu": ["wheat", "HD-2967", "DBW-187", "sowing"],
    "गेहूं": ["wheat", "HD-2967", "DBW-187", "sowing", "varieties"],
    "बिजाई": ["sowing", "seed rate", "varieties", "November"],
    "bijai": ["sowing", "seed rate", "varieties", "November"],
    "dhaan": ["paddy", "rice", "nursery", "transplanting"],
    "dhan": ["paddy", "rice", "nursery", "transplanting"],
    "धान": ["paddy", "rice", "nursery", "transplanting"],
    "khaira": ["zinc", "zinc sulphate", "micronutrients", "deficiency"],
    "खैरा": ["zinc", "zinc sulphate", "micronutrients", "deficiency"],
    "awd": ["alternate wetting and drying", "paddy", "rice", "water"],
    "wetting": ["alternate wetting and drying", "paddy", "water"],
    "kapas": ["cotton", "bollworm", "whitefly"],
    "कपास": ["cotton", "bollworm", "whitefly"],
    "tamatar": ["tomato", "leaf curl", "early blight"],
    "टमाटर": ["tomato", "leaf curl", "early blight"],
    "sarson": ["mustard", "aphid", "sarson"],
    "सरसों": ["mustard", "aphid", "sarson"],
    "ganna": ["sugarcane", "red rot", "shoot borer"],
    "गन्ना": ["sugarcane", "red rot", "shoot borer"],
    "pyaz": ["onion", "thrips", "purple blotch"],
    "प्याज": ["onion", "thrips", "purple blotch"],
    "khad": ["fertilizer", "urea", "dap", "mop", "npk"],
    "खाद": ["fertilizer", "urea", "dap", "mop", "npk"],
    "यूरिया": ["urea", "nitrogen", "fertilizer", "basal"],
    "डीएपी": ["dap", "phosphorus", "fertilizer", "basal"],
    "yuria": ["urea", "nitrogen", "fertilizer", "basal"],
    "sundi": ["bollworm", "caterpillar", "pest", "borer"],
    "सुंडी": ["bollworm", "caterpillar", "pest", "borer"],
    "kungi": ["rust", "yellow rust", "stripe rust"],
    "कुंगी": ["rust", "yellow rust", "stripe rust"],
    "peeli": ["yellow", "yellow rust", "chlorosis"],
    "पीली": ["yellow", "yellow rust", "chlorosis"],
    "dimak": ["termite", "chlorpyrifos"],
    "दीमक": ["termite", "chlorpyrifos"],
    "keeda": ["pest", "insect", "infestation"],
    "कीड़ा": ["pest", "insect", "infestation"],
    "bima": ["insurance", "pmfby", "claim"],
    "बीमा": ["insurance", "pmfby", "claim"],
    "kisan": ["farmer", "pm-kisan", "kcc", "credit card"],
    "किसान": ["farmer", "pm-kisan", "kcc", "credit card"],
    "sinchai": ["irrigation", "water", "CRI"],
    "सिंचाई": ["irrigation", "water", "CRI"],
    "mitti": ["soil", "soil health", "npk", "zinc"],
    "मिट्टी": ["soil", "soil health", "npk", "zinc"],

    # Punjabi (Gurmukhi) Agronomic Synonyms
    "ਕਣਕ": ["wheat", "HD-2967", "sowing", "yellow rust"],
    "ਪੀਲੀ": ["yellow", "yellow rust"],
    "ਕੁੰਗੀ": ["rust", "yellow rust", "propiconazole"],
    "ਸਪਰੇਅ": ["spray", "pesticide"],
    "ਦਵਾਈ": ["medicine", "chemical", "propiconazole"],
    "ਝੋਨਾ": ["paddy", "rice"],
    "ਨਰਮਾ": ["cotton", "bollworm"],

    # Marathi (Devanagari) Agronomic Synonyms
    "कापूस": ["cotton", "bollworm", "emamectin"],
    "बोंड": ["bollworm", "pink bollworm", "emamectin"],
    "अळी": ["bollworm", "caterpillar", "pest"],
    "गुलाबी": ["pink", "pink bollworm"],
    "गहू": ["wheat", "rust"],
    "भात": ["paddy", "rice"],
    "खत": ["fertilizer", "urea"],

    # Telugu Agronomic Synonyms
    "వరి": ["rice", "paddy", "BPH", "blast"],
    "దోమ": ["hopper", "BPH", "dinotefuran"],
    "పురుగు": ["pest", "bollworm"],
    "పత్తి": ["cotton", "pink bollworm"]
}

class AgriculturalRetriever:
    def __init__(self, document_store: DocumentStore = None):
        self.doc_store = document_store if document_store is not None else DocumentStore()

    def expand_query(self, query: str) -> str:
        words = query.lower().split()
        expanded_terms = []
        for word in words:
            cleaned = word.strip("?,.!;:()[]'\"")
            if cleaned in INDIC_AGRI_SYNONYMS:
                expanded_terms.extend(INDIC_AGRI_SYNONYMS[cleaned])
        if expanded_terms:
            return f"{query} {' '.join(set(expanded_terms))}"
        return query

    def retrieve(self, query: str, top_k: int = 3, min_score: float = 0.22) -> List[Dict[str, Any]]:
        expanded_query = self.expand_query(query)
        scored_chunks = self.doc_store.search(expanded_query, top_k=top_k)

        results = []
        for chunk, score in scored_chunks:
            if score >= min_score:
                item = dict(chunk)
                item["retrieval_score"] = round(float(score), 4)
                results.append(item)
        return results

    def assemble_context(self, retrieved_chunks: List[Dict[str, Any]]) -> Tuple[str, List[Dict[str, str]]]:
        """
        Combines retrieved chunks into a structured prompt context and extracts citations.
        """
        if not retrieved_chunks:
            return "No directly relevant ICAR/KVK advisory documents found.", []

        context_parts = []
        citations = []

        for i, chunk in enumerate(retrieved_chunks, 1):
            source_ref = f"[Doc {i}: {chunk['crop']} - {chunk['title']} | Source: {chunk['source']}]"
            context_parts.append(f"{source_ref}\n{chunk['text']}")
            citations.append({
                "doc_num": i,
                "title": chunk["title"],
                "crop": chunk["crop"],
                "source": chunk["source"],
                "score": chunk.get("retrieval_score", 0.0)
            })

        assembled_text = "\n\n".join(context_parts)
        return assembled_text, citations
