#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""V8.12 战略会议执行器（2026-05-13 素材，3段，5模型）

角色分配（主控不在此脚本内，由Cascade本体直接合稿）：
  作家:       claude-opus-4.6-thinking  via cpa proxy
  编辑/结构: glm-5.1                    via zai
  读者:       qwen3.6-plus              via alibaba
  科学/技术: gpt-5.5                    via cpa proxy
  军事/制度: mimo-v2.5                  via xiaomi

用法:
  python3 meeting_v812_0513.py --segment 1
  python3 meeting_v812_0513.py --segment 2
  python3 meeting_v812_0513.py --segment 3
  python3 meeting_v812_0513.py --segment all  # 一次跑完三段

规则:
  - 每模型每段单次回话, 严格 <=500中文字
  - 各模型仅看本段context pack, 不读全项目
  - 仅动大纲, 不改正文
"""
from __future__ import annotations
import argparse, json, os, re, subprocess, sys, time, datetime
from pathlib import Path

BASE = Path('/root/workspace/科武纪元')
DATE = '2026-05-13'
CARDS = BASE / '时事素材' / '素材卡' / DATE
OUT = BASE / '审核记录' / '六角色外审' / 'V812_0513会议'
RAW = OUT / 'raw'
RAW.mkdir(parents=True, exist_ok=True)

# 加载 .env
env = Path(os.path.expanduser('~/.hermes/.env'))
if env.exists():
    for line in env.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

ROLES = [
    # (key, 显示名, 模型, base_url, api_key获取)
    # 注: writer 由 Cascade 本体(claude-opus-4-7-max-fast)在 inject_writer.py 中本地写入,不走外部API
    ('editor',   '编辑/结构',  'glm-5.1',                  'https://open.bigmodel.cn/api/coding/paas/v4',         os.environ.get('ZAI_API_KEY','')),
    ('reader',   '读者',       'qwen3.6-plus',             'https://coding.dashscope.aliyuncs.com/v1',            os.environ.get('DASHSCOPE_API_KEY','')),
    ('science',  '科学/技术',  'gpt-5.5',                  'http://43.135.181.17:8080/v1',                       'sk-proxy-key-20260421'),
    ('military', '军事/制度',  'mimo-v2.5',                'https://token-plan-cn.xiaomimimo.com/v1',             os.environ.get('XIAOMI_API_KEY','tp-cu1vfx43960myk1am363otgznefs7876kbusvjw6x1yb8co0')),
]

# 段定义：每段3-4条关键议题 + 该段相关素材卡
SEGMENTS = {
    1: {
        'title': '段1 · 算力主权链',
        'focus': '算力主权、AI生态分化、量子算力服务化、谈判筹码',
        'cards': [
            CARDS / '素材卡_deepseek_华为芯片_黄仁勋随团_20260513.md',
            CARDS / '素材卡_本源悟空180_量子算力服务化_20260513.md',
        ],
        'anchor_chapters': '95（算力基础设施）、184（复合算力底座）、第二卷整体（DeepSeek类节点 vs 海外算力）',
        'questions': [
            '黄仁勋随团访华+DeepSeek跑通华为芯片，对应到第二卷应如何重塑算力供给曲线？',
            '本源悟空180量子算力服务化，能否在卷三/五落成一条独立可见的“复合算力底座”支线？',
            '是否需要在95章前后插入一组“算力主权事件链”作为V8.12增量？给出具体章节编号建议。',
        ],
    },
    2: {
        'title': '段2 · 军事AI与反无人机工业链',
        'focus': '人在环授权、民用模型军用征召、网络化量产武器、反无人机预认证供应商池',
        'cards': [
            CARDS / '素材卡_五角大楼AI合同扩张_民用模型军用征召_20260513.md',
            CARDS / '素材卡_aselsan_networked_mass_producible_weapons_20260513.md',
            CARDS / '素材卡_nato_vetted_counter_drone_vendor_pool_20260513.md',
        ],
        'anchor_chapters': '184/217/223（军事AI责任链）、110（天门封锁/UGV）、第二卷代理冲突线',
        'questions': [
            '“民用模型军用征召”是否需要写成主角团必须面对的一次合规事故？给出位置建议。',
            'Aselsan式“网络化量产武器”和NATO“预认证供应商池”，应该折射成铁幕联盟的什么制度细节？',
            '184/217/223已有算法对决/责任链/UGV，本段素材给这三条线带来哪些“补强而不重写”的小钩子？',
        ],
    },
    3: {
        'title': '段3 · 地缘 / 太空 / 信息治理（含UAP官方烟幕）',
        'focus': '复合博弈、规则制定权、月面/深空、官方透明烟幕、异常数据治理',
        'cards': [
            CARDS / '素材卡_特朗普访华_台海预算延宕_规则制定权_20260513.md',
            CARDS / '素材卡_美国官方UAP资料释放_舆论烟幕与异常数据治理_20260513.md',
        ],
        'anchor_chapters': '第一卷末/第二卷（代理冲突+预算政治）、第五卷（月面规则战争）、白盾/星穹舆论战、深空异常信号线',
        'questions': [
            '“预算延宕≠让步”如何在第二卷写成一次让主角团错判形势的事件？',
            '月面/深空“谁先持续驻留、谁定义规则”，对第五卷的卷首三章应该锁定哪些大纲变量？',
            'UAP式官方烟幕（公开但不完整、自发填空）能否在白盾/星穹舆论战里替换一个旧桥段？给出替换点。',
        ],
    },
}


def load_card_brief(path: Path) -> str:
    """从素材卡里抽 一句话/关键事实/小说映射 三块，控制每张卡<=1200字。"""
    if not path.exists():
        return f'[缺失:{path.name}]'
    txt = path.read_text(encoding='utf-8', errors='ignore')
    keep = []
    for marker in ['## 一句话', '## 关键事实', '## 小说映射', '## 不可使用']:
        i = txt.find(marker)
        if i < 0:
            continue
        j = txt.find('\n## ', i + 4)
        if j < 0: j = len(txt)
        block = txt[i:j].strip()
        keep.append(block)
    head = txt.splitlines()[0] if txt.splitlines() else path.name
    body = '\n\n'.join(keep)
    if len(body) > 1200:
        body = body[:1200] + '...[已截断]'
    return f'### {head}\n{body}'


def build_pack(seg_id: int) -> str:
    seg = SEGMENTS[seg_id]
    cards = '\n\n---\n\n'.join(load_card_brief(c) for c in seg['cards'])
    questions = '\n'.join(f'  Q{i+1}. {q}' for i, q in enumerate(seg['questions']))
    return f"""# {seg['title']}

聚焦: {seg['focus']}
大纲锚点章节: {seg['anchor_chapters']}

## 本段素材卡精要

{cards}

## 主控提问（请按编号逐条回答）
{questions}
"""


ROLE_INSTRUCTIONS = {
    'writer':   '你是《科武纪元》作家视角。从“能不能在大纲层面长成可写场景/可见钩子”的角度评估，提出场景化建议；禁止直接写正文片段。',
    'editor':   '你是结构编辑。从“章节位置/节奏/卷与卷的耦合/重复风险/与已闭环章节冲突”的角度评估；明确说出建议插入/调整的章节编号或区段。',
    'reader':   '你是普通读者代理。从“看不看得懂/会不会觉得突兀/会不会觉得在重复已有桥段/想不想看下一章”的角度评估；明确指出最容易劝退的点。',
    'science':  '你是科学/技术顾问。校验素材里的技术声明边界（如量子算力服务化、模型征召、芯片适配）；指出哪些可写、哪些只能虚化、哪些必须打补丁；输出可直接进大纲的“技术红线/边界”要点。',
    'military': '你是军事/制度顾问。校验军事AI、反无人机工业、规则制定权、预算政治；输出制度可信度建议和“写错会被读者识破”的雷区；尽量给出可落到大纲条目的具体修改方向。',
}

COMMON_RULES = (
    '硬约束:\n'
    '1) 全部回复 <=500 中文字, 超出立即截断, 不要重述提示词。\n'
    '2) 仅讨论大纲层面（章节位置/支线/钩子/制度细节/技术红线）, 禁止改写正文, 禁止生成小说片段。\n'
    '3) 必须对“主控提问”的Q1/Q2/Q3逐条回应, 每条一句到三句。\n'
    '4) 末尾另起一行, 给出 <=3 个明确的“受影响章节/区段”建议（如: 第95章前置, 184章补强, 第五卷卷首三章, 等）。\n'
    '5) 不要使用Markdown标题; 用 Q1: / Q2: / Q3: / 影响章节: 这样的纯文本前缀。\n'
)


def call_model(role_key, display, model, base, key, pack, timeout=180):
    instr = ROLE_INSTRUCTIONS[role_key]
    prompt = f"""你的角色: {display}
你的视角: {instr}

{COMMON_RULES}

以下是本段会议材料（你只看本段）:

{pack}
"""
    if not key:
        return {'ok': False, 'error': 'missing api key', 'role': role_key, 'model': model}
    payload = {
        'model': model,
        'messages': [{'role': 'user', 'content': prompt}],
        'temperature': 0.2,
        'max_tokens': 1200,
    }
    t0 = time.time()
    try:
        r = subprocess.run(
            ['curl', '-sS', '--max-time', str(timeout),
             f'{base.rstrip("/")}/chat/completions',
             '-H', f'Authorization: Bearer {key}',
             '-H', 'Content-Type: application/json',
             '-d', json.dumps(payload, ensure_ascii=False)],
            capture_output=True, text=True, timeout=timeout + 10,
        )
    except subprocess.TimeoutExpired:
        return {'ok': False, 'error': 'timeout', 'role': role_key, 'model': model, 'elapsed': time.time()-t0}
    elapsed = round(time.time() - t0, 1)
    try:
        data = json.loads(r.stdout)
    except Exception:
        return {'ok': False, 'error': f'parse_fail: {r.stdout[:200]}', 'role': role_key, 'model': model, 'elapsed': elapsed}
    err = data.get('error')
    if err:
        return {'ok': False, 'error': str(err)[:300], 'role': role_key, 'model': model, 'elapsed': elapsed}
    msg = (data.get('choices') or [{}])[0].get('message', {})
    content = (msg.get('content') or msg.get('reasoning_content') or '').strip()
    usage = data.get('usage') or {}
    cn = len(re.findall(r'[\u4e00-\u9fff]', content))
    return {
        'ok': bool(content),
        'role': role_key, 'display': display, 'model': model,
        'elapsed': elapsed,
        'content': content,
        'cn_chars': cn,
        'tokens': usage.get('total_tokens', 0),
    }


def run_segment(seg_id: int) -> dict:
    seg = SEGMENTS[seg_id]
    pack = build_pack(seg_id)
    pack_path = OUT / f'segment_{seg_id}_context_pack.md'
    pack_path.write_text(pack, encoding='utf-8')
    print(f'[seg{seg_id}] pack written: {pack_path} ({len(pack)} chars)')

    results = []
    for role_key, display, model, base, key in ROLES:
        print(f'[seg{seg_id}] -> {display} ({model}) ...', flush=True)
        res = call_model(role_key, display, model, base, key, pack)
        results.append(res)
        raw = RAW / f'seg{seg_id}_{role_key}_{int(time.time())}.json'
        raw.write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding='utf-8')
        if res.get('ok'):
            print(f'    ok: {res["cn_chars"]} 中文字, {res["elapsed"]}s, {res["tokens"]} tokens')
        else:
            print(f'    FAIL: {res.get("error")[:200]}')

    # 段汇总 markdown
    md = [f'# {seg["title"]} 讨论记录', '', f'时间: {datetime.datetime.now().isoformat(timespec="seconds")}',
          f'素材日期: {DATE}', f'聚焦: {seg["focus"]}', f'锚点章节: {seg["anchor_chapters"]}', '',
          '## 各模型发言', '']
    for res in results:
        md.append(f'### {res.get("display", res["role"])} · `{res["model"]}`')
        if res.get('ok'):
            md.append(f'_耗时 {res["elapsed"]}s · {res["cn_chars"]}中文字 · {res["tokens"]} tokens_')
            md.append('')
            md.append(res['content'])
        else:
            md.append(f'**FAIL**: {res.get("error")}')
        md.append('')
    out_md = OUT / f'segment_{seg_id}_讨论记录.md'
    out_md.write_text('\n'.join(md), encoding='utf-8')
    print(f'[seg{seg_id}] segment summary -> {out_md}')

    return {
        'segment': seg_id, 'title': seg['title'], 'pack_path': str(pack_path),
        'summary_path': str(out_md), 'results': results,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--segment', required=True, help='1 | 2 | 3 | all')
    args = ap.parse_args()
    todo = [1, 2, 3] if args.segment == 'all' else [int(args.segment)]
    out = []
    for s in todo:
        out.append(run_segment(s))
    ledger = OUT / 'segments_run_ledger.json'
    prev = []
    if ledger.exists():
        try:
            prev = json.loads(ledger.read_text(encoding='utf-8'))
        except Exception:
            prev = []
    prev.extend(out)
    ledger.write_text(json.dumps(prev, ensure_ascii=False, indent=2), encoding='utf-8')
    print(f'\nDONE. ledger -> {ledger}')

if __name__ == '__main__':
    main()
