import os
import time
from typing import Optional, Tuple

import requests


FRESHNESS_KEYWORDS = {
    "today",
    "latest",
    "recent",
    "current",
    "now",
    "breaking",
    "news",
    "update",
    "score",
    "price",
    "stock",
    "rate",
    "headline",
    "trending",
    "silver",
    "gold",
    "bitcoin",
    "crypto",
    "weather",
    "forecast",
    "temperature",
    "live",
    "real-time",
    "realtime",
}

COMPLEXITY_KEYWORDS = {
    "explain",
    "compare",
    "summarize",
    "summary",
    "analysis",
    "analyze",
    "strategy",
    "plan",
    "roadmap",
    "pros and cons",
    "advantages",
    "disadvantages",
    "step by step",
    "deep dive",
    "how to",
    "research",
}


def should_use_gemini(text: str) -> Tuple[bool, str]:
    """
    Heuristic router for complex or time-sensitive queries.
    Returns (should_use: bool, reason: str)
    """
    if not text:
        return False, "Empty query"

    text_lower = text.lower()

    # Check for freshness keywords (real-time data needed)
    for keyword in FRESHNESS_KEYWORDS:
        if keyword in text_lower:
            return True, f"Freshness keyword detected: '{keyword}'"

    # Check for complexity keywords (needs better reasoning)
    for keyword in COMPLEXITY_KEYWORDS:
        if keyword in text_lower:
            return True, f"Complexity keyword detected: '{keyword}'"

    # Longer prompts often benefit from a stronger online model
    word_count = len(text_lower.split())
    if word_count >= 18:
        return True, f"Long query ({word_count} words) - using Gemini for better reasoning"

    return False, "Simple query - using local LLM"


class GeminiClient:
    def __init__(self, api_key: Optional[str], api_url: Optional[str], timeout: int = 20):
        self.api_key = api_key
        self.api_url = api_url
        self.timeout = timeout

    @classmethod
    def from_env(cls) -> "GeminiClient":
        api_key = os.getenv("GEMINI_API_KEY")
        api_url = os.getenv("GEMINI_API_URL")
        timeout = int(os.getenv("GEMINI_TIMEOUT", "20"))
        return cls(api_key=api_key, api_url=api_url, timeout=timeout)

    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_url)

    def generate_response(self, text: str, system_prompt: str = "") -> Tuple[Optional[str], Optional[str]]:
        if not self.is_configured():
            return None, "Gemini API is not configured. Set GEMINI_API_KEY and GEMINI_API_URL."

        if not text:
            return None, "Empty prompt."

        full_prompt = text if not system_prompt else f"{system_prompt}\n\nUser: {text}"
        print(f"[Gemini Debug] API Key: {self.api_key[:20]}... (masked)")
        print(f"[Gemini Debug] API URL: {self.api_url}")
        print(f"[Gemini Debug] Full prompt: {full_prompt[:100]}...")

        # Payload for Gemini 2.0 Flash
        payload = {
            "contents": [
                {
                    "parts": [{"text": full_prompt}]
                }
            ]
        }

        # Pass API key as header (Google API standard)
        headers = {
            "Content-Type": "application/json",
            "X-goog-api-key": self.api_key
        }
        
        print(f"[Gemini Debug] Payload keys: {payload.keys()}")
        print(f"[Gemini Debug] Making POST request to: {self.api_url}")
        print(f"[Gemini Debug] Headers: Content-Type=application/json, X-goog-api-key=***")

        start_time = time.time()
        try:
            response = requests.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=self.timeout,
            )
        except Exception as exc:
            print(f"[Gemini Debug] Request failed with exception: {exc}")
            return None, f"Gemini request failed: {exc}"

        duration_ms = int((time.time() - start_time) * 1000)
        print(f"[Gemini Debug] Response status: {response.status_code}, Duration: {duration_ms}ms")
        
        if response.status_code != 200:
            print(f"[Gemini Debug] Error response body: {response.text[:500]}")
            return None, f"Gemini error {response.status_code} after {duration_ms}ms."

        try:
            data = response.json()
            print(f"[Gemini Debug] Response JSON keys: {data.keys()}")
        except Exception:
            print(f"[Gemini Debug] Failed to parse JSON")
            return None, "Gemini returned non-JSON response."

        try:
            candidates = data.get("candidates", [])
            print(f"[Gemini Debug] Candidates count: {len(candidates)}")
            if not candidates:
                print(f"[Gemini Debug] No candidates in response")
                return None, "Gemini returned no candidates."
            parts = candidates[0].get("content", {}).get("parts", [])
            print(f"[Gemini Debug] Parts count: {len(parts)}")
            if not parts:
                return None, "Gemini returned empty content."
            text_out = parts[0].get("text", "").strip()
            print(f"[Gemini Debug] Text output length: {len(text_out)}")
            if not text_out:
                return None, "Gemini returned empty text."
            return text_out, None
        except Exception as exc:
            print(f"[Gemini Debug] Response parsing failed: {exc}")
            return None, f"Gemini response parsing failed: {exc}"
