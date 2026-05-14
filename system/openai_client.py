import os
import time
from typing import Optional, Tuple

import requests


class OpenAIClient:
    def __init__(self, api_key: Optional[str], timeout: int = 20):
        self.api_key = api_key
        self.timeout = timeout

    @classmethod
    def from_env(cls) -> "OpenAIClient":
        api_key = os.getenv("OPENAI_API_KEY")
        timeout = int(os.getenv("OPENAI_TIMEOUT", "20"))
        return cls(api_key=api_key, timeout=timeout)

    def is_configured(self) -> bool:
        return bool(self.api_key)

    def generate_response(self, text: str, system_prompt: str = "") -> Tuple[Optional[str], Optional[str]]:
        if not self.is_configured():
            return None, "OpenAI API key not configured (OPENAI_API_KEY)."

        url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": text})

        payload = {
            "model": os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
            "messages": messages,
            "max_tokens": int(os.getenv("OPENAI_MAX_TOKENS", "512")),
            "temperature": float(os.getenv("OPENAI_TEMPERATURE", "0.2")),
        }

        start = time.time()
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=self.timeout)
        except Exception as e:
            return None, f"OpenAI request failed: {e}"

        dur = int((time.time() - start) * 1000)
        if r.status_code != 200:
            return None, f"OpenAI error {r.status_code} after {dur}ms: {r.text[:300]}"

        try:
            data = r.json()
        except Exception:
            return None, "OpenAI returned non-JSON response"

        try:
            # Standard OpenAI response parsing
            choices = data.get("choices") or []
            if choices:
                msg = choices[0].get("message", {})
                content = msg.get("content") or msg.get("text") or ""
                return content.strip(), None

            # Fallback
            text_out = data.get("text") or data.get("output")
            if text_out:
                return str(text_out).strip(), None

            return None, "OpenAI returned no usable text"
        except Exception as exc:
            return None, f"OpenAI response parsing failed: {exc}"
