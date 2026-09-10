from datetime import datetime, timezone

import os

import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output

from data_sources import COMPANY_TICKERS, fetch_layoffs, fetch_revenue_growth, CACHE_DIR

companies = sorted(COMPANY_TICKERS.keys())
PRIVATE_COMPANIES = sorted(c for c, ticker in COMPANY_TICKERS.items() if ticker is None)

app = Dash(__name__)
server = app.server  # gunicorn's entrypoint on Render: `gunicorn codefile:server`

card_style = {"width": "70%", "margin": "0 auto 40px", "padding": "20px",
              "backgroundColor": "white", "borderRadius": "8px",
              "boxShadow": "0 2px 6px rgba(0,0,0,0.1)"}

app.layout = html.Div([
    html.H1("Tech Company Analytics Dashboard", style={"textAlign": "center", "color": "#2c3e50", "paddingTop": "20px"}),
    html.P("live layoffs (AILayoff.live) and real quarterly revenue growth (Alpha Vantage) by company",
           style={"textAlign": "center", "color": "gray"}),
    html.P(
        f"Revenue growth isn't available for private companies: {', '.join(PRIVATE_COMPANIES)}. "
        "Layoffs data comes from a small third-party tracker, not an official government source "
        "— treat it as a useful signal, not ground truth.",
        style={"textAlign": "center", "color": "#a06a2c", "fontSize": "0.85em", "maxWidth": "700px", "margin": "0 auto"}
    ),

    html.Div([
        html.Label("Companies:", style={"fontWeight": "bold"}),
        dcc.Dropdown(
            id="company-selector",
            options=[{"label": c, "value": c} for c in companies],
            value=["Amazon", "Google", "Meta"],
            multi=True
        ),
    ], style=card_style),

    html.Div(id="last-updated", style={"textAlign": "center", "color": "gray", "fontSize": "0.8em", "marginBottom": "10px"}),
    html.Div(id="dashboard-content", style={"padding": "0 40px"}),

    # Re-render periodically so the page picks up a background cache refresh
    # without the user needing to reload; the underlying fetch functions only
    # hit the live APIs once their own cache TTL has actually expired.
    dcc.Interval(id="refresh-timer", interval=30 * 60 * 1000),
], style={"fontFamily": "Arial", "backgroundColor": "#f4f6f9", "minHeight": "100vh"})


def _cache_age_label(name):
    path = CACHE_DIR / f"{name}.json"
    if not path.exists():
        return "never fetched"
    mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
    return mtime.strftime("%Y-%m-%d %H:%M UTC")


def layoffs_chart(selected_companies):
    events = fetch_layoffs(selected_companies)
    if not events:
        return None

    ldf = pd.DataFrame(events)
    ldf["date"] = pd.to_datetime(ldf["date"])
    ldf["period"] = ldf["date"].values.astype("datetime64[M]")
    grouped = ldf.groupby(["company", "period"])["jobs_displaced"].sum().reset_index()
    return px.line(grouped, x="period", y="jobs_displaced", color="company",
                   title="Layoffs Over Time (live)", markers=True)


def revenue_growth_chart(selected_companies):
    rows = fetch_revenue_growth(selected_companies)
    if not rows:
        return None

    rdf = pd.DataFrame(rows)
    rdf = rdf[rdf["company_name"].isin(selected_companies)]
    if rdf.empty:
        return None
    rdf["fiscal_date"] = pd.to_datetime(rdf["fiscal_date"])
    return px.line(rdf, x="fiscal_date", y="revenue_growth_percent", color="company_name",
                    title="Revenue Growth % YoY Over Time (live)", markers=True)


@app.callback(
    Output("dashboard-content", "children"),
    Output("last-updated", "children"),
    Input("company-selector", "value"),
    Input("refresh-timer", "n_intervals"),
)
def update_dashboard(selected_companies, _n_intervals):
    if not selected_companies:
        return (
            html.P("select a company to see the charts", style={"textAlign": "center", "color": "gray", "marginTop": "40px"}),
            "",
        )

    figs = [
        fig for fig in [layoffs_chart(selected_companies), revenue_growth_chart(selected_companies)]
        if fig is not None
    ]

    if not figs:
        content = html.P(
            "No live data available yet — check that ALPHA_VANTAGE_API_KEY and "
            "AILAYOFF_API_KEY are set in .env.",
            style={"textAlign": "center", "color": "#a06a2c", "marginTop": "40px"},
        )
    else:
        # css grid instead of manually pairing charts into rows - handles odd numbers
        # of charts fine and reflows on narrower screens without extra work
        content = html.Div(
            [dcc.Graph(figure=fig) for fig in figs],
            style={
                "display": "grid",
                "gridTemplateColumns": "repeat(auto-fit, minmax(500px, 1fr))",
                "gap": "20px"
            }
        )

    status = f"Layoffs data as of {_cache_age_label('layoffs')} · Revenue data as of {_cache_age_label('revenue_growth')}"
    return content, status


if __name__ == "__main__":
    app.run(debug=os.environ.get("ENVIRONMENT") != "production")
