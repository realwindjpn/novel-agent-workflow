#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""V8.9 chapter refinement for ch110/ch156.
Flow: original external review -> MiMo author rewrite -> editor+reader post review -> sync.
No git commit.
"""
from pathlib import Path
from datetime import datetime
import json, os, re, shutil, subprocess, sys, yaml, requests, textwrap

BASE = Path('/root/workspace/科武纪元')
RAW = BASE/'审核记录/六角色外审/raw'
REVIEW = BASE/'审核记录/六角色外审'
TASK = BASE/'审核记录/任务卡'
TEMP = BASE/'审核记录/临时精修'
BACKUP = BASE/'审核记录/备份'/f'V89精修_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
for d in [RAW, REVIEW, TASK, TEMP, BACKUP]: d.mkdir(parents=True, exist_ok=True)

CONFIG = {
  110: {
    'title': '天门封锁',
    'source': BASE/'新版/第110章.md',
    'outline': '铁幕封锁全球能源咽喉“天门海峡”，能源、航运、保险、备件同时跳升；方宁追踪外骨骼/基地系统里被远程校验锁死的进口控制器。医疗船误击把第86章诊所误判推成跨战区信任瓦解。',
    'must': ['天门封锁=物理咽喉，不是宏观新闻背景', 'MATCH式远程锁死=存量控制器/固件/维修/位置校验失效', '能源咽喉+数字锁死形成双重绞杀', '医疗船误击呼应第86章误判，写链路/权限/规则失效，不写反派降智', '价值变化：从技术泄露疑案升级为系统级生存压力'],
    'redline': ['禁写成单纯技术泄露旧章', '禁万能破解/一键恢复', '禁宏观报告腔', 'AI/锁死只能写权限、固件、证书、位置校验、维修断供'],
    'hook': '内鬼调查：锁死清单里出现海外名校导师/Keller技术特征或活人节点',
    'next': '内鬼调查',
  },
  156: {
    'title': '重返月球',
    'source': BASE/'新版/第156章.md',
    'ref': BASE/'新版/第 156 章.md',
    'outline': '星辰小队随南天门计划重返月球，在沙克尔顿环形山建立主基地。规则权来自稳定存在：双火箭对接、救援冗余、连续补给、对接口标准、备件库存；铁幕阵营绕月高调但着陆器/加注/预算/政权摇摆拖住。',
    'must': ['主稿必须从“遗迹线索”改为“重返月球”', '写发射/对接/转移/月面部署的工程链', '稳定存在即规则权：连续到达、补给、救援、维护，而非插旗口号', '双火箭对接、救援冗余、连续补给必须落到清单/仪表/动作', '价值变化：从登月行动开始，转为月面规则竞争明牌'],
    'redline': ['短版第 156 章.md仅参考，不作主稿', '不提前写遗迹大揭秘', '不把规则权写成宣言', '不写量子/登月万能化'],
    'hook': '氦-3开采启动前，补给/救援链第一次接受实际压力测试',
    'next': '氦-3开采',
  }
}

BANNED = ['仿佛','微微','缓缓','意味着','意识到','不禁','不由得','宛如','这一刻','某种意义上','这不仅是','更是','时代洪流','命运齿轮']


def load_env():
    env = Path('/root/.hermes/.env')
    if env.exists():
        for line in env.read_text(encoding='utf-8').splitlines():
            line=line.strip()
            if line and not line.startswith('#') and '=' in line:
                k,v=line.split('=',1); os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def fanqie_count(text):
    lines=[x for x in text.splitlines() if x.strip()]
    title=lines[0] if lines else ''
    return len(re.sub(r'\s+','',text))-len(re.sub(r'\s+','',title))


def cn_count(text): return len(re.findall(r'[\u4e00-\u9fff]', text))


def strip_md(s):
    s=re.sub(r'^```(?:txt|md)?\s*','',s.strip())
    s=re.sub(r'\s*```$','',s.strip())
    return s.strip()


def call_role(role, prompt, ch, suffix, timeout=240):
    cmd=['python3', str(BASE/'工具脚本/orchestrate_review.py'), '--role', role, '--chapter', str(ch), '--prompt', prompt]
    rr=subprocess.run(cmd, cwd='/root/workspace', capture_output=True, text=True, timeout=timeout)
    raw=(rr.stdout or '')+'\n'+(rr.stderr or '')
    (RAW/f'第{ch}_{role}_{suffix}.json').write_text(raw, encoding='utf-8')
    try:
        data=json.loads(rr.stdout)
        return data
    except Exception:
        return {'role':role,'ok':False,'content':raw[:2000]}


def get_mimo():
    load_env()
    cfg=yaml.safe_load(open('/root/.hermes/config.yaml',encoding='utf-8')) or {}
    p=(cfg.get('providers') or {}).get('xiaomi',{})
    base=(p.get('base_url') or 'https://token-plan-cn.xiaomimimo.com/v1').rstrip('/')
    key=p.get('api_key') or os.environ.get(p.get('key_env') or 'XIAOMI_API_KEY','')
    model=p.get('default_model') or p.get('model') or 'mimo-v2.5'
    if not key: raise SystemExit('MIMO_KEY_MISSING')
    return base,key,model


def call_mimo(prompt, max_tokens=12000):
    base,key,model=get_mimo()
    r=requests.post(base+'/chat/completions', headers={'Authorization':f'Bearer {key}','Content-Type':'application/json'}, json={'model':model,'messages':[{'role':'user','content':prompt}],'max_tokens':max_tokens,'temperature':0.35}, timeout=520)
    if not r.ok: raise RuntimeError(f'MIMO_FAIL {r.status_code} {r.text[:300]}')
    data=r.json(); return data['choices'][0]['message']['content'].strip(), model


def verdict(data):
    c=(data.get('content') or '')
    if not data.get('ok'): return False, 'call_failed'
    if 'FAIL' in c: return False, 'FAIL'
    if 'PASS' in c: return True, 'PASS'
    return False, 'no_PASS'


def normalize(ch, title, text):
    text=strip_md(text)
    lines=text.splitlines()
    while lines and not lines[0].strip(): lines.pop(0)
    if not lines or not lines[0].startswith(f'第{ch}章'):
        lines.insert(0, f'第{ch}章 {title}')
    else:
        lines[0]=f'第{ch}章 {title}'
    while lines and not lines[-1].strip(): lines.pop()
    if not lines or not lines[-1].strip().startswith('（本章完）'):
        lines.append('（本章完）')
    else:
        lines[-1]='（本章完）'
    text='\n'.join(lines)+'\n'
    for old,repl in {'意识到':'察觉','意味着':'说明','仿佛':'','微微':'','缓缓':'','不禁':'','不由得':'','宛如':''}.items(): text=text.replace(old,repl)
    text=re.sub(r'\[\[([^\]]+)\]\]', r'\1', text)
    return text


def refine_one(ch):
    meta=CONFIG[ch]
    src=meta['source']
    orig=src.read_text(encoding='utf-8')
    ref=''
    if meta.get('ref') and meta['ref'].exists(): ref=meta['ref'].read_text(encoding='utf-8')[:2500]
    outline_top=(BASE/'wiki/raw/outline/科武纪元大纲_latest.md').read_text(encoding='utf-8')[:6500]
    news=(BASE/'时事素材/2026-05-10.md').read_text(encoding='utf-8')
    style=(Path('/root/workspace/写作角色OS/writer_role_core.md').read_text(encoding='utf-8')+'\n'+(BASE/'参考资料/作家风格OS/author_prompt_patch.md').read_text(encoding='utf-8'))[:3500]

    task=f"""# 第{ch}章V8.9精修任务卡
- 原文：{src}
- 目标标题：第{ch}章 {meta['title']}
- 最新大纲锚点：{meta['outline']}
- 必打点：\n""" + ''.join(f'  - {x}\n' for x in meta['must']) + "- 红线：\n" + ''.join(f'  - {x}\n' for x in meta['redline']) + f"- 章末钩子：{meta['hook']}，牵引《{meta['next']}》。\n- V8.9-B六问：价值变化、旧组件×2组合、反馈延迟、后勤制度摩擦、万能化红线、具名代价。\n"
    (TASK/f'第{ch}章_V89.md').write_text(task, encoding='utf-8')

    pre_prompt=f"""任务：外审原版第{ch}章。必须基于实际正文，给必改清单。输出≤900字，必须含 PASS/FAIL 与 修改清单。
{task}
【原文首尾/全文】\n{orig[:5500]}\n---尾段---\n{orig[-1800:]}
【最新大纲摘要】\n{outline_top[:2500]}
【今日素材】\n{news[:2500]}
"""
    pre={r:call_role(r, '角色：'+r+'。'+pre_prompt, ch, f'v89_pre') for r in ['editor','military','science']}

    pre_notes='\n'.join(f'## {r}\n{pre[r].get("content","")[:1200]}' for r in pre)
    author_prompt=f"""你是《科武纪元》作者，用 MiMo-2.5-Pro 执行第{ch}章六角色精修。只输出正文。

【硬格式】
首行：第{ch}章 {meta['title']}
末行：（本章完）
番茄口径目标：3600-5600字；不得少于3200。
正文不得出现“第X卷/任务卡/大纲/V8.9/外审”等元信息。
禁文艺比喻，禁公告腔/论文腔。技术必须落到操作、仪表、成本、失败模式。

【任务卡】\n{task}
【作家风格OS】\n{style}
【写前外审意见】\n{pre_notes}
【今日素材】\n{news[:3500]}
【大纲片段】\n{outline_top[:4000]}
"""
    if ref: author_prompt += f"\n【短版参考，仅取工程动作，不作主稿】\n{ref}\n"
    author_prompt += f"\n【原文全文】\n{orig}\n"
    draft, model=call_mimo(author_prompt)
    new=normalize(ch, meta['title'], draft)
    if fanqie_count(new)<3200:
        expand=f"""第{ch}章当前番茄口径{fanqie_count(new)}，不足。保留骨架扩到≥3600番茄字。补动作、仪表、反馈、代价；只输出正文。\n{new}\n"""
        draft, model=call_mimo(expand)
        new=normalize(ch, meta['title'], draft)
    tmp=TEMP/f'第{ch}章_V89精修稿.tmp.md'
    tmp.write_text(new, encoding='utf-8')

    post_prompt=f"""任务：写后复审第{ch}章精修稿。只基于下方实际正文。输出必须含 PASS 或 FAIL。若缺必打点/有红线/AI味重/章末钩子弱，判FAIL并列修改清单≤5条。
{task}
【正文】\n{new[:6500]}\n---尾段---\n{new[-1800:]}
"""
    ed=call_role('editor', '角色：网文编辑。'+post_prompt, ch, 'v89_editor_post')
    rd=call_role('reader', '角色：普通追更读者。'+post_prompt, ch, 'v89_reader_post')
    ep,er=verdict(ed); rp,rr=verdict(rd)
    banned=[w for w in BANNED if w in new]
    has_hook=any(k in new[-900:] for k in re.findall(r'[\u4e00-\u9fff]{2,}', meta['next']+meta['hook']))
    final=ep and rp and fanqie_count(new)>=3200 and not banned and has_hook

    # One repair round if needed.
    if not final:
        repair=f"""第{ch}章复审未过/机器门禁未过。
编辑：{ed.get('content','')[:1200]}
读者：{rd.get('content','')[:1200]}
禁词：{banned}
钩子命中：{has_hook}
请按意见修正文，只输出完整正文。\n{new}\n"""
        draft, model=call_mimo(repair)
        new=normalize(ch, meta['title'], draft)
        tmp.write_text(new, encoding='utf-8')
        ed=call_role('editor', '角色：网文编辑。'+post_prompt.replace(post_prompt.split('【正文】')[1], f"\n{new[:6500]}\n---尾段---\n{new[-1800:]}") , ch, 'v89_editor_repost')
        rd=call_role('reader', '角色：普通追更读者。'+post_prompt.replace(post_prompt.split('【正文】')[1], f"\n{new[:6500]}\n---尾段---\n{new[-1800:]}") , ch, 'v89_reader_repost')
        ep,er=verdict(ed); rp,rr=verdict(rd)
        banned=[w for w in BANNED if w in new]
        has_hook=any(k in new[-900:] for k in re.findall(r'[\u4e00-\u9fff]{2,}', meta['next']+meta['hook']))
        final=ep and rp and fanqie_count(new)>=3200 and not banned and has_hook

    rec=f"""# 第{ch}章 V8.9六角色精修闭环记录

时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
章节：第{ch}章《{meta['title']}》
原文：{src}
临时稿：{tmp}
作者模型：xiaomi/{model}

## 流程
- 原文外审：编辑 + 军事 + 科学（实际正文）
- 作者精修：MiMo-2.5-Pro
- 写后复审：编辑 + 读者
- 机器门禁：番茄口径、禁词、章末钩子、wikilink清理

## 结果
- 番茄口径：{fanqie_count(new)}
- 中文字数：{cn_count(new)}
- 编辑复审：{'PASS' if ep else 'FAIL'} ({er})
- 读者复审：{'PASS' if rp else 'FAIL'} ({rr})
- 禁词残留：{banned or '无'}
- 章末钩子：{'PASS' if has_hook else 'FAIL'}
- 最终：{'PASS' if final else 'FAIL'}

## 写前外审摘要
{pre_notes[:3500]}

## 编辑复审
{ed.get('content','')[:1800]}

## 读者复审
{rd.get('content','')[:1800]}
"""
    (REVIEW/f'第{ch}章_V89闭环精修_20260511.md').write_text(rec, encoding='utf-8')

    if final:
        shutil.copy2(src, BACKUP/f'第{ch}章_精修前.md')
        src.write_text(new, encoding='utf-8')
        txt=re.sub(r'^#+\s*','',new,flags=re.M)
        txt=re.sub(r'\*\*(.*?)\*\*', r'\1', txt)
        txt=re.sub(r'\[\[([^\]]+)\]\]', r'\1', txt).strip()+"\n"
        (BASE/'已投稿'/f'第{ch}章.txt').write_text(txt, encoding='utf-8')
    return {'chapter':ch,'final':final,'fanqie':fanqie_count(new),'review':str(REVIEW/f'第{ch}章_V89闭环精修_20260511.md'),'source':str(src),'txt':str(BASE/'已投稿'/f'第{ch}章.txt'),'backup':str(BACKUP/f'第{ch}章_精修前.md') if final else '', 'editor':ep, 'reader':rp, 'banned':banned, 'hook':has_hook}


def main():
    chapters=[int(x) for x in sys.argv[1:]] or [110,156]
    results=[]
    for ch in chapters:
        results.append(refine_one(ch))
    report=BASE/'审核记录'/'V89_第110_156章精修执行汇总_20260511.md'
    lines=['# V8.9 第110/156章六角色精修执行汇总','',f'时间：{datetime.now().strftime("%Y-%m-%d %H:%M:%S")}', '']
    for r in results:
        lines += [f"## 第{r['chapter']}章", f"- 最终：{'PASS' if r['final'] else 'FAIL'}", f"- 番茄口径：{r['fanqie']}", f"- 审核记录：{r['review']}", f"- 新版：{r['source']}", f"- 已投稿TXT：{r['txt']}", f"- 备份：{r['backup'] or '未替换'}", '']
    report.write_text('\n'.join(lines), encoding='utf-8')
    print(json.dumps({'results':results,'report':str(report)}, ensure_ascii=False, indent=2))
    if not all(r['final'] for r in results):
        sys.exit(2)

if __name__=='__main__': main()
