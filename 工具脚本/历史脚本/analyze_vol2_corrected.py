#!/usr/bin/env python3
"""《科武纪元》第二卷（56-105章）节奏与对话审查报告 - 修正版"""
import re
from pathlib import Path
from collections import Counter

BASE = Path('/workspace/科武纪元/新版')

# ============ 1. 对话比例统计（修正：正确使用中文弯引号） ============
def calc_dialogue_ratio(text):
    """计算对话占总字数的比例。使用中文弯引号 \u201c\u201d + 直双引号"""
    cn_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    if cn_chars == 0:
        return 0.0, 0, 0
    
    # 策略1: 中文弯引号 "" 和 直双引号 ""
    dialogues1 = re.findall(r'[\u201c"][^\u201d"]{2,}[\u201d"]', text)
    # 策略2: 角括号「」
    dialogues2 = re.findall(r'[\u300c][^\u300d]{2,}[\u300d]', text)
    
    all_dialogues = dialogues1 + dialogues2
    dialogue_chars = sum(len(d) for d in all_dialogues)
    ratio = dialogue_chars / cn_chars * 100 if cn_chars > 0 else 0
    return ratio, len(all_dialogues), dialogue_chars, cn_chars

# ============ 2. 章末钩子检测 ============
def check_ending_hook(text):
    """检查章末是否有力"""
    ending = text[-500:] if len(text) > 500 else text
    
    suspense_words = ['突然', '然而', '但是', '不对', '等等', '不对头', '奇怪',
                      '难道', '什么', '怎么会', '居然', '竟然', '没想到',
                      '就在这时', '与此同时', '远处', '身后', '屏幕',
                      '信号', '警报', '闪烁', '响起', '传来',
                      '未知', '神秘', '不对劲', '异样', '变了']
    
    conflict_words = ['杀', '攻击', '危险', '敌人', '战斗', '冲击', '爆炸',
                      '崩溃', '失控', '失败', '完了', '糟了', '跑', '逃',
                      '倒下', '受伤', '血', '死', '破坏']
    
    reversal_words = ['不是', '却', '反而', '相反', '可是', '然而', '但是',
                      '出乎', '意外', '没想', '结果', '原来']
    
    ending_sent = ending[-200:]
    has_question = bool(re.search(r'[？?]', ending_sent))
    has_exclaim = bool(re.search(r'[！!]', ending_sent))
    ends_with_dialogue = bool(re.search(r'[\u201d\u300d"][\s]*$', ending.strip()))
    
    # 计算最后几句中的关键词密度
    suspense_count = sum(1 for w in suspense_words if w in ending)
    conflict_count = sum(1 for w in conflict_words if w in ending)
    reversal_count = sum(1 for w in reversal_words if w in ending)
    
    score = suspense_count * 2 + conflict_count * 2 + reversal_count + \
            (2 if has_question else 0) + (1 if has_exclaim else 0) + \
            (2 if ends_with_dialogue else 0)
    
    if score >= 8:
        level = "🔴 强钩子"
    elif score >= 4:
        level = "🟡 中等钩子"
    elif score >= 2:
        level = "🟠 弱钩子"
    else:
        level = "⚪ 平淡收场"
    
    sentences = re.split(r'[。！？\n]+', ending.strip())
    last_sentences = [s.strip() for s in sentences if s.strip()][-3:]
    
    return level, score, last_sentences

# ============ 3. 战斗/紧张场景节奏检测 ============
def check_action_pacing(text):
    """检查战斗/紧张场景的节奏"""
    action_indicators = ['攻击', '防御', '躲避', '闪', '冲', '击', '刀', '剑',
                        '枪', '炮', '爆炸', '碎', '裂', '断', '闪', '避',
                        '追', '逃', '跑', '跳', '撞', '杀', '斗', '战',
                        '能量', '光束', '脉冲', '盾', '甲', '破', '轰']
    
    paragraphs = [p.strip() for p in text.split('\n') if p.strip() and len(p.strip()) > 10]
    
    action_paras = []
    for p in paragraphs:
        indicator_count = sum(1 for w in action_indicators if w in p)
        if indicator_count >= 2:
            action_paras.append((p, indicator_count))
    
    if not action_paras:
        return "无战斗场景", 0, []
    
    all_sentences = []
    for para, _ in action_paras:
        sentences = re.split(r'[，。；！？、\n]', para)
        all_sentences.extend([s.strip() for s in sentences if s.strip()])
    
    if not all_sentences:
        return "战斗段落异常", 0, []
    
    avg_sent_len = sum(len(s) for s in all_sentences) / len(all_sentences)
    short_sent_ratio = sum(1 for s in all_sentences if len(s) <= 10) / len(all_sentences) * 100
    
    issues = []
    if avg_sent_len > 20:
        issues.append(f"平均句长{avg_sent_len:.0f}字，偏长（网文建议<15字）")
    if short_sent_ratio < 20:
        issues.append(f"短句(≤10字)比例{short_sent_ratio:.0f}%，偏低（建议>30%）")
    
    pacing = "✅ 合格" if not issues else "⚠️ " + " | ".join(issues)
    return pacing, len(action_paras), action_paras[:2]

# ============ 4. AI腔检测 ============
def check_ai_tone(text):
    ai_words = ['仿佛', '不禁', '意识到', '意味着', '咏叹', '微微', '淡淡', 
                '轻轻', '缓缓', '宛如', '心里想', '不可思议', '似乎',
                '心中涌起', '一股', '坚定', '决心', '目光', '紧紧',
                '深深', '刻在', '烙印', '注定', '悄然', '无声',
                '不仅仅', '而是']
    results = {}
    for w in ai_words:
        count = len(re.findall(re.escape(w), text))
        if count >= 2:
            results[w] = count
    return results

# ============ 5. 长段落检测 ============
def check_long_paragraphs(text):
    paragraphs = text.split('\n')
    max_len = 0
    long_paras = []
    for i, p in enumerate(paragraphs):
        cn = len(re.findall(r'[\u4e00-\u9fff]', p))
        if cn > max_len:
            max_len = cn
        if cn > 200:
            long_paras.append((i+1, cn))
    return max_len, long_paras

# ============ 主扫描流程 ============
focus_chapters = [78, 89, 92, 96, 104]
known_zero_dialogue_old = [78, 92, 104, 102, 96, 101, 105, 97]

print("=" * 80)
print("《科武纪元》第二卷（56-105章）节奏与对话审查报告 [修正版]")
print("对话检测已修复：正确使用中文弯引号 \\u201c\\u201d")
print("=" * 80)

all_results = []
low_dialogue = []
zero_dialogue = []
flat_ending = []
weak_ending = []
strong_ending = []

for ch_num in range(56, 106):
    filepath = BASE / f'第{ch_num}章.md'
    if not filepath.exists():
        continue
    
    text = filepath.read_text(encoding='utf-8')
    
    dial_ratio, dial_count, dial_chars, total_chars = calc_dialogue_ratio(text)
    ending_level, ending_score, last_sents = check_ending_hook(text)
    pacing, action_count, action_samples = check_action_pacing(text)
    ai_tone = check_ai_tone(text)
    max_para, long_paras = check_long_paragraphs(text)
    
    result = {
        'ch': ch_num,
        'dial_ratio': dial_ratio,
        'dial_count': dial_count,
        'total_chars': total_chars,
        'ending_level': ending_level,
        'ending_score': ending_score,
        'last_sents': last_sents,
        'pacing': pacing,
        'action_count': action_count,
        'ai_tone': ai_tone,
        'max_para': max_para,
        'long_paras': long_paras,
    }
    all_results.append(result)
    
    if dial_ratio == 0:
        zero_dialogue.append(result)
    elif dial_ratio < 15:
        low_dialogue.append(result)
    
    if ending_level == "⚪ 平淡收场":
        flat_ending.append(result)
    elif ending_level in ["🟠 弱钩子", "🟡 中等钩子"]:
        weak_ending.append(result)
    else:
        strong_ending.append(result)

# ============ 报告输出 ============
print("\n" + "=" * 80)
print("一、对话比例分析")
print("=" * 80)

if zero_dialogue:
    print(f"\n🔴 对话=0%的章节（共{len(zero_dialogue)}章）：")
    for r in zero_dialogue:
        focus = "【重点】" if r['ch'] in focus_chapters else ""
        print(f"  {focus}第{r['ch']}章 | {r['total_chars']}字")

if low_dialogue:
    print(f"\n🟡 对话<15%的章节（共{len(low_dialogue)}章）：")
    for r in low_dialogue:
        focus = "【重点】" if r['ch'] in focus_chapters else ""
        print(f"  {focus}第{r['ch']}章 | {r['total_chars']}字 | 对话比例: {r['dial_ratio']:.1f}% | {r['dial_count']}处对话")

# 全量对话比例排序
print(f"\n📊 全量对话比例（56-105章，共{len(all_results)}章）：")
sorted_by_dial = sorted(all_results, key=lambda x: x['dial_ratio'])
print(f"  最低10章:")
for r in sorted_by_dial[:10]:
    focus = " ★" if r['ch'] in focus_chapters else ""
    status = "🔴" if r['dial_ratio'] < 10 else "🟡" if r['dial_ratio'] < 15 else "🟢"
    print(f"    {status} 第{r['ch']}章: {r['dial_ratio']:.1f}% ({r['dial_count']}处){focus}")

print(f"  最高5章:")
for r in sorted_by_dial[-5:]:
    print(f"    🟢 第{r['ch']}章: {r['dial_ratio']:.1f}% ({r['dial_count']}处)")

# ============ 章末钩子 ============
print("\n" + "=" * 80)
print("二、章末钩子审查")
print("=" * 80)

print(f"\n🔴 平淡收场（共{len(flat_ending)}章）：")
if flat_ending:
    for r in flat_ending:
        focus = "【重点】" if r['ch'] in focus_chapters else ""
        print(f"  {focus}第{r['ch']}章 | 评分: {r['ending_score']}")
        if r['last_sents']:
            print(f"    结尾: {' | '.join(r['last_sents'][:2])}")
else:
    print("  无")

print(f"\n🟠 弱钩子（{sum(1 for r in weak_ending if r['ending_level'] == '🟠 弱钩子')}章）：")
for r in weak_ending:
    if r['ending_level'] == "🟠 弱钩子":
        focus = "【重点】" if r['ch'] in focus_chapters else ""
        print(f"  {focus}第{r['ch']}章 | 评分: {r['ending_score']}")
        if r['last_sents']:
            print(f"    结尾: {' | '.join(r['last_sents'][:2])}")

print(f"\n🟡 中等钩子（{sum(1 for r in weak_ending if r['ending_level'] == '🟡 中等钩子')}章）：")
for r in weak_ending:
    if r['ending_level'] == "🟡 中等钩子":
        focus = "【重点】" if r['ch'] in focus_chapters else ""
        print(f"  {focus}第{r['ch']}章 | 评分: {r['ending_score']}")

print(f"\n🟢 强钩子（{len(strong_ending)}章）：")
for r in strong_ending:
    focus = " ★" if r['ch'] in focus_chapters else ""
    print(f"  第{r['ch']}章 | 评分: {r['ending_score']}{focus}")

# ============ 战斗节奏 ============
print("\n" + "=" * 80)
print("三、战斗/紧张场景节奏")
print("=" * 80)

pacing_issues = [r for r in all_results if r['action_count'] > 0 and '⚠️' in r['pacing']]
print(f"\n⚠️ 有战斗节奏问题的章节（共{len(pacing_issues)}章）：")
for r in pacing_issues:
    focus = "【重点】" if r['ch'] in focus_chapters else ""
    print(f"  {focus}第{r['ch']}章 | 战斗段落{r['action_count']}处 | {r['pacing']}")

no_action = [r for r in all_results if r['action_count'] == 0]
print(f"\n  无战斗场景: {len(no_action)}章")
action_ok = [r for r in all_results if r['action_count'] > 0 and '⚠️' not in r['pacing']]
print(f"  战斗节奏合格: {len(action_ok)}章")

# ============ 重点章节详细 ============
print("\n" + "=" * 80)
print("四、重点章节详细分析（78、89、92、96、104）")
print("=" * 80)

for ch_num in focus_chapters:
    result = next((r for r in all_results if r['ch'] == ch_num), None)
    if not result:
        print(f"\n  第{ch_num}章：文件不存在")
        continue
    
    print(f"\n{'─' * 60}")
    print(f"  第{ch_num}章")
    print(f"{'─' * 60}")
    
    # 对话
    if result['dial_ratio'] == 0:
        dial_status = "🔴 0% 完全无对话"
    elif result['dial_ratio'] < 15:
        dial_status = f"🟡 {result['dial_ratio']:.1f}% 偏低"
    else:
        dial_status = f"🟢 {result['dial_ratio']:.1f}% 正常"
    
    print(f"  对话比例: {dial_status} | {result['dial_count']}处 | {result['total_chars']}字")
    
    # 章末
    print(f"  章末钩子: {result['ending_level']} (评分: {result['ending_score']})")
    if result['last_sents']:
        for i, s in enumerate(result['last_sents']):
            if len(s) > 60:
                s = s[:60] + "..."
            print(f"    结尾句{i+1}: {s}")
    
    # 战斗节奏
    print(f"  战斗场景: {result['action_count']}处 | {result['pacing']}")
    
    # 段落
    print(f"  最大段落: {result['max_para']}字")
    if result['long_paras']:
        print(f"  超长段落(>200字): {len(result['long_paras'])处 - 行号: {[p[0] for p in result['long_paras'][:5]]}")
    
    # AI腔
    if result['ai_tone']:
        ai_list = ', '.join([f"'{k}':{v}次" for k, v in result['ai_tone'].items()])
        print(f"  AI腔词汇: {ai_list}")
    
    # 综合建议
    print(f"  ── 建议 ──")
    suggestions = []
    if result['dial_ratio'] < 15:
        suggestions.append("增加角色对话交互，用对白推进情节而非纯叙述")
    if result['ending_level'] in ["⚪ 平淡收场", "🟠 弱钩子"]:
        suggestions.append("章末改为悬念/冲突/反转，留钩子吸引继续阅读")
    if result['pacing'].startswith("⚠️"):
        suggestions.append("战斗场景用更短句（<15字），一个动作一句话")
    if result['max_para'] > 200:
        suggestions.append(f"最长段落{result['max_para']}字，建议拆分")
    if '而是' in result.get('ai_tone', {}):
        suggestions.append(f"'而是'出现{result['ai_tone']['而是']}次，减少解释性连接词")
    if not suggestions:
        suggestions.append("本章质量较好，保持")
    for s in suggestions:
        print(f"    • {s}")

# ============ 其他问题章节 ============
print("\n" + "=" * 80)
print("五、其他需注意的章节")
print("=" * 80)

# 对话<15%的额外章节
others_low = [r for r in low_dialogue if r['ch'] not in focus_chapters]
if others_low:
    print(f"\n📝 对话<15%的其他章节：")
    for r in others_low:
        print(f"  第{r['ch']}章: {r['dial_ratio']:.1f}% | {r['total_chars']}字 | 建议: 增加角色对白")

# AI腔严重
print(f"\n🤖 AI腔词汇高频章节（'而是'≥5次）：")
for r in all_results:
    if r['ai_tone'].get('而是', 0) >= 5:
        print(f"  第{r['ch']}章: '而是'{r['ai_tone']['而是']}次 | 其他: {', '.join([f'{k}({v})' for k,v in r['ai_tone'].items() if k != '而是'])}")

# ============ 汇总统计 ============
print("\n" + "=" * 80)
print("六、第二卷统计汇总（56-105章，共50章）")
print("=" * 80)

total = len(all_results)
avg_dial = sum(r['dial_ratio'] for r in all_results) / total if total > 0 else 0
avg_score = sum(r['ending_score'] for r in all_results) / total if total > 0 else 0

print(f"  对话=0%:       {len(zero_dialogue)}章")
print(f"  对话<15%:      {len(low_dialogue)}章")
print(f"  平淡收场:      {len(flat_ending)}章")
print(f"  弱钩子:        {sum(1 for r in weak_ending if r['ending_level'] == '🟠 弱钩子')}章")
print(f"  中等钩子:      {sum(1 for r in weak_ending if r['ending_level'] == '🟡 中等钩子')}章")
print(f"  强钩子:        {len(strong_ending)}章")
print(f"  战斗节奏问题:  {len(pacing_issues)}章")
print(f"  平均对话比例:  {avg_dial:.1f}%")
print(f"  平均钩子评分:  {avg_score:.1f}")
print(f"  对话最高:      {sorted_by_dial[-1]['ch']}章 ({sorted_by_dial[-1]['dial_ratio']:.1f}%)")
print(f"  对话最低:      {sorted_by_dial[0]['ch']}章 ({sorted_by_dial[0]['dial_ratio']:.1f}%)")

print("\n" + "=" * 80)
print("报告完毕")
print("=" * 80)
