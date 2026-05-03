from pathlib import Path
import re, sys, json

ch=int(sys.argv[1])
proj=Path('/root/workspace/科武纪元')
file=proj/'待确认投稿'/f'第{ch}章改.txt'
if not file.exists(): file=proj/'新版'/f'第{ch}章.md'
card=proj/'审核记录/任务卡'/f'第{ch}章.md'
outdir=proj/'审核记录/证据包'; outdir.mkdir(parents=True,exist_ok=True)
text=file.read_text(encoding='utf-8',errors='ignore')
lines=text.splitlines()
card_text=card.read_text(encoding='utf-8',errors='ignore') if card.exists() else ''

KEYS={
 '章末钩子':['第'+str(ch+1),'行动目标','准备','通知','牵引','倒计时','窗口','上线','进场','权限','坐标','信号','钩子','（本章完）'],
 '大纲锚点':['铁幕','沙海','钴矿','算力','生态','权限','壳公司','资金','芯片','AI','机器人','叶启明','张维','赵刚','陈思琪','林星辰','谢云'],
 '技术动作':['接入','隔离','镜像','哈希','日志','权限','接口','终端','服务器','数据盘','证书','密钥','沙箱','链路','协议'],
 '军事动作':['压制','突入','撤','封控','押解','装甲','火力','机枪','无人','车队','矿区','主控室','交火','拦截'],
 '投稿风险':['美国','日本','欧洲','中国','联合国','中科院','MIT','CIA','真实','恐怖袭击']
}

def contexts(words, radius=3, max_hits=10):
    hits=[]
    for i,l in enumerate(lines,1):
        if any(w and w in l for w in words):
            a=max(1,i-radius); b=min(len(lines),i+radius)
            chunk='\n'.join(f'{j}|{lines[j-1]}' for j in range(a,b+1))
            hits.append({'line':i,'chunk':chunk})
            if len(hits)>=max_hits: break
    return hits

# Last non-empty tail, wider than old 800 chars; preserves hook area.
nonempty=[i for i,l in enumerate(lines,1) if l.strip()]
last=nonempty[-1] if nonempty else len(lines)
tail_start=max(1,last-120)
head='\n'.join(f'{i}|{lines[i-1]}' for i in range(1,min(len(lines),80)+1))
tail='\n'.join(f'{i}|{lines[i-1]}' for i in range(tail_start,last+1))

pkg={
 'chapter':ch,
 'file':str(file),
 'chars':len(re.findall(r'[\u4e00-\u9fff]',text)),
 'first_line':next((l for l in lines if l.strip()),''),
 'last_nonempty_line':lines[last-1] if last else '',
 'task_card':card_text[:1200],
 'head_lines':head,
 'tail_lines':tail,
 'evidence':{name:contexts(words) for name,words in KEYS.items()}
}
json_path=outdir/f'第{ch}章_evidence.json'
md_path=outdir/f'第{ch}章_证据包.md'
json_path.write_text(json.dumps(pkg,ensure_ascii=False,indent=2),encoding='utf-8')
md=['# 第%d章 RTK证据包'%ch,'','## 文件',str(file),'','## 本地预检',f'- 字数：{pkg["chars"]}',f'- 首行：{pkg["first_line"]}',f'- 末行：{pkg["last_nonempty_line"]}','','## 任务卡摘录',pkg['task_card'],'','## 首段行号',head,'','## 尾段行号',tail]
for name,hits in pkg['evidence'].items():
    md += ['',f'## 证据地图：{name}']
    if not hits: md.append('- 未检出')
    for h in hits:
        md += [f'### 命中行 {h["line"]}',h['chunk']]
md_path.write_text('\n'.join(md),encoding='utf-8')
print(json.dumps({'chapter':ch,'json':str(json_path),'md':str(md_path),'chars':pkg['chars']},ensure_ascii=False))
