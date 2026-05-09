#!/usr/bin/env python3
"""科武纪元·低模型资料缺口采集任务生成器

目标：不让大模型裸搜。先用脚本从大纲/素材索引中抽取缺口，再输出给低模型(MiniMax/Qwen)做方向筛选与审核。

用法：
  python3 kewu_gap_collect_low_model.py --project-dir /root/workspace/科武纪元

输出：
  时事素材/缺口采集/缺口采集任务_YYYYMMDD.md
  时事素材/缺口采集/缺口采集任务_YYYYMMDD.json
"""
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path

DEFAULT_PROJECT = Path('/root/workspace/科武纪元')

TECH_SEEDS = {
    '国产算力训练主权': ['国产算力', '国产GPU', 'NPU', '低带宽互联', '分布式训练', '训练框架', '存算一体', 'AI芯片'],
    '地月规则竞赛': ['月面通信', '月球补给', '月面救援', '国际月球科研站', '外空法', '月球资源', '深空通信'],
    '军事AI蜂群': ['无人机蜂群', '反蜂群', 'OODA', '分布式控制', '电子战', '任务级授权', '边缘AI'],
    '量子先存后解': ['后量子密码', 'PQC', 'NIST PQC', '量子密钥分发', 'QKD', 'PUF', '物理不可克隆函数', '先存后解'],
    '人机协同入口': ['实时语音AI', '语音转写', '实时翻译', '边缘代理', '人机协同', '低延迟接口'],
}

SOURCE_HINTS = {
    '国产算力训练主权': ['中科院', '工信部', '企业白皮书', 'arXiv', 'IEEE', '芯片厂商公开资料'],
    '地月规则竞赛': ['国家航天局', 'NASA', 'ESA', 'UNOOSA', '外空法资料', '航天白皮书'],
    '军事AI蜂群': ['DefenseNews', 'DARPA', 'RAND', 'CSIS', 'IEEE', '军工公开材料'],
    '量子先存后解': ['NIST', 'ETSI', 'ISO/IEC', '中科院', '密码学论文', '网络安全机构'],
    '人机协同入口': ['TechCrunch', 'OpenAI docs', '企业API文档', '开发者博客'],
}


def read_text(path: Path) -> str:
    return path.read_text(encoding='utf-8', errors='ignore') if path.exists() else ''


def extract_outline_hits(outline: str) -> dict[str, list[str]]:
    hits = defaultdict(list)
    for line in outline.splitlines():
        if '第' not in line:
            continue
        for topic, kws in TECH_SEEDS.items():
            if any(kw in line for kw in kws):
                m = re.search(r'第\s*(\d+)\s*章', line)
                ch = f"第{m.group(1)}章" if m else ''
                title = line.strip()[:160]
                hits[topic].append(f"{ch} {title}".strip())
    return hits


def existing_coverage(index_text: str) -> dict[str, int]:
    cov = {}
    for topic, kws in TECH_SEEDS.items():
        cov[topic] = sum(index_text.count(kw) for kw in kws)
    return cov


def build_tasks(project_dir: Path) -> list[dict]:
    outline = read_text(project_dir / '科武纪元大纲 V8_完整版.md') or read_text(project_dir / 'wiki/raw/outline/科武纪元大纲_latest.md')
    index = read_text(project_dir / '时事素材/INDEX.md')
    hits = extract_outline_hits(outline)
    cov = existing_coverage(index)
    tasks = []
    for topic, kws in TECH_SEEDS.items():
        coverage = cov.get(topic, 0)
        priority = 'P0' if coverage < 2 else ('P1' if coverage < 5 else 'P2')
        tasks.append({
            'topic': topic,
            'priority': priority,
            'coverage_score': coverage,
            'keywords': kws,
            'source_hints': SOURCE_HINTS.get(topic, []),
            'outline_hits': hits.get(topic, [])[:12],
            'low_model_instruction': '请只做方向筛选/来源建议/风险审核，不要编造已采集事实，不要写正文。',
        })
    return sorted(tasks, key=lambda x: (x['priority'], x['coverage_score']))


def write_outputs(project_dir: Path, tasks: list[dict]) -> tuple[Path, Path]:
    today = datetime.now().strftime('%Y%m%d')
    out_dir = project_dir / '时事素材/缺口采集'
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / f'缺口采集任务_{today}.json'
    md_path = out_dir / f'缺口采集任务_{today}.md'
    json_path.write_text(json.dumps(tasks, ensure_ascii=False, indent=2), encoding='utf-8')

    lines = [f'# 科武纪元缺口采集任务 {today}', '', '用途：给低模型做方向筛选与审核；采集仍由确定性脚本/爬虫执行。', '']
    lines.append('| 优先级 | 主线 | 覆盖分 | 关键词 | 优先来源 | 大纲命中 |')
    lines.append('|---|---|---:|---|---|---|')
    for t in tasks:
        kws = ' / '.join(t['keywords'])
        src = ' / '.join(t['source_hints'])
        hits = '<br>'.join(t['outline_hits'][:4]) if t['outline_hits'] else '待从大纲补锚点'
        lines.append(f"| {t['priority']} | {t['topic']} | {t['coverage_score']} | {kws} | {src} | {hits} |")
    lines += ['', '## 低模型提示', '', 'MiniMax/Qwen只做：关键词扩展、候选筛选、来源优先级、风险审核。不得声称资料已采集。']
    md_path.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return md_path, json_path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--project-dir', default=str(DEFAULT_PROJECT))
    args = ap.parse_args()
    project_dir = Path(args.project_dir)
    tasks = build_tasks(project_dir)
    md_path, json_path = write_outputs(project_dir, tasks)
    print(json.dumps({'ok': True, 'tasks': len(tasks), 'md': str(md_path), 'json': str(json_path)}, ensure_ascii=False))


if __name__ == '__main__':
    main()
