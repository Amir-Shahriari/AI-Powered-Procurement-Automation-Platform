import torch
from chromadb.config import Settings as ChromaSettings
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from .config import settings

EMBED = HuggingFaceEmbeddings(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    model_kwargs={"device": "cuda" if torch.cuda.is_available() else "cpu"},
    encode_kwargs={"device": "cuda" if torch.cuda.is_available() else "cpu", "batch_size": 64},
)

SPLITTER = RecursiveCharacterTextSplitter(chunk_size=1200, chunk_overlap=150)

CHROMA_SETTINGS = ChromaSettings(
    anonymized_telemetry=False,
    persist_directory=str(settings.INDEX_DIR),
)
