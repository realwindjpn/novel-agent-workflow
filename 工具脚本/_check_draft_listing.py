#!/usr/bin/env python3
"""只读核查番茄草稿箱列表，输出 250-265 区间命中的章节与字数。"""
import re
import shlex
import subprocess
import sys
import time

BOOK_ID = '7628216044850531352'
BOOK_NAME_ENC = '%E7%A7%91%E6%AD%A6%E7%BA%AA%E5%85%83%EF%BC%9A%E6%88%91%E5%9C%A8%E6%9C%AB%E4%B8%96%E4%BF%AE%E4%BB%99'
DRAFT_URL = f'https://fanqienovel.com/main/writer/chapter-manage/{BOOK_ID}&{BOOK_NAME_ENC}?type=2'


def ab(cmd: str, timeout: int = 90) -> str:
    p = subprocess.run(
        f'agent-browser --session-name fanqie {cmd}',
        shell=True, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        timeout=timeout,
    )
    return '\n'.join(
        ln for ln in p.stdout.splitlines()
        if not ln.startswith('⚠ --state ignored:')
    )


def main() -> int:
    ab(f'open {shlex.quote(DRAFT_URL)}', timeout=120)
    time.sleep(8)
    url = ab('get url', timeout=40).strip()
    if 'chapter-manage' not in url:
        print(f'NOT_ON_DRAFT_PAGE: {url}')
        return 2

    # 列表区异步渲染，轮询直到出现章节行或超时
    snap = ''
    for attempt in range(8):
        snap = ab('snapshot -i', timeout=120)
        if re.search(r'第2[0-9]{2}章', snap):
            break
        ab('scroll down', timeout=40)
        time.sleep(3)
    hits = []
    for m in re.finditer(r'第(2[0-9]{2})章\s*([^\n"\\]{0,24}?)\s+(\d{3,6})\b', snap):
        ch = int(m.group(1))
        if 250 <= ch <= 265:
            hits.append((ch, m.group(2).strip(), int(m.group(3))))
    seen = set()
    uniq = []
    for h in sorted(hits):
        if h[0] in seen:
            continue
        seen.add(h[0])
        uniq.append(h)
    if not uniq:
        print('NO_MATCH_250_265')
        print('--- snapshot excerpt ---')
        print(snap[:1200])
        return 1
    print(f'DRAFT_LISTING_URL: {url}')
    for ch, title, words in uniq:
        print(f'  第{ch}章 {title} | {words}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
