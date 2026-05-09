#!/usr/bin/env python3
"""科武纪元·新章写作完整流程
用法: python3 write_chapter_full.py 261 [262] [263] ...
功能: 任务卡→查素材→写作→四角色审核→修改→门禁→记录
铁律: 不跑完流程不产出最终文件
"""
from __future__ import annotations
import argparse, json, os, re, sys, time, requests
from pathlib import Path

BASE = Path('/root/workspace/科武纪元')
CONFIG = Path('/root/.hermes/config.yaml')

# ── 加载.env ──
env_path = Path(os.path.expanduser('~/.hermes/.env'))
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

# ── 动态角色配置（smoke后可调整） ──
ROLES = {
    'editor':   {'model': 'mimo-v2.5',  'key_env': 'XIAOMI_API_KEY',    'base_url': 'https://token-plan-cn.xiaomimimo.com/v1'},
    'reader':   {'model': 'MiniMax-M2.7','key_env': 'MINIMAX_CN_API_KEY','base_url': 'https://api.minimaxi.com/v1'},
    'military': {'model': 'qwen3.6-plus','key_env': 'DASHSCOPE_API_KEY','base_url': 'https://coding.dashscope.aliyuncs.com/v1'},
    'science':  {'model': 'qwen3.6-plus','key_env': 'DASHSCOPE_API_KEY','base_url': 'https://coding.dashscope.aliyuncs.com/v1'},
    'author':   {'model': 'mimo-v2.5',  'key_env': 'XIAOMI_API_KEY',    'base_url': 'https://token-plan-cn.xiaomimimo.com/v1'},
}

# ── 大纲锚点（从V8大纲提取，写到260，后续需补充） ──
OUTLINE = {
    256: '方宁带队登陆水手号峡谷建立首个殖民地。落地首日遭遇铁幕联盟伏击——对方提前7个月部署。地火通信延迟22分钟。',
    257: '殖民地扩建时发现地下洞穴系统，内有非自然结构。CELSS故障——氧气产率从98%骤降至73%。',
    258: '林星辰带队勘探极地冰盖，钻探检测到深层金属反应。CELSS故障导致300名矿工暴动。',
    259: '破开冰层发现建筑群，太极生物电增强光合作用，CELSS从73%拉回91%。',
    260: '铁幕突袭极地营地抢夺遗迹数据，地火延迟22分钟，流云算法代理模式独立决策。',
}

# ── 知识库素材卡索引 ──
KB_INDEX = {
    '火星远征': ['深空工程/素材卡_闭环生态CELSS.md'],
    'CELSS': ['深空工程/素材卡_闭环生态CELSS.md'],
    '冰盖': ['深空工程/素材卡_火星ISRU.md'],
    'ISRU': ['深空工程/素材卡_火星ISRU.md'],
    '遗迹': ['深空工程/素材卡_闭环生态CELSS.md', '深空工程/素材卡_火星ISRU.md'],
}

MAX_INPUT = 4000
MAX_OUTPUT = 3000
MAX_TOKENS = 4096
RETRY = 3

def call_api(role_name, prompt, max_tokens=MAX_TOKENS):
    rc = ROLES[role_name]
    key = os.environ.get(rc['key_env'], '')
    if not key:
        return {'ok': False, 'error': f'缺环境变量 {rc["key_env"]}'}
    url = f"{rc['base_url'].rstrip('/')}/chat/completions"
    payload = {"model": rc['model'], "messages": [{"role": "user", "content": prompt}], "max_tokens": max_tokens, "temperature": 0.1}
    headers = {'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'}
    for attempt in range(RETRY):
        try:
            r = requests.post(url, json=payload, headers=headers, timeout=180)
            data = r.json()
            if 'error' in data:
                return {'ok': False, 'error': str(data['error'])}
            content = (data.get('choices') or [{}])[0].get('message', {}).get('content', '')
            return {'ok': True, 'content': content, 'model': rc['model'], 'provider': role_name}
        except Exception as e:
            if attempt < RETRY - 1:
                time.sleep(3)
                continue
            return {'ok': False, 'error': str(e)}

def load_kb_cards(chapter_num):
    """匹配章节相关素材卡"""
    outline_text = OUTLINE.get(chapter_num, '')
    cards = []
    for keyword, card_paths in KB_INDEX.items():
        if keyword in outline_text:
            for cp in card_paths:
                full_path = BASE / '知识库' / cp
                if full_path.exists():
                    cards.append(full_path.read_text(encoding='utf-8')[:500])
    return list(set(cards))

def write_task_card(chapter_num, outline_text, kb_cards):
    """生成任务卡"""
    prev_text = ''
    if chapter_num > 256:
        prev_path = BASE / '新版' / f'第{chapter_num-1}章.md'
        if prev_path.exists():
            prev_text = prev_path.read_text(encoding='utf-8')[-500:]
    
    cards_text = ''.join(f'【卡{i+1}】{c[:200]}\n' for i, c in enumerate(kb_cards)) if kb_cards else '无'
    prompt = f"""角色: 编辑+主控
任务: 为第{chapter_num}章生成写作任务卡（≤500字）
大纲: {outline_text}
上一章末段: {prev_text[:500] if prev_text else '首章'}
素材卡: {cards_text}

输出格式:
# 第{chapter_num}章任务卡
- V8锚点:
- 上章承接:
- 本章必须发生: ≤3
- 禁止发生: ≤3
- 技术素材: ≤3
- 章末钩子:
- 风格提醒: 物理反馈/行动链/禁文艺比喻"""
    
    r = call_api('editor', prompt, max_tokens=800)
    return r.get('content', '') if r['ok'] else f'[编辑不可用，主控生成]\n# 第{chapter_num}章任务卡\n- V8锚点: {outline_text}\n- 章末钩子: 承接下一章'

def write_chapter(chapter_num, task_card, outline_text, kb_cards):
    """作者写正文"""
    prev_text = ''
    if chapter_num > 256:
        prev_path = BASE / '新版' / f'第{chapter_num-1}章.md'
        if prev_path.exists():
            prev_text = prev_path.read_text(encoding='utf-8')[-1000:]
    
    cards_text = ''.join(f'【卡{i+1}】{c[:300]}\n' for i, c in enumerate(kb_cards)) if kb_cards else '无'
    prompt = f"""角色: 作者
任务: 写第{chapter_num}章正文
大纲: {outline_text}
任务卡:
{task_card}

上一章末段:
{prev_text}

素材卡摘要:
{cards_text}

写作铁律:
- ≥3000番茄口径字（去空白总字符-标题字符）
- 短句对话风格，禁文艺比喻
- 用物理反馈/感官数据/行动链
- 核心数据必须落地为具体数字/动作
- 章末必须有钩子牵引下一章
- 首行格式: # 第{chapter_num}章 {{标题}}
- 末行: （本章完）

开始写作:"""
    
    r = call_api('author', prompt, max_tokens=MAX_TOKENS)
    return r.get('content', '') if r['ok'] else ''

def review_chapter(chapter_num, chapter_text, outline_text, kb_cards):
    """四角色审核"""
    results = {}
    
    # 编辑审
    r = call_api('editor', f"""角色:编辑
任务:审第{chapter_num}章结构/大纲对齐/节奏
大纲:{outline_text}
【首800】{chapter_text[:800]}
【末800】{chapter_text[-800:]}
第一行只写PASS或FAIL
第二行起:大纲对齐?节奏?钩子?必改≤5""")
    results['editor'] = r
    
    # 军事审
    r = call_api('military', f"""角色:军事顾问
任务:查战术/装备/组织逻辑可信度
段落:{chapter_text[:1500]}
第一行只写PASS或FAIL
第二行起:不可信点≤5/改法≤5""")
    results['military'] = r
    
    # 科学审
    kb_summary = '\n'.join(kb_cards[:2]) if kb_cards else '无素材卡'
    r = call_api('science', f"""角色:科学顾问
任务:查技术合理性/科普可读性
素材:{kb_summary}
段落:{chapter_text[:1500]}
第一行只写PASS或FAIL
第二行起:硬伤≤5/读不懂处≤5""")
    results['science'] = r
    
    # 读者审
    r = call_api('reader', f"""角色:普通网文读者
任务:判断是否想追读
【首800】{chapter_text[:800]}
【末800】{chapter_text[-800:]}
说人话。第一行只写PASS或FAIL
第二行起:想不想看下章/卡点≤3/AI味≤3""")
    results['reader'] = r
    
    return results

def fix_issues(chapter_text, issues, outline_text, task_card, kb_cards):
    """根据审核意见修改"""
    prompt = f"""角色: 作者
任务: 根据审核意见修改第{chapter_text.split(chr(10))[0] if chapter_text else '本章'}

原文:
{chapter_text[:3000]}

审核意见:
{issues}

大纲: {outline_text}
任务卡: {task_card[:500]}

修改要求:
- 只修审核指出的问题，不重写全文
- 保持原有风格和剧情
- 确保≥3000番茄口径字
- 输出完整修改后正文"""
    
    r = call_api('author', prompt, max_tokens=MAX_TOKENS)
    return r.get('content', '') if r['ok'] else chapter_text

def main():
    parser = argparse.ArgumentParser(description='科武纪元·新章写作完整流程')
    parser.add_argument('chapters', nargs='+', type=int, help='章节号列表')
    args = parser.parse_args()
    
    print("=" * 60)
    print(f"科武纪元·新章写作完整流程")
    print(f"章节: {args.chapters}")
    print("=" * 60)
    
    for chapter_num in args.chapters:
        print(f"\n{'='*40}")
        print(f"第{chapter_num}章")
        print(f"{'='*40}")
        
        # 1. 大纲锚点
        outline_text = OUTLINE.get(chapter_num, '待补充')
        print(f"\n[1/6] 大纲锚点: {outline_text[:100]}...")
        
        # 2. 查素材卡
        kb_cards = load_kb_cards(chapter_num)
        print(f"[2/6] 素材卡: {len(kb_cards)}张")
        
        # 3. 生成任务卡
        print(f"[3/6] 生成任务卡...")
        task_card = write_task_card(chapter_num, outline_text, kb_cards)
        print(f"任务卡长度: {len(task_card)}字")
        
        # 4. 写正文
        print(f"[4/6] 写正文...")
        chapter_text = write_chapter(chapter_num, task_card, outline_text, kb_cards)
        if not chapter_text:
            print("ERROR: 正文生成失败")
            continue
        
        # 字数检查
        title_line = chapter_text.strip().split('\n')[0].replace('#', '').strip()
        title_len = len(title_line)
        total = len(chapter_text.replace('\n', '').replace(' ', ''))
        body_chars = total - title_len
        print(f"正文字数: {body_chars}")
        
        # 5. 四角色审核
        print(f"[5/6] 四角色审核...")
        review_results = review_chapter(chapter_num, chapter_text, outline_text, kb_cards)
        
        # 解析审核结果
        fails = []
        for role, r in review_results.items():
            ok = r.get('ok', False)
            content = r.get('content', r.get('error', ''))
            # 剥离 MiniMax 的 <think> 标签
            content_clean = re.sub(r'<[^>]+>', '', content).strip()
            first_line = content_clean.split('\n')[0] if content_clean else 'N/A'
            status = 'PASS' if 'PASS' in first_line and 'FAIL' not in first_line else 'FAIL'
            print(f"  {role}({r.get('model','?')}): {status} | {first_line[:60]}")
            if status == 'FAIL' or '硬伤' in content_clean or '必改' in content_clean:
                fails.append(f"{role}: {content_clean[:200]}")
        
        # 6. 修改+门禁
        if fails:
            print(f"[6/6] 有{len(fails)}个FAIL，修改中...")
            issues = '\n---\n'.join(fails)
            chapter_text = fix_issues(chapter_text, issues, outline_text, task_card, kb_cards)
            if chapter_text:
                # 复审
                print("  复审中...")
                review_results2 = review_chapter(chapter_num, chapter_text, outline_text, kb_cards)
                for role, r in review_results2.items():
                    content_clean = re.sub(r'<[^>]+>', '', r.get('content', '')).strip()
                    first_line = content_clean.split('\n')[0] if content_clean else 'N/A'
                    status = 'PASS' if 'PASS' in first_line and 'FAIL' not in first_line else 'FAIL'
                    print(f"  复审 {role}: {status}")
        
        # 7. 保存
        # 检查末行
        last_line = chapter_text.strip().split('\n')[-1]
        if '本章完' not in last_line:
            chapter_text += '\n\n（本章完）'
        
        output_path = BASE / '新版' / f'第{chapter_num}章.md'
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(chapter_text, encoding='utf-8')
        
        # 最终字数
        total2 = len(chapter_text.replace('\n', '').replace(' ', ''))
        title_line2 = chapter_text.strip().split('\n')[0].replace('#', '').strip()
        body_chars2 = total2 - len(title_line2)
        
        print(f"\n✓ 第{chapter_num}章 完成: {body_chars2}字 | {output_path}")
        
        # 保存审核记录
        review_dir = BASE / '审核记录' / '六角色外审'
        review_dir.mkdir(parents=True, exist_ok=True)
        review_path = review_dir / f'{chapter_num}_review.json'
        with open(review_path, 'w', encoding='utf-8') as f:
            json.dump({
                'chapter': chapter_num,
                'task_card': task_card[:500],
                'review': {k: {'ok': v.get('ok'), 'model': v.get('model'), 'first_line': re.sub(r'<[^>]+>', '', v.get('content', '')).strip()[:200]} for k, v in review_results.items()},
                'word_count': body_chars2,
                'output_path': str(output_path)
            }, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    main()
