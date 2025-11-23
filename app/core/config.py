from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Literal, Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "QA Testing Brain"
    api_prefix: str = "/api"

    # Directories
    base_dir: Path = Path(__file__).resolve().parent.parent.parent
    data_dir: Path = base_dir / "data"
    chroma_dir: Path = data_dir / "chroma"
    upload_dir: Path = data_dir / "uploads"
    chroma_collection: str = "qa_testing_brain"

    # Embedding configuration
    embedding_model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_device: Literal["cuda", "cpu"] = "cuda" if os.getenv("USE_CUDA", "true").lower() not in {"0", "false"} else "cpu"
    embedding_batch_size: int = 32
    chunk_size: int = 800
    chunk_overlap: int = 120

    # Retrieval
    retriever_top_k: int = 6

    # LLM providers
    groq_api_key: Optional[str] = os.getenv("GROQ_API_KEY")
    groq_model: str = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

    # Runtime
    uvicorn_host: str = "0.0.0.0"
    uvicorn_port: int = 8000

    streamlit_port: int = 8501


@lru_cache()
def get_settings() -> Settings:
    settings = Settings()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.chroma_dir.mkdir(parents=True, exist_ok=True)
    settings.upload_dir.mkdir(parents=True, exist_ok=True)
    return settings


settings = get_settings()
