#!/usr/bin/env python3
"""Simple Groq wrapper—just call Groq, no fallbacks."""
import os
from typing import Optional
from pathlib import Path

try:
    from groq import Groq
    print("[Groq] Import successful")
except Exception as import_err:
    print(f"[Groq] Import failed: {type(import_err).__name__}: {import_err}")
    Groq = None


def _load_env_if_needed():
    """Load .env file if not already loaded."""
    p = Path('.env')
    if not p.exists():
        return
    for line in p.read_text().splitlines():
        if '=' in line and not line.strip().startswith('#'):
            k, v = line.split('=', 1)
            k = k.strip()
            if k and k not in os.environ:
                os.environ[k] = v.strip().strip('"').strip("'")


def _get_client():
    _load_env_if_needed()  # Ensure .env is loaded
    key = os.getenv("GROQ_API_KEY")
    print(f"[Groq] Key found: {bool(key)}, Groq installed: {Groq is not None}")
    if not key or Groq is None:
        return None
    return Groq(api_key=key)


def explain_silver_price(price: Optional[float], source: str) -> str:
    """Ask Groq to explain silver price. If Groq unavailable, return empty string."""
    client = _get_client()
    if not client:
        print("[ExplainSilver] Groq client unavailable")
        return ""

    if price is None:
        content = (
            f"I couldn't find a live silver price (source: {source}). "
            "What factors affect silver prices? Keep it brief."
        )
    else:
        content = f"Silver price today: ${price:.2f}/oz (source: {source}). Brief explanation?"

    system_prompt = "You are a concise financial assistant. Keep answers to two sentences max."

    try:
        completion = client.chat.completions.create(
            model=os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": content},
            ],
            temperature=float(os.getenv("GROQ_TEMP", 0.2)),
            max_tokens=int(os.getenv("GROQ_MAX_TOKENS", 200)),
        )
        try:
            resp = completion.choices[0].message.content
            return resp if resp and str(resp).strip() else ""
        except Exception as e:
            print(f"[ExplainSilver] Failed to extract response: {e}")
            return ""
    except Exception as e:
        print(f"[ExplainSilver] Groq call failed: {type(e).__name__}: {e}")
        return ""


def generate(user_text: str, system_prompt: str = "You are a helpful assistant.") -> str:
    """Simple Groq call. Returns empty string if unavailable."""
    client = _get_client()
    if not client:
        print("[Generate] Groq client unavailable")
        return ""

    try:
        completion = client.chat.completions.create(
            model=os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_text},
            ],
            temperature=float(os.getenv("GROQ_TEMP", 0.2)),
            max_tokens=int(os.getenv("GROQ_MAX_TOKENS", 200)),
        )
        try:
            resp = completion.choices[0].message.content
            print(f"[Generate] Groq returned: {len(resp) if resp else 0} chars")
            return resp if resp and str(resp).strip() else ""
        except Exception as e:
            print(f"[Generate] Failed to extract response: {e}")
            return ""
    except Exception as e:
        print(f"[Generate] Groq call failed: {type(e).__name__}: {e}")
        return ""
