"""Shared UI styles and chart theming."""

import plotly.graph_objects as go

COMPANY_COLORS = {"NVDA": "#76b900", "AMD": "#ed1c24", "INTC": "#0071c5"}
COMPANY_GRADIENTS = {
    "NVDA": ("rgba(118,185,0,0.85)", "rgba(118,185,0,0.15)"),
    "AMD": ("rgba(237,28,36,0.85)", "rgba(237,28,36,0.15)"),
    "INTC": ("rgba(0,113,197,0.85)", "rgba(0,113,197,0.15)"),
}
COMPANY_NAMES = {"NVDA": "NVIDIA", "AMD": "AMD", "INTC": "Intel"}

CHART_LAYOUT = dict(
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#cbd5e1", family="Inter, system-ui, sans-serif", size=13),
    margin=dict(l=48, r=24, t=56, b=48),
    legend=dict(
        orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1,
        bgcolor="rgba(15,23,42,0.7)", bordercolor="rgba(99,102,241,0.25)", borderwidth=1,
    ),
    hoverlabel=dict(bgcolor="#1e293b", bordercolor="#6366f1", font_size=13),
    hovermode="x unified",
)

AXIS_STYLE = dict(
    showgrid=True, gridcolor="rgba(51,65,85,0.35)", gridwidth=1,
    zeroline=False, showline=True, linecolor="rgba(148,163,184,0.2)",
    tickfont=dict(color="#94a3b8", size=11),
    title_font=dict(color="#94a3b8", size=12),
)

CUSTOM_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] { font-family: 'Inter', system-ui, sans-serif; }

.stApp {
    background:
        radial-gradient(ellipse 80% 50% at 50% -20%, rgba(99,102,241,0.18), transparent),
        radial-gradient(ellipse 60% 40% at 100% 50%, rgba(118,185,0,0.06), transparent),
        linear-gradient(165deg, #080b14 0%, #0f172a 50%, #0b1120 100%);
    color: #e2e8f0;
}

.block-container { padding-top: 1.25rem; max-width: 1440px; }

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, rgba(15,23,42,0.98) 0%, rgba(17,24,39,0.98) 100%);
    border-right: 1px solid rgba(99,102,241,0.12);
}

[data-testid="stSidebar"] .block-container { padding-top: 1.5rem; }

.hero-banner {
    background: linear-gradient(135deg, rgba(30,41,59,0.6) 0%, rgba(15,23,42,0.4) 100%);
    border: 1px solid rgba(99,102,241,0.2);
    border-radius: 16px;
    padding: 1.5rem 1.75rem;
    margin-bottom: 1.5rem;
    backdrop-filter: blur(16px);
}

.hero-title {
    font-size: 2.1rem; font-weight: 800; letter-spacing: -0.04em; margin: 0;
    background: linear-gradient(135deg, #f8fafc 20%, #a5b4fc 80%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}

.hero-sub { color: #64748b; font-size: 0.92rem; margin: 0.35rem 0 0 0; }

.kpi-grid {
    display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
    gap: 1rem; margin-bottom: 1.5rem;
}

.kpi-card {
    background: linear-gradient(145deg, rgba(30,41,59,0.7), rgba(15,23,42,0.5));
    border: 1px solid rgba(148,163,184,0.12); border-radius: 14px;
    padding: 1.1rem 1.25rem; transition: all 0.2s ease;
}
.kpi-card:hover { border-color: rgba(99,102,241,0.35); transform: translateY(-2px); }

.kpi-label { font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.1em; color: #64748b; }
.kpi-value { font-size: 1.6rem; font-weight: 800; color: #f8fafc; line-height: 1.2; margin-top: 0.25rem; }
.kpi-sub { font-size: 0.78rem; color: #475569; margin-top: 0.3rem; }

.company-card {
    background: linear-gradient(160deg, rgba(30,41,59,0.75), rgba(15,23,42,0.55));
    border: 1px solid rgba(148,163,184,0.12); border-radius: 16px;
    padding: 1.35rem; border-top: 3px solid var(--accent);
    box-shadow: 0 8px 32px rgba(0,0,0,0.2); transition: transform 0.2s ease;
}
.company-card:hover { transform: translateY(-3px); }

.company-card h4 { margin: 0 0 0.85rem 0; font-size: 1.05rem; font-weight: 700; }
.company-card .stat-row {
    display: flex; justify-content: space-between; padding: 0.4rem 0;
    border-bottom: 1px solid rgba(148,163,184,0.08); font-size: 0.88rem;
}
.company-card .stat-row:last-child { border-bottom: none; }
.company-card .stat-label { color: #64748b; }
.company-card .stat-value { color: #f1f5f9; font-weight: 700; }

.chart-panel {
    background: linear-gradient(160deg, rgba(30,41,59,0.45), rgba(15,23,42,0.3));
    border: 1px solid rgba(99,102,241,0.12); border-radius: 16px;
    padding: 1rem 0.5rem 0.25rem; margin-bottom: 1rem;
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.04);
}

.status-pill {
    display: inline-flex; align-items: center; gap: 0.35rem;
    padding: 0.35rem 0.8rem; border-radius: 999px;
    font-size: 0.76rem; font-weight: 600;
}
.status-ok { background: rgba(16,185,129,0.12); color: #34d399; border: 1px solid rgba(16,185,129,0.25); }
.status-warn { background: rgba(245,158,11,0.12); color: #fbbf24; border: 1px solid rgba(245,158,11,0.25); }

.citation-box {
    background: rgba(6,78,59,0.2); border: 1px solid rgba(16,185,129,0.2);
    border-left: 3px solid #10b981; padding: 0.8rem 1rem; border-radius: 10px;
    font-size: 0.85rem; margin-top: 0.5rem; color: #d1fae5;
}
.conflict-box {
    background: rgba(120,53,15,0.2); border: 1px solid rgba(245,158,11,0.2);
    border-left: 3px solid #f59e0b; padding: 0.8rem 1rem; border-radius: 10px;
    margin-top: 0.5rem; color: #fef3c7;
}
.verify-step {
    background: rgba(30,41,59,0.35); border: 1px solid rgba(148,163,184,0.1);
    border-radius: 10px; padding: 0.9rem 1rem; margin-bottom: 0.6rem;
}
.verify-step-num {
    display: inline-block; width: 1.4rem; height: 1.4rem; line-height: 1.4rem;
    text-align: center; background: rgba(99,102,241,0.25); color: #a5b4fc;
    border-radius: 50%; font-size: 0.72rem; font-weight: 700; margin-right: 0.5rem;
}

.grounded { color: #34d399; font-weight: 600; }
.ungrounded { color: #f87171; font-weight: 600; }

.section-header {
    font-size: 1.1rem; font-weight: 700; color: #f1f5f9;
    margin: 1.25rem 0 0.6rem 0; letter-spacing: -0.02em;
    display: flex; align-items: center; gap: 0.5rem;
}
.section-header::before {
    content: ''; width: 3px; height: 1.1rem;
    background: linear-gradient(180deg, #6366f1, #818cf8); border-radius: 2px;
}

.sidebar-brand { font-size: 1.3rem; font-weight: 800; color: #f8fafc; letter-spacing: -0.03em; }
.sidebar-tagline { font-size: 0.76rem; color: #475569; margin-top: 0.2rem; }

[data-testid="stTabs"] [data-baseweb="tab-list"] {
    gap: 0.25rem; background: rgba(15,23,42,0.5); border-radius: 12px;
    padding: 0.35rem; border: 1px solid rgba(99,102,241,0.1);
}
[data-testid="stTabs"] button {
    background: transparent; color: #64748b; border-radius: 8px;
    font-weight: 600; font-size: 0.85rem; padding: 0.5rem 1rem; border: none;
}
[data-testid="stTabs"] button[aria-selected="true"] {
    background: linear-gradient(135deg, rgba(99,102,241,0.25), rgba(79,70,229,0.15));
    color: #e0e7ff; box-shadow: 0 2px 8px rgba(99,102,241,0.2);
}

[data-testid="stMetric"] {
    background: linear-gradient(145deg, rgba(30,41,59,0.6), rgba(15,23,42,0.4));
    border: 1px solid rgba(99,102,241,0.1); border-radius: 14px; padding: 0.85rem 1rem;
}

.stButton > button { border-radius: 10px; font-weight: 600; border: 1px solid rgba(99,102,241,0.2); }
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #6366f1, #4f46e5); border: none;
    box-shadow: 0 4px 14px rgba(99,102,241,0.35);
}

div[data-testid="stExpander"] {
    background: rgba(30,41,59,0.3); border: 1px solid rgba(148,163,184,0.1); border-radius: 12px;
}

a { color: #818cf8; text-decoration: none; }
a:hover { color: #a5b4fc; }

#MainMenu, footer, header { visibility: hidden; }
"""


def apply_chart_theme(fig, title=None, height=420):
    fig.update_layout(**CHART_LAYOUT, height=height)
    if title:
        fig.update_layout(
            title=dict(text=title, font=dict(size=15, color="#e2e8f0"), x=0.02, xanchor="left"),
        )
    fig.update_xaxes(**AXIS_STYLE)
    fig.update_yaxes(**AXIS_STYLE)
    return fig


def build_grouped_bar(df, x, y, color, y_title, title=None, height=420):
    fig = go.Figure()
    for ticker in sorted(df[color].unique()):
        sub = df[df[color] == ticker]
        c = COMPANY_COLORS.get(ticker, "#6366f1")
        fig.add_trace(go.Bar(
            x=sub[x], y=sub[y], name=COMPANY_NAMES.get(ticker, ticker),
            marker=dict(color=c, line=dict(width=0),
                        pattern_shape="/" if ticker == "INTC" else ""),
            hovertemplate=f"<b>{COMPANY_NAMES.get(ticker, ticker)}</b><br>"
                          f"%{{x}}<br>{y_title}: %{{y:,.1f}}<extra></extra>",
        ))
    fig.update_layout(barmode="group", bargap=0.18, bargroupgap=0.08)
    return apply_chart_theme(fig, title=title, height=height)


def build_smooth_line(df, x, y, color, y_title, title=None, height=420, facet=None):
    fig = go.Figure()
    for ticker in sorted(df[color].unique()):
        sub = df[df[color] == ticker].sort_values(x)
        c = COMPANY_COLORS.get(ticker, "#6366f1")
        fig.add_trace(go.Scatter(
            x=sub[x], y=sub[y], name=COMPANY_NAMES.get(ticker, ticker), mode="lines+markers",
            line=dict(color=c, width=2.5, shape="spline"),
            marker=dict(size=7, color=c, line=dict(width=2, color="#0f172a")),
            fill="tozeroy", fillcolor=COMPANY_GRADIENTS.get(ticker, ("rgba(99,102,241,0.5)", "rgba(99,102,241,0.05)"))[1],
            hovertemplate=f"<b>{COMPANY_NAMES.get(ticker, ticker)}</b><br>"
                          f"%{{x}}<br>{y_title}: %{{y:,.2f}}<extra></extra>",
        ))
    return apply_chart_theme(fig, title=title, height=height)


def build_margin_facets(df, x, y, color, facet, y_title, title=None, height=380):
    import plotly.express as px
    fig = px.line(df, x=x, y=y, color=color, facet_col=facet, markers=True,
                  color_discrete_map=COMPANY_COLORS,
                  labels={y: y_title, x: "Period", color: "Company"})
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1].replace("_", " ").title()))
    fig.update_traces(line=dict(width=2.5), marker=dict(size=6))
    return apply_chart_theme(fig, title=title, height=height)


def build_donut(labels, values, title=None, height=340):
    colors = [COMPANY_COLORS.get(l, "#6366f1") for l in labels]
    fig = go.Figure(go.Pie(
        labels=[COMPANY_NAMES.get(l, l) for l in labels], values=values,
        hole=0.62, marker=dict(colors=colors, line=dict(color="#0f172a", width=2)),
        textinfo="label+percent", textfont=dict(size=12, color="#e2e8f0"),
        hovertemplate="<b>%{label}</b><br>$%{value:,.0f}M<br>%{percent}<extra></extra>",
    ))
    fig.update_layout(showlegend=False)
    return apply_chart_theme(fig, title=title, height=height)


def kpi_card(label, value, sub=""):
    sub_html = f'<div class="kpi-sub">{sub}</div>' if sub else ""
    return f"""<div class="kpi-card"><div class="kpi-label">{label}</div>
<div class="kpi-value">{value}</div>{sub_html}</div>"""


def company_card(ticker, revenue, margin, form, date, url):
    rev = f"${revenue:,.0f}M" if revenue is not None else "N/A"
    nm = f"{margin:.1f}%" if margin is not None else "N/A"
    return f"""<div class="company-card" style="--accent:{COMPANY_COLORS[ticker]}">
<h4 style="color:{COMPANY_COLORS[ticker]}">{COMPANY_NAMES[ticker]} ({ticker})</h4>
<div class="stat-row"><span class="stat-label">Revenue</span><span class="stat-value">{rev}</span></div>
<div class="stat-row"><span class="stat-label">Net Margin</span><span class="stat-value">{nm}</span></div>
<div class="stat-row"><span class="stat-label">Latest Filing</span><span class="stat-value">{form} {date}</span></div>
<div style="margin-top:0.7rem"><a href="{url}" target="_blank">SEC Filing ↗</a></div></div>"""


def status_pill(ok, ok_text, warn_text):
    cls = "status-ok" if ok else "status-warn"
    text = ok_text if ok else warn_text
    return f'<span class="status-pill {cls}">{"●" if ok else "○"} {text}</span>'
