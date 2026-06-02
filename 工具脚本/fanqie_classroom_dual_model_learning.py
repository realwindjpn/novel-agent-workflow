#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""番茄作家课堂双模型学习队列。

不再写死 3 篇：
1. 从番茄作家课堂 API 自动发现全部栏目/分页课程。
2. 合并用户截图待学清单。
3. 已学跳过，未学按优先级分批学习。
4. 每篇：抓正文 -> Qwen3.6 编辑规则 -> TKX gpt-5.5 作家OS补丁 -> 写索引/状态。

默认每轮 3 篇，避免长任务空转/烧算力。可用 FANQIE_CLASSROOM_BATCH_LIMIT 调整。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import time
from pathlib import Path
from urllib.parse import urlparse

try:
    import requests
except Exception:  # pragma: no cover
    requests = None

ROOT = Path('/root/workspace/科武纪元')
OUT = ROOT / '写作技巧' / '番茄作家课堂'
STATE = OUT / 'state.json'
LOG = OUT / 'run.log'
REPORT = OUT / '阶段报告.md'
INDEX = OUT / '番茄作家课堂学习索引.md'
DISCOVERED = OUT / 'discovered_courses.json'
QUEUE_MD = OUT / '番茄作家课堂自动发现队列.md'
AUTHOR_PATCH = Path('/root/workspace/写作角色OS/fanqie_writer_classroom_patch_20260516.md')
KEWU_AUTHOR_PATCH = ROOT / '参考资料' / '作家风格OS' / 'fanqie_classroom_author_patch.md'
ENV = Path('/root/.hermes/.env')
OUT.mkdir(parents=True, exist_ok=True)
KEWU_AUTHOR_PATCH.parent.mkdir(parents=True, exist_ok=True)

TYPE_NAMES = {
    1: '新手专区',
    2: '大神专访',
    3: '写作技巧',
    4: '品类指南',
    5: '平台宝典',
}
TYPE_PRIORITY = {3: 100, 4: 80, 1: 55, 5: 35, 2: 20}
HIGH_VALUE_WORDS = [
    '节奏', '冲突', '人物', '人设', '开篇', '钩子', '爽点', '大纲', '细纲', '代入感',
    '题材', '选题', '改文', '精修', '拉新', '爆款', '短故事', '科幻', '悬疑', '新媒体',
    '改编', '剧情', '稳定', '副本', '世界观', '标签', '签约', '审核', '数据',
]
LOW_VALUE_WORDS = ['账号注册', '登录全指南', '稿费&福利', '营业执照']


def load_env() -> None:
    if not ENV.exists():
        return
    for line in ENV.read_text(encoding='utf-8', errors='ignore').splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        k, v = line.split('=', 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def log(msg: str) -> None:
    ts = time.strftime('%F %T')
    line = f'[{ts}] {msg}\n'
    with LOG.open('a', encoding='utf-8') as f:
        f.write(line)
    print(line, end='', flush=True)


def load_state() -> dict:
    if STATE.exists():
        try:
            st = json.loads(STATE.read_text(encoding='utf-8'))
        except Exception:
            st = {}
    else:
        st = {}
    st.setdefault('status', 'idle')
    st.setdefault('completed_ids', [])
    st.setdefault('failed_ids', [])
    st.setdefault('blocked_ids', [])
    return st


def save_state(**kw) -> None:
    st = load_state()
    st.update(kw)
    st['updated_at'] = time.strftime('%F %T')
    for key in ['completed_ids', 'failed_ids', 'blocked_ids']:
        if key in st:
            st[key] = list(dict.fromkeys(st[key]))[-1000:]
    STATE.write_text(json.dumps(st, ensure_ascii=False, indent=2), encoding='utf-8')


def ensure_files() -> None:
    if not INDEX.exists():
        INDEX.write_text('# 番茄作家课堂学习索引\n\n', encoding='utf-8')
    if not REPORT.exists():
        REPORT.write_text('# 番茄作家课堂阶段报告\n\n', encoding='utf-8')
    if not AUTHOR_PATCH.exists():
        AUTHOR_PATCH.write_text('# 番茄作家课堂 → 作家角色OS补丁\n\n', encoding='utf-8')
    if not KEWU_AUTHOR_PATCH.exists():
        KEWU_AUTHOR_PATCH.write_text('# 科武纪元作家风格OS｜番茄课堂补丁\n\n', encoding='utf-8')


def slug_from_url(url: str) -> str:
    m = re.search(r'/article/(\d+)', url or '')
    return m.group(1) if m else re.sub(r'\W+', '_', url or '')[:32]


def safe_slug(s: str, limit: int = 60) -> str:
    s = re.sub(r'[\\/:*?"<>|\s]+', '_', s).strip('_')
    return s[:limit] or 'untitled'


def norm_course(item: dict, source: str = 'api') -> dict:
    url = item.get('link') or item.get('url') or ''
    cid = slug_from_url(url) or safe_slug(item.get('title', ''))
    typ = int(item.get('type') or item.get('tab') or 0)
    title = str(item.get('title', '')).strip()
    detail = item.get('detail') or []
    if isinstance(detail, str):
        detail = [detail]
    return {
        'id': cid,
        'title': title,
        'url': url,
        'time': item.get('time') or '',
        'type': typ,
        'type_name': TYPE_NAMES.get(typ, item.get('type_name', '未知')),
        'detail': detail,
        'source': source,
        'priority': score_course(title, typ, detail),
    }


def score_course(title: str, typ: int, detail: list[str] | None = None) -> int:
    blob = title + ' ' + ' '.join(detail or [])
    score = TYPE_PRIORITY.get(typ, 10)
    score += sum(8 for w in HIGH_VALUE_WORDS if w in blob)
    score -= sum(20 for w in LOW_VALUE_WORDS if w in blob)
    # 新课优先：2026/2025 明显靠前。
    if '2026' in blob:
        score += 6
    return score


def discover_api(max_pages: int = 8) -> list[dict]:
    if requests is None:
        return []
    found: list[dict] = []
    sess = requests.Session()
    sess.headers.update({'User-Agent': 'Mozilla/5.0 Hermes Fanqie Classroom Learner'})
    for typ in [3, 4, 1, 5, 2]:
        for page in range(max_pages):
            url = f'https://fanqienovel.com/api/node/tutorial/list?type={typ}&page_index={page}&page_count=15'
            try:
                r = sess.get(url, timeout=20)
                data = r.json()
            except Exception as e:
                log(f'DISCOVER_API_FAIL type={typ} page={page}: {type(e).__name__}: {e}')
                break
            if data.get('code') != 0:
                log(f'DISCOVER_API_CODE type={typ} page={page}: {data.get("code")} {data.get("message", "")}')
                break
            items = data.get('data', {}).get('tutorial_list') or []
            total = int(data.get('data', {}).get('total_count') or 0)
            for it in items:
                it['type'] = typ
                found.append(norm_course(it, 'api'))
            if not items or (page + 1) * 15 >= total:
                break
    return found


def discover_from_screenshot_lists() -> list[dict]:
    courses: list[dict] = []
    for p in OUT.glob('*待学清单_*.md'):
        text = p.read_text(encoding='utf-8', errors='ignore')
        for m in re.finditer(r'《([^》]+)》', text):
            title = m.group(1).strip()
            # 若截图清单无链接，后续由 API 同名匹配补齐。
            typ = 3 if '写作技巧' in p.name else 4 if '品类指南' in p.name else 5
            courses.append(norm_course({'title': title, 'url': '', 'type': typ, 'detail': ['来自用户截图待学清单']}, f'screenshot:{p.name}'))
    return courses


def merge_courses(api_courses: list[dict], list_courses: list[dict]) -> list[dict]:
    by_key: dict[str, dict] = {}
    api_by_title = {c['title'].replace('！', '').replace(' ', ''): c for c in api_courses}
    for c in api_courses + list_courses:
        if not c.get('url'):
            c = {**c, **api_by_title.get(c['title'].replace('！', '').replace(' ', ''), c)}
        key = c.get('url') or c.get('title')
        if not key:
            continue
        old = by_key.get(key)
        if not old or c.get('priority', 0) > old.get('priority', 0):
            by_key[key] = c
    courses = list(by_key.values())
    courses.sort(key=lambda x: (x.get('priority', 0), x.get('time', '')), reverse=True)
    return courses


def learned_ids_from_files() -> set[str]:
    learned = set(load_state().get('completed_ids', []))
    for p in OUT.glob('*_writer_tkx_gpt55.md'):
        m = re.search(r'(\d{16,})', p.name)
        if m:
            learned.add(m.group(1))
    # 旧版文件名是 slug_文章ID_writer_tkx_gpt55.md；新版是 title_文章ID_writer_tkx_gpt55.md。
    for p in OUT.glob('*writer_tkx_gpt55.md'):
        m = re.search(r'(\d{16,})', p.name)
        if m:
            learned.add(m.group(1))
    idx = INDEX.read_text(encoding='utf-8', errors='ignore') if INDEX.exists() else ''
    for m in re.finditer(r'/article/(\d+)', idx):
        learned.add(m.group(1))
    return learned


def write_discovery_files(courses: list[dict]) -> None:
    DISCOVERED.write_text(json.dumps(courses, ensure_ascii=False, indent=2), encoding='utf-8')
    learned = learned_ids_from_files()
    lines = ['# 番茄作家课堂自动发现队列', '', f'- 更新时间：{time.strftime("%F %T")}', f'- 发现课程：{len(courses)}', f'- 已学：{len([c for c in courses if c["id"] in learned])}', '']
    for c in courses:
        status = '已学' if c['id'] in learned else '待学'
        lines.append(f'- [{status}] [{c["type_name"]}] {c["time"]}｜{c["title"]}｜priority={c["priority"]}｜{c["url"]}')
    QUEUE_MD.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def select_next(courses: list[dict], limit: int) -> list[dict]:
    learned = learned_ids_from_files()
    st = load_state()
    blocked = set(st.get('blocked_ids', []))
    failed = set(st.get('failed_ids', []))
    skip = learned | blocked | failed
    todo = [c for c in courses if c.get('id') not in skip and c.get('url')]
    return todo[:limit]


def fetch_article(url: str) -> str:
    """番茄 writer zone 文章：普通 crawler 可能只抓壳，优先浏览器 article.innerText。"""
    # requests 先试 SSR，够长则用；失败再浏览器。
    if requests is not None:
        try:
            r = requests.get(url, timeout=25, headers={'User-Agent': 'Mozilla/5.0'})
            text = r.text or ''
            # SSR 页面常含 article 正文；粗清理。
            body = re.sub(r'<script[\s\S]*?</script>|<style[\s\S]*?</style>', '\n', text, flags=re.I)
            body = re.sub(r'<[^>]+>', '\n', body)
            body = re.sub(r'\n{3,}', '\n\n', body)
            body = re.sub(r'[ \t]{2,}', ' ', body).strip()
            if len(body) > 1800 and ('作家课堂' in body or '适用对象' in body):
                return body[:80000]
        except Exception as e:
            log(f'requests_fetch_failed {type(e).__name__}: {e}')
    try:
        subprocess.run(['agent-browser', '--session-name', 'fanqie_classroom', 'open', url], check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, timeout=90)
        time.sleep(2)
        js = "(() => document.querySelector('article')?.innerText || document.querySelector('.article-content')?.innerText || document.body.innerText)()"
        out = subprocess.check_output(['agent-browser', '--session-name', 'fanqie_classroom', 'eval', js], text=True, timeout=90)
        text = out.strip()
        if text.startswith('"'):
            try:
                text = json.loads(text)
            except Exception:
                pass
        if len(text) > 500:
            return text
    except Exception as e:
        log(f'browser_fetch_failed {type(e).__name__}: {e}')
    raise RuntimeError('FETCH_ARTICLE_EMPTY')


def openai_chat(base_url: str, api_key: str, model: str, messages: list[dict], timeout: int = 300, max_tokens: int | None = None) -> tuple[str, str]:
    if requests is None:
        raise RuntimeError('requests missing')
    url = base_url.rstrip('/') + '/chat/completions'
    payload = {'model': model, 'messages': messages, 'temperature': 0.25}
    if max_tokens:
        payload['max_tokens'] = max_tokens
    r = requests.post(url, headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'}, json=payload, timeout=timeout)
    r.raise_for_status()
    data = r.json()
    returned = data.get('model') or model
    text = data['choices'][0]['message']['content']
    return text, returned


def qwen_editor(course: dict, article_text: str) -> tuple[str, str]:
    base = os.environ.get('DASHSCOPE_BASE_URL', 'https://coding.dashscope.aliyuncs.com/v1')
    key = os.environ.get('DASHSCOPE_API_KEY')
    model = os.environ.get('QWEN_CLASSROOM_MODEL', os.environ.get('QWEN_MODEL', 'qwen3.6-plus'))
    if not key:
        raise RuntimeError('DASHSCOPE_API_KEY missing')
    prompt = f"""你是《科武纪元》编辑学习官。请学习番茄作家课堂文章《{course['title']}》。
栏目：{course.get('type_name')}；日期：{course.get('time')}；链接：{course.get('url')}
目标：提炼可用于长篇科幻小说《科武纪元》、短故事、热点稿的编辑规则。不要鸡汤。
输出Markdown，必须包含：
1 课程核心判断（≤6条）
2 可执行编辑规则：开篇/节奏/冲突/人物/题材/改编/平台规则，按文章实际内容取舍
3 科武适配：可用点、不可硬套点
4 编辑检查表（10条以内）
5 对作家角色的输入要求：动作链、物理反馈、代价、钩子、读者预期
原文：
{article_text[:26000]}
"""
    return openai_chat(base, key, model, [{'role': 'user', 'content': prompt}], timeout=360)


def writer_model(course: dict, editor_rules: str) -> tuple[str, str]:
    provider = os.environ.get('FANQIE_CLASSROOM_WRITER_PROVIDER', 'minimax').lower()
    if provider == 'tkx':
        base = os.environ.get('TOKENX_BASE_URL', 'https://tokenx24.com/v1')
        key = os.environ.get('TOKENX_API_KEY')
        model = os.environ.get('TOKENX_MODEL', 'gpt-5.5')
        max_tokens = int(os.environ.get('TOKENX_AUTHOR_MAX_TOKENS', '20000'))
        if not key:
            raise RuntimeError('TOKENX_API_KEY missing')
    else:
        base = os.environ.get('MINIMAX_CN_BASE_URL', 'https://api.minimaxi.com/v1')
        key = os.environ.get('MINIMAX_CN_API_KEY')
        model = os.environ.get('MINIMAX_CLASSROOM_MODEL', os.environ.get('MINIMAX_MODEL', 'MiniMax-M2.7'))
        max_tokens = int(os.environ.get('MINIMAX_CLASSROOM_MAX_TOKENS', '9000'))
        if not key:
            raise RuntimeError('MINIMAX_CN_API_KEY missing')
    prompt = f"""你是《科武纪元》作家角色训练官。把编辑学习稿转成作家OS可执行补丁。
课程：{course['title']}
要求：
- 不写理论长文。
- 提炼成作者写作时可直接执行的动作、反馈、代价、失败模式、人物口吻、段落节奏、章末钩子。
- 给出“写作前任务卡字段更新”。
- 给出“章节自检清单”。
- 标注短故事/狼人篇可借点；标注科武长篇可借点；平台规则类要转成发布/包装/风险门禁。
编辑学习稿：
{editor_rules[:24000]}
"""
    try:
        return openai_chat(base, key, model, [{'role': 'user', 'content': prompt}], timeout=360, max_tokens=max_tokens)
    except Exception as e:
        log(f'WRITER_RETRY_COMPACT provider={provider} {course["title"]}: {type(e).__name__}: {e}')
        compact = prompt[:14000] + '\n\n只输出压缩版：10条写法规则 + 10条自检清单 + 3条科武落地。'
        return openai_chat(base, key, model, [{'role': 'user', 'content': compact}], timeout=300, max_tokens=min(max_tokens, 9000))


def append(path: Path, text: str) -> None:
    old = path.read_text(encoding='utf-8') if path.exists() else ''
    path.write_text(old.rstrip() + '\n\n' + text.strip() + '\n', encoding='utf-8')


def learn_one(course: dict) -> None:
    cid = course['id']
    title = course['title']
    stem = f'{safe_slug(title, 32)}_{cid}'
    save_state(status='running', current=cid, current_title=title)
    log(f'FETCH {title}')
    raw = fetch_article(course['url'])
    raw_path = OUT / f'{stem}_raw.md'
    raw_path.write_text(f"# {title}\n\n来源：{course['url']}\n栏目：{course.get('type_name')}\n日期：{course.get('time')}\n\n{raw}\n", encoding='utf-8')
    log(f'QWEN_EDITOR {title} chars={len(raw)}')
    editor, qwen_model = qwen_editor(course, raw)
    editor_path = OUT / f'{stem}_editor_qwen36.md'
    editor_path.write_text(f"# {title}｜编辑学习稿\n\nmodel: {qwen_model}\nsource: {course['url']}\n\n{editor}\n", encoding='utf-8')
    log(f'WRITER_MODEL {title} editor_chars={len(editor)}')
    writer, writer_model_name = writer_model(course, editor)
    writer_provider = os.environ.get('FANQIE_CLASSROOM_WRITER_PROVIDER', 'minimax').lower()
    writer_path = OUT / f'{stem}_writer_{writer_provider}.md'
    writer_path.write_text(f"# {title}｜作家OS转译稿\n\nmodel: {writer_model_name}\nprovider: {writer_provider}\nsource: {course['url']}\n\n{writer}\n", encoding='utf-8')

    summary = f"""
## {time.strftime('%F %T')}｜{title}

- 状态：PASS
- 栏目：{course.get('type_name')}
- 链接：{course.get('url')}
- Qwen编辑模型：{qwen_model}
- 作家转译模型：{writer_model_name}（{writer_provider}）
- 原文：`{raw_path}`
- 编辑稿：`{editor_path}`
- 作家稿：`{writer_path}`
"""
    append(REPORT, summary)
    append(INDEX, f"- [{title}]({course['url']})：栏目 `{course.get('type_name')}`；编辑稿 `{editor_path.name}`；作家稿 `{writer_path.name}`。")
    append(AUTHOR_PATCH, f"## {title}\n\n来源：`{writer_path}`\n\n{writer[:7000]}")
    append(KEWU_AUTHOR_PATCH, f"## {title}\n\n来源：`{writer_path}`\n\n{writer[:7000]}")
    st = load_state()
    completed = st.setdefault('completed_ids', [])
    if cid not in completed:
        completed.append(cid)
    save_state(status='running', current='', completed=len(completed), completed_ids=completed, last_completed=cid, last_title=title, last_report=str(writer_path))
    log(f'COMPLETED {title}')


def run(limit: int, discover_only: bool = False) -> int:
    load_env()
    ensure_files()
    log('START fanqie classroom dynamic learning')
    api = discover_api()
    screenshots = discover_from_screenshot_lists()
    courses = merge_courses(api, screenshots)
    write_discovery_files(courses)
    if discover_only:
        save_state(status='discovered', discovered=len(courses), current='')
        print(json.dumps({'discovered': len(courses), 'queue_md': str(QUEUE_MD), 'next': select_next(courses, limit)}, ensure_ascii=False, indent=2))
        return 0
    todo = select_next(courses, limit)
    if not todo:
        save_state(status='completed_no_pending', discovered=len(courses), current='')
        log('DONE no pending classroom courses')
        return 0
    save_state(status='running', total_discovered=len(courses), batch_limit=limit, batch_total=len(todo), current='')
    failed = load_state().setdefault('failed_ids', [])
    blocked = load_state().setdefault('blocked_ids', [])
    for idx, course in enumerate(todo, 1):
        log(f'BATCH {idx}/{len(todo)} {course["title"]}')
        try:
            learn_one(course)
        except Exception as e:
            err = f'{type(e).__name__}: {e}'
            log(f'ERROR {course["id"]} {err}')
            # 429/限流不是课程内容失败。先 blocked，勿烧掉课程 ID。
            if re.search(r'429 Client Error|Too Many Requests|rate limit|Rate limit', err, flags=re.I):
                if course['id'] not in blocked:
                    blocked.append(course['id'])
                save_state(status='rate_limited', blocked_ids=blocked, error=f'{course["title"]}: {err}', current='')
            else:
                failed.append(course['id'])
                save_state(status='failed_partial', failed_ids=failed, error=f'{course["title"]}: {err}', current='')
            # 单篇失败不再重试整队，避免空转；下一轮会跳过 failed/blocked 或人工处理。
            break
    st = load_state()
    pending = select_next(courses, limit=999)
    final_status = 'completed' if not pending else 'batch_completed'
    save_state(status=final_status, pending_count=len(pending), current='')
    log(f'DONE {final_status} pending={len(pending)}')
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument('--limit', type=int, default=int(os.environ.get('FANQIE_CLASSROOM_BATCH_LIMIT', '3')))
    ap.add_argument('--discover-only', action='store_true')
    args = ap.parse_args()
    return run(max(1, args.limit), args.discover_only)


if __name__ == '__main__':
    raise SystemExit(main())
