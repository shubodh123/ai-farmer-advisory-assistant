"""
Configuration settings for Kisan Mitra AI Farmer Advisory Assistant.
"""
import os

# Base paths
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
KB_DIR = os.path.join(PROJECT_ROOT, "rag", "knowledge_base")
STATIC_DIR = os.path.join(PROJECT_ROOT, "static")

# RAG Configuration
RETRIEVAL_TOP_K = 3
MIN_SIMILARITY_SCORE = 0.20
CHUNK_SIZE_WORDS = 350
CHUNK_OVERLAP_WORDS = 50

# Model Backends
AGRIPARAM_BACKEND = os.getenv("AGRIPARAM_BACKEND", "offline_rag") # 'offline_rag', 'huggingface', 'gemini'
USE_HF_MODELS = os.getenv("USE_HF_MODELS", "false").lower() == "true"

# Server Configuration
DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = int(os.getenv("PORT", 8080))

# Supported Languages
SUPPORTED_LANGUAGES = {
    "hin_Deva": "Hindi (हिन्दी)",
    "pan_Guru": "Punjabi (ਪੰਜਾਬੀ)",
    "mar_Deva": "Marathi (मराठी)",
    "tel_Telu": "Telugu (తెలుగు)",
    "tam_Taml": "Tamil (தமிழ்)",
    "ben_Beng": "Bengali (বাংলা)",
    "guj_Gujr": "Gujarati (ગુજરાતી)",
    "kan_Knda": "Kannada (ಕನ್ನಡ)",
    "eng_Latn": "English (Agronomic)"
}
