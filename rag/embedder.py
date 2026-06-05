"""
Builds FAISS vector index from parsed filing chunks.
Model: sentence-transformers/all-MiniLM-L6-v2 (free, no API key needed)
"""
import json, pickle
from pathlib import Path

PARSED_DIR  = Path(__file__).parent.parent / "data" / "parsed"
VSTORE_DIR  = Path(__file__).parent.parent / "vector_store"
VSTORE_DIR.mkdir(parents=True, exist_ok=True)
FAISS_PATH  = VSTORE_DIR / "faiss_index.faiss"
DOCS_PATH   = VSTORE_DIR / "documents.pkl"


def load_parsed():
    docs = []
    for p in sorted(PARSED_DIR.glob("*.json")):
        data = json.loads(p.read_text())
        for i, chunk in enumerate(data.get("chunks", [])):
            docs.append({
                "text": chunk, "ticker": data["ticker"],
                "company": data["company"], "form_type": data["form_type"],
                "filing_date": data["filing_date"], "source_url": data["source_url"],
                "local_file": data["local_file"], "chunk_index": i,
                "doc_id": f"{data['ticker']}_{data['form_type']}_{data['filing_date']}_{i}",
            })
    return docs


def build_index(docs=None, force_rebuild=False):
    if FAISS_PATH.exists() and DOCS_PATH.exists() and not force_rebuild:
        import faiss
        index = faiss.read_index(str(FAISS_PATH))
        docs  = pickle.loads(DOCS_PATH.read_bytes())
        return index, docs
    if docs is None:
        docs = load_parsed()
    if not docs:
        raise ValueError("No parsed documents. Run parser first.")
    from sentence_transformers import SentenceTransformer
    import faiss, numpy as np
    print(f"Building index from {len(docs)} chunks...")
    model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    embeddings = model.encode([d["text"] for d in docs], batch_size=64,
                               show_progress_bar=True, convert_to_numpy=True,
                               normalize_embeddings=True)
    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings.astype("float32"))
    faiss.write_index(index, str(FAISS_PATH))
    DOCS_PATH.write_bytes(pickle.dumps(docs))
    print(f"[OK] Index: {index.ntotal} vectors")
    return index, docs