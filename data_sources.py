"""Live data fetching for the dashboard, with file-based caching.

Both upstream free tiers are low-volume (Alpha Vantage: 25 req/day,
AILayoff.live: 100 req/day), so results are cached to disk and only
refetched once the cache goes stale. If a live fetch fails (bad key,
rate limit, network), the last good cache is served instead so the
dashboard degrades gracefully rather than going blank.
"""

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

ALPHA_VANTAGE_API_KEY = os.environ.get("ALPHA_VANTAGE_API_KEY", "")
AILAYOFF_API_KEY = os.environ.get("AILAYOFF_API_KEY", "")
AILAYOFF_BASE_URL = os.environ.get("AILAYOFF_BASE_URL", "https://ailayoffs.live/api")

CACHE_DIR = Path(__file__).parent / "cache"
CACHE_DIR.mkdir(exist_ok=True)

# Ticker map: companies without a public ticker (private) have no
# revenue-growth data available; they only appear in the layoffs chart.
COMPANY_TICKERS = {
    "Adobe": "ADBE",
    "Airbnb": "ABNB",
    "Amazon": "AMZN",
    "Anthropic": None,
    "Apple": "AAPL",
    "Databricks": None,
    "Google": "GOOGL",
    "Intel": "INTC",
    "Meta": "META",
    "Microsoft": "MSFT",
    "NVIDIA": "NVDA",
    "Netflix": "NFLX",
    "OpenAI": None,
    "Oracle": "ORCL",
    "Palantir": "PLTR",
    "SAP": "SAP",
    "Salesforce": "CRM",
    "Spotify": "SPOT",
    "Stripe": None,
    "Uber": "UBER",
}


def _read_cache(name, max_age_hours):
    path = CACHE_DIR / f"{name}.json"
    if not path.exists():
        return None
    with open(path, "r") as f:
        cached = json.load(f)
    fetched_at = datetime.fromisoformat(cached["fetched_at"])
    age_hours = (datetime.now(timezone.utc) - fetched_at).total_seconds() / 3600
    if age_hours > max_age_hours:
        return None
    return cached["data"]


def _write_cache(name, data):
    path = CACHE_DIR / f"{name}.json"
    with open(path, "w") as f:
        json.dump({"fetched_at": datetime.now(timezone.utc).isoformat(), "data": data}, f)


def _stale_cache(name):
    """Last-resort fallback when a live fetch fails: serve whatever we have, however old."""
    path = CACHE_DIR / f"{name}.json"
    if not path.exists():
        return None
    with open(path, "r") as f:
        return json.load(f)["data"]


def fetch_layoffs(companies, max_age_hours=12):
    """Real layoff events from AILayoff.live, filtered to the given companies."""
    cached = _read_cache("layoffs", max_age_hours)
    if cached is not None:
        return cached

    if not AILAYOFF_API_KEY:
        stale = _stale_cache("layoffs")
        if stale is not None:
            return stale
        return []

    try:
        resp = requests.get(
            f"{AILAYOFF_BASE_URL}/layoffs",
            params={"sector": "tech"},
            headers={"Authorization": f"Bearer {AILAYOFF_API_KEY}"},
            timeout=15,
        )
        resp.raise_for_status()
        events = resp.json().get("data", [])
    except requests.RequestException:
        stale = _stale_cache("layoffs")
        return stale if stale is not None else []

    wanted = {c.lower() for c in companies}
    events = [e for e in events if e.get("company", "").lower() in wanted]
    _write_cache("layoffs", events)
    return events


def fetch_revenue_growth(companies, max_age_hours=24):
    """Real quarterly revenue (and YoY growth computed from it) via Alpha Vantage.

    Only companies with a public ticker are queried; private companies are
    skipped since there's no financial-statement data available for them.
    """
    cached = _read_cache("revenue_growth", max_age_hours)
    if cached is not None:
        return cached

    if not ALPHA_VANTAGE_API_KEY:
        stale = _stale_cache("revenue_growth")
        if stale is not None:
            return stale
        return []

    rows = []
    for company in companies:
        ticker = COMPANY_TICKERS.get(company)
        if not ticker:
            continue
        try:
            resp = requests.get(
                "https://www.alphavantage.co/query",
                params={
                    "function": "INCOME_STATEMENT",
                    "symbol": ticker,
                    "apikey": ALPHA_VANTAGE_API_KEY,
                },
                timeout=15,
            )
            resp.raise_for_status()
            reports = resp.json().get("quarterlyReports", [])
        except requests.RequestException:
            continue

        # quarterlyReports is newest-first; walk oldest-to-newest so we can
        # compute YoY growth against the report 4 quarters prior.
        reports = list(reversed(reports))
        for i, report in enumerate(reports):
            if i < 4:
                continue
            try:
                current = float(report["totalRevenue"])
                prior = float(reports[i - 4]["totalRevenue"])
            except (KeyError, TypeError, ValueError):
                continue
            if prior == 0:
                continue
            rows.append({
                "company_name": company,
                "fiscal_date": report["fiscalDateEnding"],
                "revenue_growth_percent": (current - prior) / prior * 100,
            })

        time.sleep(1)  # be polite to the free-tier rate limit

    if rows:
        _write_cache("revenue_growth", rows)
        return rows

    stale = _stale_cache("revenue_growth")
    return stale if stale is not None else []
