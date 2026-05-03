#!/usr/bin/env python3
from pathlib import Path
p=Path('/root/workspace/科武纪元/新版/第241章.md')
s=p.read_text(encoding='utf-8')
additions={
'林星辰坐在椅子上等。椅子还是那把木头的，靠背很直，硌得脊椎生疼。他把笔记本摊在腿上，翻到NTM-SYNC-0001那一页。':'林星辰坐在椅子上等。椅子还是那把木头的，靠背很直，硌得脊椎生疼。他把笔记本摊在腿上，翻到NTM-SYNC-0001那一页。纸页边缘有折痕，上次翻的时候折的。他用手指把折痕抚平。',
'树莓派上跑着一个脚本，监控USB端口的连接状态。':'树莓派上跑着一个脚本，监控USB端口的连接状态。脚本是林泽远写的，大约二十行Python代码。逻辑很简单：轮询lsusb输出，如果检测到Android设备就弹通知。',
'林星辰按住手机的电源键。':'林星辰按住手机的电源键。指尖能感觉到电源键的弹簧阻力。按下去，松手，再按回去。'
}
for a,b in additions.items():
    if a in s: s=s.replace(a,b)
    else: print('MISS',a[:50])
p.write_text(s,encoding='utf-8')
chars=sum(1 for c in s if '\u4e00'<=c<='\u9fff')
print('chars',chars)
