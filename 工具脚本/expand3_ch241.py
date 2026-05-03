#!/usr/bin/env python3
from pathlib import Path
p=Path('/root/workspace/科武纪元/新版/第241章.md')
s=p.read_text(encoding='utf-8')
# add more content
additions={
'脚本开始跑。树莓派的风扇转速上去了，嗡嗡声比之前大了不少。CPU温度从四十二度升到六十七度。进度条走得慢。ARM架构编译C++代码本来就不快，树莓派的散热也一般。':'脚本开始跑。树莓派的风扇转速上去了，嗡嗡声比之前大了不少。CPU温度从四十二度升到六十七度。进度条走得慢。ARM架构编译C++代码本来就不快，树莓派的散热也一般。林泽远从抽屉里翻出一个小USB风扇，插在树莓派旁边，对着CPU那片吹。风速不大，但至少能让热气散得快一点。',
'他坐在椅子上等。椅子还是那把木头的，靠背很直，硌得脊椎生疼。':'他坐在椅子上等。椅子还是那把木头的，靠背很直，硌得脊椎生疼。他把笔记本摊在腿上，膝盖顶着桌子的边缘。桌腿有一条不平，他随手折了一小片硬纸板垫在下面。桌子稳了一些。',
'"除非。"':'"除非。"他从口袋里摸出一块巧克力，是昨天在高铁站便利店买的。包装纸皱了，巧克力已经有点发软。他掰了一半放进嘴里，甜得发腻。剩下的放回口袋。'
}
for a,b in additions.items():
    if a in s: s=s.replace(a,b)
    else: print('MISS',a[:50])
p.write_text(s,encoding='utf-8')
chars=sum(1 for c in s if '\u4e00'<=c<='\u9fff')
print('chars',chars)
