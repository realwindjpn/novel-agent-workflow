#!/usr/bin/env python3
"""六角色外审编排器 —— 统一调用不同模型，自动加载配置、重试、截断。

用法:
  python3 orchestrate_review.py --role editor --chapter 228 --prompt "..."
  python3 orchestrate_review.py --role reader --chapter 228 --prompt "..."
  python3 orchestrate_review.py --role military --chapter 228 --prompt "..."
  python3 orchestrate_review.py --role science --chapter 228 --prompt "..."
  python3 orchestrate_review.py --status  # 输出可用模型列表和状态

输出格式 (JSON):
  {"role": "...", "provider": "...", "model": "...", "ok": true, "content": "...", "tokens_used": ...}
  失败时 ok: false, content 为错误信息。
"""
from __future__ import annotations
import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

BASE = Path('/root/workspace/科武纪元')
CONFIG = Path('/root/.hermes/config.yaml')

ROLE_CONFIG = {
    'editor': {'provider': 'xiaomi', 'model': 'mimo-v2.5', 'key_env': 'XIAOMI_API_KEY', 'base_url': 'https://token-plan-cn.xiaomimimo.com/v1'},
    'reader': {'provider': 'xiaomi', 'model': 'mimo-v2.5', 'key_env': 'XIAOMI_API_KEY', 'base_url': 'https://token-plan-cn.xiaomimimo.com/v1'},
    'military': {'provider': 'alibaba', 'model': 'qwen3.6-plus', 'key_env': 'DASHSCOPE_API_KEY', 'base_url': 'https://coding.dashscope.aliyuncs.com/v1'},
    'science': {'provider': 'alibaba', 'model': 'qwen3.6-plus', 'key_env': 'DASHSCOPE_API_KEY', 'base_url': 'https://coding.dashscope.aliyuncs.com/v1'},
    'master': {'provider': 'zai', 'model': 'glm-5.1', 'key_env': 'ZAI_API_KEY', 'base_url': 'https://open.bigmodel.cn/api/coding/paas/v4'},
}

MAX_INPUT_CHARS = 4000
MAX_OUTPUT_CHARS = 3000
MAX_TOKENS = 1200
RETRY = 3


def load_env():
    env = Path(os.path.expanduser('~/.hermes/.env'))
    if env.exists():
        for line in env.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, v = line.split('=', 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def get_endpoint(role: str):
    cfg = ROLE_CONFIG[role]
    key = os.environ.get(cfg['key_env'])
    return cfg['base_url'], key, cfg['provider'], cfg['model']


def truncate(text: str) -> str:
    if len(text) <= MAX_INPUT_CHARS:
        return text
    return text[:MAX_INPUT_CHARS] + '\n...[已截断]'


def call(role: str, prompt: str):
    base, key, provider, model = get_endpoint(role)
    if not key:
        return {'role': role, 'provider': provider, 'model': model, 'ok': False, 'content': f'缺少环境变量 {ROLE_CONFIG[role]["key_env"]}'}
    payload = {"model": model, "messages": [{"role": "user", "content": prompt}], "max_tokens": MAX_TOKENS, "temperature": 0.1}
    for attempt in range(RETRY):
        try:
            r = subprocess.run(['curl', '-sS', '--max-time', '180', f'{base.rstrip("/")}/chat/completions',
                                '-H', f'Authorization: Bearer {key}',
                                '-H', 'Content-Type: application/json',
                                '-d', json.dumps(payload, ensure_ascii=False)],
                               capture_output=True, text=True, timeout=200)
            data = json.loads(r.stdout)
            err = data.get('error')
            msg = (data.get('choices') or [{}])[0].get('message', {})
            content = (msg.get('content') or msg.get('reasoning_content') or '').strip()
            if content:
                content = content[:MAX_OUTPUT_CHARS]
                return {'role': role, 'provider': provider, 'model': model, 'ok': True, 'content': content, 'tokens_used': (data.get('usage') or {}).get('total_tokens', 0)}
            if err:
                if attempt == RETRY - 1:
                    return {'role': role, 'provider': provider, 'model': model, 'ok': False, 'content': str(err)}
                time.sleep(2 * (attempt + 1))
                continue
            if attempt == RETRY - 1:
                return {'role': role, 'provider': provider, 'model': model, 'ok': False, 'content': f'无内容返回 ({r.stdout[:150]})'}
            time.sleep(1)
        except subprocess.TimeoutExpired:
            if attempt == RETRY - 1:
                return {'role': role, 'provider': provider, 'model': model, 'ok': False, 'content': '超时 (200s)'}
            time.sleep(3)
        except Exception as e:
            return {'role': role, 'provider': provider, 'model': model, 'ok': False, 'content': repr(e)}
    return {'role': role, 'provider': provider, 'model': model, 'ok': False, 'content': '未知错误'}


def status():
    load_env()
    print("# 角色模型状态")
    for role, cfg in ROLE_CONFIG.items():
        key = os.environ.get(cfg['key_env'])
        print(f"- {role}: {cfg['provider']}/{cfg['model']} {'[OK]' if key else '[MISSING KEY]'}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--role', choices=ROLE_CONFIG.keys())
    ap.add_argument('--chapter', type=int)
    ap.add_argument('--prompt')
    ap.add_argument('--status', action='store_true')
    args = ap.parse_args()
    if args.status:
        status()
        return
    if not args.role or not args.prompt:
        ap.print_help()
        sys.exit(1)
    load_env()
    res = call(args.role, truncate(args.prompt))
    print(json.dumps(res, ensure_ascii=False))

if __name__ == '__main__':
    main()