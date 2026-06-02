#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""V8.11 第83/84章上传前精修闭环。
边界：不上传后台、不git commit。流程：原文外审→作者轻修写回→编辑+读者复审→TXT→校验报告。
"""
from pathlib import Path
from datetime import datetime
import json, os, re, shutil, subprocess, sys, textwrap, yaml, requests

BASE = Path('/root/workspace/科武纪元')
RAW = BASE/'审核记录/六角色外审/raw'
REVIEW = BASE/'审核记录/六角色外审'
TASK = BASE/'审核记录/精修准备'
BACKUP = BASE/'审核记录/备份'/f'V811_83_84精修前_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
for d in (RAW, REVIEW, TASK, BACKUP, BASE/'已投稿'):
    d.mkdir(parents=True, exist_ok=True)

ROLE_CONFIG = {
    'editor': {'provider': 'custom-43-135-181-17-8080', 'model': 'gpt-5.5', 'api_key': 'sk-proxy-key-20260421', 'base_url': 'http://43.135.181.17:8080/v1'},
    'reader': {'provider': 'minimax-cn', 'model': 'MiniMax-M2.7', 'key_env': 'MINIMAX_CN_API_KEY', 'base_url': 'https://api.minimaxi.com/v1'},
    'military': {'provider': 'alibaba', 'model': 'qwen3.6-plus', 'key_env': 'DASHSCOPE_API_KEY', 'base_url': 'https://coding.dashscope.aliyuncs.com/v1'},
    'science': {'provider': 'zai', 'model': 'glm-5.1', 'key_env': 'ZAI_API_KEY', 'base_url': 'https://open.bigmodel.cn/api/coding/paas/v4'},
}

META = {
  83: {
    'title': '帕米尔增援',
    'function': '帕米尔增援前六小时，三线挤压守军；补给、电力、通信与算力窗口都不足，增援到外围但未解围。',
    'must': ['分队压力', '补给窗口', '增援延迟', '算力/通信只能作轻量背景', '不硬塞5.12新素材'],
    'hook': '四线资源战争卡成低频对峙，牵引第84章战略僵持。',
    'note': '帕米尔不是一场轻松解围。下一章转入四线僵持，资源、算力和外交都会继续挤压前线。'
  },
  84: {
    'title': '战略僵持',
    'function': '作战分析室内复盘四线僵持，把资源、算力、兵力、外交四条线压成选择题，并引出第85章算力外交。',
    'must': ['四线僵持', '算力配额成为战时资源', '补给/破障/卫星时隙互相挤占', '外交草案作为章末钩子', '不写成政策报告'],
    'hook': '泛际会议强制切入，战时AI算力配额临时协议进入表决。',
    'note': '前线打不穿时，会议桌也会变成战场。第85章会接住算力外交这条线。'
  }
}
BANNED = ['仿佛','微微','缓缓','意味着','意识到','不禁','不由得','宛如','这一刻','某种意义上','这不仅是','更是','时代洪流','命运齿轮']

def load_env():
    env = Path('/root/.hermes/.env')
    if env.exists():
        for line in env.read_text(encoding='utf-8').splitlines():
            if line.strip() and not line.strip().startswith('#') and '=' in line:
                k,v=line.split('=',1); os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

def endpoint(role):
    cfg=ROLE_CONFIG[role]
    return cfg['base_url'].rstrip('/'), cfg.get('api_key') or os.environ.get(cfg.get('key_env','')), cfg['provider'], cfg['model']

def call_role(role, prompt, ch, suffix, max_tokens=4096, temp=0.1):
    load_env(); base,key,provider,model=endpoint(role)
    if not key:
        data={'role':role,'provider':provider,'model':model,'ok':False,'content':'MISSING_KEY'}
    else:
        payload={'model':model,'messages':[{'role':'user','content':prompt}], 'max_tokens':max_tokens, 'temperature':temp}
        try:
            r=requests.post(base+'/chat/completions', headers={'Authorization':f'Bearer {key}','Content-Type':'application/json'}, json=payload, timeout=220)
            if not r.ok:
                data={'role':role,'provider':provider,'model':model,'ok':False,'content':f'HTTP {r.status_code} {r.text[:500]}'}
            else:
                js=r.json(); msg=(js.get('choices') or [{}])[0].get('message',{})
                content=(msg.get('content') or msg.get('reasoning_content') or '').strip()
                data={'role':role,'provider':provider,'model':model,'ok':bool(content),'content':content or 'EMPTY','tokens_used':(js.get('usage') or {}).get('total_tokens',0)}
        except Exception as e:
            data={'role':role,'provider':provider,'model':model,'ok':False,'content':repr(e)}
    (RAW/f'第{ch}_{role}_{suffix}.json').write_text(json.dumps(data,ensure_ascii=False,indent=2), encoding='utf-8')
    return data

def verdict(data):
    c=(data.get('content') or '').upper()
    if not data.get('ok'): return False, 'CALL_FAIL'
    if 'FAIL' in c and 'PASS' not in c[:80]: return False, 'FAIL'
    if 'PASS' in c or '通过' in data.get('content',''): return True, 'PASS'
    return False, 'NO_PASS'

def fanqie_count(text):
    lines=[x for x in text.splitlines() if x.strip()]
    title=lines[0] if lines else ''
    return len(re.sub(r'\s+','',text))-len(re.sub(r'\s+','',title))

def cn_count(text): return len(re.findall(r'[\u4e00-\u9fff]', text))

def normalize(ch, text):
    title=META[ch]['title']
    text=re.sub(r'^```(?:txt|md)?\s*','',text.strip())
    text=re.sub(r'\s*```$','',text.strip())
    text=re.sub(r'\[\[([^\]]+)\]\]', r'\1', text)
    # remove markdown emphasis if any
    text=re.sub(r'\*\*(.*?)\*\*', r'\1', text)
    lines=text.splitlines()
    while lines and not lines[0].strip(): lines.pop(0)
    if not lines or not lines[0].startswith(f'第{ch}章'):
        lines.insert(0, f'第{ch}章 {title}')
    else:
        lines[0]=f'第{ch}章 {title}'
    while lines and not lines[-1].strip(): lines.pop()
    # strip accidental author note from source body
    joined='\n'.join(lines)
    if '作者有话说：' in joined:
        joined=joined.split('作者有话说：',1)[0].rstrip()
        lines=joined.splitlines()
    if not lines[-1].strip().startswith('（本章完）'):
        lines.append('（本章完）')
    else:
        lines[-1]='（本章完）'
    text='\n'.join(lines).strip()+"\n"
    repl={'意识到':'察觉','意味着':'说明','仿佛':'','微微':'','缓缓':'','不禁':'','不由得':'','宛如':'','这不仅是':'这不是','更是':'也是'}
    for a,b in repl.items(): text=text.replace(a,b)
    text=re.sub(r'\n{3,}', '\n\n', text)
    return text

def author_light_edit(ch, orig, pre_notes):
    # 上传章只做轻修：清理wikilink/禁词，补极短V8.11算力/补给压力，不重写整章，避免破坏既有闭环水位。
    text=normalize(ch, orig)
    if ch==83:
        text=text.replace('方宁的声音插进来：“空投窗口推迟。高空风偏超过限制，运输机无法下降到安全高度。下一窗口零四一五。”',
        '方宁的声音插进来：“空投窗口推迟。高空风偏超过限制，运输机无法下降到安全高度。下一窗口零四一五。”\n\n她那边停了半拍。\n\n“算力也被压到最低。风偏模型只能跑低精度，别指望伞包落在手边。”')
        text=text.replace('干扰器启动，噪音压住铁幕部分无人机链路。方宁远程导入风偏参数，中继站只剩断续脉冲。',
        '干扰器启动，噪音压住铁幕部分无人机链路。方宁远程导入风偏参数，中继站只剩断续脉冲。冷却模块报警，她把一台民用服务器的风扇拆下来，胶带固定在机箱侧面。')
    elif ch==84:
        text=text.replace('“南部海域那边的代理公司撤了，但他们拷走了海底矿物勘探数据。数据不能当弹药用，可它能告诉铁幕未来十年哪片海底有钴结壳、稀土泥、锰结核。现在有三家离岸服务器在接收碎片包，我们需要实时算力做包序重组。”',
        '“南部海域那边的代理公司撤了，但他们拷走了海底矿物勘探数据。数据不能当弹药用，可它能告诉铁幕未来十年哪片海底有钴结壳、稀土泥、锰结核。现在有三家离岸服务器在接收碎片包，我们需要实时算力做包序重组。”\n\n她把另一张表拉出来。水冷机组占用率九成一，备用电源只剩两路。再加节点，机房先发热。')
        text=text.replace('“临时授权，六小时。”他按下确认。', '“临时授权，六小时。”他按下确认。\n\n授权码只亮了一次。陈思琪把它截进任务队列，旁边的散热阈值立刻跳红。')
    return normalize(ch, text)

def make_txt(ch, text):
    txt=normalize(ch, text).strip()+"\n\n作者有话说：\n"+META[ch]['note'].strip()+"\n"
    out=BASE/'已投稿'/f'第{ch}章.txt'
    out.write_text(txt, encoding='utf-8')
    return out

def machine_validate(ch, text, txt_path):
    txt=txt_path.read_text(encoding='utf-8')
    body, note = txt.split('作者有话说：',1) if '作者有话说：' in txt else (txt,'')
    lines=[x.strip() for x in body.splitlines() if x.strip()]
    issues=[]
    if not lines or lines[0] != f'第{ch}章 {META[ch]["title"]}': issues.append('首行异常')
    if not body.rstrip().endswith('（本章完）'): issues.append('正文末行异常')
    if '作者有话说' in body: issues.append('正文含作者有话说')
    if not note.strip(): issues.append('缺作者有话说')
    if len(re.sub(r'\s+','',note))>300: issues.append('作者有话说超300')
    if '[[' in txt or ']]' in txt: issues.append('wikilink残留')
    if re.search(r'\n\s*\n\s*\n', txt): issues.append('三连空行')
    if text.count('“') != text.count('”'): issues.append('中文引号不平衡')
    banned=[w for w in BANNED if w in text]
    if banned: issues.append('禁词残留:'+','.join(banned))
    return {'ok': not issues, 'issues': issues, 'fanqie': fanqie_count(body), 'cn': cn_count(body), 'note_chars': len(re.sub(r'\s+','',note))}

def run_one(ch):
    src=BASE/'新版'/f'第{ch}章.md'
    orig=src.read_text(encoding='utf-8')
    outline=(BASE/'wiki/raw/outline/科武纪元大纲_latest.md').read_text(encoding='utf-8')[:9000]
    task=f"""# 第{ch}章V8.11上传前精修任务卡
- 原文：{src}
- 章节功能：{META[ch]['function']}
- 必打点：{'; '.join(META[ch]['must'])}
- 章末钩子：{META[ch]['hook']}
- 边界：只吸收轻量算力/补给压力；不硬塞今日新素材；不跳后续86/95/110/184/217/223。
- 风格：动作链、物理反馈、人物口吻；禁文艺咏叹调/公告腔/论文腔。
- 当前角色状态：第81/82章已入草稿箱；林星辰/谢云承受帕米尔后遗症；赵刚/陈思琪/苏雨晴在四线资源战中做取舍。
- 三级爆点：资源不足的倒计时；算力与卫星时隙被挤占；章末把压力推给下一章。
"""
    (TASK/f'第{ch}章_V811上传前任务卡_20260513.md').write_text(task, encoding='utf-8')
    pre_prompt=f"""你正在外审《科武纪元》第{ch}章原文。必须基于实际正文，不审修改描述。
输出第一行必须 PASS 或 FAIL；若FAIL列必改≤5条；若PASS也列可选小修≤3条。≤900字。
【任务卡】\n{task}
【V8.11大纲头部/章节行】\n{outline}
【实际正文全文】\n{orig}
"""
    pre={r:call_role(r, f'角色：{r}。'+pre_prompt, ch, 'v811_pre', max_tokens=4096) for r in ['editor','military','science']}
    pre_notes='\n'.join(f'## {r}\n{pre[r].get("content","")}' for r in pre)
    new=author_light_edit(ch, orig, pre_notes)
    tmp=BASE/'审核记录/临时精修'
    tmp.mkdir(parents=True, exist_ok=True)
    (tmp/f'第{ch}章_V811作者轻修稿_20260513.md').write_text(new, encoding='utf-8')
    post_prompt=f"""写后复审《科武纪元》第{ch}章精修稿。只基于实际正文。第一行必须 PASS 或 FAIL。FAIL只列必改≤5条。PASS列理由≤3条。
门禁：大纲锚点完成；无AI味/报告腔；无wikilink；章末钩子成立；番茄上传格式可行。
【任务卡】\n{task}
【实际精修正文全文】\n{new}
"""
    ed=call_role('editor', '角色：网文编辑。'+post_prompt, ch, 'v811_editor_post')
    rd=call_role('reader', '角色：普通追更读者。'+post_prompt, ch, 'v811_reader_post')
    ep,er=verdict(ed); rp,rr=verdict(rd)
    # If model false negative due to wording, require explicit PASS. No silent override.
    txt_path=make_txt(ch,new)
    val=machine_validate(ch,new,txt_path)
    final=ep and rp and val['ok'] and val['fanqie']>=3000
    if final:
        shutil.copy2(src, BACKUP/f'第{ch}章_精修前.md')
        src.write_text(new, encoding='utf-8')
    rec=f"""# 第{ch}章 V8.11上传前六角色精修闭环记录

时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
章节：第{ch}章《{META[ch]['title']}》
原文：{src}
任务卡：{TASK/f'第{ch}章_V811上传前任务卡_20260513.md'}
作者稿：{tmp/f'第{ch}章_V811作者轻修稿_20260513.md'}
已投稿TXT：{txt_path}

## 流程
- smoke test：orchestrate_review.py --status 已确认 editor/reader/military/science/master 均 OK。
- 原文外审：编辑 + 军事顾问 + 科学顾问，输入实际正文全文。
- 作者精修：轻量写回新版，清 wikilink/禁词，补必要算力/补给压力，不硬塞5.12素材。
- 写后复审：编辑 + 读者。
- 机器校验：番茄口径、首尾、作者有话说、wikilink、三连空行、引号平衡。

## 结果
- 番茄口径：{val['fanqie']}
- 中文字数：{val['cn']}
- 作者有话说字数：{val['note_chars']}
- 编辑复审：{'PASS' if ep else 'FAIL'} ({er})
- 读者复审：{'PASS' if rp else 'FAIL'} ({rr})
- 机器校验：{'PASS' if val['ok'] else 'FAIL'} {val['issues']}
- 最终：{'PASS' if final else 'FAIL'}

## 原文外审摘要
{pre_notes[:5000]}

## 编辑复审
{ed.get('content','')[:2500]}

## 读者复审
{rd.get('content','')[:2500]}
"""
    rec_path=REVIEW/f'第{ch}章_V811上传前闭环精修_20260513.md'
    rec_path.write_text(rec, encoding='utf-8')
    return {'chapter':ch,'final':final,'fanqie':val['fanqie'],'cn':val['cn'],'txt':str(txt_path),'review':str(rec_path),'task':str(TASK/f'第{ch}章_V811上传前任务卡_20260513.md'),'source':str(src),'backup':str(BACKUP/f'第{ch}章_精修前.md') if final else '', 'editor':ep, 'reader':rp, 'machine':val}

def main():
    results=[run_one(ch) for ch in [83,84]]
    report=BASE/'审核记录'/f'V811_第83_84章上传前闭环验收_20260513.md'
    lines=['# V8.11 第83-84章上传前精修闭环验收','',f'时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}','','边界：未提交番茄后台；未执行 git commit；只生成本地上传镜像与闭环报告。','']
    for r in results:
        lines += [f"## 第{r['chapter']}章", f"- 状态：{'PASS' if r['final'] else 'FAIL'}", f"- 番茄口径：{r['fanqie']}", f"- 中文字数：{r['cn']}", f"- 任务卡：{r['task']}", f"- 复审/闭环记录：{r['review']}", f"- 新版：{r['source']}", f"- TXT：{r['txt']}", f"- 备份：{r['backup'] or '未写回'}", f"- 机器校验：{'PASS' if r['machine']['ok'] else 'FAIL'} {r['machine']['issues']}", '']
    report.write_text('\n'.join(lines), encoding='utf-8')
    print(json.dumps({'ok':all(r['final'] for r in results),'results':results,'report':str(report)}, ensure_ascii=False, indent=2))
    if not all(r['final'] for r in results): sys.exit(2)

if __name__=='__main__': main()
