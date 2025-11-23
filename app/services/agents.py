from __future__ import annotations

import asyncio
import json
import logging
from typing import List

from langchain.schema import HumanMessage, SystemMessage

from app.models.schemas import (
    SeleniumScriptRequest,
    SeleniumScriptResponse,
    TestCase,
    TestCaseRequest,
    TestCaseResponse,
)
from app.services.llm import get_llm_service
from app.services.prompts import (
    build_selenium_prompt,
    build_system_prompt,
    build_test_case_prompt,
)
from app.services.retriever import KnowledgeRetriever
from app.services.state import app_state
from app.services.document_loader import DocumentLoader
from app.utils.parsers import JSONParsingError, ensure_string_list, extract_json_array

logger = logging.getLogger(__name__)


def _ensure_event_loop() -> asyncio.AbstractEventLoop:
    try:
        return asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop


class AgentOrchestrator:
    def __init__(self, retriever: KnowledgeRetriever) -> None:
        self.retriever = retriever
        self.llm_service = get_llm_service()
        self.document_loader = DocumentLoader()

    async def generate_test_cases(self, request: TestCaseRequest) -> TestCaseResponse:
        contexts = self.retriever.raw_search(request.query, top_k=request.top_k)
        if not contexts:
            raise ValueError("Knowledge base returned no context for the query.")

        prompt = build_test_case_prompt(request.query, contexts)
        raw_output = await self._invoke_llm(prompt)

        try:
            parsed = extract_json_array(raw_output)
        except JSONParsingError as exc:  # noqa: BLE001
            logger.error("Failed to parse test cases JSON: %s", exc)
            raise

        test_cases: List[TestCase] = []
        for idx, item in enumerate(parsed, start=1):
            test_cases.append(
                TestCase(
                    test_id=str(item.get("test_id", f"TC-{idx:03d}")),
                    feature=str(item.get("feature", "")),
                    scenario=str(item.get("scenario", "")),
                    steps=ensure_string_list(item.get("steps", [])),
                    expected_result=str(item.get("expected_result", "")),
                    grounded_in=ensure_string_list(item.get("grounded_in", [])),
                )
            )

        return TestCaseResponse(test_cases=test_cases, raw_output=raw_output)

    async def generate_selenium_script(self, request: SeleniumScriptRequest) -> SeleniumScriptResponse:
        test_case = request.test_case
        query = f"{test_case.feature}: {test_case.scenario}. Steps: {'; '.join(test_case.steps)}"
        contexts = self.retriever.raw_search(query, top_k=6)
        if not contexts:
            raise ValueError("Unable to retrieve context for the provided test case.")

        if not app_state.latest_html_path:
            raise ValueError("checkout.html has not been ingested yet; upload it before generating scripts.")

        html_raw = self.document_loader.load_html_raw(app_state.latest_html_path)
        test_case_json = json.dumps(test_case.model_dump(), indent=2)
        prompt = build_selenium_prompt(test_case_json, contexts, html_raw)
        raw_output = await self._invoke_llm(prompt)

        grounded_sources = set(test_case.grounded_in)
        for ctx in contexts:
            source = ctx.get("metadata", {}).get("source")
            if source:
                grounded_sources.add(source)

        return SeleniumScriptResponse(script=raw_output, grounded_in=sorted(grounded_sources), raw_output=raw_output)

    async def _invoke_llm(self, user_prompt: str) -> str:
        model = self.llm_service.get_model()
        messages = [SystemMessage(content=build_system_prompt()), HumanMessage(content=user_prompt)]

        loop = _ensure_event_loop()
        response = await asyncio.to_thread(model.invoke, messages)
        output = response.content if hasattr(response, "content") else str(response)
        logger.debug("LLM response length: %s", len(output))
        return output.strip()
