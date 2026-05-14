#!/usr/bin/env python3
import os
import requests
import json
from pathlib import Path

# Load .env
p = Path('.env')
if p.exists():
    for line in p.read_text().splitlines():
        if '=' in line and not line.strip().startswith('#'):
            k,v = line.split('=',1)
            if k and k not in os.environ:
                os.environ[k.strip()] = v.strip()

openai_key = os.getenv('OPENAI_API_KEY')
print('[OPENAI CHECK] OPENAI_API_KEY set:', bool(openai_key))
if not openai_key:
    print('  → OPENAI_API_KEY not set in .env or environment. Skipping API test.')
else:
    url = 'https://api.openai.com/v1/chat/completions'
    headers = {'Authorization': f'Bearer {openai_key}','Content-Type':'application/json'}
    payload = {
        'model':'gpt-3.5-turbo',
        'messages':[{'role':'user','content':'Say hello'}],
        'max_tokens':5
    }
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=10)
        print('  Status:', r.status_code)
        try:
            print('  Response snippet:', json.dumps(r.json())[:300])
        except Exception:
            print('  Non-JSON response, length:', len(r.text))
    except Exception as e:
        print('  Request failed:', type(e).__name__, e)
