"""
Comparative Financial Analysis Dashboard
Companies: NVIDIA (NVDA) · AMD · Intel (INTC)
Source: SEC EDGAR public filings (10-K & 10-Q, 2022-2024)
"""
import os
import sys
import json
from pathlib import Path

import streamlit as st
import pandas as pd
from dotenv import load_dotenv

from ui.styles import (
    CUSTOM_CSS, COMPANY_COLORS, COMPANY_NAMES,
    apply_chart_theme, kpi_card, company_card, status_pill,
    build_grouped_bar, build_smooth_line, build_margin_facets, build_donut,
)
from ui.verification import (
    get_health_summary, get_filing_inventory, get_ticker_completeness,
    get_spot_check, compute_health_score, FINANCIAL_FIELDS,
)

load_dotenv(Path(__file__).parent / ".env")
ROOT = Path(__file__).parent
sys.path.insert(0, str(ROOT))

st.set_page_config(
    page_title="FinAnalyst AI",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)
st.markdown(f"<style>{CUSTOM_CSS}</style>", unsafe_allow_html=True)


# ── helpers ───────────────────────────────────────────────────────────────────
def check_filings_ready():
    m = ROOT / "data" / "filings" / "metadata.json"
    if not m.exists():
        return False
    meta = json.loads(m.read_text())
    if not meta or len(meta) < 15:
        return False
    return all(
        (ROOT / "data" / "filings" / item["local_file"]).exists()
        and (ROOT / "data" / "filings" / item["local_file"]).stat().st_size > 50_000
        for item in meta
    )


def check_index_ready():
    return (ROOT / "vector_store" / "faiss_index.faiss").exists()


@st.cache_data(show_spinner=False)
def load_data():
    from analytics.metrics import get_all_metrics
    return get_all_metrics()


@st.cache_data(show_spinner=False)
def load_narratives(_df):
    from analytics.narrator import generate_narrative_insights
    return generate_narrative_insights(_df)


@st.cache_data(show_spinner=False)
def load_health():
    return get_health_summary(ROOT)


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown('<div class="sidebar-brand">FinAnalyst AI</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sidebar-tagline">SEC EDGAR · NVDA · AMD · INTC</div>',
        unsafe_allow_html=True,
    )
    st.divider()
    st.markdown("**Data Pipeline**")

    filings_ready = check_filings_ready()
    index_ready = check_index_ready()
    health = load_health()

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(
            status_pill(filings_ready, f"{health['valid_filings']} filings", "No filings"),
            unsafe_allow_html=True,
        )
    with col_b:
        st.markdown(
            status_pill(index_ready, "Index ready", "No index"),
            unsafe_allow_html=True,
        )

    if st.button("Download Filings from EDGAR", use_container_width=True, disabled=filings_ready):
        with st.spinner("Downloading from SEC EDGAR…"):
            from ingest.downloader import run_download
            run_download()
        st.cache_data.clear()
        st.rerun()

    if st.button("Parse & Build Index", use_container_width=True, disabled=not filings_ready):
        with st.spinner("Parsing filings & building FAISS index…"):
            from ingest.parser import parse_all
            parse_all()
            from rag.embedder import build_index
            build_index(force_rebuild=True)
        st.cache_data.clear()
        st.success("Pipeline complete!")
        st.rerun()

    st.divider()
    score = compute_health_score(health)
    st.progress(score / 100, text=f"Data health: {score}%")
    st.caption("Sources: SEC EDGAR · Claude Sonnet · MiniLM-L6-v2")


# ── Main header ───────────────────────────────────────────────────────────────
health_banner = load_health()
score_banner = compute_health_score(health_banner)
st.markdown(f"""
<div class="hero-banner">
  <h1 class="hero-title">Comparative Financial Analysis</h1>
  <p class="hero-sub">NVIDIA · AMD · Intel — SEC 10-K & 10-Q filings (2022–2024) · Data health {score_banner}%</p>
</div>""", unsafe_allow_html=True)

tabs = st.tabs([
    "Overview",
    "Verify Data",
    "Derived Metrics",
    "RAG Chatbot",
    "Conflicts",
    "Evaluation",
])


# ══ TAB 1: Financial Overview ════════════════════════════════════════════════
with tabs[0]:
    if not check_filings_ready():
        st.info("Use the sidebar to download and parse filings first.")
        st.stop()

    df, cagr_df, conflicts = load_data()
    if df.empty:
        st.warning("No financial data extracted yet — click **Parse & Build Index** in the sidebar.")
        st.stop()

    latest = df.sort_values("filing_date").groupby("ticker").last().reset_index()
    cards = "".join(
        company_card(
            row["ticker"],
            row.get("revenue"),
            row.get("net_margin_pct"),
            row["form_type"],
            str(row["filing_date"])[:10],
            row["source_url"],
        )
        for _, row in latest.iterrows()
    )
    st.markdown(f'<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:1rem">{cards}</div>',
                unsafe_allow_html=True)

    col_l, col_r = st.columns([2, 1])
    with col_l:
        st.markdown('<div class="section-header">Revenue by Company & Period</div>', unsafe_allow_html=True)
        if "revenue" in df.columns:
            rd = df[df["revenue"].notna()].copy()
            rd["period"] = rd["filing_date"].dt.strftime("%Y-%m")
            fig = build_grouped_bar(rd, "period", "revenue", "ticker", "Revenue ($M)",
                                    title="Quarterly & Annual Revenue")
            st.markdown('<div class="chart-panel">', unsafe_allow_html=True)
            st.plotly_chart(fig, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

    with col_r:
        st.markdown('<div class="section-header">Latest Revenue Share</div>', unsafe_allow_html=True)
        if "revenue" in df.columns:
            share = latest[["ticker", "revenue"]].dropna()
            fig_d = build_donut(share["ticker"].tolist(), share["revenue"].tolist(),
                                title="Most Recent Period")
            st.markdown('<div class="chart-panel">', unsafe_allow_html=True)
            st.plotly_chart(fig_d, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

    mcols = [c for c in ["gross_margin_pct", "operating_margin_pct", "net_margin_pct"] if c in df.columns]
    if mcols:
        st.markdown('<div class="section-header">Profit Margins</div>', unsafe_allow_html=True)
        md = df[["ticker", "filing_date"] + mcols].melt(
            id_vars=["ticker", "filing_date"], value_vars=mcols,
            var_name="Margin", value_name="Pct").dropna()
        md["period"] = md["filing_date"].dt.strftime("%Y-%m")
        md["Margin"] = md["Margin"].str.replace("_pct", "").str.replace("_", " ").str.title()
        fig2 = build_margin_facets(md, "period", "Pct", "ticker", "Margin", "Margin (%)",
                                   title="Margin Trends by Type")
        st.markdown('<div class="chart-panel">', unsafe_allow_html=True)
        st.plotly_chart(fig2, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with st.expander("Raw extracted financials"):
        show_cols = [c for c in [
            "ticker", "form_type", "filing_date", "revenue", "gross_profit",
            "operating_income", "net_income", "total_assets", "total_debt",
            "total_equity", "operating_cash_flow", "capex",
        ] if c in df.columns]
        st.dataframe(df[show_cols].sort_values(["ticker", "filing_date"]), use_container_width=True, hide_index=True)
        st.caption("All values in millions USD. Cross-check against SEC source links in the **Verify Data** tab.")


# ══ TAB 2: Data Verification ═════════════════════════════════════════════════
with tabs[1]:
    health = load_health()
    score = compute_health_score(health)

    kpis = (
        kpi_card("Health Score", f"{score}%", "Overall pipeline completeness")
        + kpi_card("Filings Downloaded", f"{health['valid_filings']}/{health['total_filings']}",
                   "Valid HTML files from EDGAR")
        + kpi_card("Parsed with Financials", f"{health['with_financials']}/{health['parsed_count']}",
                   f"{health['total_chunks']:,} text chunks indexed")
        + kpi_card("Vector Index", "Ready" if health["index_ready"] else "Not built",
                   "Required for chatbot & narratives")
    )
    st.markdown(f'<div class="kpi-grid">{kpis}</div>', unsafe_allow_html=True)

    st.markdown('<div class="section-header">How to Verify Your Data</div>', unsafe_allow_html=True)
    steps = [
        ("Check the filing inventory below — every row should show Parsed ✓ and ≥4 financial fields."),
        ("Open the SEC URL for any filing and compare revenue, net income, and total assets against the spot-check panel."),
        ("Review the Conflicts tab — >400% jumps between filings flag unit mismatches or restatements."),
        ("Run the Evaluation tab (20 questions) to test whether the RAG chatbot answers correctly from your corpus."),
    ]
    for i, step in enumerate(steps, 1):
        st.markdown(
            f'<div class="verify-step"><span class="verify-step-num">{i}</span>{step}</div>',
            unsafe_allow_html=True,
        )

    st.markdown('<div class="section-header">Filing Inventory</div>', unsafe_allow_html=True)
    inv = get_filing_inventory(ROOT)
    if not inv.empty:
        display = inv.drop(columns=["SEC URL", "Local File"])
        st.dataframe(display, use_container_width=True, hide_index=True)
        st.caption("Click a filing below to spot-check extracted values against the SEC source.")

        filing_options = inv["Local File"].tolist()
        labels = [
            f"{row['Ticker']} {row['Form']} ({row['Filing Date']})"
            for _, row in inv.iterrows()
        ]
        selected_idx = st.selectbox("Spot-check a filing", range(len(labels)),
                                    format_func=lambda i: labels[i])
        local_file = filing_options[selected_idx]
        check = get_spot_check(ROOT, local_file)

        if check:
            meta = check["meta"]
            fin = check["financials"]
            c1, c2 = st.columns([1, 1])
            with c1:
                st.markdown("**Extracted financials** (millions USD)")
                if fin:
                    fin_df = pd.DataFrame([{"Metric": k.replace("_", " ").title(),
                                            "Value ($M)": f"{v:,.1f}"}
                                           for k, v in fin.items()])
                    st.dataframe(fin_df, use_container_width=True, hide_index=True)
                else:
                    st.warning("No financials extracted for this filing.")
            with c2:
                st.markdown("**Source reference**")
                st.markdown(f"- **Company:** {meta['company']}")
                st.markdown(f"- **Form:** {meta['form_type']}")
                st.markdown(f"- **Date:** {meta['filing_date']}")
                st.markdown(f"- **Text chunks:** {check['chunks']}")
                st.markdown(f"- **Fields found:** {sum(1 for k in FINANCIAL_FIELDS if fin.get(k) is not None)}/{len(FINANCIAL_FIELDS)}")
                st.link_button("Open original filing on SEC.gov ↗", meta["source_url"])
    else:
        st.info("No filings found. Download from the sidebar first.")

    st.markdown('<div class="section-header">Completeness by Company</div>', unsafe_allow_html=True)
    comp = get_ticker_completeness(ROOT)
    if not comp.empty:
        st.dataframe(comp, use_container_width=True, hide_index=True)

    if check_filings_ready():
        _, _, conflicts = load_data()
        if conflicts:
            st.markdown('<div class="section-header">Quick Conflict Summary</div>', unsafe_allow_html=True)
            st.warning(f"{len(conflicts)} potential issue(s) detected — see the **Conflicts** tab for details.")
            for c in conflicts[:3]:
                st.markdown(
                    f'<div class="conflict-box">'
                    f'<b>{COMPANY_NAMES.get(c["ticker"], c["ticker"])}</b> · '
                    f'{c["metric"].replace("_", " ").title()}: '
                    f'{c["value_prev"]:,.0f} → {c["value_curr"]:,.0f} '
                    f'({c["ratio"]}× jump between {c["date_prev"]} and {c["date_curr"]})'
                    f'</div>',
                    unsafe_allow_html=True,
                )
        else:
            st.success("No major metric conflicts detected between consecutive filings.")


# ══ TAB 3: Derived Metrics ═════════════════════════════════════════════════════
with tabs[2]:
    st.caption("Every metric is computed from extracted filing figures — formulas shown for traceability.")

    if not check_filings_ready():
        st.info("Download and parse filings first.")
        st.stop()

    df, cagr_df, conflicts = load_data()

    if "revenue_yoy_growth_pct" in df.columns:
        st.markdown('<div class="section-header">Year-over-Year Revenue Growth</div>', unsafe_allow_html=True)
        st.code("Formula: (Revenue_t − Revenue_{t-1}) / Revenue_{t-1} × 100", language="text")
        yd = df[df["revenue_yoy_growth_pct"].notna()].copy()
        yd["period"] = yd["filing_date"].dt.strftime("%Y-%m")
        fig = build_grouped_bar(yd, "period", "revenue_yoy_growth_pct", "ticker",
                                "YoY Growth (%)", title="Revenue Growth Rate")
        fig.add_hline(y=0, line_dash="dot", line_color="rgba(148,163,184,0.5)", line_width=1)
        st.markdown('<div class="chart-panel">', unsafe_allow_html=True)
        st.plotly_chart(fig, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    if not cagr_df.empty:
        st.markdown('<div class="section-header">Revenue CAGR (10-K filings)</div>', unsafe_allow_html=True)
        st.code("Formula: (end_value / start_value)^(1/n_years) − 1", language="text")
        st.dataframe(
            cagr_df.style.format({
                "cagr_pct": "{:.2f}%", "start_value": "${:,.0f}M",
                "end_value": "${:,.0f}M", "n_years": "{:.1f} yrs",
            }),
            use_container_width=True,
        )

    if "free_cash_flow" in df.columns:
        st.markdown('<div class="section-header">Free Cash Flow</div>', unsafe_allow_html=True)
        st.code("Formula: Operating Cash Flow − Capital Expenditures", language="text")
        fd = df[df["free_cash_flow"].notna()].copy()
        fd["period"] = fd["filing_date"].dt.strftime("%Y-%m")
        fig3 = build_grouped_bar(fd, "period", "free_cash_flow", "ticker",
                                 "FCF ($M)", title="Free Cash Flow")
        fig3.add_hline(y=0, line_dash="dot", line_color="rgba(148,163,184,0.5)", line_width=1)
        st.markdown('<div class="chart-panel">', unsafe_allow_html=True)
        st.plotly_chart(fig3, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    if "debt_to_equity" in df.columns:
        st.markdown('<div class="section-header">Debt-to-Equity Ratio</div>', unsafe_allow_html=True)
        st.code("Formula: Total Debt / Total Stockholders' Equity", language="text")
        ded = df[df["debt_to_equity"].notna()].copy()
        ded["period"] = ded["filing_date"].dt.strftime("%Y-%m")
        fig4 = build_smooth_line(ded, "period", "debt_to_equity", "ticker",
                                 "D/E Ratio", title="Leverage Over Time")
        st.markdown('<div class="chart-panel">', unsafe_allow_html=True)
        st.plotly_chart(fig4, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="section-header">Quant-to-Narrative Linkage</div>', unsafe_allow_html=True)
    st.caption("Material metric moves (>10%) connected to MD&A commentary from the same filing.")
    if not df.empty and check_index_ready():
        with st.spinner("Connecting metrics to MD&A passages…"):
            insights = load_narratives(df)
        if insights:
            for ins in insights[:12]:
                icon = "▲" if ins["direction"] == "increase" else "▼"
                st.markdown(
                    f"**{icon} {COMPANY_NAMES.get(ins['ticker'], ins['ticker'])} · "
                    f"{ins['metric'].replace('_', ' ').title()}** · "
                    f"**{ins['change_pct']:+.1f}%** "
                    f"({ins['prev_value']} → {ins['curr_value']}) · {ins['filing_date'][:7]}"
                )
                st.markdown(f'<div class="citation-box">{ins["narrative"]}</div>', unsafe_allow_html=True)
        else:
            st.info("No material moves detected in the current dataset.")
    else:
        st.info("Build the vector index (sidebar) to enable narrative linkage.")


# ══ TAB 4: RAG Chatbot ═════════════════════════════════════════════════════════
with tabs[3]:
    st.caption("Natural-language Q&A over SEC filings. Every answer cites its source document.")

    if not check_index_ready():
        st.info("Build the vector index first (sidebar).")
        st.stop()
    if not os.getenv("ANTHROPIC_API_KEY"):
        st.warning("Set ANTHROPIC_API_KEY in your `.env` file to use the chatbot.")
        st.stop()

    with st.expander("Example questions"):
        examples = [
            "What was NVIDIA's revenue growth in fiscal year 2024?",
            "How do AMD's gross margins compare to Intel's in 2023?",
            "What risk factors did Intel identify in their 2023 10-K?",
            "What did AMD say about AI chip demand in their MD&A?",
            "Compare free cash flow across NVIDIA, AMD and Intel in 2023.",
        ]
        for ex in examples:
            if st.button(ex, key=f"ex_{hash(ex)}"):
                st.session_state["prefill"] = ex

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("citations"):
                with st.expander(f"{len(msg['citations'])} source(s)"):
                    for c in msg["citations"]:
                        st.markdown(
                            f'<div class="citation-box">'
                            f'<b>{c["company"]}</b> · {c["form_type"]} · '
                            f'{c["filing_date"][:7]} · relevance: {c["score"]}<br>'
                            f'<a href="{c["source_url"]}" target="_blank">View on SEC.gov ↗</a>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )

    user_input = st.chat_input("Ask about NVIDIA, AMD, or Intel filings…")
    if not user_input and "prefill" in st.session_state:
        user_input = st.session_state.pop("prefill")

    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner("Searching filings…"):
                from rag.agent import run_agent
                result = run_agent(user_input)

            ans = result.get("answer", "No answer generated.")
            cits = result.get("citations", [])
            rq = result.get("rewritten_query", user_input)
            grounded = result.get("is_grounded", True)

            st.markdown(ans)
            label = "Grounded in filings" if grounded else "Low confidence — verify manually"
            cls = "grounded" if grounded else "ungrounded"
            st.markdown(f'<span class="{cls}">{"✓" if grounded else "⚠"} {label}</span>', unsafe_allow_html=True)

            if cits:
                with st.expander(f"{len(cits)} source(s)"):
                    for c in cits:
                        st.markdown(
                            f'<div class="citation-box">'
                            f'<b>{c["company"]}</b> · {c["form_type"]} · '
                            f'{c["filing_date"][:7]}<br>'
                            f'<a href="{c["source_url"]}" target="_blank">View on SEC.gov ↗</a>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )
            if rq != user_input:
                st.caption(f"Rewritten query: _{rq}_")

        st.session_state.messages.append({
            "role": "assistant", "content": ans,
            "citations": cits, "rewritten_query": rq,
        })


# ══ TAB 5: Conflict Detector ═══════════════════════════════════════════════════
with tabs[4]:
    st.caption("Flags >400% jumps between consecutive filings — likely unit mismatches or restatements.")

    if not check_filings_ready():
        st.info("Download and parse filings first.")
        st.stop()

    df, cagr_df, conflicts = load_data()

    if not conflicts:
        st.success("No major conflicts detected in the current dataset.")
        st.info("Absence of flags does not guarantee accuracy — always verify against the original filing.")
    else:
        st.warning(f"{len(conflicts)} potential conflict(s) detected")
        for c in conflicts:
            st.markdown(f"""
<div class="conflict-box">
  <b>{COMPANY_NAMES.get(c['ticker'], c['ticker'])}</b> ·
  <b>{c['metric'].replace('_', ' ').title()}</b><br>
  {c['type_prev']} {c['date_prev']}: <code>{c['value_prev']:,.1f}</code>
  → {c['type_curr']} {c['date_curr']}: <code>{c['value_curr']:,.1f}</code>
  · {c['ratio']}× jump<br>
  <i>{c['note']}</i><br>
  <a href="{c['url_prev']}" target="_blank">Source 1 ↗</a>
  · <a href="{c['url_curr']}" target="_blank">Source 2 ↗</a>
</div>""", unsafe_allow_html=True)

    if not df.empty:
        st.markdown('<div class="section-header">Cross-Filing Metric Comparison</div>', unsafe_allow_html=True)
        opts = [c for c in ["revenue", "net_income", "gross_profit", "operating_income", "total_assets"]
                if c in df.columns]
        if opts:
            sel = st.selectbox("Select metric", opts)
            piv = df[["ticker", "filing_date", "form_type", sel]].dropna().copy()
            piv["period"] = piv["filing_date"].dt.strftime("%Y-%m") + " " + piv["form_type"]
            try:
                pt = piv.pivot(index="period", columns="ticker", values=sel)
                st.dataframe(
                    pt.style.format("${:,.1f}M").highlight_null("rgba(51,65,85,0.5)"),
                    use_container_width=True,
                )
            except Exception:
                st.dataframe(piv, use_container_width=True)
            st.caption("Values in millions USD.")


# ══ TAB 6: Evaluation ════════════════════════════════════════════════════════════
with tabs[5]:
    st.caption("20 labeled questions — 14 answerable, 6 unanswerable. Honest reporting including failures.")

    results_path = ROOT / "evaluation" / "eval_results.json"
    left, right = st.columns([2, 1])

    with left:
        if results_path.exists():
            res = json.loads(results_path.read_text())
            s = res.get("summary", {})

            m1, m2, m3 = st.columns(3)
            m1.metric("Answer Correctness", f"{s.get('answer_correctness_pct', '–')}%")
            m2.metric("Citation Accuracy", f"{s.get('citation_accuracy_pct', '–')}%")
            m3.metric("Hallucination Rate", f"{s.get('hallucination_rate_pct', '–')}%",
                      delta_color="inverse")
            st.info(s.get("interpretation", ""))

            with st.expander("Answerable questions detail"):
                adf = pd.DataFrame(res.get("answerable", []))
                if not adf.empty:
                    st.dataframe(
                        adf[["id", "question", "correctness", "citation_ok", "num_citations"]],
                        use_container_width=True, hide_index=True,
                    )

            with st.expander("Unanswerable questions detail"):
                udf = pd.DataFrame(res.get("unanswerable", []))
                if not udf.empty:
                    udf["result"] = udf["refused"].map(
                        {True: "Correctly refused", False: "Hallucinated"})
                    st.dataframe(
                        udf[["id", "question", "result", "reason"]],
                        use_container_width=True, hide_index=True,
                    )
        else:
            st.info("No evaluation results yet. Run evaluation using the button on the right.")

    with right:
        st.markdown("**Run Evaluation**")
        if not check_index_ready():
            st.warning("Build the vector index first.")
        elif not os.getenv("ANTHROPIC_API_KEY"):
            st.warning("Set ANTHROPIC_API_KEY in `.env` to run evaluation.")
        else:
            if st.button("Run Full Evaluation (20 Qs)", use_container_width=True, type="primary"):
                with st.spinner("Running 20 questions against the corpus…"):
                    from evaluation.evaluator import run_evaluation
                    run_evaluation(verbose=False)
                st.success("Evaluation complete!")
                st.rerun()

        st.divider()
        qs = json.loads((ROOT / "evaluation" / "eval_questions.json").read_text())
        st.markdown(f"**{len(qs['answerable'])}** answerable · **{len(qs['unanswerable'])}** unanswerable")

    with st.expander("View all 20 questions"):
        qs = json.loads((ROOT / "evaluation" / "eval_questions.json").read_text())
        st.markdown("**Answerable (14)**")
        for q in qs["answerable"]:
            st.markdown(f"- `{q['id']}` {q['question']}")
        st.markdown("**Unanswerable (6)**")
        for q in qs["unanswerable"]:
            st.markdown(f"- `{q['id']}` {q['question']} _(reason: {q['reason']})_")
