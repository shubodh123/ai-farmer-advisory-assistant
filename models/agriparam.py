"""
BharatGen AgriParam Domain LLM Interface.
Specialized for Indian agriculture with ICAR-grounded prompt engineering,
structured agronomic advice synthesis, and verified citations.
"""
import os
import re
from typing import List, Dict, Any, Optional

AGRIPARAM_SYSTEM_PROMPT = """You are AgriParam, an expert AI Agricultural Advisory LLM powered by BharatGen and ICAR knowledge.
Your mission is to provide accurate, grounded agronomic advice to Indian farmers.
Guidelines:
1. ONLY recommend chemicals, dosages, and practices found in the verified ICAR/KVK reference context.
2. Clearly specify dosages in standard Indian units: per acre or per litre of water.
3. State the optimal application stage (e.g. CRI stage, first sign of ETL).
4. Highlight mandatory safety cautions (e.g., waiting period, wearing masks, protecting honeybees).
5. Always cite your source document.
6. If the context does not contain sufficient information, state that clearly and advise consulting the local KVK or Krishi Adhikari.
"""

class AgriParamModel:
    def __init__(self, backend: str = "offline_rag", model_checkpoint: str = "bharatgenai/AgriParam"):
        self.backend = backend
        self.model_checkpoint = model_checkpoint
        self.api_key = os.getenv("GEMINI_API_KEY") or os.getenv("OPENAI_API_KEY")

        if self.backend == "huggingface":
            try:
                import torch
                from transformers import AutoModelForCausalLM, AutoTokenizer
                print(f"[AgriParam] Loading {model_checkpoint}...")
                self.tokenizer = AutoTokenizer.from_pretrained(model_checkpoint)
                self.model = AutoModelForCausalLM.from_pretrained(
                    model_checkpoint,
                    torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                    device_map="auto" if torch.cuda.is_available() else None
                )
            except Exception as e:
                print(f"[AgriParam] HuggingFace load failed: {e}. Falling back to offline RAG engine.")
                self.backend = "offline_rag"

    def generate_advisory(self, query: str, context: str, citations: List[Dict[str, Any]]) -> str:
        """
        Synthesizes agronomic response grounded in retrieved ICAR context.
        """
        if not context or "No directly relevant" in context:
            return (
                "**सलाह / Advisory:**\n\n"
                "I could not locate an official ICAR/KVK package of practices matching your specific query in our verified repository.\n\n"
                "📌 **Recommendation:** Please contact your nearest Krishi Vigyan Kendra (KVK), "
                "District Agricultural Officer, or call the Kisan Call Centre at **1800-180-1551** (Toll-Free) for verified local guidance."
            )

        if self.backend == "gemini" and os.getenv("GEMINI_API_KEY"):
            return self._call_gemini_api(query, context, citations)
        elif self.backend == "huggingface" and hasattr(self, 'model'):
            return self._call_hf_model(query, context, citations)

        # High-Fidelity Domain Synthesis Engine (Offline BharatGen AgriParam Mode)
        return self._synthesize_grounded_response(query, context, citations)

    def _synthesize_grounded_response(self, query: str, context: str, citations: List[Dict[str, Any]]) -> str:
        """
        Structured, citation-grounded response synthesis adhering strictly to retrieved context.
        """
        # Determine primary crop or subject
        crop = citations[0]["crop"] if citations else "Crop"
        title = citations[0]["title"] if citations else "Agronomic Advisory"
        source = citations[0]["source"] if citations else "ICAR Package of Practices"

        # Extract context sentences
        sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', context) if len(s.strip()) > 15]

        # Extract actions and dosages
        actions = []
        dosages = []
        preventions = []

        for s in sentences:
            s_lower = s.lower()
            if any(k in s_lower for k in ["spray", "apply", "treat", "sow", "irrigate", "install", "drain", "variety", "varieties", "recommend", "optimal", "deficiency", "critical", "window", "maintain", "adopt", "water", "schedule"]):
                actions.append(s)
            if any(k in s_lower for k in ["g/l", "ml/l", "kg/ha", "kg/acre", "l/acre", "g/acre", "per acre", "%"]):
                dosages.append(s)
            if any(k in s_lower for k in ["avoid", "prevent", "precaution", "never", "resist"]):
                preventions.append(s)

        response_lines = []
        response_lines.append(f"### 🌾 {crop} Advisory: {title}")
        response_lines.append("")
        response_lines.append("#### 📋 Diagnostic & Key Guidance:")
        # Provide informative sentences from context
        selected_sentences = []
        # Include first informative sentence from top chunk
        for s in sentences:
            if not s.startswith("[Doc") and len(s) > 20:
                selected_sentences.append(s)
                break
        for a in actions:
            if a not in selected_sentences:
                selected_sentences.append(a)
            if len(selected_sentences) >= 4:
                break

        for item in selected_sentences:
            response_lines.append(f"- {item.strip()}")

        if dosages:
            response_lines.append("")
            response_lines.append("#### 💧 Prescribed Dosages & Chemical Application:")
            unique_dosages = list(dict.fromkeys(dosages))[:3]
            for dose in unique_dosages:
                response_lines.append(f"- **Dosage Note:** {dose.strip()}")

        if preventions:
            response_lines.append("")
            response_lines.append("#### ⚠️ Precautions & Safety Advisory:")
            for p in preventions[:2]:
                response_lines.append(f"- {p.strip()}")
        else:
            response_lines.append("")
            response_lines.append("#### ⚠️ Safety Caution:")
            response_lines.append("- Follow all chemical handling precautions: wear protective mask/gloves, spray in morning/late afternoon, and adhere to minimum pre-harvest waiting periods.")

        response_lines.append("")
        response_lines.append("#### 📚 Verified ICAR/KVK Sources:")
        for c in citations:
            response_lines.append(f"- **Doc {c['doc_num']}**: *{c['title']}* — {c['source']} (Confidence: {int(c.get('score', 1.0)*100)}%)")

        return "\n".join(response_lines)

    def _call_gemini_api(self, query: str, context: str, citations: List[Dict[str, Any]]) -> str:
        try:
            import urllib.request
            import json
            api_key = os.getenv("GEMINI_API_KEY")
            url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
            prompt = f"{AGRIPARAM_SYSTEM_PROMPT}\n\nContext:\n{context}\n\nFarmer Query: {query}\n\nAgriParam Advisory:"
            data = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode("utf-8")
            req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                res_data = json.loads(resp.read().decode("utf-8"))
                return res_data["candidates"][0]["content"]["parts"][0]["text"]
        except Exception as e:
            return self._synthesize_grounded_response(query, context, citations)

    def _call_hf_model(self, query: str, context: str, citations: List[Dict[str, Any]]) -> str:
        prompt = f"<|im_start|>system\n{AGRIPARAM_SYSTEM_PROMPT}<|im_end|>\n<|im_start|>user\nContext:\n{context}\n\nQuery: {query}<|im_end|>\n<|im_start|>assistant\n"
        inputs = self.tokenizer(prompt, return_tensors="pt")
        if hasattr(self.model, "device"):
            inputs = {k: v.to(self.model.device) for k, v in inputs.items()}
        outputs = self.model.generate(**inputs, max_new_tokens=350, temperature=0.2)
        raw_out = self.tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
        return raw_out
