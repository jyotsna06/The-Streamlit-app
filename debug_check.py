import json
from pathlib import Path

parsed_dir = Path("data/parsed")
filings_dir = Path("data/filings")

print("=== FILING SIZES ===")
for f in sorted(filings_dir.glob("*.html"))[:3]:
    print(f"  {f.name}: {f.stat().st_size / 1024:.1f} KB")

print("\n=== PARSED CHUNKS ===")
for f in sorted(parsed_dir.glob("*.json"))[:5]:
    data = json.loads(f.read_text())
    fin  = data.get("financials", {})
    nchk = len(data.get("chunks", []))
    print(f"  {f.name}")
    print(f"    chunks: {nchk}")
    print(f"    financials: {fin}")