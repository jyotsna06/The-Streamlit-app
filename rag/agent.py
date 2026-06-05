"""
5-step agentic RAG pipeline using Claude (Anthropic).
1. Query rewriting   2. Dual retrieval   3. Relevance verification
4. Grounded answer   5. Self-check (refuse if hallucinated)
"""
import os, json, re


def get_llm(model: str = "claude-sonnet-4-5"):
    """
    Supported models (cheapest → most capable):
      claude-haiku-3-5        ~$0.80/$4   per M tokens  (fastest, cheapest)
      claude-sonnet-4-5       ~$3/$15     per M tokens  (recommended)
      claude-opus-4           ~$15/$75    per M tokens  (most capable)
    """
    key = os.getenv("ANTHROPIC_API_KEY", "")
    if not key:
        raise EnvironmentError("ANTHROPIC_API_KEY not set. Add it to .env or the sidebar.")
    from langchain_anthropic import ChatAnthropic
    return ChatAnthropic(model=model, temperature=0, api_key=key, max_tokens=1024)


def run_agent(query: str, model: str = "claude-sonnet-4-5") -> dict:
    """Full agentic pipeline. Returns answer, citations, is_grounded, rewritten_query."""
    try:
        llm = get_llm(model)
    except EnvironmentError as e:
        return {"answer": f"⚠️ {e}", "citations": [], "is_grounded": False,
                "rewritten_query": query, "chunks_used": 0}

    # Step 1 — Query rewriting
    try:
        rq = llm.invoke(
            "Rewrite this question for searching SEC 10-K/10-Q filings. "
            "Expand abbreviations, add relevant financial terms. "
            "Return ONLY the rewritten question, nothing else.\n\n"
            f"Original: {query}"
        ).content.strip()
    except Exception:
        rq = query

    # Step 2 — Dual retrieval (rewritten + original)
    from rag.retriever import retrieve, format_context
    chunks = retrieve(rq, top_k=6)
    seen   = {c["doc_id"] for c in chunks}
    for c in retrieve(query, top_k=4):
        if c["doc_id"] not in seen:
            chunks.append(c); seen.add(c["doc_id"])
    chunks = chunks[:8]

    # Step 3 — Relevance verification
    if not chunks or sum(c["score"] for c in chunks) / len(chunks) < 0.25:
        return {
            "answer": "⚠️ No relevant passages found in the indexed filings for this question.",
            "citations": [], "is_grounded": False,
            "rewritten_query": rq, "chunks_used": len(chunks)
        }

    # Step 4 — Answer generation
    context = format_context(chunks)
    try:
        answer = llm.invoke(
            "You are a precise financial analyst. Answer using ONLY the context "
            "below from SEC filings.\n"
            "- Cite every fact with [Source N] matching the labels in context.\n"
            "- For computed metrics, show the formula and inputs.\n"
            "- If a specific figure is NOT in context, say so — never invent numbers.\n"
            "- If the question is entirely unanswerable from context, reply exactly: "
            "'This information is not available in the indexed filings.'\n\n"
            f"Context:\n{context}\n\n"
            f"Question: {query}\n\n"
            "Answer:"
        ).content.strip()
    except Exception as e:
        return {"answer": f"Error calling Claude: {e}", "citations": [],
                "is_grounded": False, "rewritten_query": rq, "chunks_used": len(chunks)}

    # Build citation list from sources referenced in the answer
    citations = [
        {
            "ref":          f"[Source {i}]",
            "company":      c["company"],
            "ticker":       c["ticker"],
            "form_type":    c["form_type"],
            "filing_date":  c["filing_date"],
            "source_url":   c["source_url"],
            "score":        round(c["score"], 3),
        }
        for i, c in enumerate(chunks, 1)
        if f"[Source {i}]" in answer
    ]

    # Step 5 — Self-check grounding
    is_grounded = True
    try:
        chk = llm.invoke(
            "Does every factual claim in the Answer appear in the Context?\n\n"
            f"Context (first 1200 chars):\n{context[:1200]}\n\n"
            f"Answer:\n{answer}\n\n"
            'Reply with JSON only — no other text: '
            '{"grounded": true, "issues": ""} or {"grounded": false, "issues": "explanation"}'
        ).content.strip()
        m = re.search(r'\{.*\}', chk, re.DOTALL)
        if m:
            r = json.loads(m.group())
            if not r.get("grounded", True):
                answer = (f"⚠️ **Self-check flagged:** {r.get('issues', '')}\n\n"
                          f"{answer}")
                is_grounded = False
    except Exception:
        pass  # Self-check failure is non-fatal; return answer as-is

    return {
        "answer":          answer,
        "citations":       citations,
        "is_grounded":     is_grounded,
        "rewritten_query": rq,
        "chunks_used":     len(chunks),
    }