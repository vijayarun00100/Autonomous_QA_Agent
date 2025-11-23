from __future__ import annotations

import logging
from typing import List, Optional, Tuple

from langchain_community.vectorstores import Chroma

from app.core.config import settings
from app.services.embeddings import get_embedding_service

logger = logging.getLogger(__name__)


class VectorStoreManager:
    def __init__(self) -> None:
        self.embedding_service = get_embedding_service()
        self.vector_store: Optional[Chroma] = None

    def load(self) -> Chroma:
        if self.vector_store is None:
            logger.info("Loading Chroma vector store from %s", settings.chroma_dir)
            self.vector_store = Chroma(
                collection_name=settings.chroma_collection,
                embedding_function=self.embedding_service,
                persist_directory=str(settings.chroma_dir),
            )
        return self.vector_store

    def reset(self) -> None:
        self.vector_store = None

    def similarity_search(self, query: str, k: int) -> List[dict]:
        store = self.load()
        docs = store.similarity_search(query, k=k)
        return [
            {
                "page_content": doc.page_content,
                "metadata": doc.metadata,
                "id": doc.metadata.get("chunk_id"),
            }
            for doc in docs
        ]

    def similarity_search_with_score(self, query: str, k: int) -> List[Tuple[dict, float]]:
        store = self.load()
        docs_with_scores = store.similarity_search_with_score(query, k=k)
        results: List[Tuple[dict, float]] = []
        for doc, score in docs_with_scores:
            payload = {
                "page_content": doc.page_content,
                "metadata": doc.metadata,
                "id": doc.metadata.get("chunk_id"),
            }
            results.append((payload, score))
        return results

    def as_retriever(self, search_kwargs: Optional[dict] = None):
        store = self.load()
        return store.as_retriever(search_kwargs=search_kwargs or {"k": settings.retriever_top_k})


vector_store_manager = VectorStoreManager()
