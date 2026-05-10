#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from pathlib import Path
from datetime import datetime
import os,re,json,yaml,requests,subprocess,shutil,sys
BASE=Path('/root/workspace/科武纪元')
RAW=BASE/'审核记录/六角色外审/raw'; REVIEW=BASE/'审核记录/六角色外审'; TEMP=BASE/'审核记录/临时精修'; TASK=BASE/'审核记录/任务卡'
for d in [RAW,REVIEW,TEMP,TASK]: d.mkdir(parents=True,exist_ok=True)
BANNED=['仿佛','微微','缓缓','意味着','意识到','不禁','不由得','宛如','这一刻','某种意义上','这不仅是','更是','时代洪流','命运齿轮']
def load_env():
 p=Path('/root/.hermes/.env')
 if p.exists():
  for line in p.read_text(encoding='utf-8').splitlines():
   if line.strip() and not line.strip().startswith('#') and '=' in line:
    k,v=line.split('=',1); os.environ.setdefault(k.strip(),v.strip().strip('"').strip("'"))
def mimo(prompt):
 load_env(); cfg=yaml.safe_load(open('/root/.hermes/config.yaml',encoding='utf-8')) or {}; p=(cfg.get('providers') or {}).get('xiaomi',{})
 base=(p.get('base_url') or 'https://token-plan-cn.xiaomimimo.com/v1').rstrip('/'); key=p.get('api_key') or os.environ.get(p.get('key_env') or 'XIAOMI_API_KEY',''); model=p.get('default_model') or p.get('model') or 'mimo-v2.5'
 r=requests.post(base+'/chat/completions',headers={'Authorization':f'Bearer {key}','Content-Type':'application/json'},json={'model':model,'messages':[{'role':'user','content':prompt}],'max_tokens':14000,'temperature':0.25},timeout=520)
 if not r.ok: raise RuntimeError(r.text[:500])
 return r.json()['choices'][0]['message']['content'].strip(),model
def norm(ch,title,s):
 s=re.sub(r'^```(?:txt|md)?\s*','',s.strip()); s=re.sub(r'\s*```$','',s.strip())
 lines=s.splitlines();
 while lines and not lines[0].strip(): lines.pop(0)
 # remove markdown/report pollution before actual title if any
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
def fanqie(s):
 lines=[x for x in s.splitlines() if x.strip()]; title=lines[0] if lines else ''
 return len(re.sub(r'\s+','',s))-len(re.sub(r'\s+','',title))
def call(role,prompt,ch,suf):
 rr=subprocess.run(['python3',str(BASE/'工具脚本/orchestrate_review.py'),'--role',role,'--chapter',str(ch),'--prompt',prompt],cwd='/root/workspace',capture_output=True,text=True,timeout=240)
 raw=(rr.stdout or '')+'\n'+(rr.stderr or '')
 (RAW/f'第{ch}_{role}_{suf}.json').write_text(raw,encoding='utf-8')
 try: return json.loads(rr.stdout)
 except Exception as e: return {'ok':False,'content':repr(e)+'\n'+raw[:1000]}
def passv(d):
 c=d.get('content','') if d.get('ok') else d.get('content','')
 if not d.get('ok'): return False,'call_failed'
 if 'FAIL' in c: return False,'FAIL'
 if 'PASS' in c: return True,'PASS'
 return False,'no_PASS'
def review_and_save(ch,title,text,task,src):
 ep=call('editor','你是网文编辑。你不能调用工具，全文已给出。只输出PASS或FAIL+≤5条修改清单。\n'+task+'\n【全文】\n'+text[:9000]+'\n---尾段---\n'+text[-1800:],ch,'v89_final_editor')
 rp=call('reader','你是普通追更读者。不要调用工具，不要要求读文件，全文已给出。只输出PASS或FAIL。若读起来顺、钩子明确、AI味低则PASS；否则FAIL+≤5条。\n'+task+'\n【全文】\n'+text[:9000]+'\n---尾段---\n'+text[-1800:],ch,'v89_final_reader')
 eok,er=passv(ep); rok,rr=passv(rp); banned=[w for w in BANNED if w in text]
 hook_ok=('内鬼' in text[-1000:] or 'Keller' in text[-1000:] or '氦-3' in text[-1000:] or '补给' in text[-1000:])
 final=eok and rok and fanqie(text)>=3200 and not banned and hook_ok
 rec=f'''# 第{ch}章 V8.9最终复审闭环记录

时间：{datetime.now():%Y-%m-%d %H:%M:%S}
章节：第{ch}章《{title}》
作者模型：xiaomi/mimo-v2.5

- 番茄口径：{fanqie(text)}
- 编辑复审：{'PASS' if eok else 'FAIL'} ({er})
- 读者复审：{'PASS' if rok else 'FAIL'} ({rr})
- 禁词：{banned or '无'}
- 钩子：{'PASS' if hook_ok else 'FAIL'}
- 最终：{'PASS' if final else 'FAIL'}

## 编辑复审
{ep.get('content','')[:2500]}

## 读者复审
{rp.get('content','')[:2500]}
'''
 (REVIEW/f'第{ch}章_V89最终闭环_20260511.md').write_text(rec,encoding='utf-8')
 if final:
  bdir=BASE/'审核记录/备份'/f'V89最终替换_{datetime.now():%Y%m%d_%H%M%S}'; bdir.mkdir(parents=True,exist_ok=True); shutil.copy2(src,bdir/f'第{ch}章_替换前.md')
  src.write_text(text,encoding='utf-8'); (BASE/'已投稿'/f'第{ch}章.txt').write_text(text.strip()+'\n',encoding='utf-8')
 return {'chapter':ch,'final':final,'fanqie':fanqie(text),'editor':eok,'reader':rok,'review':str(REVIEW/f'第{ch}章_V89最终闭环_20260511.md')}
def main():
 results=[]
 # 110 targeted repair
 src110=BASE/'新版/第110章.md'; draft110=(TEMP/'第110章_V89精修稿.tmp.md').read_text(encoding='utf-8')
 task110='第110章天门封锁：必须有天门海峡能源/航运封锁、MATCH式证书/位置/固件/维修锁死、医疗船误击呼应第86章、章末Keller/海外导师/活人节点牵引内鬼调查。禁万能破解。'
 p110=f'''你是《科武纪元》作者。修第110章，只输出完整正文。
现稿已基本达标，但缺两处：1医疗船误击链路；2章末内鬼调查钩子。
请在后半段自然加入：医疗船被旧敌我识别/证书白名单/跨战区规则同步失败误击，呼应第86章诊所误判；写权限、识别规则、链路延迟，不写反派降智。
结尾必须落到：锁死清单/固件签名/白名单维护人里出现Keller或海外名校导师技术特征，牵引《内鬼调查》。
保持标题“第110章 天门封锁”，末行（本章完），不要解释。
【现稿】\n{draft110}
'''
 text110,model=mimo(p110); text110=norm(110,'天门封锁',text110); (TEMP/'第110章_V89最终稿.tmp.md').write_text(text110,encoding='utf-8')
 results.append(review_and_save(110,'天门封锁',text110,task110,src110))
 # 156 rewrite from scratch
 src156=BASE/'新版/第156章.md'; ref=(BASE/'新版/第 156 章.md').read_text(encoding='utf-8') if (BASE/'新版/第 156 章.md').exists() else ''
 task156='第156章重返月球：主线为发射/双火箭对接/地月转移/月面着陆/沙克尔顿主基地部署。必须写稳定存在即规则权：连续到达、补给、救援、维护。章末为氦-3开采前补给/救援链首次压力测试。禁遗迹大揭秘、禁量子万能。'
 p156=f'''你是《科武纪元》作者。重写第156章，只输出小说正文，不要评审，不要清单，不要解释。
首行：第156章 重返月球
末行：（本章完）
番茄口径3600-5200字。

硬要求：
1 发射准备→双火箭入轨→轨道对接→地月转移→近月制动→沙克尔顿环形山着陆→主基地展开。
2 双火箭对接要有相对速度、锁紧环、压力检测、人员/货舱通道确认。
3 救援冗余：备用返回舱、轨道待命舱段、氧气/电力余量、救援窗口。
4 连续补给：首批/第二批/第三批补给、备件箱、密封圈、通信中继、生命保障包。
5 规则权不能宣言；用清单、仪表、维护动作、对接口标准体现。
6 铁幕对照：可绕月宣传，但着陆器/加注/预算/政权摇摆拖住，形成“能绕”和“能长期存在”的差距。
7 章末具体钩子：氦-3开采启动前，补给/救援链第一次压力测试（如补给舱着陆偏差、救援窗口延迟、密封圈需授权更换）。
8 禁止遗迹/火星/量子纠缠/未知合金大揭秘。
9 风格：动作、仪表、物理反馈、具名代价。禁文艺比喻、报告腔。

短版参考只能借工程动作，不得复制评审/清单：\n{ref[:2500]}
'''
 text156,model=mimo(p156); text156=norm(156,'重返月球',text156); (TEMP/'第156章_V89最终稿.tmp.md').write_text(text156,encoding='utf-8')
 results.append(review_and_save(156,'重返月球',text156,task156,src156))
 out=BASE/'审核记录/V89_第110_156章最终修复汇总_20260511.md'
 out.write_text('# V8.9 第110/156章最终修复汇总\n\n'+json.dumps(results,ensure_ascii=False,indent=2),encoding='utf-8')
 print(json.dumps({'results':results,'report':str(out)},ensure_ascii=False,indent=2))
 if not all(r['final'] for r in results): sys.exit(2)
if __name__=='__main__': main()
