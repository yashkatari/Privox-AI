"""Orchestrator: fetch today's silver price then ask Groq to explain/summarize/advice.

Usage:
  - Set `GROQ_API_KEY` in environment or .env to enable Groq calls.
  - Optionally set `METALS_API_KEY` to use Metals-API instead of the public fallback.
"""
import os
from pathlib import Path

# Load .env if present
env_path = Path('.env')
if env_path.exists():
    for line in env_path.read_text().splitlines():
        if '=' in line and not line.strip().startswith('#'):
            k, v = line.split('=', 1)
            if k and k not in os.environ:
                os.environ[k.strip()] = v.strip().strip('"').strip("'")

from utils.market_data import get_silver_price
from system.groq_client import explain_silver_price


def main():
    print('Fetching today\'s silver price...')
    info = get_silver_price()
    price = info.get('price_usd_per_oz')
    source = info.get('source')
    raw = info.get('raw')

    if price:
        print(f"Silver: ${price:.2f} per troy oz (source: {source})")
    else:
        print(f"Silver price not found. Source: {source}. Raw: {raw}")

    try:
        print('\nAsking Groq to explain/summarize...')
        explanation = explain_silver_price(price, source)
        print('\n--- Groq Response ---')
        print(explanation)
        print('--- End Response ---')
    except EnvironmentError as e:
        print('Groq unavailable:', e)
    except Exception as e:
        print('Groq request failed:', type(e).__name__, e)


if __name__ == '__main__':
    main()
