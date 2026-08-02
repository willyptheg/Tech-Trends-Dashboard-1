import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output

df = pd.read_csv("layoff_data.csv")

df = df.dropna(subset=["company_name", "industry", "country", "layoffs_count"])
df["company_name"] = df["company_name"].str.strip().str.title()
df["industry"] = df["industry"].str.strip().str.title()
df["country"] = df["country"].str.strip().str.title()

# months are Jan/Feb/etc, need actual dates to sort properly
df["month"] = pd.to_datetime(df["month"], format="%b").dt.month
df["period"] = pd.to_datetime(
    df["year"].astype(str) + "-" + df["month"].astype(str).str.zfill(2),
    format="%Y-%m"
)
df = df.sort_values("period")

companies = sorted(df["company_name"].unique())

# (column, chart title, agg func) - layoffs is a sum, everything else is a mean
METRICS = [
    ("layoffs_count", "Layoffs Over Time", "sum"),
    ("ai_adoption_level", "AI Adoption Level Over Time", "mean"),
    ("job_security_score", "Job Security Score Over Time", "mean"),
    ("revenue_growth_percent", "Revenue Growth % Over Time", "mean"),
    ("salary_budget_change", "Salary Budget Change Over Time", "mean"),
]

app = Dash(__name__)

card_style = {"width": "70%", "margin": "0 auto 40px", "padding": "20px",
              "backgroundColor": "white", "borderRadius": "8px",
              "boxShadow": "0 2px 6px rgba(0,0,0,0.1)"}

app.layout = html.Div([
    html.H1("Tech Company Analytics Dashboard", style={"textAlign": "center", "color": "#2c3e50", "paddingTop": "20px"}),
    html.P("layoffs, AI adoption, job security, revenue + salary trends by company",
           style={"textAlign": "center", "color": "gray"}),

    html.Div([
        html.Label("Companies:", style={"fontWeight": "bold"}),
        dcc.Dropdown(
            id="company-selector",
            options=[{"label": c, "value": c} for c in companies],
            value=["Amazon", "Google", "Meta"],
            multi=True
        ),
    ], style=card_style),

    html.Div(id="dashboard-content", style={"padding": "0 40px"})
], style={"fontFamily": "Arial", "backgroundColor": "#f4f6f9", "minHeight": "100vh"})


def line_chart(data, y_col, title, agg):
    grouped = data.groupby(["company_name", "period"])[y_col].agg(agg).reset_index()
    return px.line(grouped, x="period", y=y_col, color="company_name", title=title, markers=True)


@app.callback(Output("dashboard-content", "children"), Input("company-selector", "value"))
def update_dashboard(selected_companies):
    if not selected_companies:
        return html.P("select a company to see the charts", style={"textAlign": "center", "color": "gray", "marginTop": "40px"})

    filtered = df[df["company_name"].isin(selected_companies)]

    figs = [line_chart(filtered, col, title, agg) for col, title, agg in METRICS]

    # css grid instead of manually pairing charts into rows - handles odd numbers
    # of charts fine and reflows on narrower screens without extra work
    grid = html.Div(
        [dcc.Graph(figure=fig) for fig in figs],
        style={
            "display": "grid",
            "gridTemplateColumns": "repeat(auto-fit, minmax(500px, 1fr))",
            "gap": "20px"
        }
    )

    return grid


if __name__ == "__main__":
    app.run(debug=True)