import os
from pathlib import Path
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATA_DIR: Path = Path(os.getenv("DATA_DIR", "/tmp"))
    OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "google")  # cloud default = google

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
