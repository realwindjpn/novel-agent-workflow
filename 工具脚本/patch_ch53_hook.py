from pathlib import Path
import re
p = Path('/root/workspace/科武纪元/待确认投稿/第53章改.txt')
t = p.read_text(encoding='utf-8')
lines = t.splitlines()
while lines and not lines[-1].strip():
    lines.pop()
if lines and lines[-1].strip().startswith('（本章完）'):
    lines.pop()
t = '\n'.join(lines).rstrip()
addon = '''

赵刚没有再问第二遍。他把红笔摁在触控屏上，指尖用力，屏幕边缘压出一圈浅白。

“T减三天，不等他们接样。”

作战系统随即切入布控界面。沙海区域“门廊”外侧三十七公里，三条公路线、一条废弃矿道、两个临时通信塔同时亮成红色。无人机中队编号、电子压制车位置、边检协查权限，一项一项落到屏幕右侧。不是讨论。是行动清单。

李梦瑶把时间轴最后一栏补上。

T-30个月，张维舟调用七十二小时临时权限，完成A-3热控镜像脱壳导出，提取特征码。T-29个月，境外账户收到第一笔三百七十万美元，备注代码与Q-17热控板BOM清单采购单号一致。顾问组不是事后接货的人。他们从权限窗口打开那一刻，就已经在链条里。

林星辰看着那串采购单号，舌根发紧。

同一秒，会议室主屏左上角弹出红色警报。

白鹭站残留加密频段强制接入。频谱图拉开一道窄缝，机械合成音从扬声器里切出来，带着电流断续的沙声。

“样件已离库。门廊坐标取消。”

下一行坐标自动刷新。

沙海区域，旧矿道三号竖井。

预计接触时间：四十七分钟。

赵刚抬头，声音压得很低。

“全员上车。”
'''
new = t + addon + '\n\n（本章完）\n'
p.write_text(new, encoding='utf-8')
cn = len(re.findall(r'[\u4e00-\u9fff]', new))
print('patched ch53', cn)
