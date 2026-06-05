"""Quant-to-narrative: surfaces MD&A commentary for material metric moves."""
import re
THRESHOLD_PCT = 10.0

def find_narrative(ticker, metric, filing_date, direction):
    try:
        from rag.retriever import retrieve
        query = f"{ticker} {metric.replace('_',' ')} {direction} explanation {filing_date[:4]} MD&A"
        chunks = retrieve(query, top_k=3, filters={"ticker": ticker})
        nearby = [c for c in chunks if filing_date[:4] in c["filing_date"]] or chunks[:2]
        relevant = []
        for c in nearby:
            for s in re.split(r'(?<=[.!?])\s+', c["text"]):
                if any(w in s.lower() for w in [metric.replace("_"," "), direction, "revenue","margin"]):
                    relevant.append(f'"{s.strip()}" [{c["company"]} {c["form_type"]} {c["filing_date"][:7]}]')
        return "\n".join(relevant[:3]) or None
    except Exception:
        return None

def generate_narrative_insights(df):
    insights = []
    cols = [c for c in ["revenue","gross_margin_pct","operating_margin_pct","net_margin_pct"] if c in df.columns]
    for ticker, grp in df.groupby("ticker"):
        grp = grp.sort_values("filing_date").reset_index(drop=True)
        for metric in cols:
            vals = grp[[metric,"filing_date","source_url"]].dropna()
            for i in range(1, len(vals)):
                prev, curr = vals.iloc[i-1][metric], vals.iloc[i][metric]
                if prev == 0: continue
                chg = (curr-prev)/abs(prev)*100
                if abs(chg) < THRESHOLD_PCT: continue
                direction = "increase" if chg > 0 else "decrease"
                narrative = find_narrative(ticker, metric, str(vals.iloc[i]["filing_date"])[:10], direction)
                insights.append({
                    "ticker": ticker, "metric": metric,
                    "filing_date": str(vals.iloc[i]["filing_date"])[:10],
                    "prev_value": round(prev,2), "curr_value": round(curr,2),
                    "change_pct": round(chg,2), "direction": direction,
                    "narrative": narrative or "No MD&A passage found in corpus.",
                    "source_url": vals.iloc[i]["source_url"],
                })
    return insights