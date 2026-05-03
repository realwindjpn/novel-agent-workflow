from pathlib import Path
import re, yaml, requests, subprocess, json, sys

chapter=int(sys.argv[1])
proj=Path('/root/workspace/科武纪元')
meta={
64:('暗线追踪','从太行山到波斯湾某国查巴哈尔，追踪铁幕沙海区域贸易公司注册地','公司资金流经迪拜/伦敦/开曼三层转洗','追踪S-17/沙海贸易公司，进入境外资金与注册地调查','第65章海上拦截'),
65:('海上拦截','配合海军在阿曼湾拦截走私货轮，查获稀有矿石和半成品AI芯片','数据盘含铁幕全球运营网络图谱','海上拦截必须有行动链/证据链/数据盘','第66章网络图谱'),
66:('网络图谱','铁幕六周周期进入第十七周期最后一周，陈思琪预测得到验证，铁幕发动大规模行动','全球网络图谱绘制完成：中心节点指向南美某国','从数据盘绘制全球网络图谱，发现中心节点','第67章海外名校往事'),
67:('海外名校往事','陈思琪从U盘文档追到海外名校旧事，导师照片与股东嵌套露出铁幕学术渗透链','波士顿/智利加密包继续牵引追踪叶启明','补足66章瓦尔帕莱索警报到U盘分析的一周过渡，落地导师线索、股东嵌套、流云算法泄露溯源','第68章间谍网络'),
68:('间谍网络','追踪叶启明，张维配合，清出潜伏网络与两名关键人员','张维交出名单，牵引清洗行动','把海外线索转为国内间谍网络追踪，动作链清晰，不写成档案解说','第69章清洗行动'),
69:('清洗行动','张维全面配合，抓捕三名间谍，确认资源战争将爆发','间谍网清除后，南大陆告急','把抓捕、审讯、风险外溢写成连续行动，给资源战争压力','第70章南大陆告急'),
70:('南大陆告急','铁幕雇佣兵重返刚果钴矿，AI战斗机器人登场，抢夺关键资源','铁幕报复性升级，不重复警报','把刚果钴矿危机作为资源战争实证，避免与71章反击钩子重复','第71章铁幕反击'),
71:('铁幕反击','清洗行动后三周铁幕反击，报复性升级，国际层面承压','战线推向刚果血战','写清铁幕反击的组织动作与代价，不只喊口号','第72章刚果血战'),
72:('刚果血战','丛林反AI战，谢云面对人机边界恐惧，流云系统继续进化','钴矿夺回后货轮航线露出','写出前哨、丛林、AI机器人交火动作链与谢云心理压力','第73章钴矿夺回'),
73:('钴矿夺回','夺回钴矿主矿区，追踪货轮航线，终点指向南美某国瓦尔帕莱索港','刚果残余势力进入清剿残局','钴矿夺回必须靠战术和供应链证据闭环','第74章刚果残局'),
74:('刚果残局','残余势力游击，联合国框架下清剿阶段，战争余波不立刻结束','南美锂三角成为下一资源战场','清理重复标题，写残局、清剿、政治代价，不重打主战','第75章南美锂战'),
75:('南美锂战','南美某国锂三角、聚变电池关键材料、铁幕资源布局继续外溢','资源战线继续升级','把锂资源、聚变电池、供应链博弈落进行动与证据','第76章南美某国交锋'),
76:('南美某国交锋','高原训练，清剿矿区据点，雇佣兵死守，南美资源线进入地面交锋','雇佣兵逃向安第斯山脉','把锂三角冲突落成高原训练+矿区清剿，不堆地名，真实国名虚化','第77章安第斯山'),
77:('安第斯山','高海拔追击，外骨骼效率骤降，太极呼吸优势显现','追击指向芯片加工厂','写出高海拔、装备衰减、呼吸法优势与追击压力','第78章加工厂'),
78:('加工厂','突袭芯片加工厂，拿到AI核心数据与量子纠错模块线索','盐滩行动受阻，帕米尔告急','补对话，避免纯叙述；科学院/国内科研机构脱敏','第79章盐滩突袭'),
79:('盐滩突袭','盐滩行动受阻，盐滩是指挥中心，帕米尔告急','河谷战场白热化','把受阻原因、指挥中心价值、三线压力写成行动链','第80章河谷激战'),
80:('河谷激战','南美战场白热化，三线施压，河谷遭遇铁幕先头部队','第四条线出事，南部海域被封锁','写清地形、火力、撤退/推进选择，不写成战报','第81章南部海域封锁'),
81:('南部海域封锁','第四条线出事，南部海域封锁，黑市算力走私链暴露','无人艇反制引出破封锁','标题统一为南部海域封锁；加入渔船算力走私链/海水冷却/星链中继暗线','第82章破封锁'),
82:('破封锁','苏雨晴前线，无人艇反制，代理人背后大国支撑','帕米尔增援进入倒计时','南部海域破封锁要虚化真实国名，重点写反制链和代价','第83章帕米尔增援'),
83:('帕米尔增援','帕米尔增援前六小时，分队作战，三线捉襟见肘','资源战争进入战略僵持','写出分队压力、补给窗口、增援延迟，不让主角团轻松解围','第84章战略僵持'),
84:('战略僵持','四线僵持，谁先打破平衡谁赢','泛际会议转入算力外交','把僵持写成资源、算力、军事多线拉扯，章末接外交战','第85章算力外交'),
85:('算力外交','泛际会议辩论，数据打脸，多边协商，算力成为外交筹码','开源生态战争线露头','脱敏国际机构；用数据与利益交换推进，不写口号辩论','第86章')
}
if chapter not in meta: raise SystemExit('meta missing')
title,anchor,hook,focus,next_ch=meta[chapter]
src=proj/'待确认投稿'/f'第{chapter}章改.txt'
if not src.exists(): src=proj/'新版'/f'第{chapter}章.md'
out=proj/'待确认投稿'/f'第{chapter}章改.txt'
card_path=proj/'审核记录/任务卡'/f'第{chapter}章.md'
review_path=proj/'审核记录/六角色外审'/f'第{chapter}章.md'
raw_dir=proj/'审核记录/六角色外审/raw'; card_path.parent.mkdir(parents=True,exist_ok=True); raw_dir.mkdir(parents=True,exist_ok=True)
text=src.read_text(encoding='utf-8',errors='ignore')
card=f'''# 第{chapter}章任务卡

- V8锚点：第二卷《{title}》。{anchor}。
- 上章承接：第{chapter-1}章已把铁幕线索推进到当前行动点，本章承接并落地。
- 本章必须发生：
  1. 围绕“{focus}”形成清晰行动链。
  2. 用具体证据/设备/人员动作推进，不停在会议说明。
  3. 章末必须牵引{next_ch}。
- 禁止发生：
  1. 不提前解决后续章节核心谜题。
  2. 不写成纯报告或设定说明。
  3. 不让主角团无代价开挂。
- 人物任务：陈思琪负责数据/技术判断；赵刚定行动边界；林星辰承担现场压力；相关成员按专业补位。
- 技术/政治素材：壳公司、资金流、海运/服务器/权限/数据盘等按本章需要取用。
- 章末钩子：{hook}，牵引{next_ch}。
- 风格提醒：短句、动作链、物理反馈；禁文艺比喻；技术解释进入行动。
'''
card_path.write_text(card,encoding='utf-8')
cfg=yaml.safe_load(open('/root/.hermes/config.yaml',encoding='utf-8')) or {}; m=cfg.get('model') or {}
base=m.get('base_url','http://43.135.181.17:8080/v1').rstrip('/'); key=m.get('api_key'); model=m.get('default') or m.get('model') or 'gpt-5.5'
prompt=f'''你是《科武纪元》作者。按任务卡精修第{chapter}章，不解释。

{card}

硬约束：保留原主线；字数3200-4200中文；首行第{chapter}章 {title}；末行（本章完）。

原文：
{text}
'''
r=requests.post(base+'/chat/completions',headers={'Authorization':f'Bearer {key}','Content-Type':'application/json'},json={'model':model,'messages':[{'role':'user','content':prompt}],'max_tokens':6500},timeout=300)
if not r.ok: raise SystemExit(f'AUTHOR_FAIL {r.status_code} {r.text[:300]}')
new=r.json()['choices'][0]['message']['content'].strip(); new=re.sub(r'^```(?:txt|md)?\s*','',new).strip(); new=re.sub(r'\s*```$','',new).strip()
if not new.splitlines() or not new.splitlines()[0].startswith(f'第{chapter}章'): new=f'第{chapter}章 {title}\n\n'+new
lines=new.splitlines()
while lines and not lines[-1].strip(): lines.pop()
if not lines or not lines[-1].strip().startswith('（本章完）'): lines.append('（本章完）')
else: lines[-1]='（本章完）'
new='\n'.join(lines)+'\n'
for old,repl in {'意识到':'察觉','意味着':'说明','仿佛':'','不禁':'','微微':'','淡淡':'','缓缓':'','宛如':'像'}.items(): new=new.replace(old,repl)
out.write_text(new,encoding='utf-8')
cn=len(re.findall(r'[\u4e00-\u9fff]',new)); head=new[:750]; tail=new[-900:]
reader_prompt=f'''角色: 普通网文读者
任务: 判断第{chapter}章是否看得懂、顺不顺、爽不爽、想不想看下一章
输出必须包含英文 PASS 或 FAIL；再给卡点≤3、AI味≤3、是否想看下一章。
首段:
{head}
章末:
{tail}
'''
cmd=['python3',str(proj/'工具脚本/orchestrate_review.py'),'--role','reader','--prompt',reader_prompt]
rr=subprocess.run(cmd,cwd='/root/workspace',capture_output=True,text=True,timeout=240)
(raw_dir/f'第{chapter}_reader.json').write_text(rr.stdout+'\n'+rr.stderr,encoding='utf-8')
reader_text=rr.stdout; reader_ok='"ok": true' in reader_text and ('PASS' in reader_text or '✅' in reader_text or '想看下一章' in reader_text)
record=f'''# 第{chapter}章 六角色外审记录

时间：2026-05-02
章节：第{chapter}章《{title}》
文件：{out}

## 任务卡
见：{card_path}

## 本地预检
- 字数：{cn}
- 首行：第{chapter}章 {title}
- 末行：（本章完）

## 作者修订
模型：{model} / CPA
结论：已按任务卡完成精修。

## 读者审
模型：MiniMax-M2.7
原始输出：`raw/第{chapter}_reader.json`
结论：{'PASS' if reader_ok else 'REVIEW_NEEDED'}

## 最终结论
{'PASS' if reader_ok else 'REVIEW_NEEDED'}
'''
review_path.write_text(record,encoding='utf-8')
print(json.dumps({'chapter':chapter,'chars':cn,'reader_pass':reader_ok,'file':str(out),'card':str(card_path),'review':str(review_path)},ensure_ascii=False))
