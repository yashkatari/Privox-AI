import os
import time
from typing import Optional, Tuple

import requests


class OpenRouterClient:
    def __init__(self, api_key: Optional[str], base_url: Optional[str] = None, timeout: int = 20):
        self.api_key = api_key
        # Default OpenRouter chat completions endpoint
        self.base_url = base_url or os.getenv("OPENROUTER_URL", "https://api.openrouter.ai/v1/chat/completions")
        self.timeout = timeout

    @classmethod
    def from_env(cls) -> "OpenRouterClient":
        api_key = os.getenv("OPENROUTER_API_KEY")
        base = os.getenv("OPENROUTER_URL")
        timeout = int(os.getenv("OPENROUTER_TIMEOUT", "20"))
        return cls(api_key=api_key, base_url=base, timeout=timeout)

    def is_configured(self) -> bool:
        return bool(self.api_key and self.base_url)

    def generate_response(self, text: str, system_prompt: str = "") -> Tuple[Optional[str], Optional[str]]:
        if not self.is_configured():
            return None, "OpenRouter API not configured. Set OPENROUTER_API_KEY."

        full_prompt = text if not system_prompt else f"{system_prompt}\n\nUser: {text}"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

        payload = {
            "model": os.getenv("OPENROUTER_MODEL", "gpt-4o-mini"),
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
            # Keep response short for speed
            "max_tokens": int(os.getenv("OPENROUTER_MAX_TOKENS", "512"))
        }

        start = time.time()
        try:
            print(f"[OpenRouter] Connecting to {self.base_url}...")
            r = requests.post(self.base_url, headers=headers, json=payload, timeout=self.timeout)
        except requests.exceptions.ConnectionError as e:
            dur = int((time.time() - start) * 1000)
            error = f"Connection error (DNS/Network): {str(e)[:100]}"
            print(f"[OpenRouter] ❌ {error} ({dur}ms)")
            return None, error
        except requests.exceptions.Timeout as e:
            dur = int((time.time() - start) * 1000)
            error = f"Timeout after {dur}ms"
            print(f"[OpenRouter] ❌ {error}")
            return None, error
        except Exception as e:
            dur = int((time.time() - start) * 1000)
            error = f"Request failed: {str(e)[:100]}"
            print(f"[OpenRouter] ❌ {error}")
            return None, error

        dur = int((time.time() - start) * 1000)
        if r.status_code != 200:
            error_msg = f"HTTP {r.status_code} after {dur}ms"
            print(f"[OpenRouter] ❌ {error_msg}")
            return None, error_msg

        try:
            data = r.json()
        except Exception:
            return None, "OpenRouter returned non-JSON response"

        # Try common response shapes
        try:
            # Chat completions style
            if isinstance(data, dict):
                # OpenRouter may return choices -> message -> content
                choices = data.get("choices") or []
                if choices:
                    msg = choices[0].get("message", {})
                    text_out = msg.get("content") or msg.get("content", "")
                    if isinstance(text_out, dict):
                        text_out = text_out.get("text", "")
                    print(f"[OpenRouter] ✅ Got response ({dur}ms)")
                    return text_out.strip(), None

                # Fallback to `output` or `text`
                out = data.get("output") or data.get("text")
                if out:
                    if isinstance(out, list):
                        out = "\n".join(out)
                    print(f"[OpenRouter] ✅ Got response ({dur}ms)")
                    return str(out).strip(), None

            return None, "OpenRouter returned no usable text"
        except Exception as exc:
            return None, f"OpenRouter response parsing failed: {exc}"
