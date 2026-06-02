#!/usr/bin/env python3
"""Run V4 refine with Octopus Anthropic Messages endpoint by monkeypatching requests.post.

Keeps the project V4 workflow intact, but routes OpenAI-style chat/completions
calls to Octopus /v1/messages when KEWU_AUTHOR_ROUTE=octopus-opus46 or when the
script's internal review helpers call configured roles.
"""
import os, sys, json, subprocess
from pathlib import Path

PROJECT = Path('/root/workspace/科武纪元')
TARGET = PROJECT / '工具脚本' / 'run_refine_chapter_v4.py'

# Prefer Octopus for author route. If Octopus fails, caller may set
# KEWU_AUTHOR_ROUTE=wf-opus46 / wf-opus46-thinking / wf-opus47fast.
os.environ.setdefault('KEWU_AUTHOR_ROUTE', 'octopus-opus46')
os.environ.setdefault('OCTOPUS_BASE_URL', os.environ.get('OCTOPUS_BASE_URL', 'https://octopus.asia'))
os.environ.setdefault('CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC', '1')

# Execute patched copy in-process so monkeypatch applies.
source = TARGET.read_text(encoding='utf-8')

patch = r'''
# ---- Octopus Anthropic direct route patch ----
_orig_requests_post = requests.post
class _OctopusResp:
    def __init__(self, status_code, text):
        self.status_code=status_code; self.text=text; self.ok=200 <= status_code < 300
    def json(self):
        return json.loads(self.text)

def _octopus_messages_to_chat_json(data):
    content = ''
    for item in data.get('content', []) or []:
        if isinstance(item, dict) and item.get('type') == 'text':
            content += item.get('text', '')
    return {
        'id': data.get('id', 'octopus-msg'),
        'object': 'chat.completion',
        'model': data.get('model'),
        'choices': [{'index': 0, 'message': {'role': 'assistant', 'content': content}, 'finish_reason': data.get('stop_reason') or 'stop'}],
        'usage': data.get('usage') or {},
    }

def _patched_post(url, headers=None, json=None, timeout=None, **kwargs):
    try:
        route = os.environ.get('KEWU_AUTHOR_ROUTE','').strip().lower()
        if isinstance(url, str) and url.rstrip('/').endswith('/chat/completions'):
            # WF OpenAI-compatible fallback. Exact WF IDs use dots for Opus 4.6.
            wf_map = {
                'wf-opus46': 'claude-opus-4.6',
                'wf-opus4.6': 'claude-opus-4.6',
                'wf-opus46-thinking': 'claude-opus-4.6-thinking',
                'wf-opus4.6-thinking': 'claude-opus-4.6-thinking',
                'wf-opus47fast': 'claude-opus-4-7-high-fast',
                'opus47fast': 'claude-opus-4-7-high-fast',
            }
            if route in wf_map:
                base = os.environ.get('WF_BASE_URL','').rstrip('/')
                key = os.environ.get('WF_API_KEY','')
                if not base or not key:
                    return _OctopusResp(401, '{"error":"missing WF_BASE_URL/WF_API_KEY"}')
                payload = dict(json or {})
                payload['model'] = wf_map[route]
                payload.pop('temperature', None)
                h = {'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json', 'User-Agent': 'HermesKewuV4/1.0'}
                rr = _orig_requests_post(base + '/chat/completions', headers=h, json=payload, timeout=timeout or 420, **kwargs)
                return rr
            # Route explicit octopus calls to Anthropic Messages, preserving other normal providers.
            if route in {'octopus','octopus-opus46','claude-opus-4-6','opus46'}:
                base = os.environ.get('OCTOPUS_BASE_URL','https://octopus.asia').rstrip('/')
                key = os.environ.get('OCTOPUS_AUTH_TOKEN') or os.environ.get('ANTHROPIC_AUTH_TOKEN') or ''
                if not key:
                    return _OctopusResp(401, '{"error":"missing OCTOPUS_AUTH_TOKEN"}')
                model = 'claude-opus-4-6'
                messages = (json or {}).get('messages') or []
                max_tokens = (json or {}).get('max_tokens') or (json or {}).get('max_completion_tokens') or 10000
                payload = {'model': model, 'max_tokens': min(int(max_tokens), 12000), 'messages': messages}
                h = {
                    'Authorization': 'Bearer ' + key,
                    'x-api-key': key,
                    'anthropic-version': '2023-06-01',
                    'content-type': 'application/json',
                    'User-Agent': 'HermesKewuV4/1.0',
                }
                rr = _orig_requests_post(base + '/v1/messages', headers=h, json=payload, timeout=timeout or 420, **kwargs)
                if not rr.ok:
                    return _OctopusResp(rr.status_code, rr.text)
                data = rr.json()
                return _OctopusResp(rr.status_code, __import__('json').dumps(_octopus_messages_to_chat_json(data), ensure_ascii=False))
    except Exception as e:
        return _OctopusResp(500, '{"error":"octopus_wf_patch_exception: '+str(e).replace('"','')[:300]+'"}')
    return _orig_requests_post(url, headers=headers, json=json, timeout=timeout, **kwargs)
requests.post = _patched_post
# ---- end Octopus patch ----
'''

# Insert after the combined import line and before code uses requests.post.
marker = "import re, yaml, requests, subprocess, json, sys, os\n"
if marker in source:
    source = source.replace(marker, marker + patch + "\n", 1)
else:
    marker2 = "import requests\n"
    if marker2 in source:
        source = source.replace(marker2, marker2 + patch + "\n", 1)
    else:
        source = patch + "\n" + source

ns = {'__name__': '__main__', '__file__': str(TARGET)}
exec(compile(source, str(TARGET), 'exec'), ns)
