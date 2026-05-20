"""
norton_acquisition.py — QBL Commerce Application Layer
======================================================
Acquisition intelligence module for Tane Norton
ABN: 94 266 884 889 | Kippa-Ring QLD 4021

Integrates with QBL Commerce Standard (Chapter 12):
- Tool 1: Helium/DePIN Hotspot Calculator → feeds DePINMonitor agent
- Tool 2: RWA Token Scanner → feeds QuantumPortfolio correlation engine
- Tool 3: Liquidation Auction Monitor → feeds QuantumMarketSearch (Grover)
- Tool 4: PPSR Search Info → risk assessment layer

Usage:
    python3 -m qbl.applications.norton_acquisition
    from qbl.applications.norton_acquisition import main
"""

from __future__ import annotations

import json
import re
import sys
import time
from datetime import datetime, timezone
from typing import Any, Dict, List

import httpx
import numpy as np
from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

OWNER = "Tane Norton"
ABN = "94 266 884 889"
LOCATION = "Kippa-Ring QLD 4021"
CURRENCY = "AUD"

BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-AU,en;q=0.9",
}

JSON_HEADERS = {
    **BROWSER_HEADERS,
    "Accept": "application/json, text/javascript, */*; q=0.01",
}

TIMEOUT = 20

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fmt_aud(value: float | None) -> str:
    if value is None:
        return "N/A"
    return f"${value:,.2f} AUD"

def _fmt_pct(value: float | None) -> str:
    if value is None:
        return "N/A"
    sign = "+" if value >= 0 else ""
    return f"{sign}{value:.2f}%"

# ===========================================================================
# TOOL 1 — HELIUM / DePIN HOTSPOT CALCULATOR
# ===========================================================================

HELIUM_5G_HARDWARE_COST_AUD = 1_200.00
HELIUM_IOT_HARDWARE_COST_AUD = 650.00
MONTHLY_POWER_COST_AUD = 4.50
MONTHLY_INTERNET_COST_AUD = 0.00
HELIUM_5G_MONTHLY_HNT_ESTIMATE = 15.0
HELIUM_IOT_MONTHLY_HNT_ESTIMATE = 8.0
KIPPA_RING_LAT = -27.2167
KIPPA_RING_LON = 153.0833
COINGECKO_BASE = "https://api.coingecko.com/api/v3"

def _fetch_hnt_price_aud() -> Dict[str, Any]:
    """Fetch live HNT price in AUD from CoinGecko."""
    url = (
        f"{COINGECKO_BASE}/simple/price"
        f"?ids=helium&vs_currencies=aud,usd"
        f"&include_market_cap=true&include_24hr_change=true"
    )
    try:
        r = httpx.get(url, headers=JSON_HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
        data = r.json().get("helium", {})
        return {
            "price_aud": data.get("aud"),
            "price_usd": data.get("usd"),
            "market_cap_aud": data.get("aud_market_cap"),
            "change_24h": data.get("aud_24h_change"),
            "source": "CoinGecko",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    except Exception as exc:
        return {"price_aud": None, "error": str(exc), "source": "CoinGecko (failed)"}


def helium_hotspot_calculator() -> Dict[str, Any]:
    """
    Tool 1: Helium/DePIN Hotspot ROI Calculator for Kippa-Ring QLD 4021.
    Fetches live HNT price and calculates ROI for 5G and IoT hotspots.
    """
    result: Dict[str, Any] = {
        "tool": "Helium / DePIN Hotspot Calculator",
        "owner": OWNER,
        "location": LOCATION,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    hnt = _fetch_hnt_price_aud()
    result["hnt_price"] = hnt
    price_aud = hnt.get("price_aud") or 0.0

    # 5G ROI
    rev_5g = HELIUM_5G_MONTHLY_HNT_ESTIMATE * price_aud
    cost_5g = MONTHLY_POWER_COST_AUD + MONTHLY_INTERNET_COST_AUD
    profit_5g = rev_5g - cost_5g
    payback_5g = HELIUM_5G_HARDWARE_COST_AUD / profit_5g if profit_5g > 0 else float("inf")

    result["hotspot_5g"] = {
        "hardware_cost_aud": HELIUM_5G_HARDWARE_COST_AUD,
        "monthly_hnt_estimate": HELIUM_5G_MONTHLY_HNT_ESTIMATE,
        "monthly_revenue_aud": round(rev_5g, 2),
        "monthly_profit_aud": round(profit_5g, 2),
        "payback_months": round(payback_5g, 1) if payback_5g != float("inf") else "N/A",
        "annual_roi_pct": round((profit_5g * 12) / HELIUM_5G_HARDWARE_COST_AUD * 100, 1),
    }

    # IoT ROI
    rev_iot = HELIUM_IOT_MONTHLY_HNT_ESTIMATE * price_aud
    profit_iot = rev_iot - cost_5g
    payback_iot = HELIUM_IOT_HARDWARE_COST_AUD / profit_iot if profit_iot > 0 else float("inf")

    result["hotspot_iot"] = {
        "hardware_cost_aud": HELIUM_IOT_HARDWARE_COST_AUD,
        "monthly_hnt_estimate": HELIUM_IOT_MONTHLY_HNT_ESTIMATE,
        "monthly_revenue_aud": round(rev_iot, 2),
        "monthly_profit_aud": round(profit_iot, 2),
        "payback_months": round(payback_iot, 1) if payback_iot != float("inf") else "N/A",
        "annual_roi_pct": round((profit_iot * 12) / HELIUM_IOT_HARDWARE_COST_AUD * 100, 1),
    }

    result["depin_alternatives"] = [
        {"name": "GEODNET", "hardware_aud": 800, "monthly_usd": "30-80"},
        {"name": "Hivemapper", "hardware_aud": 700, "monthly_usd": "20-150"},
    ]

    return result

# ===========================================================================
# TOOL 2 — RWA TOKEN SCANNER
# ===========================================================================

RWA_TOKENS = [
    {"id": "ondo-finance", "symbol": "ONDO", "name": "Ondo Finance",
     "yield_type": "US Treasury yield (~4.7% p.a.)"},
    {"id": "centrifuge", "symbol": "CFG", "name": "Centrifuge",
     "yield_type": "Variable pool yields (5-12% p.a.)"},
    {"id": "maple", "symbol": "MPL", "name": "Maple Finance",
     "yield_type": "Institutional credit (6-10% p.a.)"},
    {"id": "clearpool", "symbol": "CPOOL", "name": "Clearpool",
     "yield_type": "Borrower-set rates (8-15% p.a.)"},
]

AU_SAVINGS_RATE = 4.5

def rwa_token_scanner() -> Dict[str, Any]:
    """Tool 2: RWA Token Scanner — live prices for ONDO, CFG, MPL, CPOOL."""
    result: Dict[str, Any] = {
        "tool": "RWA Token Scanner",
        "owner": OWNER,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "au_savings_rate_pct": AU_SAVINGS_RATE,
        "tokens": [],
    }

    ids = ",".join(t["id"] for t in RWA_TOKENS)
    url = (
        f"{COINGECKO_BASE}/coins/markets"
        f"?vs_currency=aud&ids={ids}&order=market_cap_desc"
        f"&per_page=20&page=1&sparkline=false"
    )

    try:
        r = httpx.get(url, headers=JSON_HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
        market_data = {item["id"]: item for item in r.json()}
    except Exception as exc:
        result["error"] = f"CoinGecko fetch failed: {exc}"
        market_data = {}

    for token_def in RWA_TOKENS:
        md = market_data.get(token_def["id"], {})
        result["tokens"].append({
            **token_def,
            "price_aud": md.get("current_price"),
            "market_cap_aud": md.get("market_cap"),
            "change_24h_pct": md.get("price_change_percentage_24h"),
            "volume_24h_aud": md.get("total_volume"),
        })

    return result

# ===========================================================================
# TOOL 3 — LIQUIDATION AUCTION MONITOR
# ===========================================================================

SEARCH_TERMS = ["networking equipment", "server", "solar panels", "Milwaukee", "tools"]

RETAIL_BENCHMARKS = {
    "server": 3000, "rack": 800, "switch": 600, "router": 400,
    "solar": 1500, "panel": 400, "milwaukee": 500, "drill": 300,
    "grinder": 250, "saw": 400, "generator": 1200, "ups": 600,
    "networking": 500, "cisco": 800, "hp": 600, "dell": 800,
}

GRAYS_ALGOLIA_APP_ID = "CKPAMVUUBE"
GRAYS_ALGOLIA_API_KEY = "1a31357659d5c40f4641cc0d46c172d0"
GRAYS_ALGOLIA_INDEX = "GOL_MAIN"
GRAYS_ALGOLIA_URL = f"https://{GRAYS_ALGOLIA_APP_ID.lower()}-dsn.algolia.net/1/indexes/{GRAYS_ALGOLIA_INDEX}/query"
GRAYS_BASE_URL = "https://www.grays.com"

def _estimate_retail(title: str) -> float | None:
    title_lower = title.lower()
    best = None
    for kw, price in RETAIL_BENCHMARKS.items():
        if kw in title_lower:
            if best is None or price > best:
                best = price
    return best

def _scrape_grays(search_term: str, max_results: int = 5) -> List[Dict]:
    """Search Grays Online via Algolia API."""
    headers = {
        "X-Algolia-Application-Id": GRAYS_ALGOLIA_APP_ID,
        "X-Algolia-API-Key": GRAYS_ALGOLIA_API_KEY,
        "Content-Type": "application/json",
    }
    payload = {
        "query": search_term,
        "hitsPerPage": max_results,
        "filters": "ObjectType:LOT OR ObjectType:RETAIL",
    }
    try:
        r = httpx.post(GRAYS_ALGOLIA_URL, json=payload, headers=headers, timeout=TIMEOUT)
        r.raise_for_status()
        hits = r.json().get("hits", [])
        results = []
        for hit in hits:
            title = hit.get("ObjectTitle", "Unknown")
            price = hit.get("ObjectPrice")
            retail_est = _estimate_retail(title)
            results.append({
                "source": "Grays Online",
                "title": title,
                "current_price_aud": price,
                "retail_estimate_aud": retail_est,
                "undervalue": price is not None and retail_est is not None and price < retail_est * 0.5,
                "url": f"{GRAYS_BASE_URL}{hit.get('ITEM_URL', '')}",
            })
        return results
    except Exception as exc:
        return [{"source": "Grays Online", "error": str(exc)}]


def liquidation_auction_monitor() -> Dict[str, Any]:
    """Tool 3: Scan Grays Online for undervalued equipment."""
    result: Dict[str, Any] = {
        "tool": "Liquidation Auction Monitor",
        "owner": OWNER,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "search_terms": SEARCH_TERMS,
        "items": [],
        "flagged_undervalue": [],
    }

    all_items = []
    for term in SEARCH_TERMS:
        items = _scrape_grays(term, max_results=4)
        all_items.extend([i for i in items if "error" not in i])
        time.sleep(0.3)

    # Deduplicate
    seen = set()
    for item in all_items:
        key = item.get("title", "")[:60]
        if key not in seen:
            seen.add(key)
            result["items"].append(item)

    result["flagged_undervalue"] = [i for i in result["items"] if i.get("undervalue")]
    result["total_items"] = len(result["items"])
    result["flagged_count"] = len(result["flagged_undervalue"])
    return result

# ===========================================================================
# TOOL 4 — PPSR SEARCH INFO
# ===========================================================================

def ppsr_search_info() -> Dict[str, Any]:
    """Tool 4: PPSR info — how to check auction items for liens."""
    return {
        "tool": "PPSR Search Info",
        "owner": OWNER,
        "abn": ABN,
        "ppsr_url": "https://ppsr.gov.au",
        "cost_per_search_aud": 2.00,
        "recommendation": (
            "Search PPSR before any auction purchase over $500. "
            "At $2/search, it's cheap insurance against hidden liens."
        ),
        "search_types": [
            "Serial Number (VIN/chassis) — most reliable",
            "Grantor (seller ABN/ACN) — shows all their encumbrances",
            "Collateral description — broad class search",
        ],
    }

# ===========================================================================
# QBL INTEGRATION — Connect to Quantum Commerce Engine
# ===========================================================================

def run_with_quantum_commerce():
    """
    Run all 4 tools and feed results into QBL Commerce Engine.
    This bridges classical data fetching with quantum decision-making.
    """
    try:
        from qbl.commerce import (
            QRNGPricingEngine, QuantumMarketSearch, QuantumPortfolio,
            create_acquisition_agent
        )
        HAS_QBL = True
    except ImportError:
        HAS_QBL = False

    print("=" * 70)
    print("  NORTON ACQUISITION INTELLIGENCE + QBL QUANTUM COMMERCE")
    print(f"  Owner: {OWNER} | ABN: {ABN} | Location: {LOCATION}")
    print(f"  Time: {datetime.now().strftime('%d %B %Y %H:%M AEST')}")
    print("=" * 70)

    # Run classical tools
    print("\n[1/4] Helium/DePIN Calculator...")
    t1 = helium_hotspot_calculator()
    hnt_price = t1.get("hnt_price", {}).get("price_aud")
    print(f"  HNT: {_fmt_aud(hnt_price)}")
    h5g = t1.get("hotspot_5g", {})
    print(f"  5G ROI: {h5g.get('annual_roi_pct', 'N/A')}% | Payback: {h5g.get('payback_months', 'N/A')} months")

    print("\n[2/4] RWA Token Scanner...")
    t2 = rwa_token_scanner()
    for tok in t2.get("tokens", []):
        p = tok.get("price_aud")
        c = tok.get("change_24h_pct")
        print(f"  {tok['symbol']:6s} {_fmt_aud(p):>16s}  {_fmt_pct(c)}")

    print("\n[3/4] Liquidation Auction Monitor...")
    t3 = liquidation_auction_monitor()
    print(f"  Found: {t3.get('total_items', 0)} items | Flagged: {t3.get('flagged_count', 0)} undervalue")
    for item in t3.get("flagged_undervalue", [])[:5]:
        ratio = item["retail_estimate_aud"] / item["current_price_aud"] if item.get("current_price_aud") else 0
        print(f"  ★ {item['title'][:50]} — {_fmt_aud(item['current_price_aud'])} ({ratio:.1f}× value)")

    print("\n[4/4] PPSR Search Info...")
    t4 = ppsr_search_info()
    print(f"  URL: {t4['ppsr_url']} | Cost: {_fmt_aud(t4['cost_per_search_aud'])}/search")

    # Quantum Commerce Layer
    if HAS_QBL:
        print("\n" + "=" * 70)
        print("  QBL QUANTUM COMMERCE ENGINE (d=13)")
        print("=" * 70)

        # Feed auction items into Grover search
        if t3.get("items"):
            searcher = QuantumMarketSearch(dimension=13)
            searcher.load_catalog(t3["items"])
            condition = lambda item: item.get("undervalue", False)
            result = searcher.quantum_search(condition)
            print(f"\n  Grover Search: {'Found' if result['found'] else 'No match'}")
            if result.get("result_item"):
                print(f"    → {result['result_item'].get('title', 'N/A')[:50]}")
            print(f"    Iterations: {result['grover_iterations']} (vs {result['classical_comparisons_needed']} classical)")

        # Feed RWA tokens into correlation engine
        portfolio = QuantumPortfolio(dimension=13)
        for tok in t2.get("tokens", []):
            # Generate synthetic returns from price (in production: use historical API)
            returns = np.random.normal(0.02, 0.10, 13).tolist()
            portfolio.add_asset(tok["symbol"], returns)

        matrix = portfolio.full_correlation_matrix()
        print(f"\n  Portfolio Correlations (quantum):")
        for pair, corr in sorted(matrix["correlations"].items(), key=lambda x: -x[1])[:3]:
            print(f"    {pair}: {corr:.4f}")

        # Quantum pricing for DePIN ROI decision
        engine = QRNGPricingEngine(dimension=13)
        if hnt_price:
            qp = engine.quantum_price(hnt_price, volatility=0.15)
            print(f"\n  QRNG Price Signal for HNT:")
            print(f"    Base: {_fmt_aud(hnt_price)} → Quantum: {_fmt_aud(qp['final_price'])} (|{qp['quantum_signal']}⟩)")

        # Run acquisition agent
        agent = create_acquisition_agent("Norton_Acquisition_Oracle")
        agent.run(max_steps=5)
        print(f"\n  Acquisition Agent: {agent.status()['strategy']} mode, {agent.status()['step_count']} steps")

    print("\n" + "=" * 70)
    print("  COMPLETE")
    print("=" * 70)

    return {"helium": t1, "rwa": t2, "auctions": t3, "ppsr": t4}


def main():
    return run_with_quantum_commerce()


if __name__ == "__main__":
    main()
