#!/usr/bin/env python3
"""第259章确定性机检：首末行、引号规范、禁词零容忍、净中文、承上锚点、大纲剧情链。"""
import hashlib
import json
import re
import sys

PATH = sys.argv[1] if len(sys.argv) > 1 else '新版/第259章.md'

text = open(PATH, encoding='utf-8').read()
lines = [l.rstrip('\n') for l in text.split('\n')]
non_empty = [l for l in lines if l.strip()]

result = {"path": PATH, "checks": {}, "hard_failures": []}


def check(name, ok, detail=""):
    result["checks"][name] = {"ok": bool(ok), "detail": detail}
    if not ok:
        result["hard_failures"].append(name)


# 1. 首行 / 末行
first, last = non_empty[0].strip(), non_empty[-1].strip()
check("first_line", bool(re.match(r'^第\d+章\s+\S+', first)), first)
check("last_line", last == '（本章完）', last)

# 2. 引号统计（仅信息项，非门禁）
# 项目既往实态：256/257/258 均以 ASCII 双引号定稿并入草稿箱（118/116/146 处），
# 故 ASCII 双引号不构成硬失败。禁自造更严门禁（AGENTS.md）。
ascii_dq = text.count('"')
result["info_ascii_double_quote"] = ascii_dq
# 引号必须成对，奇数即真错
check("quote_balanced", ascii_dq % 2 == 0, f'count={ascii_dq}')

# 3. 禁词零容忍
FORBIDDEN = ['AI', '人工智能', 'ChatGPT', '算法', '神经网络', '深度学习',
             '机器学习', '大模型', '智能体']
hits = {w: text.count(w) for w in FORBIDDEN if w in text}
check("forbidden_words", not hits, json.dumps(hits, ensure_ascii=False))

# 4. wikilink
wl = re.findall(r'\[\[[^\]]+\]\]', text)
check("no_wikilink", not wl, f'count={len(wl)}')

# 5. 字数硬线 >= 3000
# 口径校准（工具脚本/_calibrate_fanqie_wordcount.py，三样本平均误差 9 字）：
# 番茄列表字数 = 正文去空白字符数，不含「作者有话说」段。
# CJK-only 口径会低估约 500-600 字，不可用于判定硬线。
def _strip_author_note(t: str) -> str:
    for marker in ('作者有话说', '作者说：', '作者的话'):
        i = t.find(marker)
        if i != -1:
            return t[:i]
    return t


body = _strip_author_note(text)
fanqie_chars = len(re.sub(r'\s', '', body))
cjk = len(re.findall(r'[\u4e00-\u9fff]', text))
check("fanqie_chars_min_3000", fanqie_chars >= 3000,
      f'fanqie_chars={fanqie_chars} (cjk_only={cjk}, 仅参考)')

# 6. 章节身份：不得出现错稿元素
WRONG = ['欧罗巴', '木卫二', '木星', '李维']
wrong_hits = {w: text.count(w) for w in WRONG if w in text}
check("chapter_identity", not wrong_hits, json.dumps(wrong_hits, ensure_ascii=False))

# 7. 大纲 L467 剧情链锚点
CHAIN = {
    "破冰钻探": r'钻头|钻探|钻杆|冰层',
    "半埋建筑群": r'建筑群|半埋|结构',
    "风格迥异非人类": r'不像人|不像任何人类|一体成型',
    "未知合金": r'合金|识别不了|元素库',
    "百万年测年": r'一百一十七万年|万年',
    "太极生物电": r'太极|生物电|净脉',
    "光合效率": r'光合|类囊体|光系统',
    "闭合度73到91": r'七十三|九十一|闭合度',
    "平息暴动": r'配给恢复|矿工|老周',
    "首次非战斗用途": r'头一回|只用来打过架|第一次',
}
missing = [k for k, pat in CHAIN.items() if not re.search(pat, text)]
check("outline_chain_L467", not missing, f'missing={missing}')

# 8. 承上锚点（258 结尾）
UP = {
    "三十天": r'三十天',
    "一千八百公里": r'一千八百公里',
    "沙尘暴": r'沙尘暴',
    "辐射计2.1": r'2\.1毫希沃特',
    "氧气产率54": r'百分之五十四',
}
up_missing = [k for k, pat in UP.items() if not re.search(pat, text)]
check("upstream_anchors_ch258", not up_missing, f'missing={up_missing}')

# 9. 启下留白：259 不得写铁幕突袭/数据争夺（那是 260）
DOWN_LEAK = {w: text.count(w) for w in ['铁幕', '数据争夺', '突袭'] if w in text}
check("no_ch260_leak", not DOWN_LEAK, json.dumps(DOWN_LEAK, ensure_ascii=False))

result["cjk"] = cjk
result["total_chars"] = len(text)
result["sha256"] = hashlib.sha256(text.encode('utf-8')).hexdigest()
result["gate_pass"] = not result["hard_failures"]

print(json.dumps(result, ensure_ascii=False, indent=2))
