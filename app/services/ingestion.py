from __future__ import annotations

import hashlib
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List

from langchain.text_splitter import RecursiveCharacterTextSplitter
import shutil

from langchain_community.vectorstores import Chroma
from langchain.schema import Document

from app.core.config import settings
from app.services.document_loader import DocumentLoader
from app.services.embeddings import get_embedding_service
from app.services.vector_store import vector_store_manager

logger = logging.getLogger(__name__)


@dataclass
class Chunk:
    id: str
    source: str
    content: str
    order: int
    start_index: int
    doc_hash: str


class KnowledgeBaseBuilder:
    def __init__(self) -> None:
        self.loader = DocumentLoader()
        self.embedding_service = get_embedding_service()
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            add_start_index=True,
        )
        self.persist_directory = settings.chroma_dir
        self.persist_directory.mkdir(parents=True, exist_ok=True)

    def save_upload(self, filename: str, contents: bytes) -> Path:
        target = settings.upload_dir / filename
        target.write_bytes(contents)
        return target

    def build_knowledge_base(self, files: Dict[str, Path]) -> None:
        documents = self.loader.load_documents(files)
        chunks: List[Chunk] = []
        start = time.perf_counter()

        for source_name, text in documents:
            doc_hash = hashlib.md5(text.encode("utf-8")).hexdigest()
            document_chunks = self.split_into_chunks(text, source_name, doc_hash)
            for i, doc_chunk in enumerate(document_chunks):
                chunk_text = doc_chunk.page_content.strip()
                if not chunk_text:
                    continue
                start_index = int(doc_chunk.metadata.get("start_index", 0))
                chunk_id = self._make_chunk_id(source_name, doc_hash, i, chunk_text)
                chunks.append(
                    Chunk(
                        id=chunk_id,
                        source=source_name,
                        content=chunk_text,
                        order=i,
                        start_index=start_index,
                        doc_hash=doc_hash,
                    )
                )

        if not chunks:
            raise ValueError("No textual content extracted from uploaded files.")

        if self.persist_directory.exists():
            shutil.rmtree(self.persist_directory)
        self.persist_directory.mkdir(parents=True, exist_ok=True)

        chroma = Chroma(
            collection_name=settings.chroma_collection,
            embedding_function=self.embedding_service,
            persist_directory=str(self.persist_directory),
        )

        chroma.add_texts(
            texts=[chunk.content for chunk in chunks],
            metadatas=[
                {
                    "source": chunk.source,
                    "chunk_id": chunk.id,
                    "order": chunk.order,
                    "start_index": chunk.start_index,
                    "doc_hash": chunk.doc_hash,
                }
                for chunk in chunks
            ],
            ids=[chunk.id for chunk in chunks],
        )
        chroma.persist()
        build_duration = time.perf_counter() - start
        logger.info("Persisted %s chunks to Chroma in %.2fs", len(chunks), build_duration)
        vector_store_manager.reset()

    def split_into_chunks(self, text: str, source_name: str, doc_hash: str) -> List[Document]:
        base_metadata = {"source": source_name, "doc_hash": doc_hash}
        return self.text_splitter.create_documents([text], metadatas=[base_metadata])

    def _make_chunk_id(self, source: str, doc_hash: str, index: int, content: str) -> str:
        digest = hashlib.md5(f"{doc_hash}:{index}:{content[:50]}".encode("utf-8")).hexdigest()
        return f"{source}-{index}-{digest}"
