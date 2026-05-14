#!/usr/bin/env python3
import os
import requests
import json
from pathlib import Path

# Load .env if present
p = Path('.env')
if p.exists():
    for line in p.read_text().splitlines():
        if '=' in line and not line.strip().startswith('#'):
            k,v = line.split('=',1)
            if k and k not in os.environ:
                os.environ[k.strip()] = v.strip()

HF_API_KEY = os.getenv('HF_API_KEY')
if not HF_API_KEY:
    print('[HF TEST] HF_API_KEY not set in environment or .env. Set HF_API_KEY and re-run.')
    raise SystemExit(1)

headers = {"Authorization": f"Bearer {HF_API_KEY}", "Content-Type": "application/json"}
# Use the new Hugging Face router endpoint (api-inference is deprecated)
payload = {"inputs": "Explain AI in one line"}

models_to_try = [
    os.getenv('HF_MODEL', 'google/flan-t5-base'),
    'google/flan-t5-small',
    'gpt2'
]

print('[HF TEST] Calling HuggingFace (router) for multiple models...')
for model in models_to_try:
    url = os.getenv('HF_URL', f"https://router.huggingface.co/models/{model}")
    print(f"[HF TEST] Trying model: {model} -> {url}")
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=20)
        print('[HF TEST] Status:', r.status_code)
        text = r.text
        # Try to print JSON if possible
        try:
            j = r.json()
            print('[HF TEST] JSON response:', json.dumps(j, indent=2)[:1000])
        except Exception:
            print('[HF TEST] Text response:', text[:1000])
    except Exception as e:
        print('[HF TEST] Request failed:', type(e).__name__, e)
    print('-'*40)
