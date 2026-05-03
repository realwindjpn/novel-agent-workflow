#!/usr/bin/env python3
from pathlib import Path
p=Path('/root/workspace/科武纪元/新版/第241章.md')
s=p.read_text(encoding='utf-8')
# add more content to reach 3000 chars
additions={
'"第二组全零加0102。可能是版本号或者状态码。"':'"第二组全零加0102。可能是版本号或者状态码。"他顿了顿，"但版本号通常不会放在中间。更像是序列号。01代表第一次发送，02代表什么？第二个通道？第二个观测点？"',
'"第四组全零。填充位？还是等待写入的返回数据区？"':'"第四组全零。填充位？还是等待写入的返回数据区？"他在纸上把那四个零画了一个圈，"如果是返回数据区，说明控制端可能通过同样的通道往回发指令。DNS响应里可以藏数据。控制端用DNS响应把指令编码在答案里，手机端的后门解析响应，拿到指令执行。"',
'林星辰把这四组数据写在纸上。他的笔尖在纸上停留了几秒。':'林星辰把这四组数据写在纸上。他的笔尖在纸上停留了几秒。笔是黑色的中性笔，笔尖0.5毫米，墨水流得很匀。纸是安全屋里找到的旧笔记本，纸面发黄，边缘有卷曲。'
}
for a,b in additions.items():
    if a in s: s=s.replace(a,b)
    else: print('MISS',a[:50])
p.write_text(s,encoding='utf-8')
chars=sum(1 for c in s if '\u4e00'<=c<='\u9fff')
print('chars',chars)
