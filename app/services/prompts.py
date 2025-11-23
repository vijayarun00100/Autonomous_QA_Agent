from __future__ import annotations

from textwrap import dedent
from typing import List


def build_system_prompt() -> str:
    return dedent(
        """
        You are QA-TestBrain, an autonomous quality assurance expert. You strictly ground every response in the provided documentation excerpts.
        You must never invent features that are not explicitly referenced in the supplied context. Cite the source document identifiers for every statement.
        """
    ).strip()


def build_test_case_prompt(query: str, contexts: List[dict]) -> str:
    context_blocks = []
    for idx, ctx in enumerate(contexts, start=1):
        source = ctx.get("metadata", {}).get("source", "unknown_source")
        snippet = ctx.get("page_content", "").strip()
        context_blocks.append(f"Context {idx} (source: {source}):\n{snippet}")

    combined_context = "\n\n".join(context_blocks)
    return dedent(
        f"""
        CONTEXT MATERIAL
        -----------------
        {combined_context}

        TASK
        ----
        Follow the user instruction below to produce a comprehensive, structured QA test plan.
        - Cover both positive and negative scenarios when applicable.
        - Provide each test case as a JSON object with the following keys:
          test_id, feature, scenario, steps (array of strings), expected_result, grounded_in (array of source documents).
        - Ensure grounded_in references only source documents present in the context.
        - Output MUST be a JSON array. Do not include any commentary before or after the JSON.

        USER INSTRUCTION: {query}
        """
    ).strip()


def build_selenium_prompt(test_case_json: str, contexts: List[dict], html_snippet: str) -> str:
    context_blocks = []
    for idx, ctx in enumerate(contexts, start=1):
        source = ctx.get("metadata", {}).get("source", "unknown_source")
        snippet = ctx.get("page_content", "").strip()
        context_blocks.append(f"Context {idx} (source: {source}):\n{snippet}")

    combined_context = "\n\n".join(context_blocks)

    return dedent(
        f"""
        CONTEXT MATERIAL
        -----------------
        {combined_context}

        HTML SOURCE (checkout.html extract)
        -----------------------------------
        {html_snippet}

        TASK
        ----
        Using the provided test case JSON, generate a complete Python Selenium 4 script that automates the scenario.
        Requirements:
        - Use Selenium's modern API with WebDriverWait and expected_conditions for synchronization.
        - Use accurate selectors (prefer id, name; otherwise CSS selectors) that exist in the provided HTML.
        - Include comments describing each major step.
        - Include assertions to verify the expected outcomes from the documentation.
        - Wrap the script in a main guard so it can be run directly.
        - Output ONLY the Python script without additional commentary.

        TEST CASE JSON
        --------------
        {test_case_json}
        """
    ).strip()
