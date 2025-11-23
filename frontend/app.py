from __future__ import annotations

import io
import json
import time
import uuid
from typing import Dict, List

import httpx
import streamlit as st
import streamlit.components.v1 as components

API_BASE_URL = "http://localhost:8000"

st.set_page_config(page_title="QA Testing Brain", layout="wide")
st.title("QA Testing Brain")

st.markdown(
    """
    <style>
    .block-container {padding: 2.5rem 3rem 3rem;}
    .stTextInput>div>div>input,
    .stTextArea textarea,
    .stNumberInput input {
        border-radius: 8px;
        border: 1px solid #CBD5E1;
    }
    .stButton>button {
        border-radius: 8px;
        padding: 0.6rem 1.2rem;
    }
    .divider {
        margin: 1.5rem 0 1.75rem;
        border-top: 1px solid #E2E8F0;
    }
    .phase-label {
        color: #475569;
        font-size: 0.85rem;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        margin-bottom: 0.2rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def post_files(endpoint: str, files: Dict[str, io.BytesIO]) -> dict:
    multipart_files = []
    for filename, buffer in files.items():
        buffer.seek(0)
        multipart_files.append(("files", (filename, buffer.read(), "application/octet-stream")))
    with httpx.Client(timeout=180.0) as client:
        response = client.post(f"{API_BASE_URL}{endpoint}", files=multipart_files)
        response.raise_for_status()
        return response.json()


def post_json(endpoint: str, payload: dict) -> dict:
    with httpx.Client(timeout=180.0) as client:
        response = client.post(f"{API_BASE_URL}{endpoint}", json=payload)
        response.raise_for_status()
        return response.json()


if "test_cases" not in st.session_state:
    st.session_state.test_cases = []


def render_copy_button(script: str, key: str) -> None:
    result = components.html(
        f"""
        <div style="margin-top:0.5rem;">
            <button id="{key}" style="border:none;background:#0f172a;color:white;padding:0.45rem 0.9rem;border-radius:6px;cursor:pointer;">
                Copy to clipboard
            </button>
        </div>
        <script>
        const button = document.getElementById('{key}');
        if (button) {{
            button.addEventListener('click', async () => {{
                await navigator.clipboard.writeText({json.dumps(script)});
                window.parent.postMessage(JSON.stringify({{'type': 'streamlit:setComponentValue', 'key': '{key}', 'value': 'copied'}}), '*');
            }});
        }}
        </script>
        """,
        height=60,
        key=key,
    )
    if result == "copied":
        st.toast("Copied to clipboard", icon="✅")


with st.sidebar:
    API_BASE_URL = st.text_input("FastAPI Base URL", value=API_BASE_URL)

st.markdown("<div class='phase-label'>Phase 1</div>", unsafe_allow_html=True)
st.subheader("Build the knowledge base", anchor=False)
st.caption("Upload the supporting documentation and checkout page to seed the testing brain.")

col1, col2 = st.columns(2, gap="large")
with col1:
    doc_files = st.file_uploader(
        "Support documents",
        type=["md", "txt", "json", "pdf"],
        accept_multiple_files=True,
    )
with col2:
    html_files = st.file_uploader("Checkout HTML", type=["html", "htm"], accept_multiple_files=False)

build_kb = st.button("Build knowledge base", type="primary")

if build_kb:
    if not doc_files and not html_files:
        st.error("Please upload at least one document or HTML file.")
    else:
        buffers: Dict[str, io.BytesIO] = {}
        for uploaded in doc_files or []:
            buffer = io.BytesIO(uploaded.getvalue())
            buffers[uploaded.name] = buffer
        if html_files is not None:
            buffer = io.BytesIO(html_files.getvalue())
            buffers[html_files.name] = buffer

        with st.spinner("Building knowledge base with high-fidelity embeddings and metadata..."):
            start_time = time.perf_counter()
            try:
                payload = post_files("/ingest", buffers)
            except Exception as exc:  # noqa: BLE001
                st.error(f"Failed to build knowledge base: {exc}")
            else:
                duration = payload.get("duration_seconds", time.perf_counter() - start_time)
                st.success(
                    f"Knowledge base built in {duration:.2f}s · {payload.get('documents_processed', 0)} documents"
                )
                st.session_state.test_cases = []

st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

st.markdown("<div class='phase-label'>Phase 2</div>", unsafe_allow_html=True)
st.subheader("Ask for grounded test cases", anchor=False)

query = st.text_area(
    "Prompt",
    placeholder="Generate all positive and negative test cases for the discount code feature.",
    height=110,
)
controls_col, info_col = st.columns([1, 3], gap="large")
with controls_col:
    top_k = st.number_input("Retriever Top-K", min_value=1, max_value=12, value=6, step=1)
with info_col:
    st.caption("Describe the coverage you need; retrieved context keeps every test grounded in the docs.")

generate_cases = st.button("Generate test cases", type="primary")

if generate_cases:
    if not query.strip():
        st.error("Please provide an instruction for the agent.")
    else:
        with st.spinner("Retrieving knowledge base context and drafting cases..."):
            try:
                response = post_json("/generate-test-cases", {"query": query, "top_k": top_k})
            except httpx.HTTPStatusError as exc:
                st.error(f"Agent failed: {exc.response.text}")
            except Exception as exc:  # noqa: BLE001
                st.error(f"Unexpected error: {exc}")
            else:
                st.session_state.test_cases = response.get("test_cases", [])
                st.success(f"Generated {len(st.session_state.test_cases)} test cases.")

st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

if st.session_state.test_cases:
    st.markdown("<div class='phase-label'>Phase 3</div>", unsafe_allow_html=True)
    st.subheader("Review & automate", anchor=False)

    for case in st.session_state.test_cases:
        with st.expander(f"{case['test_id']} · {case['feature']}"):
            st.markdown(f"**Scenario**: {case['scenario']}")
            st.markdown("**Steps**")
            for step in case.get("steps", []):
                st.markdown(f"- {step}")
            st.markdown(f"**Expected result**: {case['expected_result']}")
            st.markdown(f"**Grounded in**: {', '.join(case.get('grounded_in', []))}")

    options = [f"{case['test_id']} · {case['scenario']}" for case in st.session_state.test_cases]
    selected_label = st.selectbox("Select a test case to automate", options=options)
    generate_script = st.button("Generate Selenium script", type="secondary")

    if generate_script:
        selected_case = st.session_state.test_cases[options.index(selected_label)]
        with st.spinner("Assembling HTML context and crafting Selenium steps..."):
            try:
                response = post_json("/generate-selenium-script", {"test_case": selected_case})
            except httpx.HTTPStatusError as exc:
                st.error(f"Script generation failed: {exc.response.text}")
            except Exception as exc:  # noqa: BLE001
                st.error(f"Unexpected error: {exc}")
            else:
                st.success("Selenium script ready.")
                st.code(response.get("script", ""), language="python")
                st.caption(f"Grounded in: {', '.join(response.get('grounded_in', []))}")
else:
    st.info("Generate test cases to unlock Selenium automation.")
