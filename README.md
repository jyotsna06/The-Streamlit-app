# Comparative Financial Analysis Dashboard

**Companies:** NVIDIA (NVDA) · AMD · Intel (INTC)  
**Data Source:** [SEC EDGAR](https://www.sec.gov/cgi-bin/browse-edgar) — public 10-K and 10-Q filings

## Quick Start

```bash
git clone https://github.com/jyotsna06/The-Streamlit-app.git
cd The-Streamlit-app
python -m venv venv
.\venv\Scripts\Activate.ps1   # Windows
pip install -r requirements.txt
copy .env.example .env
# Add your Anthropic API key to .env
python -m streamlit run app.py
```

## Usage

1. **Sidebar → Download Filings** — pulls 15 filings from SEC EDGAR
2. **Sidebar → Parse & Build Index** — extracts text, builds FAISS vector index
3. Explore the dashboard tabs: Overview, Verify Data, Derived Metrics, RAG Chatbot, Conflicts, Evaluation

## API Key

The Anthropic API key is loaded from `.env` only (not shown in the UI):

```
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

Required for the RAG Chatbot and Evaluation tabs.

## Design Choices

- **Embeddings:** sentence-transformers/all-MiniLM-L6-v2 (free, local)
- **LLM:** Claude Sonnet via Anthropic API
- **Vector DB:** FAISS (local, no infra needed)
- **Agentic pipeline:** query rewriting → retrieval → verification → answer → self-check
- **Conflict detection:** flags >400% metric change between consecutive filings

## Document Sources

- NVIDIA CIK: 1045810
- AMD CIK: 2488
- Intel CIK: 50863
