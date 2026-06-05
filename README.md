# Comparative Financial Analysis Dashboard

**Companies:** NVIDIA (NVDA) · AMD · Intel (INTC)  
**Data Source:** [SEC EDGAR](https://www.sec.gov/cgi-bin/browse-edgar) — public 10-K and 10-Q filings (2022–2024)

An interactive Streamlit dashboard that downloads SEC filings, extracts financial metrics, builds a local vector search index, and provides grounded Q&A with source citations.

---

## How to Run

### 1. Clone and install

```bash
git clone https://github.com/jyotsna06/The-Streamlit-app.git
cd The-Streamlit-app
python -m venv venv
```

**Windows (PowerShell):**
```powershell
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

**macOS / Linux:**
```bash
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

### 2. Configure API key

Edit `.env` and add your Anthropic key (required for RAG Chatbot and Evaluation tabs only):

```
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

The key is loaded from `.env` only — it is never shown in the UI. `.env` is listed in `.gitignore` and must not be committed.

### 3. Start the app

```bash
python -m streamlit run app.py
```

Open **http://localhost:8501** in your browser.

> Use `python -m streamlit` rather than calling `streamlit` directly if the command is not found on your PATH.

### 4. Build the data pipeline (sidebar, in order)

| Step | Button | What it does |
|------|--------|--------------|
| 1 | **Download Filings from EDGAR** | Fetches 15 HTML filings (~1–2 min) |
| 2 | **Parse & Build Index** | Extracts financials + builds FAISS search index (~2–5 min) |

Wait until the sidebar shows **15 filings**, **Index ready**, and **Data health: 100%**.

### 5. Explore the dashboard

| Tab | Purpose |
|-----|---------|
| **Overview** | Revenue, margins, KPI cards, charts |
| **Verify Data** | Health score, filing inventory, spot-check vs SEC links |
| **Derived Metrics** | YoY growth, CAGR, FCF, debt-to-equity (formulas shown) |
| **RAG Chatbot** | Ask questions about the filings; answers cite SEC sources |
| **Conflicts** | Flags >400% metric jumps between consecutive filings |
| **Evaluation** | Run 20 labeled test questions; scores correctness and hallucination rate |

### 6. Clean and re-fetch data (optional)

```powershell
# From project root — stop Streamlit first (Ctrl+C)
Remove-Item "data\filings\*.html" -Force -ErrorAction SilentlyContinue
Remove-Item "data\filings\metadata.json" -Force -ErrorAction SilentlyContinue
Remove-Item "data\parsed\*.json" -Force -ErrorAction SilentlyContinue
Remove-Item "vector_store\*" -Force -Recurse -ErrorAction SilentlyContinue
```

Then restart the app and run sidebar steps 1 → 2 again.

**CLI alternative (no UI):**
```bash
python -m ingest.downloader
python -c "from ingest.parser import parse_all; parse_all(); from rag.embedder import build_index; build_index(force_rebuild=True)"
python -m streamlit run app.py
```

---

## Design Choices (and Why)

| Choice | What we use | Why |
|--------|-------------|-----|
| **Embeddings** | `sentence-transformers/all-MiniLM-L6-v2` | Free, runs locally, no API cost for indexing ~1,000 filing chunks |
| **Vector store** | FAISS (`IndexFlatIP`, local files) | No cloud DB or server needed; index lives in `vector_store/` and rebuilds from parsed data |
| **LLM** | Claude Sonnet 4.5 (Anthropic API) | Strong financial reasoning at reasonable cost; used only for Q&A and evaluation |
| **Extraction** | Regex over parsed HTML text | Transparent and debuggable; formulas and raw tables visible in Verify Data tab |
| **Orchestration** | Direct function calls in `rag/agent.py` | Simpler than LangGraph for a linear 5-step pipeline; easier to debug |
| **Agentic RAG pipeline** | Rewrite → dual retrieve → relevance check → grounded answer → self-check | Improves recall (query rewrite), reduces hallucination (self-check + citation requirement) |
| **Conflict detection** | >400% jump between consecutive filings | Catches unit mismatches, restatements, and acquisition-driven spikes |
| **Quant-to-narrative** | Semantic search over MD&A for >10% metric moves | Connects numbers to management commentary in the same filing |
| **UI** | Streamlit + custom dark theme + Plotly | Single-file deploy, no separate frontend; charts use company-branded colors |

**Why not Chroma / Pinecone?** The project is designed to be **self-contained and portable** — delete `data/` and `vector_store/`, re-run the pipeline, and everything rebuilds locally.

**Why not OpenAI for embeddings?** Local sentence-transformers keep indexing free; only answer generation requires a paid API.

---

## Document Sources

All filings are downloaded directly from [SEC EDGAR](https://www.sec.gov/cgi-bin/browse-edgar) via the public submissions API. No proprietary data feeds are used.

### Companies

| Ticker | Company | CIK | EDGAR browse |
|--------|---------|-----|--------------|
| NVDA | NVIDIA Corporation | [1045810](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=1045810) | [Browse filings](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=1045810&type=10-) |
| AMD | Advanced Micro Devices | [2488](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=2488) | [Browse filings](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=2488&type=10-) |
| INTC | Intel Corporation | [50863](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=50863) | [Browse filings](https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=50863&type=10-) |

### Filings fetched (15 total)

For each company, the downloader retrieves:

- **3 × Form 10-K** — annual reports for fiscal years ending in 2022, 2023, and 2024
- **2 × Form 10-Q** — quarterly reports from 2024 (H1 and H2 windows)

Filings are stored as HTML in `data/filings/`. Parsed text chunks and extracted financials are saved to `data/parsed/`. Every chart value and chatbot citation links back to the original filing URL on sec.gov.

### Metrics extracted

Revenue, gross profit, operating income, net income, total assets, total debt, total equity, operating cash flow, and capital expenditures — all normalized to **millions USD** with unit detection (thousands / millions / billions).

---

## Project Structure

```
app.py              # Streamlit entry point
ingest/             # EDGAR downloader + HTML parser
rag/                # FAISS embedder, retriever, agentic RAG pipeline
analytics/          # Derived metrics + quant-to-narrative linkage
evaluation/         # 20-question labeled evaluation harness
ui/                 # Styles, charts, data verification helpers
data/               # Downloaded filings + parsed JSON (gitignored)
vector_store/       # FAISS index (gitignored)
```

---

## License & Disclaimer

This tool is for educational and exploratory analysis. Always verify key figures against the original SEC filings before making decisions. Flagged conflicts in the dashboard are heuristics, not proof of data errors.
