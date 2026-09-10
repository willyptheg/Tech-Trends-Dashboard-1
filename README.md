# Dashboard Project

Set out on this project intending it to be a short, fun project built in Python and Dash to explore layoff trends and revenue growth across 20 major tech companies. Now pulls from live APIs instead of a static Kaggle snapshot.

Primary features:
- Multi-select dropdown to filter by company
- Layoffs over time per company (live)
- Revenue growth % over time per company (live)
- All charts update dynamically based on company selection

Tools used:
- Python
- pandas, plotly, dash, requests, python-dotenv

Live data sources:
- Layoffs: [AILayoff.live](https://ailayoffs.live/) API (free tier, 100 req/day). Small third-party tracker, not an official/government source — treat as a signal, not ground truth.
- Revenue growth: [Alpha Vantage](https://www.alphavantage.co/) `INCOME_STATEMENT` endpoint (free tier, 25 req/day). Real quarterly revenue; YoY growth is computed locally from it. Only covers publicly traded companies — Anthropic, Databricks, OpenAI, and Stripe are private and have no revenue data.

Dropped from the original Kaggle-based version: AI adoption level, job security score, and salary budget change. Those columns were synthetic in the Kaggle dataset and have no real live-data equivalent, so rather than fake a "live" number for them, those charts were removed.

Both APIs have low daily request caps, so responses are cached to disk (`cache/`) and only refetched once the cache goes stale (12h for layoffs, 24h for revenue growth) — see `data_sources.py`.

Companies shown (A-Z):
- Adobe, Airbnb, Amazon, Anthropic, Apple, Databricks, Google, Intel, Meta,
Microsoft, NVIDIA, Netflix, OpenAI, Oracle, Palantir, SAP, Salesforce,
Spotify, Stripe, Uber

How to run:
1. `pip install -r requirements.txt`
2. Copy `.env.example` to `.env` and fill in `ALPHA_VANTAGE_API_KEY` (free key: https://www.alphavantage.co/support/#api-key) and `AILAYOFF_API_KEY` (free key: https://ailayoffs.live/)
3. `python codefile.py`
4. Go to the address shown in terminal

Challenges + WIP features:
- Creating overlapping charts that are readable
- Comprehensive report
- Neither free API tier supports enough request volume for a snappy manual refresh button — currently relies on a background timer plus disk caching instead
- Creating an export to PDF or CSV capability
