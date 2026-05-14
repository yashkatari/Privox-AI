#!/usr/bin/env python3
"""Test Gemini API connectivity"""
import os
from pathlib import Path

# Load .env
def load_env_file(path=".env"):
    """Lightweight .env loader."""
    try:
        if not Path(path).exists():
            print(f"[ERROR] {path} not found!")
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
        print(f"[ERROR] Failed to load {path}: {e}")

load_env_file()

# Test imports
print("[TEST] Testing Gemini API...")
print(f"✓ GEMINI_API_KEY: {os.getenv('GEMINI_API_KEY', 'NOT SET')[:20]}...")
print(f"✓ GEMINI_API_URL: {os.getenv('GEMINI_API_URL', 'NOT SET')}")

from system.gemini_online import GeminiClient, should_use_gemini

# Test 1: Check should_use_gemini routing
print("\n[TEST 1] Testing should_use_gemini routing...")
test_queries = [
    "today silver price",
    "what is the weather",
    "explain quantum physics",
    "what time is it",
    "hello how are you"
]

for query in test_queries:
    use_gemini, reason = should_use_gemini(query)
    status = "🟢 GEMINI" if use_gemini else "🔵 QWEN"
    print(f"  {status} | '{query}' → {reason}")

# Test 2: Check Gemini API connectivity
print("\n[TEST 2] Testing Gemini API connectivity...")
gemini = GeminiClient.from_env()
print(f"  Configured: {gemini.is_configured()}")

if gemini.is_configured():
    print("  Attempting API call...")
    response, error = gemini.generate_response("What is the current price of silver?")
    if response:
        print(f"  ✅ SUCCESS! Response: {response[:100]}...")
    else:
        print(f"  ❌ FAILED! Error: {error}")
else:
    print("  ❌ Gemini not configured!")

print("\n[TEST] Done!")
