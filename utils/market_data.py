#!/usr/bin/env python3
"""Market data helpers: get today's silver price from reliable sources.

Priority order:
- data-asg.goldprice.org (no key required)
- Metals-API (if METALS_API_KEY provided)
- fallback: utils.web_scraper.get_live_info("silver price")
"""
from pathlib import Path
import os
import requests
from typing import Optional, Dict, Any


def _from_goldprice_org(timeout=10) -> Optional[Dict[str, Any]]:
    url = "https://data-asg.goldprice.org/dbXRates/USD"
    try:
        r = requests.get(url, timeout=timeout)
        r.raise_for_status()
        j = r.json()
        items = j.get("items") or []
        if items:
            item = items[0]
            # xagPrice is usually price per troy ounce in USD
            xag = item.get("xagPrice")
            if xag:
                return {"price_usd_per_oz": float(xag), "source": "goldprice.org"}
    except Exception:
        return None
    return None


def _from_metals_api(timeout=10) -> Optional[Dict[str, Any]]:
    key = os.getenv("METALS_API_KEY")
    if not key:
        return None
    # metals-api.com endpoint (may require signup)
    url = f"https://metals-api.com/api/latest?access_key={key}&base=USD&symbols=XAG"
    try:
        r = requests.get(url, timeout=timeout)
        r.raise_for_status()
        j = r.json()
        rates = j.get("rates") or {}
        xag = rates.get("XAG")
        if xag:
            # metals-api returns how many XAG equals 1 USD, so price per XAG in USD = 1 / xag
            price = 1.0 / float(xag) if float(xag) != 0 else None
            if price:
                return {"price_usd_per_oz": price, "source": "metals-api"}
    except Exception:
        return None
    return None


def get_silver_price() -> Dict[str, Any]:
    """Return a dict with keys: price_usd_per_oz, source, raw (optional).

    Tries multiple providers and returns the first successful.
    """
    # 1) Try goldprice.org (no API key)
    res = _from_goldprice_org()
    if res:
        return res

    # 2) Try Metals-API (if key provided)
    res = _from_metals_api()
    if res:
        return res

    # 3) Fallback to the project's web_scraper if present
    try:
        from utils.web_scraper import get_live_info
        snippet = get_live_info("silver price")
        return {"price_usd_per_oz": None, "source": "web_scraper", "raw": snippet}
    except Exception:
        return {"price_usd_per_oz": None, "source": "none", "raw": None}
