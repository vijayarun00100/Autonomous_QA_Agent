from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, Field


class DocumentMetadata(BaseModel):
    source_document: str
    source_path: Optional[Path] = None


class IngestionStatus(BaseModel):
    success: bool
    message: str
    documents_processed: int = 0
    duration_seconds: float = 0.0


class TestCaseRequest(BaseModel):
    query: str = Field(..., description="Instruction for generating test cases")
    top_k: int = Field(6, description="Number of context chunks to retrieve")


class TestCase(BaseModel):
    test_id: str
    feature: str
    scenario: str
    steps: List[str]
    expected_result: str
    grounded_in: List[str]


class TestCaseResponse(BaseModel):
    test_cases: List[TestCase]
    raw_output: str


class SeleniumScriptRequest(BaseModel):
    test_case: TestCase


class SeleniumScriptResponse(BaseModel):
    script: str
    grounded_in: List[str]
    raw_output: str
