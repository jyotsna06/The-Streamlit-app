"""Computes derived financial metrics. All formulas are traceable to source."""
import json
from pathlib import Path
import pandas as pd

PARSED_DIR = Path(__file__).parent.parent / "data" / "parsed"

def load_financials():
    rows = []
    for p in sorted(PARSED_DIR.glob("*.json")):
        data = json.loads(p.read_text())
        fin  = data.get("financials", {})
        if not fin: continue
        row = {k: data[k] for k in ["ticker","company","form_type","filing_date","source_url","local_file"]}
        row.update(fin)
        rows.append(row)
    if not rows: return pd.DataFrame()
    df = pd.DataFrame(rows)
    df["filing_date"] = pd.to_datetime(df["filing_date"])
    return df.sort_values(["ticker","filing_date"]).reset_index(drop=True)

def compute_derived(df):
    if df.empty: return df
    eps = 1e-9
    if "gross_profit" in df.columns and "revenue" in df.columns:
        df["gross_margin_pct"] = (df["gross_profit"]/(df["revenue"]+eps)*100).round(2)
    if "operating_income" in df.columns and "revenue" in df.columns:
        df["operating_margin_pct"] = (df["operating_income"]/(df["revenue"]+eps)*100).round(2)
    if "net_income" in df.columns and "revenue" in df.columns:
        df["net_margin_pct"] = (df["net_income"]/(df["revenue"]+eps)*100).round(2)
    if "revenue" in df.columns:
        df["revenue_yoy_growth_pct"] = (df.groupby("ticker")["revenue"].pct_change()*100).round(2)
    if "operating_cash_flow" in df.columns and "capex" in df.columns:
        df["free_cash_flow"] = (df["operating_cash_flow"]-df["capex"]).round(2)
    if "total_debt" in df.columns and "total_equity" in df.columns:
        df["debt_to_equity"] = (df["total_debt"]/(df["total_equity"]+eps)).round(3)
    return df

def compute_cagr(df, metric="revenue"):
    results = []
    annual = df[df["form_type"]=="10-K"]
    for ticker, grp in annual.groupby("ticker"):
        grp  = grp.sort_values("filing_date")
        vals = grp[metric].dropna()
        if len(vals) < 2: continue
        sv, ev = vals.iloc[0], vals.iloc[-1]
        ny = (grp["filing_date"].iloc[-1]-grp["filing_date"].iloc[0]).days/365.25
        if sv <= 0 or ny < 0.5: continue
        cagr = ((ev/sv)**(1/ny)-1)*100
        results.append({"ticker":ticker,"cagr_pct":round(cagr,2),"start_value":round(sv,2),
                        "end_value":round(ev,2),"n_years":round(ny,2),
                        "start_date":str(grp["filing_date"].iloc[0])[:7],
                        "end_date":str(grp["filing_date"].iloc[-1])[:7],
                        "formula":f"({ev:.0f}/{sv:.0f})^(1/{ny:.2f})-1"})
    return pd.DataFrame(results)

def detect_conflicts(df):
    conflicts = []
    for ticker, grp in df.groupby("ticker"):
        for metric in ["revenue","net_income","total_assets"]:
            if metric not in grp.columns: continue
            vals = grp[[metric,"form_type","filing_date","source_url"]].dropna().sort_values("filing_date")
            for i in range(1, len(vals)):
                vp, vc = vals.iloc[i-1][metric], vals.iloc[i][metric]
                if vp == 0: continue
                ratio = abs(vc-vp)/abs(vp)
                if ratio > 4.0:
                    conflicts.append({
                        "ticker":ticker, "metric":metric, "value_prev":vp, "value_curr":vc,
                        "date_prev":str(vals.iloc[i-1]["filing_date"])[:10],
                        "date_curr":str(vals.iloc[i]["filing_date"])[:10],
                        "type_prev":vals.iloc[i-1]["form_type"],
                        "type_curr":vals.iloc[i]["form_type"],
                        "ratio":round(ratio,2), "note":"Possible unit mismatch or restatement",
                        "url_prev":vals.iloc[i-1]["source_url"],
                        "url_curr":vals.iloc[i]["source_url"],
                    })
    return conflicts

def get_all_metrics():
    raw = load_financials()
    if raw.empty: return raw, pd.DataFrame(), []
    enr  = compute_derived(raw)
    cagr = compute_cagr(enr)
    conf = detect_conflicts(enr)
    return enr, cagr, conf