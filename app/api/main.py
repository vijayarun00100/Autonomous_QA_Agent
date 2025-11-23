from __future__ import annotations

import time
import logging
from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.models.schemas import (
    IngestionStatus,
    SeleniumScriptRequest,
    SeleniumScriptResponse,
    TestCaseRequest,
    TestCaseResponse,
)
from app.services.agents import AgentOrchestrator
from app.services.ingestion import KnowledgeBaseBuilder
from app.services.retriever import KnowledgeRetriever
from app.services.state import app_state


logger = logging.getLogger(__name__)


app = FastAPI(title=settings.app_name)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"]
    ,
    allow_headers=["*"],
)


kb_builder = KnowledgeBaseBuilder()
retriever = KnowledgeRetriever()
agent_orchestrator = AgentOrchestrator(retriever=retriever)


@app.get("/health", tags=["system"])
def health_check() -> Dict[str, str]:
    return {"status": "ok"}


@app.post("/ingest", response_model=IngestionStatus, tags=["knowledge-base"])
async def ingest_documents(files: list[UploadFile]) -> IngestionStatus:
    if not files:
        raise HTTPException(status_code=400, detail="No files provided for ingestion")

    start = time.perf_counter()
    documents_processed = 0
    stored_files: Dict[str, Path] = {}

    try:
        for upload in files:
            contents = await upload.read()
            saved_path = kb_builder.save_upload(upload.filename, contents)
            stored_files[upload.filename] = saved_path
            documents_processed += 1
            app_state.update_file(upload.filename, saved_path)

        kb_builder.build_knowledge_base(stored_files)
        retriever.refresh()

        duration = time.perf_counter() - start
        return IngestionStatus(
            success=True,
            message="Knowledge base built successfully",
            documents_processed=documents_processed,
            duration_seconds=duration,
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception("Ingestion failed")
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/generate-test-cases", response_model=TestCaseResponse, tags=["agents"])
async def generate_test_cases(request: TestCaseRequest) -> TestCaseResponse:
    if not retriever.is_ready:
        raise HTTPException(status_code=400, detail="Knowledge base is not ready. Please ingest documents first.")

    result = await agent_orchestrator.generate_test_cases(request)
    return result


@app.post("/generate-selenium-script", response_model=SeleniumScriptResponse, tags=["agents"])
async def generate_selenium_script(request: SeleniumScriptRequest) -> SeleniumScriptResponse:
    if not retriever.is_ready:
        raise HTTPException(status_code=400, detail="Knowledge base is not ready. Please ingest documents first.")

    result = await agent_orchestrator.generate_selenium_script(request)
    return result


@app.exception_handler(Exception)
async def general_exception_handler(request: Any, exc: Exception) -> JSONResponse:  # noqa: ANN401
    return JSONResponse(status_code=500, content={"detail": str(exc)})
