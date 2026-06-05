"""Evaluates the RAG system: correctness, citation accuracy, hallucination rate."""
import json, re
from pathlib import Path

EVAL_DIR = Path(__file__).parent
QUESTIONS = json.loads((EVAL_DIR / "eval_questions.json").read_text())
RESULTS_FILE = EVAL_DIR / "eval_results.json"

REFUSAL_PATTERNS = [r"not available",r"cannot answer",r"not in the",r"unable to",r"⚠️",r"no relevant"]

def is_refusal(answer):
    return any(re.search(p, answer.lower()) for p in REFUSAL_PATTERNS)

def check_correctness(answer, expected):
    return sum(1 for kw in expected if kw.lower() in answer.lower()) / len(expected) if expected else 0.0

def check_citation(citations, ticker, form):
    return any(c.get("ticker")==ticker and c.get("form_type")==form for c in citations)

def run_evaluation(verbose=True):
    from rag.agent import run_agent
    results = {"answerable":[], "unanswerable":[], "summary":{}}
    correct_scores, cite_hits = [], []
    for q in QUESTIONS["answerable"]:
        if verbose: print(f"  [{q['id']}] {q['question'][:60]}...")
        resp = run_agent(q["question"], model="claude-sonnet-4-5")
        ans, cits = resp.get("answer",""), resp.get("citations",[])
        corr = check_correctness(ans, q.get("expected_contains",[]))
        cite = check_citation(cits, q.get("expected_source_ticker",""), q.get("expected_form",""))
        correct_scores.append(corr); cite_hits.append(int(cite))
        results["answerable"].append({"id":q["id"],"question":q["question"],
            "answer":ans[:500],"correctness":round(corr,3),"citation_ok":cite})
    refusals = []
    for q in QUESTIONS["unanswerable"]:
        if verbose: print(f"  [{q['id']}] {q['question'][:60]}...")
        resp = run_agent(q["question"])
        refused = is_refusal(resp.get("answer",""))
        refusals.append(int(refused))
        results["unanswerable"].append({"id":q["id"],"question":q["question"],
            "answer":resp.get("answer","")[:300],"refused":refused,"reason":q.get("reason","")})
    n_a, n_u = len(QUESTIONS["answerable"]), len(QUESTIONS["unanswerable"])
    summary = {
        "answer_correctness_pct": round(sum(correct_scores)/n_a*100,1),
        "citation_accuracy_pct":  round(sum(cite_hits)/n_a*100,1),
        "hallucination_rate_pct": round((1-sum(refusals)/n_u)*100,1),
        "refusal_rate_pct":       round(sum(refusals)/n_u*100,1),
    }
    summary["interpretation"] = (
        f"System correctly answered {summary['answer_correctness_pct']}% of answerable questions "
        f"with {summary['citation_accuracy_pct']}% citation accuracy. "
        f"Hallucination rate on unanswerable questions: {summary['hallucination_rate_pct']}%."
    )
    results["summary"] = summary
    RESULTS_FILE.write_text(json.dumps(results, indent=2))
    if verbose:
        for k,v in summary.items(): print(f"  {k}: {v}")
    return results

if __name__ == "__main__":
    run_evaluation()