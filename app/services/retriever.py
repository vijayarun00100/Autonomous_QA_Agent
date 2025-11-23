from __future__ import annotations

import logging
from typing import List

from app.core.config import settings
from app.services.vector_store import vector_store_manager

logger = logging.getLogger(__name__)


class KnowledgeRetriever:
    def __init__(self) -> None:
        self._is_ready: bool = False

    @property
    def is_ready(self) -> bool:
        if self._is_ready:
            return True
        try:
            vector_store_manager.load()
            self._is_ready = True
        except Exception:  # noqa: BLE001
            self._is_ready = False
        return self._is_ready

    def refresh(self) -> None:
        try:
            vector_store_manager.load()
            self._is_ready = True
        except Exception as exc:  # noqa: BLE001
            logger.error("Failed to refresh vector store: %s", exc)
            self._is_ready = False

    def retrieve(self, query: str, top_k: int | None = None):
        store = vector_store_manager.load()
        return store.similarity_search_with_score(query, k=top_k or settings.retriever_top_k)

    def raw_search(self, query: str, top_k: int | None = None) -> List[dict]:
        docs_with_scores = self.retrieve(query, top_k)
        results = []
        for doc, score in docs_with_scores:
            metadata = doc.metadata.copy()
            metadata.update({
                "score": score,
                "chunk_id": metadata.get("chunk_id"),
            })
            results.append({
                "page_content": doc.page_content,
                "metadata": metadata,
            })
        return results
