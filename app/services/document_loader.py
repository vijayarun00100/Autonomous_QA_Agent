from __future__ import annotations

import io
import json
import mimetypes
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import fitz  # type: ignore
from bs4 import BeautifulSoup
from unstructured.partition.auto import partition

TEXT_EXTENSIONS = {".txt", ".md", ".markdown"}
JSON_EXTENSIONS = {".json"}
HTML_EXTENSIONS = {".html", ".htm"}
PDF_EXTENSIONS = {".pdf"}


def detect_mime_type(path: Path) -> str:
    mime, _ = mimetypes.guess_type(path.name)
    return mime or "text/plain"


def read_text_document(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def read_json_document(path: Path) -> str:
    data = json.loads(path.read_text(encoding="utf-8"))
    return json.dumps(data, indent=2)


def read_pdf_document(path: Path) -> str:
    with fitz.open(path) as doc:
        text = []
        for page in doc:
            text.append(page.get_text())
        return "\n".join(text)


def read_html_document(path: Path) -> str:
    soup = BeautifulSoup(path.read_text(encoding="utf-8"), "lxml")
    return soup.get_text(separator="\n")


def read_with_unstructured(path: Path) -> str:
    elements = partition(filename=str(path))
    return "\n".join(element.text for element in elements if element.text)


READERS = {
    "text": read_text_document,
    "json": read_json_document,
    "pdf": read_pdf_document,
    "html": read_html_document,
}


class DocumentLoader:
    """Loads heterogeneous document types into raw text."""

    def load_documents(self, files: Dict[str, Path]) -> List[Tuple[str, str]]:
        documents: List[Tuple[str, str]] = []
        for filename, path in files.items():
            suffix = path.suffix.lower()
            if suffix in TEXT_EXTENSIONS:
                text = read_text_document(path)
            elif suffix in JSON_EXTENSIONS:
                text = read_json_document(path)
            elif suffix in HTML_EXTENSIONS:
                text = read_html_document(path)
            elif suffix in PDF_EXTENSIONS:
                text = read_pdf_document(path)
            else:
                try:
                    text = read_with_unstructured(path)
                except Exception as exc:  # noqa: BLE001
                    raise ValueError(f"Unsupported document type for {filename}: {suffix}") from exc
            documents.append((filename, text))
        return documents

    def load_html_raw(self, path: Path) -> str:
        return path.read_text(encoding="utf-8")

    def load_bytes(self, filename: str, contents: bytes) -> io.BytesIO:
        buffer = io.BytesIO(contents)
        buffer.name = filename
        buffer.seek(0)
        return buffer
