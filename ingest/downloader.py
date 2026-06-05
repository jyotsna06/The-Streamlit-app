"""
SEC EDGAR filing downloader.
Downloads actual 10-K and 10-Q filing documents for NVDA, AMD, INTC.
"""
import re, time, requests, json
from pathlib import Path
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "FinancialDashboard jyotsna@example.com",
    "Accept-Encoding": "gzip, deflate",
    "Accept": "text/html,application/xhtml+xml",
}

COMPANIES = {
    "NVDA": {"cik": 1045810, "name": "NVIDIA Corporation"},
    "AMD":  {"cik": 2488,    "name": "Advanced Micro Devices"},
    "INTC": {"cik": 50863,   "name": "Intel Corporation"},
}
FILINGS_TO_FETCH = [
    ("10-K", "2022-01-01", "2022-12-31"),
    ("10-K", "2023-01-01", "2023-12-31"),
    ("10-K", "2024-01-01", "2024-12-31"),
    ("10-Q", "2024-01-01", "2024-06-30"),
    ("10-Q", "2024-07-01", "2024-12-31"),
]
DATA_DIR  = Path(__file__).parent.parent / "data" / "filings"
META_FILE = DATA_DIR / "metadata.json"


def get_recent_filings(cik, form_type, start, end, count=1):
    url = f"https://data.sec.gov/submissions/CIK{cik:010d}.json"
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        r.raise_for_status()
        f = r.json().get("filings", {}).get("recent", {})
    except Exception as e:
        print(f"  [WARN] submissions fetch failed: {e}"); return []
    results = []
    for form, date, accno in zip(
        f.get("form", []), f.get("filingDate", []), f.get("accessionNumber", [])
    ):
        if form == form_type and start <= date <= end:
            results.append((accno, date, form))
        if len(results) >= count:
            break
    return results


def get_filing_index(cik, accno):
    """Fetch the filing index JSON from EDGAR (www.sec.gov hosts the index)."""
    clean = accno.replace("-", "")
    url   = f"https://www.sec.gov/Archives/edgar/data/{cik}/{clean}/{accno}-index.json"
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        r.raise_for_status()
        return r.json()
    except Exception:
        return None


def resolve_doc_url(href):
    """Convert SEC index href to a direct Archives download URL."""
    if not href:
        return None
    if "ix?doc=" in href:
        match = re.search(r"ix\?doc=(/Archives/edgar/data/[^&\s]+)", href)
        if match:
            return f"https://www.sec.gov{match.group(1)}"
    if href.startswith("/Archives/"):
        return f"https://www.sec.gov{href}"
    if href.startswith("http"):
        return href
    return None


def find_primary_doc_url(cik, accno):
    """
    Find the actual 10-K/10-Q HTML document URL from the filing index.
    Strategy:
      1. Try the EDGAR index JSON first (most reliable)
      2. Fall back to parsing the HTML index page
    """
    clean = accno.replace("-", "")

    # Strategy 1: Use index JSON
    idx = get_filing_index(cik, accno)
    if idx:
        files = idx.get("directory", {}).get("item", [])
        # Look for the primary document (largest .htm file that is the actual report)
        candidates = []
        for item in files:
            name = item.get("name", "")
            ftype = item.get("type", "")
            size  = int(item.get("size", 0))
            if ftype in ("10-K", "10-Q") and name.endswith((".htm", ".html")):
                candidates.append((size, name))
        if candidates:
            # Pick largest — that's the full filing
            candidates.sort(reverse=True)
            doc_name = candidates[0][1]
            return f"https://www.sec.gov/Archives/edgar/data/{cik}/{clean}/{doc_name}"

        # Fallback: biggest .htm file overall
        htm_files = [
            (int(item.get("size", 0)), item.get("name", ""))
            for item in files
            if item.get("name", "").endswith((".htm", ".html"))
            and "index" not in item.get("name", "").lower()
            and item.get("name", "") != ""
        ]
        if htm_files:
            htm_files.sort(reverse=True)
            doc_name = htm_files[0][1]
            return f"https://www.sec.gov/Archives/edgar/data/{cik}/{clean}/{doc_name}"

    # Strategy 2: Parse HTML index page
    idx_url = f"https://www.sec.gov/Archives/edgar/data/{cik}/{clean}/{accno}-index.htm"
    try:
        r    = requests.get(idx_url, headers=HEADERS, timeout=20)
        soup = BeautifulSoup(r.text, "lxml")
        rows = soup.find_all("tr")
        best = None
        best_size = -1
        for row in rows:
            cells = row.find_all("td")
            if len(cells) < 4:
                continue
            doc_type = cells[3].get_text(strip=True)
            link     = cells[2].find("a")
            size_cell = cells[4] if len(cells) >= 5 else cells[1]
            size_str  = size_cell.get_text(strip=True).replace(",", "")
            size      = int(size_str) if size_str.isdigit() else 0
            if doc_type in ("10-K", "10-Q") and link:
                url = resolve_doc_url(link.get("href", ""))
                if url and size >= best_size:
                    best_size = size
                    best = url
        if best:
            return best

        # Last resort: largest direct .htm link on the index page
        links = []
        for a in soup.find_all("a", href=True):
            url = resolve_doc_url(a["href"])
            if (url and url.endswith((".htm", ".html"))
                    and "index" not in url.lower()):
                links.append(url)
        if links:
            return links[0]
    except Exception as e:
        print(f"  [WARN] HTML index parse failed: {e}")

    return None


def download_filing(url, dest):
    try:
        r = requests.get(url, headers=HEADERS, timeout=120)
        r.raise_for_status()
        size_kb = len(r.content) / 1024
        if size_kb < 50:
            print(f"  [WARN] File too small ({size_kb:.1f} KB) — likely a redirect: {url}")
            return False
        dest.write_text(r.text, encoding="utf-8", errors="replace")
        print(f"    [OK] Saved {size_kb:.0f} KB")
        return True
    except Exception as e:
        print(f"  [WARN] Download failed: {e}")
        return False


def run_download():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    parsed_dir = Path(__file__).parent.parent / "data" / "parsed"
    vstore_dir = Path(__file__).parent.parent / "vector_store"

    # Clear old bad downloads and stale derived data
    removed = False
    for f in DATA_DIR.glob("*.html"):
        if f.stat().st_size < 50_000:   # delete files under 50 KB
            print(f"  [CLEAN] Removing bad file: {f.name}")
            f.unlink()
            removed = True
    if removed and parsed_dir.exists():
        for p in parsed_dir.glob("*.json"):
            p.unlink()
        for p in [vstore_dir / "faiss_index.faiss", vstore_dir / "documents.pkl"]:
            if p.exists():
                p.unlink()

    metadata = []
    for ticker, info in COMPANIES.items():
        print(f"\n=== {ticker} ({info['name']}) ===")
        for form, start, end in FILINGS_TO_FETCH:
            filings = get_recent_filings(info["cik"], form, start, end)
            if not filings:
                print(f"  [SKIP] No {form} found between {start} and {end}")
                continue
            for accno, date, ftype in filings:
                print(f"  {ftype} {date} — accession: {accno}")
                doc_url = find_primary_doc_url(info["cik"], accno)
                if not doc_url:
                    print(f"  [SKIP] Could not find document URL")
                    continue
                print(f"    URL: {doc_url}")
                fname = f"{ticker}_{ftype}_{date}_{accno.replace('-','')}.html"
                dest  = DATA_DIR / fname
                if dest.exists() and dest.stat().st_size > 50_000:
                    print(f"    [CACHED] {dest.stat().st_size/1024:.0f} KB")
                else:
                    if not download_filing(doc_url, dest):
                        continue
                    time.sleep(0.6)   # be polite to SEC servers
                metadata.append({
                    "ticker":       ticker,
                    "company":      info["name"],
                    "cik":          info["cik"],
                    "form_type":    ftype,
                    "filing_date":  date,
                    "accession":    accno,
                    "source_url":   doc_url,
                    "local_file":   fname,
                })
    META_FILE.write_text(json.dumps(metadata, indent=2))
    print(f"\n[DONE] {len(metadata)} filings saved to {DATA_DIR}")
    return metadata


if __name__ == "__main__":
    run_download()