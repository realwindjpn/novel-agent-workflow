from pathlib import Path
import re, sys, json

sys.path.insert(0, str(Path(__file__).resolve().parent))
from humanity_precard import default_card_path, validate_card

ch=int(sys.argv[1])
proj=Path('/root/workspace/科武纪元')
# Prefer current candidate draft when present. Older versions looked at
# 待确认投稿/ or 新版/, which let review gates miss candidate-only AI residue.
file=proj/'审核记录/临时精修'/f'第{ch}章_精修稿.tmp.md'
if not file.exists(): file=proj/'待确认投稿'/f'第{ch}章改.txt'
if not file.exists(): file=proj/'新版'/f'第{ch}章.md'
humanity_card=default_card_path(file)
humanity=validate_card(humanity_card,file)
if humanity['status'] != 'PASS':
    print(json.dumps({'chapter':ch,'status':'BLOCKED','humanity_card':str(humanity_card),'errors':humanity['errors']},ensure_ascii=False))
    raise SystemExit(2)
card=proj/'审核记录/任务卡'/f'第{ch}章.md'
outdir=proj/'审核记录/证据包'; outdir.mkdir(parents=True,exist_ok=True)
text=file.read_text(encoding='utf-8',errors='ignore')
lines=text.splitlines()
card_text=card.read_text(encoding='utf-8',errors='ignore') if card.exists() else ''

DEAI_PATTERNS={
 'NOT_BUT_HARD':re.compile(r'不是[^。！？\n]{0,100}而是'),
 'NUM_ENUM_HARD':re.compile(r'(^|[。！？\n]\s*)\d{1,2}[、.．：:]'),
 'CN_ENUM_HARD':re.compile(r'(^|[。！？\n]\s*)[一二三四五六七八九十][、.．：:]'),
 'META_INFO_HARD':re.compile(r'(下一章|第\d+章|第[一二三四五六七八九十]+章|第\d+卷|第[一二三四五六七八九十]+卷|后续篇章|第二卷后半段)'),
 'REPORT_TONE_SOFT':re.compile(r'(本质上|换句话说|这意味着|分为|层面|维度|路径|机制|核心是|更重要的是|首先|其次|最后)')
}

def deai_hits(max_hits=80):
    out=[]
    for i,l in enumerate(lines,1):
        if not l.strip(): continue
        for typ,pat in DEAI_PATTERNS.items():
            # 标题行“第X章 标题”是合法格式，不算章节元信息。
            if typ == 'META_INFO_HARD' and i == 1 and re.match(r'^第\d+章\s+', l.strip()):
                continue
            if pat.search(l):
                out.append({'line':i,'type':typ,'text':l.strip()[:260]})
                if len(out)>=max_hits: return out
    return out

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

_deai_hits=deai_hits()
pkg={
 'chapter':ch,
 'file':str(file),
 'chars':len(re.findall(r'[\u4e00-\u9fff]',text)),
 'first_line':next((l for l in lines if l.strip()),''),
 'last_nonempty_line':lines[last-1] if last else '',
 'task_card':card_text[:1200],
 'humanity_card':humanity,
 'head_lines':head,
 'tail_lines':tail,
 'deai_hits':_deai_hits,
 'deai_counts':{typ:sum(1 for h in _deai_hits if h['type']==typ) for typ in DEAI_PATTERNS},
 'evidence':{name:contexts(words) for name,words in KEYS.items()}
}
json_path=outdir/f'第{ch}章_evidence.json'
md_path=outdir/f'第{ch}章_证据包.md'
json_path.write_text(json.dumps(pkg,ensure_ascii=False,indent=2),encoding='utf-8')
md=['# 第%d章 RTK证据包'%ch,'','## 文件',str(file),'','## 人味前置卡',f'- 路径：{humanity["card_path"]}',f'- SHA256：{humanity["card_sha256"]}',f'- 状态：{humanity["status"]}',f'- 锚点数：{humanity["anchor_count"]}','','## 后验人味审硬字段','- 编辑必须输出 `HUMANITY_EDITOR_PASS` 或 `HUMANITY_EDITOR_FAIL`，逐锚点核验七类约束。','- 读者必须输出 `HUMANITY_READER_PASS` 或 `HUMANITY_READER_FAIL`，逐锚点核验听感与人物行为兑现。','- 不得以“AI味不重”替代锚点核验。','','## 本地预检',f'- 字数：{pkg["chars"]}',f'- 首行：{pkg["first_line"]}',f'- 末行：{pkg["last_nonempty_line"]}','','## 去AI硬闸扫描',json.dumps(pkg['deai_counts'],ensure_ascii=False),'|行号|类型|证据|','|---:|---|---|']
for h in pkg['deai_hits'][:80]:
    md.append(f"|{h['line']}|{h['type']}|{h['text'].replace('|','｜')}|")
if not pkg['deai_hits']:
    md.append('- 未检出')
md += ['','## 任务卡摘录',pkg['task_card'],'','## 首段行号',head,'','## 尾段行号',tail]
for name,hits in pkg['evidence'].items():
    md += ['',f'## 证据地图：{name}']
    if not hits: md.append('- 未检出')
    for h in hits:
        md += [f'### 命中行 {h["line"]}',h['chunk']]
md_path.write_text('\n'.join(md),encoding='utf-8')
print(json.dumps({'chapter':ch,'json':str(json_path),'md':str(md_path),'chars':pkg['chars']},ensure_ascii=False))
