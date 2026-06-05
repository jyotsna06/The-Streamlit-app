"""Semantic retriever over the FAISS index."""
import pickle
from pathlib import Path

VSTORE_DIR = Path(__file__).parent.parent / "vector_store"
_model = _index = _docs = None

def _load():
    global _model, _index, _docs
    if _model is None:
        from sentence_transformers import SentenceTransformer
        import faiss
        _model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        _index = faiss.read_index(str(VSTORE_DIR / "faiss_index.faiss"))
        _docs  = pickle.loads((VSTORE_DIR / "documents.pkl").read_bytes())

def retrieve(query, top_k=6, filters=None):
    _load()
    vec = _model.encode([query], normalize_embeddings=True).astype("float32")
    scores, indices = _index.search(vec, top_k * 3)
    results = []
    for score, idx in zip(scores[0], indices[0]):
        if idx < 0: continue
        doc = dict(_docs[idx]); doc["score"] = float(score)
        if filters and not all(doc.get(k)==v for k,v in filters.items()):
            continue
        results.append(doc)
        if len(results) >= top_k: break
    return results

def format_context(chunks):
    parts = []
    for i, c in enumerate(chunks, 1):
        src = f"[Source {i}: {c['company']} {c['form_type']} {c['filing_date'][:7]}]"
        parts.append(f"{src}\n{c['text']}")
    return "\n\n---\n\n".join(parts)