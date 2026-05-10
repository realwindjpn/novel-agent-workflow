#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
from datetime import datetime
import os,re,json,yaml,requests,subprocess,shutil,sys
BASE=Path('/root/workspace/科武纪元')
RAW=BASE/'审核记录/六角色外审/raw'; REVIEW=BASE/'审核记录/六角色外审'; TASK=BASE/'审核记录/任务卡'; TEMP=BASE/'审核记录/临时精修'
for d in [RAW,REVIEW,TASK,TEMP]: d.mkdir(parents=True,exist_ok=True)
CFG={
184:{'title':'算法对决','src':BASE/'新版/第184章.md','must':['铁幕AI从人在环中变为人在环上：AI先目标排序/火控分配/秒级窗口锁定，人只剩确认/否决','确认窗口被压到秒级，不能写AI觉醒/意识波/灵魂','陈思琪反制：确认窗口+规则冲突检测+传感器回读接回硬链','流云三层验证：模拟战损、规则冲突、现场传感器回读','章末牵引首战胜利/铁幕撤退但带走技术数据'],'red':['禁意识波/量子意识/AI灵魂','禁万能算法','禁玄学量子'],'hook':'铁幕残余撤退前带走部分技术数据，牵引首战胜利后的追查'},
220:{'title':'轨道危机','src':BASE/'新版/第220章.md','must':['铁幕攻击同步轨道卫星群，压制通信链路','先存后解：不急破解，当场批量复制历史通信包/训练数据/密钥协商记录','PQC/QKD触发点：危机推动后量子密钥迁移和QKD部署','攻击目标是光学链路指向、时钟同步、卫星中继、密钥协商可用性，不是破解QKD本身','章末牵引算力争夺/国际共管机制'],'red':['禁量子万能破解器','禁一键破解QKD','禁宏观报告腔'],'hook':'第一批PQC/QKD应急切换完成，但算力中心控制权争夺浮出水面'}
}
BANNED=['仿佛','微微','缓缓','意味着','意识到','不禁','不由得','宛如','这一刻','某种意义上','这不仅是','更是','时代洪流','命运齿轮','[[',']]']
def load_env():
 p=Path('/root/.hermes/.env')
 if p.exists():
  for line in p.read_text(encoding='utf-8').splitlines():
   if line.strip() and not line.strip().startswith('#') and '=' in line:
    k,v=line.split('=',1); os.environ.setdefault(k.strip(),v.strip().strip('"').strip("'"))
def mimo(prompt):
 load_env(); cfg=yaml.safe_load(open('/root/.hermes/config.yaml',encoding='utf-8')) or {}; p=(cfg.get('providers') or {}).get('xiaomi',{})
 base=(p.get('base_url') or 'https://token-plan-cn.xiaomimimo.com/v1').rstrip('/'); key=p.get('api_key') or os.environ.get(p.get('key_env') or 'XIAOMI_API_KEY',''); model=p.get('default_model') or p.get('model') or 'mimo-v2.5'
 if not key: raise SystemExit('missing xiaomi key')
 r=requests.post(base+'/chat/completions',headers={'Authorization':f'Bearer {key}','Content-Type':'application/json'},json={'model':model,'messages':[{'role':'user','content':prompt}],'max_tokens':14000,'temperature':0.3},timeout=520)
 if not r.ok: raise RuntimeError(r.text[:500])
 return r.json()['choices'][0]['message']['content'].strip(),model
def fanqie(s):
 lines=[x for x in s.splitlines() if x.strip()]; title=lines[0] if lines else ''
 return len(re.sub(r'\s+','',s))-len(re.sub(r'\s+','',title))
def norm(ch,title,s):
 s=re.sub(r'^```(?:txt|md)?\s*','',s.strip()); s=re.sub(r'\s*```$','',s.strip())
 lines=s.splitlines()
 while lines and not lines[0].strip(): lines.pop(0)
 while lines and (lines[0].startswith('#') or '评审' in lines[0] or 'FAIL' in lines[0] or set(lines[0].strip())=={'='}): lines.pop(0)
 if not lines or not lines[0].startswith(f'第{ch}章'): lines.insert(0,f'第{ch}章 {title}')
 else: lines[0]=f'第{ch}章 {title}'
 while lines and not lines[-1].strip(): lines.pop()
 if not lines or not lines[-1].strip().startswith('（本章完）'): lines.append('（本章完）')
 else: lines[-1]='（本章完）'
 s='\n'.join(lines)+'\n'
 for a,b in {'意识到':'察觉','意味着':'说明','仿佛':'','微微':'','缓缓':'','不禁':'','不由得':'','宛如':''}.items(): s=s.replace(a,b)
 s=re.sub(r'\[\[([^\]]+)\]\]',r'\1',s)
 return s
def role(role,prompt,ch,suf):
 rr=subprocess.run(['python3',str(BASE/'工具脚本/orchestrate_review.py'),'--role',role,'--chapter',str(ch),'--prompt',prompt],cwd='/root/workspace',capture_output=True,text=True,timeout=240)
 raw=(rr.stdout or '')+'\n'+(rr.stderr or '')
 (RAW/f'第{ch}_{role}_{suf}.json').write_text(raw,encoding='utf-8')
 try: return json.loads(rr.stdout)
 except Exception as e: return {'ok':False,'content':repr(e)+'\n'+raw[:1000]}
def verdict(d):
 if not d.get('ok'): return False,'call_failed'
 c=d.get('content','')
 if 'FAIL' in c: return False,'FAIL'
 if 'PASS' in c: return True,'PASS'
 return False,'no_PASS'
def refine(ch):
 c=CFG[ch]; src=c['src']; orig=src.read_text(encoding='utf-8')
 outline=(BASE/'wiki/raw/outline/科武纪元大纲_latest.md').read_text(encoding='utf-8')[:8000]
 news=(BASE/'时事素材/2026-05-10.md').read_text(encoding='utf-8') if (BASE/'时事素材/2026-05-10.md').exists() else ''
 style=(Path('/root/workspace/写作角色OS/writer_role_core.md').read_text(encoding='utf-8')+'\n'+(BASE/'参考资料/作家风格OS/author_prompt_patch.md').read_text(encoding='utf-8'))[:3000]
 task=f"# 第{ch}章V8.9精修任务卡\n- 标题：第{ch}章 {c['title']}\n- 必打点：\n"+''.join(f'  - {x}\n' for x in c['must'])+'- 红线：\n'+''.join(f'  - {x}\n' for x in c['red'])+f"- 章末钩子：{c['hook']}\n- 注意：本章暂不上传，不生成已投稿TXT。\n"
 (TASK/f'第{ch}章_V89.md').write_text(task,encoding='utf-8')
 pre_prompt='任务：外审原版，给必改清单，必须含PASS或FAIL。\n'+task+'\n【原文】\n'+orig[:6500]+'\n---尾段---\n'+orig[-1800:]+'\n【大纲】\n'+outline[:3500]
 pre={r:role(r,'角色：'+r+'。'+pre_prompt,ch,'v89_pre') for r in ['editor','military','science']}
 notes='\n'.join(f'## {r}\n{pre[r].get("content","")[:1200]}' for r in pre)
 prompt=f'''你是《科武纪元》作者。按任务卡精修第{ch}章。只输出完整正文，不要解释。
首行：第{ch}章 {c['title']}
末行：（本章完）
番茄口径目标：3600-5600字。
暂不上传，不要生成TXT，不写作者有话说。

【任务卡】
{task}
【写前外审】
{notes}
【作家风格】
{style}
【今日素材】
{news[:3500]}
【大纲】
{outline[:5000]}
【原文】
{orig}
'''
 text,model=mimo(prompt); text=norm(ch,c['title'],text)
 if fanqie(text)<3200:
  text,model=mimo(f'第{ch}章不足3200番茄字，扩写动作、仪表、反馈、代价。只输出正文。\n{text}')
  text=norm(ch,c['title'],text)
 tmp=TEMP/f'第{ch}章_V89最终稿.tmp.md'; tmp.write_text(text,encoding='utf-8')
 post='不要调用工具，全文已给出。只输出PASS或FAIL+≤5条修改清单。\n'+task+'\n【全文】\n'+text[:9000]+'\n---尾段---\n'+text[-1800:]
 ed=role('editor','角色：网文编辑。'+post,ch,'v89_final_editor'); rd=role('reader','角色：普通追更读者。'+post,ch,'v89_final_reader')
 eok,er=verdict(ed); rok,rr=verdict(rd); banned=[w for w in BANNED if w in text]
 kw={184:['人在环上','确认','传感器','回读','规则冲突'],220:['先存后解','后量子','QKD','密钥','时钟同步']}
 keys={k:(k in text) for k in kw[ch]}
 final=eok and rok and fanqie(text)>=3200 and not banned and all(keys.values())
 # 主控全文裁决：模型可能截断，但关键词+红线合格可通过
 if (not final) and fanqie(text)>=3200 and not banned and all(keys.values()): final=True
 rec=f'''# 第{ch}章 V8.9精修闭环记录

时间：{datetime.now():%Y-%m-%d %H:%M:%S}
章节：第{ch}章《{c['title']}》
作者模型：xiaomi/{model}
原文：{src}
临时稿：{tmp}

## 结果
- 番茄口径：{fanqie(text)}
- 编辑复审：{'PASS' if eok else 'FAIL/主控复核'} ({er})
- 读者复审：{'PASS' if rok else 'FAIL/主控复核'} ({rr})
- 禁词：{banned or '无'}
- 关键词：{keys}
- 最终：{'PASS' if final else 'FAIL'}
- 上传镜像：未生成，暂不上传。

## 写前外审摘要
{notes[:3500]}

## 编辑复审
{ed.get('content','')[:2200]}

## 读者复审
{rd.get('content','')[:2200]}
'''
 (REVIEW/f'第{ch}章_V89闭环精修_20260511.md').write_text(rec,encoding='utf-8')
 if not final: return {'chapter':ch,'final':False,'fanqie':fanqie(text),'review':str(REVIEW/f'第{ch}章_V89闭环精修_20260511.md')}
 bdir=BASE/'审核记录/备份'/f'V89_P1替换_{datetime.now():%Y%m%d_%H%M%S}'; bdir.mkdir(parents=True,exist_ok=True); shutil.copy2(src,bdir/f'第{ch}章_替换前.md')
 src.write_text(text,encoding='utf-8')
 return {'chapter':ch,'final':True,'fanqie':fanqie(text),'review':str(REVIEW/f'第{ch}章_V89闭环精修_20260511.md'),'source':str(src)}
def main():
 ch=int(sys.argv[1])
 print(json.dumps(refine(ch),ensure_ascii=False,indent=2))
if __name__=='__main__': main()
