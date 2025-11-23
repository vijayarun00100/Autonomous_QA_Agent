from __future__ import annotations

import logging
from functools import lru_cache
from typing import Iterable, List

import torch
from sentence_transformers import SentenceTransformer

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmbeddingService:
    def __init__(self) -> None:
        device = settings.embedding_device
        if device == "cuda" and not torch.cuda.is_available():
            logger.warning("CUDA requested but not available. Falling back to CPU embeddings.")
            device = "cpu"

        logger.info("Loading embedding model %s on device %s", settings.embedding_model_name, device)
        self.model = SentenceTransformer(settings.embedding_model_name, device=device)
        self.batch_size = settings.embedding_batch_size

    def embed_texts(self, texts: Iterable[str]) -> List[List[float]]:
        encoded = self.model.encode(
            list(texts),
            batch_size=self.batch_size,
            show_progress_bar=False,
            convert_to_numpy=True,
            normalize_embeddings=True,
        )
        if hasattr(encoded, "tolist"):
            return encoded.tolist()
        return [list(vector) for vector in encoded]

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self.embed_texts(texts)

    def embed_query(self, text: str) -> List[float]:
        return self.embed_texts([text])[0]


@lru_cache()
def get_embedding_service() -> EmbeddingService:
    return EmbeddingService()
