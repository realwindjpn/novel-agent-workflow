# 机器门禁扫描器
# 输入：目标正文文件路径
# 输出：非PASS项列表（0=全过）

import sys, re, json
def cjk_count(s):
    return len(re.findall(r"[一-鿿]", s))
def has_bend_quote(s):
    return "，" in s or "、" in s or "‘" in s or "’" in s or "“" in s or "”" in s
def has_arabic_in_body(s):
    return re.search(r"\d", s) and not s.startswith("第") and not s.endswith("章")

with open(sys.argv[1]) as f:
    text = f.read()
lines = text.split("\n")
non_pass = []
for i, line in enumerate(lines,1):
    if cjk_count(line) < 3:
        non_pass.append(f"行{i}: 净中文<3")
    if has_bend_quote(line):
        non_pass.append(f"行{i}: 弯引号")
    if has_arabic_in_body(line) and "第" not in line:
        non_pass.append(f"行{i}: 阿拉伯数字非标题")
print(json.dumps(non_pass, ensure_ascii=False, indent=2))
print("CJK total:", cjk_count(text))
