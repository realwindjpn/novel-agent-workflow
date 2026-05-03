#!/usr/bin/env python3
"""《科武纪元》第二卷（56-105章）节奏与对话审查脚本"""
import re
from pathlib import Path
from collections import Counter

BASE = Path('/workspace/科武纪元/新版')

# ============ 1. 对话比例统计 ============
def calc_dialogue_ratio(text):
    """计算对话占总字数的比例。对话定义为引号内内容（含""和""）"""
    cn_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    if cn_chars == 0:
        return 0.0, 0, 0
    # 匹配中文引号内对话
    dialogues = re.findall(r'[""「""][^""「""]{2,}[""」""]', text)
    dialogue_chars = sum(len(d) for d in dialogues)
    ratio = dialogue_chars / cn_chars * 100 if cn_chars > 0 else 0
    return ratio, dialogue_chars, cn_chars

# ============ 2. 章末钩子检测 ============
def check_ending_hook(text):
    """检查章末是否有力：悬念/冲突/反转/钩子 vs 平淡收场"""
    # 取最后500字
    ending = text[-500:] if len(text) > 500 else text
    
    # 钩子信号词
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
    
    hook_words = ['未完待续', '敬请期待', '...', '——', '：']
    
    suspense_count = sum(1 for w in suspense_words if w in ending)
    conflict_count = sum(1 for w in conflict_words if w in ending)
    reversal_count = sum(1 for w in reversal_words if w in ending)
    hook_count = sum(1 for w in hook_words if w in ending[-100:])
    
    # 结尾是问句或感叹句 → 有钩子
    ending_sent = ending[-200:]
    has_question = bool(re.search(r'[？?]', ending_sent))
    has_exclaim = bool(re.search(r'[！!]', ending_sent))
    
    # 以对话结尾 → 通常有力
    ends_with_dialogue = bool(re.search(r'[""」""][\s]*$', ending.strip()))
    
    score = suspense_count * 2 + conflict_count * 2 + reversal_count + hook_count + (2 if has_question else 0) + (1 if has_exclaim else 0) + (2 if ends_with_dialogue else 0)
    
    if score >= 8:
        level = "🔴 强钩子"
    elif score >= 4:
        level = "🟡 中等钩子"
    elif score >= 2:
        level = "🟠 弱钩子"
    else:
        level = "⚪ 平淡收场"
    
    # 提取最后3句话
    sentences = re.split(r'[。！？\n]+', ending.strip())
    last_sentences = [s.strip() for s in sentences if s.strip()][-3:]
    
    return level, score, last_sentences

# ============ 3. 战斗/紧张场景节奏检测 ============
def check_action_pacing(text):
    """检查战斗/紧张场景的节奏：短句比例、动作密度"""
    # 检测可能的战斗/紧张段落
    action_indicators = ['攻击', '防御', '躲避', '闪', '冲', '击', '刀', '剑',
                        '枪', '炮', '爆炸', '碎', '裂', '断', '闪', '避',
                        '追', '逃', '跑', '跳', '撞', '杀', '斗', '战',
                        '能量', '光束', '脉冲', '盾', '甲', '破', '轰']
    
    # 分段
    paragraphs = [p.strip() for p in text.split('\n') if p.strip() and len(p.strip()) > 10]
    
    action_paras = []
    for p in paragraphs:
        indicator_count = sum(1 for w in action_indicators if w in p)
        if indicator_count >= 2:
            action_paras.append((p, indicator_count))
    
    if not action_paras:
        return "无战斗场景", 0, []
    
    # 分析战斗段落的句子长度
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
        issues.append(f"平均句长{avg_sent_len:.0f}字，偏长（网文战斗建议<15字）")
    if short_sent_ratio < 20:
        issues.append(f"短句(≤10字)比例{short_sent_ratio:.0f}%，偏低（建议>30%）")
    
    pacing = "✅ 合格" if not issues else "⚠️ " + " | ".join(issues)
    return pacing, len(action_paras), action_paras[:3]  # 返回前3个战斗段落示例

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
print("=" * 80)
print("《科武纪元》第二卷（56-105章）节奏与对话审查报告")
print("=" * 80)

focus_chapters = [78, 89, 92, 96, 104]  # 重点审查章节
known_zero_dialogue = [78, 92, 104, 102, 96, 101, 105, 97]  # 已知0%对话

all_results = []
low_dialogue = []
zero_dialogue = []
flat_ending = []

for ch_num in range(56, 106):
    filepath = BASE / f'第{ch_num}章.md'
    if not filepath.exists():
        continue
    
    text = filepath.read_text(encoding='utf-8')
    
    # 1. 对话比例
    dial_ratio, dial_chars, total_chars = calc_dialogue_ratio(text)
    
    # 2. 章末钩子
    ending_level, ending_score, last_sents = check_ending_hook(text)
    
    # 3. 战斗节奏
    pacing, action_count, action_samples = check_action_pacing(text)
    
    # 4. AI腔
    ai_tone = check_ai_tone(text)
    
    # 5. 长段落
    max_para, long_paras = check_long_paragraphs(text)
    
    result = {
        'ch': ch_num,
        'dial_ratio': dial_ratio,
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

# ============ 输出总报告 ============
print("\n" + "=" * 80)
print("一、对话比例异常章节")
print("=" * 80)

if zero_dialogue:
    print(f"\n🔴 对话=0%的章节（共{len(zero_dialogue)}章）：")
    for r in zero_dialogue:
        focus_tag = "【重点】" if r['ch'] in focus_chapters else ""
        known_tag = "【已知】" if r['ch'] in known_zero_dialogue else ""
        print(f"  {focus_tag}{known_tag}第{r['ch']}章 | {r['total_chars']}字 | 对话比例: 0.0%")
        print(f"    → 建议：增加角色对白推进情节，至少加入2-3处对话交互")

if low_dialogue:
    print(f"\n🟡 对话<15%的章节（共{len(low_dialogue)}章）：")
    for r in low_dialogue:
        focus_tag = "【重点】" if r['ch'] in focus_chapters else ""
        print(f"  {focus_tag}第{r['ch']}章 | {r['total_chars']}字 | 对话比例: {r['dial_ratio']:.1f}%")
        print(f"    → 建议：增加角色互动，用对话替代部分叙述")

# ============ 章末钩子报告 ============
print("\n" + "=" * 80)
print("二、章末钩子审查")
print("=" * 80)

print(f"\n🔴 平淡收场的章节（共{len(flat_ending)}章）：")
for r in flat_ending:
    focus_tag = "【重点】" if r['ch'] in focus_chapters else ""
    print(f"  {focus_tag}第{r['ch']}章 | 钩子评分: {r['ending_score']} | {r['ending_level']}")
    if r['last_sents']:
        print(f"    结尾: {' | '.join(r['last_sents'][:2])}")
    print(f"    → 建议：章末改为悬念/冲突/反转，留钩子吸引继续阅读")

print(f"\n🟡 钩子较弱的章节（🟠 弱钩子 + 🟡 中等钩子）：")
for r in all_results:
    if r['ending_level'] in ["🟠 弱钩子", "🟡 中等钩子"]:
        focus_tag = "【重点】" if r['ch'] in focus_chapters else ""
        print(f"  {focus_tag}第{r['ch']}章 | 钩子评分: {r['ending_score']} | {r['ending_level']}")
        if r['last_sents']:
            print(f"    结尾: {' | '.join(r['last_sents'][:2])}")

print(f"\n🟢 强钩子章节（{sum(1 for r in all_results if r['ending_level'] == '🔴 强钩子')}章）：")
for r in all_results:
    if r['ending_level'] == "🔴 强钩子":
        focus_tag = "【重点】" if r['ch'] in focus_chapters else ""
        print(f"  {focus_tag}第{r['ch']}章 | 钩子评分: {r['ending_score']}")

# ============ 战斗节奏报告 ============
print("\n" + "=" * 80)
print("三、战斗/紧张场景节奏")
print("=" * 80)

for r in all_results:
    if r['action_count'] > 0 and '⚠️' in r['pacing']:
        focus_tag = "【重点】" if r['ch'] in focus_chapters else ""
        print(f"  {focus_tag}第{r['ch']}章 | 战斗段落{r['action_count']}处 | {r['pacing']}")

has_no_action = [r for r in all_results if r['action_count'] == 0]
print(f"\n  无战斗场景的章节：{len(has_no_action)}章（属正常，非战斗章无需战斗节奏）")

# ============ 逐章详细（重点章节） ============
print("\n" + "=" * 80)
print("四、重点章节详细分析")
print("=" * 80)

for ch_num in focus_chapters:
    result = next((r for r in all_results if r['ch'] == ch_num), None)
    if not result:
        print(f"\n  第{ch_num}章：文件不存在")
        continue
    
    print(f"\n--- 第{ch_num}章 ---")
    print(f"  总字数: {result['total_chars']}字")
    print(f"  对话比例: {result['dial_ratio']:.1f}% {'🔴 严重偏低(0%)' if result['dial_ratio']==0 else '🟡 偏低(<15%)' if result['dial_ratio']<15 else '✅ 正常'}")
    print(f"  章末钩子: {result['ending_level']} (评分: {result['ending_score']})")
    if result['last_sents']:
        print(f"  结尾三句: {' | '.join(result['last_sents'])}")
    print(f"  战斗场景: {result['action_count']}处 | 节奏: {result['pacing']}")
    print(f"  最大段落: {result['max_para']}字")
    if result['long_paras']:
        print(f"  超长段落(>200字): {len(result['long_paras'])}处")
    if result['ai_tone']:
        ai_list = ', '.join([f"'{k}':{v}次" for k, v in result['ai_tone'].items()])
        print(f"  AI腔词汇: {ai_list}")

# ============ 统计汇总 ============
print("\n" + "=" * 80)
print("五、第二卷统计汇总")
print("=" * 80)

total = len(all_results)
print(f"  扫描章节数: {total}章（56-105）")
print(f"  对话=0%: {len(zero_dialogue)}章")
print(f"  对话<15%: {len(low_dialogue)}章")
print(f"  平淡收场: {len(flat_ending)}章")
print(f"  有战斗节奏问题: {sum(1 for r in all_results if r['action_count'] > 0 and '⚠️' in r['pacing'])}章")

avg_dial = sum(r['dial_ratio'] for r in all_results) / total if total > 0 else 0
avg_score = sum(r['ending_score'] for r in all_results) / total if total > 0 else 0
print(f"  平均对话比例: {avg_dial:.1f}%")
print(f"  平均钩子评分: {avg_score:.1f}")

print("\n" + "=" * 80)
print("报告生成完毕")
print("=" * 80)
