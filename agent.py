"""
Core Kisan Mitra / AI Farmer Advisory Assistant Agent.
Orchestrates Multilingual Translation (IndicTrans2), Knowledge Retrieval (RAG),
Domain LLM Advisory Generation (BharatGen AgriParam), Safety Guardrails,
and Agentic Tools (Fertilizer Calculator, MSP Lookup, Pest Diagnoser).
"""
import time
import re
from typing import Dict, Any, Optional

from rag.document_store import DocumentStore
from rag.retriever import AgriculturalRetriever
from models.indictrans2 import IndicTrans2Translator, INDIC_LANGUAGE_MAP
from models.agriparam import AgriParamModel
from models.guardrails import AgriculturalGuardrails
from tools.fertilizer_calc import FertilizerCalculator
from tools.mandi_prices import MandiPriceTool
from tools.pest_diagnoser import PestDiagnoser

class FarmerAdvisoryAssistant:
    def __init__(self, use_hf_models: bool = False, agriparam_backend: str = "offline_rag"):
        self.doc_store = DocumentStore()
        self.retriever = AgriculturalRetriever(self.doc_store)
        self.translator = IndicTrans2Translator(use_hf=use_hf_models)
        self.agriparam = AgriParamModel(backend=agriparam_backend)
        self.guardrails = AgriculturalGuardrails()

        # Agentic tools
        self.fertilizer_tool = FertilizerCalculator()
        self.mandi_tool = MandiPriceTool()
        self.pest_tool = PestDiagnoser()

    def process_query(self, query: str, user_language: str = "hin_Deva", acreage: float = 1.0) -> Dict[str, Any]:
        """
        End-to-end processing pipeline for farmer queries.
        """
        start_time = time.time()

        # Step 1: Safety & Guardrail Check
        is_safe, refusal_reason = self.guardrails.check_safety(query)
        if not is_safe:
            return {
                "status": "refusal",
                "original_query": query,
                "language": user_language,
                "answer": refusal_reason,
                "citations": [],
                "groundedness": {"groundedness_score": 0.0, "is_grounded": False},
                "tool_used": None,
                "tool_output": None,
                "latency_ms": round((time.time() - start_time) * 1000, 2)
            }

        # Step 2: Multilingual Translation (Indic -> English for RAG)
        query_en = self.translator.translate_indic_to_en(query, src_lang=user_language)

        # Step 3: Agentic Tool Routing
        tool_used = None
        tool_output = None
        q_lower = query_en.lower()

        # Route to Fertilizer Calculator
        if any(term in q_lower for term in ["fertilizer calculation", "how many bags", "how much urea", "dap bags", "npk dosage", "खाद की मात्रा", "यूरिया कितना", "khad calculator"]):
            tool_used = "FertilizerCalculator"
            crop = "wheat"
            for c in ["wheat", "paddy", "cotton", "sugarcane", "mustard", "tomato", "onion"]:
                if c in q_lower:
                    crop = c
                    break
            tool_output = self.fertilizer_tool.calculate(crop, acreage=acreage)

        # Route to Mandi Price Tool
        elif any(term in q_lower for term in ["msp", "mandi price", "bhav", "rate", "bhaav", "मंडी भाव", "एमएसपी"]):
            tool_used = "MandiPriceTool"
            crop = "wheat"
            for c in ["wheat", "paddy", "cotton", "mustard", "sugarcane", "onion", "tomato"]:
                if c in q_lower:
                    crop = c
                    break
            tool_output = {
                "msp_info": self.mandi_tool.get_msp(crop),
                "mandi_rates": self.mandi_tool.get_mandi_rates(crop)
            }

        # Route to Pest Diagnoser
        elif any(term in q_lower for term in ["diagnose", "symptom", "identify disease", "disease diagnosis", "रोग की पहचान", "lakshan"]):
            tool_used = "PestDiagnoser"
            crop = "wheat"
            for c in ["wheat", "cotton", "rice", "paddy", "tomato"]:
                if c in q_lower:
                    crop = c
                    break
            tool_output = self.pest_tool.diagnose(crop, query_en)

        # Step 4: Knowledge Base Retrieval (RAG)
        retrieved_chunks = self.retriever.retrieve(query_en, top_k=3, min_score=0.20)
        context_str, citations = self.retriever.assemble_context(retrieved_chunks)

        # Step 5: Domain LLM Generation (AgriParam)
        if tool_used and tool_output:
            # Augment context with tool output
            tool_summary = f"[Agentic Tool {tool_used} Output]\n" + str(tool_output)
            combined_context = f"{tool_summary}\n\n{context_str}"
            raw_answer = self.agriparam.generate_advisory(query_en, combined_context, citations)
        else:
            raw_answer = self.agriparam.generate_advisory(query_en, context_str, citations)

        # Step 6: Groundedness & Hallucination Verification
        groundedness = self.guardrails.calculate_groundedness(raw_answer, retrieved_chunks)

        # Step 7: Translate Advisory back to Indian Language (IndicTrans2)
        final_answer = self.translator.translate_en_to_indic(raw_answer, tgt_lang=user_language)

        latency = round((time.time() - start_time) * 1000, 2)

        return {
            "status": "success",
            "original_query": query,
            "query_en": query_en,
            "language": user_language,
            "answer": final_answer,
            "english_advisory": raw_answer,
            "citations": citations,
            "retrieved_chunks": retrieved_chunks,
            "groundedness": groundedness,
            "tool_used": tool_used,
            "tool_output": tool_output,
            "latency_ms": latency
        }
