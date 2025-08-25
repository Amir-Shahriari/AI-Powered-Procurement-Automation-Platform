import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Settings:
    DATA_DIR = Path("./data"); DATA_DIR.mkdir(exist_ok=True)
    INDEX_DIR = Path("./chroma"); INDEX_DIR.mkdir(exist_ok=True)
    FAISS_DIR = Path("./faiss"); FAISS_DIR.mkdir(exist_ok=True)

    VECTOR_BACKEND = os.getenv("VECTOR_BACKEND", "faiss_gpu").lower()  # "faiss_gpu" | "chroma"

    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma3:12b")

    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "local-anything")

settings = Settings()
