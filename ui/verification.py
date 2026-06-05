"""Data verification helpers — inspect filing health and extraction quality."""
import json
from pathlib import Path

import pandas as pd

FINANCIAL_FIELDS = [
    "revenue", "gross_profit", "operating_income", "net_income",
    "total_assets", "total_debt", "total_equity",
    "operating_cash_flow", "capex",
]


def get_paths(root: Path):
    return {
        "filings": root / "data" / "filings",
        "parsed": root / "data" / "parsed",
        "metadata": root / "data" / "filings" / "metadata.json",
        "index": root / "vector_store" / "faiss_index.faiss",
    }


def load_metadata(root: Path) -> list:
    meta_path = get_paths(root)["metadata"]
    if not meta_path.exists():
        return []
    return json.loads(meta_path.read_text())


def get_health_summary(root: Path) -> dict:
    paths = get_paths(root)
    meta = load_metadata(root)
    parsed_files = list(paths["parsed"].glob("*.json")) if paths["parsed"].exists() else []

    with_financials = 0
    total_chunks = 0
    for p in parsed_files:
        data = json.loads(p.read_text())
        if data.get("financials"):
            with_financials += 1
        total_chunks += len(data.get("chunks", []))

    valid_filings = 0
    for item in meta:
        fpath = paths["filings"] / item["local_file"]
        if fpath.exists() and fpath.stat().st_size > 50_000:
            valid_filings += 1

    return {
        "total_filings": len(meta),
        "valid_filings": valid_filings,
        "parsed_count": len(parsed_files),
        "with_financials": with_financials,
        "total_chunks": total_chunks,
        "index_ready": paths["index"].exists(),
        "tickers": sorted({m["ticker"] for m in meta}) if meta else [],
    }


def get_filing_inventory(root: Path) -> pd.DataFrame:
    paths = get_paths(root)
    rows = []
    for item in load_metadata(root):
        fpath = paths["filings"] / item["local_file"]
        size_kb = round(fpath.stat().st_size / 1024, 1) if fpath.exists() else 0
        parsed_path = paths["parsed"] / f"{fpath.stem}.json"
        parsed = parsed_path.exists()
        fin_fields = 0
        chunks = 0
        if parsed:
            data = json.loads(parsed_path.read_text())
            fin = data.get("financials", {})
            fin_fields = sum(1 for k in FINANCIAL_FIELDS if fin.get(k) is not None)
            chunks = len(data.get("chunks", []))
        rows.append({
            "Ticker": item["ticker"],
            "Form": item["form_type"],
            "Filing Date": item["filing_date"],
            "File Size (KB)": size_kb,
            "Parsed": "✓" if parsed else "—",
            "Financial Fields": fin_fields,
            "Text Chunks": chunks,
            "SEC URL": item["source_url"],
            "Local File": item["local_file"],
        })
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).sort_values(["Ticker", "Filing Date"])


def get_ticker_completeness(root: Path) -> pd.DataFrame:
    inv = get_filing_inventory(root)
    if inv.empty:
        return pd.DataFrame()
    rows = []
    for ticker, grp in inv.groupby("Ticker"):
        total = len(grp)
        parsed = (grp["Parsed"] == "✓").sum()
        avg_fields = grp["Financial Fields"].mean()
        rows.append({
            "Ticker": ticker,
            "Filings": total,
            "Parsed": parsed,
            "Parse Rate": f"{parsed / total * 100:.0f}%",
            "Avg Fields/Filing": round(avg_fields, 1),
            "Status": "Complete" if parsed == total and avg_fields >= 4 else "Partial",
        })
    return pd.DataFrame(rows)


def get_spot_check(root: Path, local_file: str) -> dict:
    paths = get_paths(root)
    meta = {m["local_file"]: m for m in load_metadata(root)}
    item = meta.get(local_file)
    if not item:
        return {}
    parsed_path = paths["parsed"] / f"{Path(local_file).stem}.json"
    parsed_data = json.loads(parsed_path.read_text()) if parsed_path.exists() else {}
    return {
        "meta": item,
        "financials": parsed_data.get("financials", {}),
        "chunks": len(parsed_data.get("chunks", [])),
        "parsed": parsed_path.exists(),
    }


def compute_health_score(summary: dict) -> int:
    if summary["total_filings"] == 0:
        return 0
    score = 0
    score += 25 * (summary["valid_filings"] / summary["total_filings"])
    score += 25 * (summary["parsed_count"] / summary["total_filings"])
    score += 25 * (summary["with_financials"] / max(summary["parsed_count"], 1))
    score += 25 if summary["index_ready"] else 0
    return round(score)
