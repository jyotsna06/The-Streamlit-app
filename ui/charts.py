"""Plotly chart builders."""

import plotly.express as px
import plotly.graph_objects as go

from ui.styles import (
    AXIS_STYLE, CHART_LAYOUT, COMPANY_COLORS, COMPANY_GRADIENTS, COMPANY_NAMES,
)


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
            marker=dict(color=c, line=dict(width=0)),
            hovertemplate=(
                f"<b>{COMPANY_NAMES.get(ticker, ticker)}</b><br>"
                f"%{{x}}<br>{y_title}: %{{y:,.1f}}<extra></extra>"
            ),
        ))
    fig.update_layout(barmode="group", bargap=0.18, bargroupgap=0.08)
    return apply_chart_theme(fig, title=title, height=height)


def build_smooth_line(df, x, y, color, y_title, title=None, height=420):
    fig = go.Figure()
    for ticker in sorted(df[color].unique()):
        sub = df[df[color] == ticker].sort_values(x)
        c = COMPANY_COLORS.get(ticker, "#6366f1")
        grad = COMPANY_GRADIENTS.get(ticker, ("rgba(99,102,241,0.5)", "rgba(99,102,241,0.05)"))
        fig.add_trace(go.Scatter(
            x=sub[x], y=sub[y], name=COMPANY_NAMES.get(ticker, ticker),
            mode="lines+markers",
            line=dict(color=c, width=2.5, shape="spline"),
            marker=dict(size=7, color=c, line=dict(width=2, color="#0f172a")),
            fill="tozeroy", fillcolor=grad[1],
            hovertemplate=(
                f"<b>{COMPANY_NAMES.get(ticker, ticker)}</b><br>"
                f"%{{x}}<br>{y_title}: %{{y:,.2f}}<extra></extra>"
            ),
        ))
    return apply_chart_theme(fig, title=title, height=height)


def build_margin_facets(df, x, y, color, facet, y_title, title=None, height=380):
    fig = px.line(df, x=x, y=y, color=color, facet_col=facet, markers=True,
                  color_discrete_map=COMPANY_COLORS,
                  labels={y: y_title, x: "Period", color: "Company"})
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1].replace("_", " ").title()))
    fig.update_traces(line=dict(width=2.5), marker=dict(size=6))
    return apply_chart_theme(fig, title=title, height=height)


def build_donut(labels, values, title=None, height=340):
    colors = [COMPANY_COLORS.get(lbl, "#6366f1") for lbl in labels]
    fig = go.Figure(go.Pie(
        labels=[COMPANY_NAMES.get(lbl, lbl) for lbl in labels], values=values,
        hole=0.62, marker=dict(colors=colors, line=dict(color="#0f172a", width=2)),
        textinfo="label+percent", textfont=dict(size=12, color="#e2e8f0"),
        hovertemplate="<b>%{label}</b><br>$%{value:,.0f}M<br>%{percent}<extra></extra>",
    ))
    fig.update_layout(showlegend=False)
    return apply_chart_theme(fig, title=title, height=height)
