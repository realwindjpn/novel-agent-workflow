#!/usr/bin/env python3
"""生成 302 作者席任务包。

关键防护：G4 的 plot 原文含公式句「不是X，而是Y」，实测作者席会照抄触门禁。
本脚本对素材段做脱毒改写，并加显式防污染声明，然后拿目标门禁正则回扫 prompt 自身。
"""
import json
import pathlib
import re
import sys

TASK = pathlib.Path('/root/workspace/科武纪元/任务运行态/20260828_kewu_selfcycle_daily')
KEWU = pathlib.Path('/root/workspace/科武纪元')
rel = json.loads((TASK / 'output' / 'G4_RELEASE_302.json').read_text(encoding='utf-8'))

prev = (KEWU / '已投稿' / '第301章.txt').read_text(encoding='utf-8')
prev_body = prev.split('作者有话说：')[0].strip()

hg = rel['author_hard_gate']

# ===== plot 脱毒：去掉公式句结构，保留信息 =====
PLOT_DETOXED = """301 的联盟只是火星本地框架，管得住值守与核查，管不住权属。分水岭落在泛际会议全体会期：《戴森球合作宪章》付表决，一百八十二票赞成通过，确立全人类共建原则，并设立泛际会议太空技术监督委员会作为常设机构。

主戏在联邦的三轮闭门谈判。联邦握有否决权。第一轮争条文措辞，第二轮争豁免边界，第三轮才碰到真价码——监督委员会的席位与核查权怎么落，宪章条文本身一个字都没动。联邦最终放弃否决。放弃的理由与被说服无关：没人愿意在记录上留下否决文明未来的那一票。否决权在这一刻反过来成了共识的催化剂，因为它把责任精确标注到投票人头上。安理会五常一致赞成。

方宁一线出席但只作技术陈述：戴森球全技术链路的完整性属于工程约束，不属于政治口号；能源、算力、制造任一段被单方切断则整链归零。他给出的仍是既有账目——缺口一百四十千瓦未消、L1 阵列设计九百四十九千瓦、三一九开尔文硬线，并明确宪章通过不等于电力到位。韩铮与陈思琪提交的火星核查口径成为监督委员会的首份技术附件底稿。

收束：宪章通过之后，泛际会议的性质变了。此前各方带着诉求来协商，此后它有常设机构、有核查权、有履约义务，成为一个治理结构。但纸面权力落地要时间，第一批监督席位还没坐满，L1 授权仍在流程里。章末为 303 留口：宪章通过后，第一环组装的政治条件才终于齐备。"""

lines = []
A = lines.append

A('你是《科武纪元》的作者。写第302章《戴森共识》正文。')
A('')
A('【最重要的一条：素材是参考的意思，不是照抄的句子】')
A('下面所有素材段、上一章正文、剧情纲要，都只提供信息与语境。')
A('你必须用自己的句式重写。素材里若残留「不是X，而是Y」「不是X，是Y」这类结构，')
A('一律改写为单向陈述句或两个独立短句。这条是硬门禁，撞了直接返修。')
A('')
A('【硬门禁（逐条自查后再交稿）】')
A('- 首行必须是：%s' % hg['first_line'])
A('- 末行必须是：%s' % hg['last_line'])
A('- 净中文字数目标 %d—%d，硬下限 %d' % (hg['net_cjk_target'][0], hg['net_cjk_target'][1], hg['net_cjk_min']))
A('- 拉丁字母只允许出现：%s' % '、'.join(hg['no_latin_except']))
A('- 代词：%s' % hg['pronoun_rule'])
A('- 文体：%s' % hg['style_ban'])
A('- 必须出现的硬数字：%s' % '、'.join(hg['hard_numbers_required']))
A('- 正文纯文本，不含 Markdown、井号、星号、项目符号、过程语')
A('- 不写作者有话说（另派）')
A('')
A('【禁项（全部为硬性）】')
for f in rel['forbidden']:
    A('- %s' % f)
A('')
A('【角色边界】')
for k, v in rel['role_boundaries'].items():
    A('- %s：%s' % (k, v))
A('')
A('【上一章（301《联合防御》）结束时锁定的状态】')
for h in rel['handoff_from_301_locked_state']:
    A('- %s' % h)
A('')
A('【本章剧情纲要（信息用，句式须重写）】')
A(PLOT_DETOXED)
A('')
A('【大纲原始条目（口径参考）】')
A(str(rel.get('outline_raw', '')))
A('')
A('【写作要求】')
A('1. 场景要有物理落点：会场、闭门谈判室、技术陈述席、火星岗位，各有具体动作与器物。')
A('2. 表决与谈判写程序细节：轮次、条文编号、签返时限、记录员落笔、确认灯，不写情绪渲染。')
A('3. 方宁的技术陈述用数字说话，不作政治表态；周棠一句话卡住「通过即到位」的错觉。')
A('4. 联邦放弃否决的动机落在记录责任上，用程序与文本痕迹体现，不由叙述者解释。')
A('5. 长短句交替，段落收束方式不得同调复现。')
A('6. 不替角色下全知定论，未确认的事保持未确认。')
A('')
A('【上一章正文全文（承接语境用，不要复述其情节）】')
A(prev_body)

prompt = '\n'.join(lines)

# ===== 拿目标门禁正则回扫 prompt 自身 =====
FORMULA_RE = re.compile(r'不是[^。；\n]{0,25}[，,]?\s*(而)?是')
BANNED = ['真正', '核心', '关键', '意味着', '赋能', '生态闭环']

# 只扫「素材与要求」段，排除明确列为禁项说明的行
scan_lines = []
for l in prompt.split('\n'):
    if l.startswith('- 文体：') or '一律改写为单向陈述句' in l or '这类结构' in l:
        continue
    if l.startswith('- 禁') or l.startswith('- 不得'):
        continue
    scan_lines.append(l)
scan = '\n'.join(scan_lines)

hits = FANHITS = FORMULA_RE.findall(scan)
formula_lines = [l for l in scan_lines if FORMULA_RE.search(l)]
banned_lines = {w: [l[:90] for l in scan_lines if w in l] for w in BANNED}
banned_lines = {k: v for k, v in banned_lines.items() if v}

print('=== prompt 自扫（防污染）===')
print('公式句命中行数:', len(formula_lines))
for l in formula_lines:
    print('   !', l[:120])
print('禁词命中:', list(banned_lines.keys()))
for w, ls in banned_lines.items():
    for l in ls:
        print('   !', w, '|', l)

out = TASK / 'output' / 'AUTHOR_302_PROMPT.md'
out.write_text(prompt, encoding='utf-8')
print('\nwrote', out, out.stat().st_size, 'bytes')
print('prev_body_chars', len(prev_body))
print('total_prompt_chars', len(prompt))

clean = not formula_lines and not banned_lines
print('\nPROMPT_CLEAN' if clean else '\nPROMPT_HAS_CONTAMINATION')
sys.exit(0 if clean else 1)
