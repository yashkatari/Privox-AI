#!/usr/bin/env python3
"""Network connectivity diagnostic script"""
import os
import sys
import requests

def load_env_file(path=".env"):
    """Load .env file"""
    from pathlib import Path
    try:
        if not Path(path).exists():
            return
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = value
    except Exception as e:
        print(f"Failed to load {path}: {e}")

load_env_file()

print("="*70)
print("🔍 NETWORK & API CONNECTIVITY DIAGNOSTIC")
print("="*70)

# Test 1: Basic internet ping
print("\n[TEST 1] Can reach Google DNS (8.8.8.8)?")
try:
    r = requests.get("https://dns.google/", timeout=5)
    print(f"  ✅ SUCCESS (status {r.status_code})")
except Exception as e:
    print(f"  ❌ FAILED: {e}")

# Test 2: DuckDuckGo reachability
print("\n[TEST 2] Can reach DuckDuckGo?")
try:
    r = requests.get("https://html.duckduckgo.com/", timeout=5)
    print(f"  ✅ SUCCESS (status {r.status_code})")
except Exception as e:
    print(f"  ❌ FAILED: {e}")

# Test 3: CoinGecko reachability
print("\n[TEST 3] Can reach CoinGecko API?")
try:
    r = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd", timeout=5)
    print(f"  ✅ SUCCESS (status {r.status_code})")
    print(f"     Data: {r.json()}")
except Exception as e:
    print(f"  ❌ FAILED: {e}")

# Test 4: OpenRouter connectivity
print("\n[TEST 4] Can reach OpenRouter API?")
api_key = os.getenv("OPENROUTER_API_KEY")
url = os.getenv("OPENROUTER_URL", "https://api.openrouter.ai/v1/chat/completions")

if not api_key:
    print(f"  ❌ NO API KEY SET")
else:
    print(f"  API Key: {api_key[:20]}...")
    print(f"  URL: {url}")
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        payload = {
            "model": "gpt-4o-mini",
            "messages": [{"role": "user", "content": "test"}],
            "max_tokens": 10
        }
        r = requests.post(url, headers=headers, json=payload, timeout=10)
        print(f"  ✅ CONNECTION SUCCESS (status {r.status_code})")
        if r.status_code == 200:
            print(f"     Response: {r.json()}")
        else:
            print(f"     Error: {r.text[:200]}")
    except Exception as e:
        print(f"  ❌ FAILED: {type(e).__name__}: {e}")

# Test 5: Web scraper test
print("\n[TEST 5] Test web_scraper.get_live_info()?")
try:
    from utils.web_scraper import get_live_info
    result = get_live_info("silver price")
    print(f"  Result: {result}")
    if result:
        print(f"  ✅ SUCCESS")
    else:
        print(f"  ⚠️  No result (might be expected)")
except Exception as e:
    print(f"  ❌ FAILED: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*70)
print("SUMMARY:")
print("  - Check if GoogleDNS/DuckDuckGo work to verify internet")
print("  - Check OpenRouter to verify API key & network")
print("  - Check CoinGecko for web scraper capability")
print("="*70)
