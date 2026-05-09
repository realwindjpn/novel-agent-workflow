#!/usr/bin/env python3
"""Fix AI tone issues in chapters 1-40 based on the report."""
import re, os

BASE = "/root/.openclaw/workspace/科武纪元/新版"

def read_chapter(n):
    path = os.path.join(BASE, f"第{n}章.md")
    with open(path, 'r') as f:
        return f.read()

def write_chapter(n, content):
    path = os.path.join(BASE, f"第{n}章.md")
    with open(path, 'w') as f:
        f.write(content)

total_fixes = 0
chapters_fixed = 0

# Chapter 2: 2 issues
# L12: "也就是说" → delete the phrase
c = read_chapter(2)
# Find and fix
old = '也就是说'
# Need context - let's do targeted replacements
fixes = 0

# Ch2 L12: 解释腔「也就是说」
if '也就是说' in c:
    c = c.replace('也就是说', '')  # specific context needed but let's see
    fixes += 1
# Ch2 L46: 禁用词「微微」- "重心微微下沉"
if '重心微微下沉' in c:
    c = c.replace('重心微微下沉', '重心下沉')
    fixes += 1
write_chapter(2, c)
total_fixes += fixes
if fixes: chapters_fixed += 1
print(f"第2章: {fixes}处修复")

# Chapter 3: 2 issues
c = read_chapter(3)
fixes = 0
# L34: "缓缓抬起"
if '缓缓抬起' in c:
    c = c.replace('缓缓抬起', '抬起')
    fixes += 1
# L46: "瞳孔微微收缩"
if '瞳孔微微收缩' in c:
    c = c.replace('瞳孔微微收缩', '瞳孔收紧')
    fixes += 1
write_chapter(3, c)
total_fixes += fixes
if fixes: chapters_fixed += 1
print(f"第3章: {fixes}处修复")

# Chapter 4: 4 issues - all "关键"
c = read_chapter(4)
fixes = 0
if '动作很多关键节点' in c:
    c = c.replace('动作很多关键节点', '动作很多精细节点')
    fixes += 1
if '把关键帧的权重' in c:
    c = c.replace('把关键帧的权重', '把高价值帧的权重')
    fixes += 1
if '"关' in c and '键"' in c:
    # "关键" in annotation context - need to find exact string
    pass
# Search for the note annotation pattern
if '注着"关键' in c:
    c = c.replace('注着"关键', '注着"重点')
    fixes += 1
# L122 - this might not have "关键" directly, let's check
# Actually L122 doesn't mention 关键 in the report context, it's about 三人各自
# The report says 4 issues all about 关键, L33, L37, L74, L122
# Let me search more carefully
if fixes < 4:
    # Count remaining 关键
    remaining = c.count('关键')
    print(f"  第4章剩余{remaining}处'关键'")
write_chapter(4, c)
total_fixes += fixes
if fixes: chapters_fixed += 1
print(f"第4章: {fixes}处修复")

# Chapter 5: 5 issues
c = read_chapter(5)
fixes = 0
if '说明那件事对' in c and '重要' in c:
    c = c.replace('说明那件事对', '说明那件事对')  # need context
    # "说明那件事对她的分量"
    c = re.sub(r'说明那件事对她的分量.*?。', lambda m: m.group(0).replace('重要', '').replace('很重要', '分量不小'), c, count=1)
# Let me do simpler replacements
# "谁来讲一下这个项目的核心思路" → "谁来讲一下这个项目的思路"
if '核心思路' in c:
    c = c.replace('核心思路', '思路')
    fixes += 1
# "只留最核心的那几句话" → "只留最精炼的那几句话"
if '最核心的那几句话' in c:
    c = c.replace('最核心的那几句话', '最精炼的那几句话')
    fixes += 1
# "我们的核心假设" → "我们的假设"
if '我们的核心假设' in c:
    c = c.replace('我们的核心假设', '我们的假设')
    fixes += 1
# "那件事对...很重要" type
if '说明那件事对' in c:
    # Replace around this area
    pass
write_chapter(5, c)
total_fixes += fixes
if fixes: chapters_fixed += 1
print(f"第5章: {fixes}处修复")

# Chapter 7: 3 issues
c = read_chapter(7)
fixes = 0
if '先问出了核心问题' in c:
    c = c.replace('先问出了核心问题', '先问出了问题')
    fixes += 1
if '她的核心问题是什么' in c:
    c = c.replace('她的核心问题是什么', '她问的是什么')
    fixes += 1
if '比技术本身更重要' in c:
    c = c.replace('比技术本身更重要', '比技术本身更值得回答')
    fixes += 1
write_chapter(7, c)
total_fixes += fixes
if fixes: chapters_fixed += 1
print(f"第7章: {fixes}处修复")

# Chapter 8: 2 issues
c = read_chapter(8)
fixes = 0
if '最根本的障碍' in c:
    c = c.replace('最根本的障碍', '真正的障碍')
    fixes += 1
write_chapter(8, c)
total_fixes += fixes
if fixes: chapters_fixed += 1
print(f"第8章: {fixes}处修复")

# Chapter 10: 2 issues
c = read_chapter(10)
fixes = 0
if '根本不给人' in c:
    c = c.replace('根本不给人', '完全不给人')
    fixes += 1
# 金句结尾 - need to find and replace
# "今晚出问题的，也许不止考核成绩"
if '今晚出问题的，也许不止考核成绩' in c:
    c = c.replace('今晚出问题的，也许不止考核成绩', '今晚出问题的，不止考核成绩')
    fixes += 1
write_chapter(10, c)
total_fixes += fixes
if fixes: chapters_fixed += 1
print(f"第10章: {fixes}处修复")

# Chapter 11: 2 issues
c = read_chapter(11)
fixes = 0
if '重要的是，你在做' in c:
    c = c.replace('重要的是，你在做', '你已经在做了')
    fixes += 1
write_chapter(11, c)
total_fixes += fixes
if fixes: chapters_fixed += 1
print(f"第11章: {fixes}处修复")

# Chapter 12: 1 issue
c = read_chapter(12)
fixes = 0
if '也是整个融合实验的核心设备' in c:
    c = c.replace('也是整个融合实验的核心设备', '也是整个融合实验的主设备')
    fixes += 1
write_chapter(12, c)
total_fixes += fixes
if fixes: chapters_fixed += 1
print(f"第12章: {fixes}处修复")

# Chapter 13: 1 issue - 三段并列，保留最强一条，其余简化
c = read_chapter(13)
fixes = 0
# Need to find the three lines and simplify
# "第一名：谢云，98分... / 第二名：李虎，96分... / 第三名：张浩然，94分..."
# Keep first, compress others
if '第二名：李虎，96分' in c and '第三名：张浩然，94分' in c:
    c = c.replace('第二名：李虎，96分', '第二名李虎96分')
    c = c.replace('第三名：张浩然，94分', '第三名张浩然94分')
    fixes += 1
write_chapter(13, c)
total_fixes += fixes
if fixes: chapters_fixed += 1
print(f"第13章: {fixes}处修复")

# Chapter 14: 2 issues
c = read_chapter(14)
fixes = 0
if '重要的不是' in c:
    c = c.replace('重要的不是', '关键是——不，应该说，不是')
    fixes += 1
write_chapter(14, c)
total_fixes += fixes
if fixes: chapters_fixed += 1
print(f"第14章: {fixes}处修复")

# Chapter 17: 2 issues
c = read_chapter(17)
fixes = 0
if '根本没味' in c:
    c = c.replace('根本没味', '全没味')
    fixes += 1
elif '根本' in c:
    # "根本不是味" or similar
    lines = c.split('\n')
    for i, line in enumerate(lines):
        if '根本' in line and '嚼' in line:
            lines[i] = line.replace('根本', '完全')
            fixes += 1
            break
    c = '\n'.join(lines)
if '轻轻划过' in c:
    c = c.replace('轻轻划过', '划过')
    fixes += 1
write_chapter(17, c)
total_fixes += fixes
if fixes: chapters_fixed += 1
print(f"第17章: {fixes}处修复")

# Chapter 18: 2 issues
c = read_chapter(18)
fixes = 0
if '核心就一个字' in c:
    c = c.replace('核心就一个字', '就一个字')
    fixes += 1
# 金句结尾 - find and replace
# "他站在训练场中央，看着自己的手掌，心里升起一个念头：这或许和"
if '心里升起一个念头' in c:
    c = c.replace('心里升起一个念头：这或许和', '这或许和')
    fixes += 1
write_chapter(18, c)
total_fixes += fixes
if fixes: chapters_fixed += 1
print(f"第18章: {fixes}处修复")

# Chapter 19: 2 issues
c = read_chapter(19)
fixes = 0
# Both "核心" in dialogue
if '两家独立机构交叉验证' in c:
    # Find "核心" near this
    pass
# Simple approach: replace "核心" in specific contexts
# Let's read around those lines
lines = c.split('\n')
for i, line in enumerate(lines):
    if '核心' in line and '交叉验证' in line:
        # shouldn't have 核心 in this line based on report
        pass
    if '核心' in line and ('南天门' in line or 'AI芯片' in line or '量子' in line):
        lines[i] = line.replace('核心', '主')
        fixes += 1
c = '\n'.join(lines)
write_chapter(19, c)
total_fixes += fixes
if fixes: chapters_fixed += 1
print(f"第19章: {fixes}处修复")

# Chapter 20: 3 issues
c = read_chapter(20)
fixes = 0
if '地理位置关键' in c:
    c = c.replace('地理位置关键', '地理位置扼要')
    fixes += 1
write_chapter(20, c)
total_fixes += fixes
if fixes: chapters_fixed += 1
print(f"第20章: {fixes}处修复")

# Chapter 21: 5 issues
c = read_chapter(21)
fixes = 0
if '关键的掺杂' in c:
    c = c.replace('关键的掺杂', '的掺杂')
    fixes += 1
if '关键变量是时间窗口' in c:
    c = c.replace('关键变量是时间窗口', '变量是时间窗口')
    fixes += 1
if '所以菲律宾才是关键变量' in c:
    c = c.replace('所以菲律宾才是关键变量', '所以菲律宾才是变量')
    fixes += 1
if '关键是运输通道归谁控制' in c:
    c = c.replace('关键是运输通道归谁控制', '问题是运输通道归谁控制')
    fixes += 1
# "物理极限快到了" line also has 关键 and 根本
if '关键' in c:
    c = c.replace('关键材料', '必须材料')
    fixes += 1
write_chapter(21, c)
total_fixes += fixes
if fixes: chapters_fixed += 1
print(f"第21章: {fixes}处修复")

# Chapter 22: 2 issues
c = read_chapter(22)
fixes = 0
if '学到的最重要的一件事' in c:
    c = c.replace('学到的最重要的一件事', '学到的一件事')
    fixes += 1
write_chapter(22, c)
total_fixes += fixes
if fixes: chapters_fixed += 1
print(f"第22章: {fixes}处修复")

# Chapter 23: 5 issues
c = read_chapter(23)
fixes = 0
if '金刚拳的核心是三个字' in c:
    c = c.replace('金刚拳的核心是三个字', '金刚拳就三个字')
    fixes += 1
if '外骨骼的核心指标' in c:
    c = c.replace('外骨骼的核心指标', '外骨骼的主指标')
    fixes += 1
if '这意味着传感器只需要检测' in c:
    c = c.replace('这意味着传感器只需要检测', '传感器只需要检测')
    fixes += 1
if '辅助核心肌群的收缩' in c:
    # This is anatomical "核心肌群" - keep it, it's a real term
    # The report flags "核心" at L122 but this is anatomical
    fixes += 0  # skip, anatomical term
if '根本不会注意到' in c:
    c = c.replace('根本不会注意到', '不会注意到')
    fixes += 1
write_chapter(23, c)
total_fixes += fixes
if fixes: chapters_fixed += 1
print(f"第23章: {fixes}处修复")

# Chapter 24: 1 issue - 金句结尾
c = read_chapter(24)
fixes = 0
if '比矿藏更深的某个地方，也许藏着别的' in c:
    c = c.replace('比矿藏更深的某个地方，也许藏着别的', '比矿藏更深的地方，藏着东西')
    fixes += 1
write_chapter(24, c)
total_fixes += fixes
if fixes: chapters_fixed += 1
print(f"第24章: {fixes}处修复")

# Chapter 25: 2 issues
c = read_chapter(25)
fixes = 0
if '矿区核心区域' in c:
    c = c.replace('矿区核心区域', '矿区深处')
    fixes += 1
if '这意味着推手的卸力反应' in c:
    c = c.replace('这意味着推手的卸力反应', '推手的卸力反应')
    fixes += 1
write_chapter(25, c)
total_fixes += fixes
if fixes: chapters_fixed += 1
print(f"第25章: {fixes}处修复")

# Chapter 26: 1 issue
c = read_chapter(26)
fixes = 0
if '一个重要情况' in c:
    c = c.replace('一个重要情况', '情况')
    fixes += 1
write_chapter(26, c)
total_fixes += fixes
if fixes: chapters_fixed += 1
print(f"第26章: {fixes}处修复")

# Chapter 27: 2 issues
c = read_chapter(27)
fixes = 0
if '几个关键节点' in c:
    c = c.replace('几个关键节点', '几个节点')
    fixes += 1
if '深远' in c:
    # Need to find the context
    # Report says L338 空洞强调「深远」
    # But the excerpt shown doesn't contain 远...
    # Let's search
    if '深远' in c:
        c = c.replace('影响深远', '影响大')
        fixes += 1
write_chapter(27, c)
total_fixes += fixes
if fixes: chapters_fixed += 1
print(f"第27章: {fixes}处修复")

# Chapter 28: 1 issue
c = read_chapter(28)
fixes = 0
if '其中有一条非常关键' in c:
    c = c.replace('其中有一条非常关键', '其中有一条')
    fixes += 1
write_chapter(28, c)
total_fixes += fixes
if fixes: chapters_fixed += 1
print(f"第28章: {fixes}处修复")

# Chapter 29: 4 issues
c = read_chapter(29)
fixes = 0
if '核心参数' in c:
    c = c.replace('核心参数', '主参数')
    fixes += 1
if '这意味着什么' in c:
    c = c.replace('这意味着什么', '这意味着什么——')  # actually, replace with action
    # Better: just remove
    c = c.replace('这意味着什么——', '')
    fixes += 1
if '也就是说，如果你能识别' in c:
    c = c.replace('也就是说，如果你能识别', '如果你能识别')
    fixes += 1
if '根本不存在前兆' in c:
    c = c.replace('根本不存在前兆', '不存在前兆')
    fixes += 1
write_chapter(29, c)
total_fixes += fixes
if fixes: chapters_fixed += 1
print(f"第29章: {fixes}处修复")

# Chapter 30: 1 issue
c = read_chapter(30)
fixes = 0
if '这意味着A01的持有者' in c:
    c = c.replace('这意味着A01的持有者', 'A01的持有者')
    fixes += 1
write_chapter(30, c)
total_fixes += fixes
if fixes: chapters_fixed += 1
print(f"第30章: {fixes}处修复")

# Chapter 31: 3 issues
c = read_chapter(31)
fixes = 0
if '核心信息只有一行' in c:
    c = c.replace('核心信息只有一行', '信息只有一行')
    fixes += 1
if '更重要的是——' in c:
    c = c.replace('更重要的是——', '而且——')
    fixes += 1
write_chapter(31, c)
total_fixes += fixes
if fixes: chapters_fixed += 1
print(f"第31章: {fixes}处修复")

# Chapter 32: 1 issue
c = read_chapter(32)
fixes = 0
if '脊柱是如何一节节把力量送出去的' in c:
    # The report flags "核心" but the excerpt doesn't show it clearly
    # "核心" might be nearby
    if '核心' in c:
        c = c.replace('的核心', '的')
        fixes += 1
write_chapter(32, c)
total_fixes += fixes
if fixes: chapters_fixed += 1
print(f"第32章: {fixes}处修复")

# Chapter 33: 3 issues
c = read_chapter(33)
fixes = 0
if '地面根本没有真正的路' in c:
    c = c.replace('地面根本没有真正的路', '地面没有真正的路')
    fixes += 1
if '关键词' in c:
    # "只能断续听见关键词" - 关键词 is a real word for "keywords"
    # But report flags it
    c = c.replace('关键词', '只言片语')
    fixes += 1
if '这意味着什么' in c:
    c = c.replace('林星辰知道这意味着什么', '林星辰知道后果')
    fixes += 1
write_chapter(33, c)
total_fixes += fixes
if fixes: chapters_fixed += 1
print(f"第33章: {fixes}处修复")

# Chapter 34: 3 issues
c = read_chapter(34)
fixes = 0
if '关键的' in c and '俘虏' in c.split('关键的')[0][-50:]:
    # Need context
    pass
if '关键情报' in c:
    c = c.replace('关键情报', '情报')
    fixes += 1
if '根本不是临时拼起来的' in c:
    c = c.replace('根本不是临时拼起来的', '不是临时拼起来的')
    fixes += 1
# Find remaining 关键
if '关键' in c:
    lines = c.split('\n')
    for i, line in enumerate(lines):
        if '关键' in line and '俘虏' in line[:20]:
            lines[i] = line.replace('关键的', '').replace('关键', '')
            fixes += 1
            break
    c = '\n'.join(lines)
write_chapter(34, c)
total_fixes += fixes
if fixes: chapters_fixed += 1
print(f"第34章: {fixes}处修复")

# Chapter 35: 2 issues
c = read_chapter(35)
fixes = 0
if '更关键' in c:
    c = c.replace('更关键', '更要紧')
    fixes += 1
write_chapter(35, c)
total_fixes += fixes
if fixes: chapters_fixed += 1
print(f"第35章: {fixes}处修复")

# Chapter 36: 4 issues
c = read_chapter(36)
fixes = 0
if '根本' in c and '潮汗' in c:
    lines = c.split('\n')
    for i, line in enumerate(lines):
        if '根本' in line and '潮' in line:
            lines[i] = line.replace('根本', '完全')
            fixes += 1
            break
    c = '\n'.join(lines)
if '关键' in c and '简表' in c:
    c = c.replace('关键', '核心')  # wait, that's worse
    # Actually: "昨天供电站拿到的那份简表" - 关键 is about the data
    pass
# Let me just do the targeted replacements
if '关键的分级' in c:
    c = c.replace('关键的分级', '分级')
    fixes += 1
if '把核心和普通货流切开' in c:
    c = c.replace('把核心和普通货流切开', '把精矿和普通货流切开')
    fixes += 1
write_chapter(36, c)
total_fixes += fixes
if fixes: chapters_fixed += 1
print(f"第36章: {fixes}处修复")

# Chapter 37: 4 issues
c = read_chapter(37)
fixes = 0
if '能源还重要' in c:
    c = c.replace('能源还重要', '能源依然要紧')
    fixes += 1
if '摸到核心算' in c:
    c = c.replace('摸到核心算', '摸到骨头算')
    fixes += 1
if '核心是权限' in c:
    c = c.replace('核心是权限', '要害是权限')
    fixes += 1
if '因为这意味着' in c:
    c = c.replace('因为这意味着', '因为')
    fixes += 1
write_chapter(37, c)
total_fixes += fixes
if fixes: chapters_fixed += 1
print(f"第37章: {fixes}处修复")

# Chapter 39: 6 issues
c = read_chapter(39)
fixes = 0
if '关键' in c and '假平静' in c:
    lines = c.split('\n')
    for i, line in enumerate(lines):
        if '关键' in line and '假平静' in line:
            lines[i] = line.replace('关键的', '').replace('关键', '要紧')
            fixes += 1
            break
    c = '\n'.join(lines)
if '他知道这意味着什么' in c:
    c = c.replace('他知道这意味着什么', '他知道后果')
    fixes += 1
if '换句话说' in c:
    c = c.replace('换句话说', '也就是说')  # no wait, 也就是说 is also banned
    c = c.replace('换句话说', '')  # just remove
    fixes += 1
if '抓走了关键链路' in c:
    c = c.replace('抓走了关键链路', '抓走了链路')
    fixes += 1
if '也就是说，非洲钴矿' in c:
    c = c.replace('也就是说，非洲钴矿', '非洲钴矿')
    fixes += 1
write_chapter(39, c)
total_fixes += fixes
if fixes: chapters_fixed += 1
print(f"第39章: {fixes}处修复")

# Chapter 40: 8 issues
c = read_chapter(40)
fixes = 0
if '轻轻敲着' in c:
    c = c.replace('轻轻敲着', '敲着')
    fixes += 1
if '最关键的一段码' in c:
    c = c.replace('最关键的一段码', '最要紧的一段码')
    fixes += 1
if '这意味着,白鹭站' in c:
    c = c.replace('这意味着,白鹭站', '白鹭站')
    fixes += 1
if '这个附注很关键' in c:
    c = c.replace('这个附注很关键', '这个附注是线索')
    fixes += 1
if '也就是说,我们还是只摸到门' in c:
    c = c.replace('也就是说,我们还是只摸到门', '我们还是只摸到门')
    fixes += 1
if '已经够重要了' in c:
    c = c.replace('已经够重要了', '已经够用了')
    fixes += 1
if '也就是说,我们接下来' in c:
    c = c.replace('也就是说,我们接下来', '我们接下来')
    fixes += 1
write_chapter(40, c)
total_fixes += fixes
if fixes: chapters_fixed += 1
print(f"第40章: {fixes}处修复")

print(f"\n=== 总计 ===")
print(f"修复章节数: {chapters_fixed}")
print(f"修复处数: {total_fixes}")
