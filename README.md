# QA Testing Brain

An autonomous QA agent that builds a documentation-grounded "testing brain" to produce structured test plans and generate executable Selenium test scripts for a target web experience.

The system ingests heterogeneous documentation (product specs, UI/UX guidelines, API references) alongside a target HTML page, builds a fast GPU-accelerated knowledge base using ChromaDB, and exposes two agentic capabilities:

1. **Test Case Generation** – Creates rich, citation-backed QA test cases based on user instructions.
2. **Selenium Script Generation** – Converts a selected test case into a runnable Python Selenium automation, grounded in the provided HTML.

---

## Project Layout

```
QA_GENERATOR/
├── app/
│   ├── api/                # FastAPI routers & dependency wiring
│   ├── core/               # Settings and shared config
│   ├── models/             # Pydantic request/response schemas
│   ├── services/           # Ingestion, embeddings, agents, state managers
│   └── utils/              # Parsing helpers
├── assets/
│   └── checkout.html       # Sample E-Shop checkout page (selectors for Selenium)
├── frontend/
│   └── app.py              # Streamlit user interface
├── support_docs/           # Example documentation used to ground the agents
├── requirements.txt        # Python dependencies
├── README.md               # (this file)
└── main.py                 # FastAPI entrypoint (dev convenience)
```

---

## Prerequisites

* **Python**: 3.10+
* **CUDA-capable GPU** (recommended) with compatible NVIDIA drivers + CUDA toolkit
* **pip** & **virtualenv** (or conda)

> **Note:** The system detects CUDA availability and will fall back to CPU if GPUs are unavailable. To force CPU mode, set `USE_CUDA=false` in the environment.

---

## Setup Instructions

1. **Clone the repository**
   ```bash
   git clone <repo-url>
   cd QA_GENERATOR
   ```

2. **Create & activate a virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   Copy the example file and fill in your credentials:
   ```bash
   cp .env.example .env
   ```
   Then edit `.env` with your Groq API key:
   ```bash
   GROQ_API_KEY=gsk_...
   USE_CUDA=true  # set to false to force CPU
   ```

---

## Running the Applications

### 1. Start the FastAPI Backend

```bash
uvicorn app.api.main:app --host 0.0.0.0 --port 8000 --reload
```

*Or use the convenience script:*
```bash
python main.py
```

### 2. Launch the Streamlit Frontend

In a separate terminal (with the same virtualenv activated):
```bash
streamlit run frontend/app.py
```

By default, the FastAPI API base URL is `http://localhost:8000`. If you deploy elsewhere, update it in the Streamlit sidebar.

---

## Usage Walkthrough

1. **Upload Documentation & HTML**
   * Use the Streamlit UI to upload support documents (Markdown, TXT, JSON, PDF) and the `checkout.html` page.
   * Click **Build Knowledge Base**. The backend parses documents, chunks them, and embeds the content using a CUDA-enabled SentenceTransformer, persisting vectors in ChromaDB. Typical builds finish in seconds for the sample docs (<5 minutes even with larger corpora).

2. **Generate Test Cases**
   * Provide a natural-language instruction (e.g., “Generate all positive and negative test cases for the discount code feature.”)
   * The agent retrieves the most relevant documentation snippets and produces citation-backed JSON test cases.

3. **Generate Selenium Scripts**
   * Select a previously generated test case and click **Generate Selenium Script**.
   * The agent retrieves full `checkout.html` markup + contextual docs and returns a runnable Python Selenium script with accurate selectors, waits, and assertions.

4. **Copy & Execute Scripts**
   * Copy the script from Streamlit, save it as a `.py` file, install Selenium drivers (e.g., ChromeDriver), and execute it in your automation environment.

---

## Support Documents Included

* `support_docs/product_specs.md` – Business rules (discount codes, shipping, cart logic, payment success criteria).
* `support_docs/ui_ux_guide.txt` – UX requirements (color usage, validation behaviors, accessibility cues, interaction feedback).
* `support_docs/api_endpoints.json` – Mock API contract for coupon application and order submission.
* `assets/checkout.html` – Target E-Shop checkout page with product catalog, cart UI, validation, and success banner.

The agent references these files by name in every response to guarantee grounded outputs.

---

## Demo Video

Record a 5–10 minute walkthrough demonstrating:

1. Uploading the provided documentation & HTML.
2. Building the knowledge base.
3. Generating test cases for a feature.
4. Selecting a test case and producing Selenium code.

> Include the final video at `demo/demo.mp4` or upload it separately per submission requirements.

---

## Performance Considerations

* **GPU Acceleration:** Embedding generation leverages CUDA when available, massively reducing knowledge base build times.
* **Batching & Chunking:** The ingestion pipeline batches chunks to minimize model invocations.
* **Warm Model Reuse:** The embedding model and Groq client are instantiated once and reused across requests.

With the sample documentation set, knowledge base construction typically completes in under 30 seconds on a modern GPU.

---

## Testing & Validation

1. Start FastAPI and Streamlit.
2. Upload the provided support docs and `checkout.html`.
3. Generate test cases for discount codes.
4. Generate a Selenium script for the SAVE15 scenario.
5. Verify the script uses selectors present in `assets/checkout.html` and includes assertions for discount and payment success messaging.

---

## Roadmap Ideas

* Multi-page project ingestion with sitemap parsing.
* Feedback loop to validate generated Selenium scripts directly against a running test server.
* Fine-grained document tagging (requirements vs. UI vs. API) to steer test views.

---

## License

MIT License (add the license text or adjust according to your needs).
