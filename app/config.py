import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Settings:
    DATA_DIR = Path("./data"); DATA_DIR.mkdir(exist_ok=True)
    INDEX_DIR = Path("./chroma"); INDEX_DIR.mkdir(exist_ok=True)
    FAISS_DIR = Path("./faiss"); FAISS_DIR.mkdir(exist_ok=True)

    VECTOR_BACKEND = os.getenv("VECTOR_BACKEND", "faiss_gpu").lower()  # "faiss_gpu" | "chroma"

    # ---- Providers ----
    # Primary provider: "gemini" (auto-fallback to Ollama on quota/rate/billing errors)
    # or set to "ollama" to force local-only operation.
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini").lower()

    # ---- Gemini ----
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "000")

    # ---- Ollama (local) ----
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:latest")

settings = Settings()
