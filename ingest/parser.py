"""
Parses HTML SEC filings → text chunks + extracted financial figures.
Detects reporting units (thousands/millions/billions) to normalize values.
"""
import re, json, warnings
from pathlib import Path
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)

DATA_DIR   = Path(__file__).parent.parent / "data" / "filings"
META_FILE  = DATA_DIR / "metadata.json"
PARSED_DIR = Path(__file__).parent.parent / "data" / "parsed"
PARSED_DIR.mkdir(parents=True, exist_ok=True)

LINE_PATTERNS = {
    "revenue": [
        r"(?:net\s+)?revenue[s]?\s*[\$\|]?\s*([\d,]+)",
        r"total\s+(?:net\s+)?revenue[s]?\s*[\$\|]?\s*([\d,]+)",
    ],
    "gross_profit": [r"gross\s+profit\s*[\$\|]?\s*([\d,]+)"],
    "operating_income": [
        r"(?:income|loss)\s+from\s+operations\s*[\$\|]?\s*\(?([\d,]+)\)?",
        r"operating\s+(?:income|loss)\s*[\$\|]?\s*\(?([\d,]+)\)?",
    ],
    "net_income": [r"net\s+(?:income|loss)\s*[\$\|]?\s*\(?([\d,]+)\)?"],
    "total_assets": [r"total\s+assets\s*[\$\|]?\s*([\d,]+)"],
    "total_debt": [r"total\s+(?:long[- ]term\s+)?debt\s*[\$\|]?\s*([\d,]+)"],
    "total_equity": [r"(?:total\s+)?stockholders['']?\s+equity\s*[\$\|]?\s*\(?([\d,]+)\)?"],
    "operating_cash_flow": [
        r"cash\s+(?:provided|used)\s+(?:by|in)\s+operating\s+activities\s*[\$\|]?\s*\(?([\d,]+)\)?"
    ],
    "capex": [
        r"(?:purchases?\s+of|capital\s+expenditures?)\s+(?:property|pp&e|fixed)\s*[\$\|]?\s*\(?([\d,]+)\)?"
    ],
}


def html_to_text(html):
    soup = BeautifulSoup(html, "lxml")
    for tag in soup(["script","style"]):
        tag.decompose()
    for table in soup.find_all("table"):
        rows = ["\t".join(td.get_text(" ",strip=True) for td in tr.find_all(["td","th"]))
                for tr in table.find_all("tr")]
        table.replace_with("\n" + "\n".join(rows) + "\n")
    text = soup.get_text("\n", strip=True)
    return re.sub(r"\n{4,}", "\n\n\n", text)


def chunk_text(text, chunk_size=800, overlap=100):
    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks, current, length = [], [], 0
    for sent in sentences:
        slen = len(sent.split())
        if length + slen > chunk_size and current:
            chunks.append(" ".join(current))
            overlap_words = " ".join(current).split()[-overlap:]
            current, length = [" ".join(overlap_words)], overlap
        current.append(sent)
        length += slen
    if current:
        chunks.append(" ".join(current))
    return [c for c in chunks if len(c.strip()) > 50]


def _parse_amount(raw):
    if not raw:
        return None
    cleaned = raw.replace(",", "").strip()
    if not cleaned or not re.search(r"\d", cleaned):
        return None
    try:
        return float(cleaned.replace("(", "-").replace(")", ""))
    except ValueError:
        return None


def _first_valid_amount(matches, min_value=10):
    for raw in matches:
        val = _parse_amount(raw)
        if val is not None and abs(val) >= min_value:
            return val
    return None


def _extract_section(text, markers, window=12000):
    for marker in markers:
        idx = text.find(marker)
        if idx >= 0:
            return text[idx:idx + window]
    return text


def _find_income_table(text):
    for marker in [
        "(In millions, except per share data)",
        "($ in millions, except per share data)",
        "Fiscal Year 2024 Summary",
        "Fiscal Year 2023 Summary",
        "Fiscal Year 2022 Summary",
        "Fiscal Year 2021 Summary",
    ]:
        idx = text.find(marker)
        if idx >= 0:
            return text[idx:idx + 3500]

    for pat in [r"Net revenue\t+\$\s*([\d,]{3,})", r"Revenue\t\$\s*([\d,]{3,})"]:
        match = re.search(pat, text, re.IGNORECASE)
        if match:
            start = max(0, match.start() - 200)
            return text[start:start + 3500]

    return _extract_section(
        text,
        ["CONSOLIDATED STATEMENTS OF INCOME", "Consolidated Statements of Income"],
        window=3500,
    )


def _normalize_to_millions(metric, val, text):
    if val is None:
        return None
    text_lower = text.lower()
    if re.search(r"in\s+(?:thousands|000s)", text_lower):
        val *= 0.001
    elif metric in {"revenue", "net_income", "gross_profit", "operating_income", "total_assets"}:
        if val > 500_000:
            val /= 1000.0
    return round(val, 2)


def extract_financials(text):
    text_lower = text.lower()
    income  = _find_income_table(text)
    balance = _extract_section(
        text,
        ["CONSOLIDATED BALANCE SHEETS", "Consolidated Balance Sheets"],
        window=5000,
    )
    cashflow = _extract_section(
        text,
        ["CONSOLIDATED STATEMENTS OF CASH FLOWS", "Consolidated Statements of Cash Flows"],
        window=5000,
    )

    table_patterns = {
        "revenue": [
            r"net\s+revenue\t+\$\s*([\d,]+)",
            r"revenue\t\$\s*([\d,]+)",
            r"total\s+revenue\t\$\s*([\d,]+)",
            r"total\t\$\s*([\d,]+)\s+\t",
        ],
        "gross_profit": [
            r"gross\s+margin\t+([\d,]{3,})",
            r"gross\s+profit\t([\d,]{3,})",
            r"gross\s+profit\t\$\s*([\d,]+)",
        ],
        "operating_income": [
            r"operating\s+income\t([\d,]{3,})",
            r"income\s+from\s+operations\t([\d,]{3,})",
        ],
        "net_income": [r"net\s+income\t\$\s*([\d,]+)"],
        "total_assets": [r"total\s+assets\t\$\s*([\d,]+)"],
        "total_debt": [r"(?:long[- ]term\s+)?debt\t\$\s*([\d,]+)"],
        "total_equity": [
            r"total\s+stockholders['']?\s+equity\t\$\s*([\d,]+)",
            r"total\s+shareholders['']?\s+equity\t\$\s*([\d,]+)",
        ],
        "operating_cash_flow": [
            r"net\s+cash\s+provided\s+by\s+operating\s+activities\t\$\s*([\d,]+)"
        ],
        "capex": [
            r"purchases?\s+of\s+property(?:,\s*plant)?\s+and\s+equipment\t\(?([\d,]+)\)?"
        ],
    }

    results = {}
    sections = {
        "revenue": income,
        "gross_profit": income,
        "operating_income": income,
        "net_income": income,
        "total_assets": balance,
        "total_debt": balance,
        "total_equity": balance,
        "operating_cash_flow": cashflow,
        "capex": cashflow,
    }

    for metric, patterns in table_patterns.items():
        section = sections.get(metric, text)
        for pat in patterns:
            val = _first_valid_amount(re.findall(pat, section, re.IGNORECASE), min_value=50)
            if val is not None:
                results[metric] = _normalize_to_millions(metric, val, section)
                break

    for metric, patterns in LINE_PATTERNS.items():
        if metric in results:
            continue
        for pat in patterns:
            val = _first_valid_amount(re.findall(pat, text_lower), min_value=50)
            if val is not None:
                results[metric] = _normalize_to_millions(metric, val, text)
                break

    if "revenue" in results and "gross_profit" in results:
        if results["gross_profit"] > results["revenue"]:
            results.pop("gross_profit", None)

    if "revenue" in results and "capex" in results:
        if results["capex"] > results["revenue"] * 0.5:
            results.pop("capex", None)

    return results


def parse_all():
    if not META_FILE.exists():
        raise FileNotFoundError("Run downloader first.")
    metadata = json.loads(META_FILE.read_text())
    parsed = []
    for meta in metadata:
        out_path = PARSED_DIR / meta["local_file"].replace(".html", ".json")
        fpath = DATA_DIR / meta["local_file"]
        if not fpath.exists():
            continue
        stale = (
            out_path.exists()
            and (
                not json.loads(out_path.read_text()).get("financials")
                or fpath.stat().st_mtime > out_path.stat().st_mtime
            )
        )
        if out_path.exists() and not stale:
            parsed.append(json.loads(out_path.read_text()))
            continue
        print(f"  Parsing {meta['local_file']}...")
        html   = fpath.read_text(encoding="utf-8", errors="replace")
        text   = html_to_text(html)
        chunks = chunk_text(text)
        fins   = extract_financials(text)
        result = {**meta, "num_chunks": len(chunks), "chunks": chunks, "financials": fins}
        out_path.write_text(json.dumps(result, indent=2))
        parsed.append(result)
    print(f"Parsed {len(parsed)} filings.")
    return parsed

if __name__ == "__main__":
    parse_all()