import re
import requests
from typing import Optional


def _search_duckduckgo(query: str) -> Optional[str]:
    """Perform a lightweight DuckDuckGo HTML search and return the first text snippet."""
    try:
        params = {"q": query}
        # DuckDuckGo lightweight HTML endpoint
        r = requests.get("https://html.duckduckgo.com/html/", params=params, timeout=8)
        text = r.text
        # Try to extract result snippets
        # Snippets often appear in <a class="result__a"> or <div class="result__snippet">
        m = re.search(r'<div class="result__snippet">\s*([^<]+)', text)
        if m:
            return m.group(1).strip()
        # fallback: look for any dollar amounts in page
        m2 = re.search(r"\$[0-9,.]+", text)
        if m2:
            return m2.group(0)
    except Exception as e:
        print(f"[WebScraper] DuckDuckGo error: {e}")
        return None
    return None


def _check_metalprices(query: str) -> Optional[str]:
    """Check for silver/gold prices using a simple search with price pattern."""
    q = query.lower()
    if any(word in q for word in ("silver", "gold", "platinum", "price")):
        try:
            # Add "price" to query if not present
            search_q = query if "price" in q else f"{query} price today"
            params = {"q": search_q}
            r = requests.get("https://html.duckduckgo.com/html/", params=params, timeout=5)
            text = r.text
            # Look for price patterns like $XX.XX
            prices = re.findall(r"\$\d+(?:\.\d{2})?", text)
            if prices:
                print(f"[WebScraper] Found prices: {prices}")
                return f"💰 {prices[0]} per ounce (from live search)"
        except Exception as e:
            print(f"[WebScraper] Metal price check error: {e}")
    return None


def _coingecko_price(query: str) -> Optional[str]:
    """If query references crypto, use CoinGecko public API - no auth needed."""
    q = query.lower()
    
    # Map tokens
    token_map = {
        "bitcoin": "bitcoin",
        "btc": "bitcoin",
        "ethereum": "ethereum",
        "eth": "ethereum",
        "doge": "dogecoin",
        "dogecoin": "dogecoin",
        "litecoin": "litecoin",
        "ltc": "litecoin",
        "ripple": "ripple",
        "xrp": "ripple",
    }
    
    # Find matching token
    token = None
    for keyword, token_id in token_map.items():
        if keyword in q:
            token = token_id
            break
    
    if not token:
        return None
    
    try:
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={token}&vs_currencies=usd"
        r = requests.get(url, timeout=6)
        data = r.json()
        price = data.get(token, {}).get("usd")
        if price:
            return f"💰 {token.capitalize()} price: ${price:,.2f} USD"
    except Exception as e:
        print(f"[WebScraper] CoinGecko error: {e}")
        return None
    return None


def get_live_info(query: str) -> Optional[str]:
    """Try several lightweight sources to extract live info (prices, weather snippets).
    Returns a short text result or None if not found.
    """
    print(f"[WebScraper] Attempting to scrape: '{query}'")
    
    # Try CoinGecko for crypto (no auth needed!)
    try:
        cg = _coingecko_price(query)
        if cg:
            print(f"[WebScraper] ✅ Got CoinGecko result: {cg}")
            return cg
    except Exception as e:
        print(f"[WebScraper] CoinGecko attempt failed: {e}")

    # Try metal/commodity prices
    try:
        mp = _check_metalprices(query)
        if mp:
            print(f"[WebScraper] ✅ Got metal price: {mp}")
            return mp
    except Exception as e:
        print(f"[WebScraper] Metal price attempt failed: {e}")

    # Try DuckDuckGo search result snippet
    try:
        dd = _search_duckduckgo(query)
        if dd:
            # Clean snippet a bit
            dd = re.sub(r"\s+", " ", dd).strip()
            # If contains useful info
            if len(dd) > 10:
                print(f"[WebScraper] ✅ Got DuckDuckGo snippet: {dd[:50]}...")
                return f"Live info: {dd}"
            # If contains a dollar amount, return it
            m = re.search(r"\$[0-9,.]+", dd)
            if m:
                print(f"[WebScraper] ✅ Found price: {m.group(0)}")
                return f"Found: {m.group(0)}"
    except Exception as e:
        print(f"[WebScraper] DuckDuckGo attempt failed: {e}")

    print(f"[WebScraper] ⚠️  No live info found for: '{query}'")
    return None