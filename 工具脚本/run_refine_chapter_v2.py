from pathlib import Path
import re, yaml, requests, subprocess, json, sys, os
# Load .env if present
env_path = Path.home() / '.hermes' / '.env'
if env_path.exists():
    for line in env_path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            os.environ.setdefault(k.strip(), v.strip())

ch=int(sys.argv[1])
proj=Path('/root/workspace/科武纪元')
meta={
62:('审讯','张维/方致远审讯，供述壳公司、联络方式与沙海贸易公司线索','沙海区域贸易公司与三层壳结构浮出','补足审讯证据链、胁迫+利诱、李国强交接链，明确沙海区域贸易公司','第63章铁幕轮廓'),
63:('铁幕轮廓','李国强被捕后，铁幕联盟轮廓浮出：内部不透明、生态标准垄断、芯片+闭源软件+大模型绑定','暗线追踪露出','补方宁工程生态判断，写清生态锁定与各频道权限隔离，不写成纯报告','第64章暗线追踪'),
66:('网络图谱','铁幕六周周期进入第十七周期最后一周，陈思琪预测得到验证，铁幕发动大规模行动','中心节点与海外名校旧档案关联','缝合海上拦截到数据室分析，行动化绘制全球网络图谱，章末牵引海外名校往事','第67章海外名校往事'),
67:('海外名校往事','陈思琪从U盘文档追到海外名校旧事，导师照片与股东嵌套露出铁幕学术渗透链','波士顿/智利加密包继续牵引追踪叶启明','落地导师旧照、股权穿透、流云算法特征码溯源，章末抓到叶启明活跃信号','第68章间谍网络'),
76:('南美某国交锋','高原训练，清剿矿区据点，雇佣兵死守，南美资源线进入地面交锋','雇佣兵逃向安第斯山脉','把锂三角冲突落成高原训练+矿区清剿，不堆地名，真实国名虚化','第77章安第斯山'),
77:('安第斯山','高海拔追击，外骨骼效率骤降，太极呼吸优势显现','追击指向芯片加工厂','写出高海拔、装备衰减、呼吸法优势与追击压力','第78章加工厂'),
78:('加工厂','突袭芯片加工厂，拿到AI核心数据与量子纠错模块线索','盐滩行动受阻，帕米尔告急','补对话，避免纯叙述；科学院/国内科研机构脱敏','第79章盐滩突袭'),
79:('盐滩突袭','盐滩行动受阻，盐滩是指挥中心，帕米尔告急','河谷战场白热化','把受阻原因、指挥中心价值、三线压力写成行动链','第80章河谷激战'),
80:('河谷激战','南美战场白热化，三线施压，河谷遭遇铁幕先头部队','第四条线出事，南部海域被封锁','写清地形、火力、撤退/推进选择，不写成战报','第81章南部海域封锁'),
81:('南部海域封锁','第四条线出事，南部海域封锁，黑市算力走私链暴露','无人艇反制引出破封锁','标题统一为南部海域封锁；加入渔船算力走私链/海水冷却/星链中继暗线','第82章破封锁'),
82:('破封锁','苏雨晴前线，无人艇反制，代理人背后大国支撑','帕米尔增援进入倒计时','南部海域破封锁要虚化真实国名，重点写反制链和代价','第83章帕米尔增援'),
83:('帕米尔增援','帕米尔增援前六小时，分队作战，三线捉襟见肘','资源战争进入战略僵持','写出分队压力、补给窗口、增援延迟，不让主角团轻松解围','第84章战略僵持'),
84:('战略僵持','四线僵持，谁先打破平衡谁赢','泛际会议转入算力外交','把僵持写成资源、算力、军事多线拉扯，章末接外交战','第85章算力外交'),
85:('算力外交','泛际会议辩论，数据打脸，多边协商，算力成为外交筹码','开源生态战争线露头','脱敏国际机构；用数据与利益交换推进，不写口号辩论','第86章铁幕反击'),
86:('铁幕反击','铁幕发动全球网络攻击，并在泛际会议发起开源生态安全审查提案，围剿开源路线','开源vs闭源两条道路第一次正面交锋，攻击代码源自海外名校导师','写出网络攻击、会议围剿、欧陆分支3秒延迟、陈思琪反制；生态争论要进入行动，不写口号','第87章算法对决'),
87:('算法对决','陈思琪模拟测试进入关键阶段，流云迎战铁幕AI，虚拟空间算力攻防','铁幕AI核心弱点：伦理判断模块逻辑死循环','把算法对决写成可感知的攻防链：算力调度、规则冲突、误判代价；避免论文腔','第88章算力崩溃'),
88:('算力崩溃','铁幕AI崩溃但潜伏代码失控，城市基础设施瘫痪，陈思琪出现道德危机','算力攻击引发连锁反应，陈思琪承受心理重压','写出失控后果、城市代价和陈思琪责任感；不要把哭戏写空','第89章城市巷战'),
89:('城市巷战','算力攻击结束后城市基础设施失控，小队在废墟中与失控智能机器巷战','谢云金刚拳在城市建筑掩护下威力倍增','写清巷战地形、误伤风险、失控机器行为逻辑；动作链优先','第90章能源危机'),
90:('能源危机','全球能源告警扩散，算力攻击连锁反应导致能源配给制启动；算力券成为硬通货','能源-算力恶性循环形成，资本垄断催生黑市生态','落地民生压力、算力券、黑市黄牛、三层壳公司吃差价；勿写成宏观报告','第91章南部海域再战'),
91:('南部海域再战','南部海域封锁被撕开后并未安静，苏雨晴指挥后续清剿战','海底矿物开采权回归联合政府管理','写出清剿代价、无人艇反制、海上秩序重建；虚化真实国名','第92章盐滩计划'),
92:('盐滩计划','盐滩突袭详细计划在圣地亚哥安全屋用三天完成','盐滩是铁幕全球供应链关键枢纽','写计划推演、风险拆解、补给窗口和行动取舍；避免纯会议纪要','第93章南大陆牵制'),
93:('南大陆牵制','盐滩突袭原定提前启动，被南大陆急报压住，铁幕在刚果发动新一轮攻势','双线牵制拖住兵力，盐滩只能延后','写出两线拉扯、兵力不足、指挥层艰难取舍；不轻松解围','第94章盐滩之战'),
94:('盐滩之战','林星辰靴底碾碎盐壳，阿塔卡马盐滩夜袭启动','盐滩据点地下发现铁幕全球指挥网络核心节点','写夜袭、盐壳地形、地下节点发现与战术代价；动作链要硬','第95章算力对决'),
95:('算力对决','南部海域决战与算法对决交汇，陈思琪利用铁幕内部分歧，策反欧陆分支提供密钥，流云险胜','流云获胜但出现自生成代码，东方开源生态链形成','写出欧陆分支密钥、流云险胜、自主芯片适配与开源生态分水岭；不要口号化','第96章数字地震')
}
if ch not in meta: raise SystemExit('meta missing')
title,anchor,hook,focus,next_ch=meta[ch]
orig=proj/'新版'/f'第{ch}章.md'
if not orig.exists(): orig=proj/'待确认投稿'/f'第{ch}章改.txt'
out=proj/'待确认投稿'/f'第{ch}章改.txt'
card=proj/'审核记录/任务卡'/f'第{ch}章.md'
review=proj/'审核记录/六角色外审'/f'第{ch}章.md'
raw_dir=proj/'审核记录/六角色外审/raw'
card.parent.mkdir(parents=True,exist_ok=True); review.parent.mkdir(parents=True,exist_ok=True); raw_dir.mkdir(parents=True,exist_ok=True)
text=orig.read_text(encoding='utf-8',errors='ignore')
head=text[:900]; tail=text[-1100:]

def call(role,prompt,timeout=260):
    cmd=['python3',str(proj/'工具脚本/orchestrate_review.py'),'--role',role,'--prompt',prompt]
    rr=subprocess.run(cmd,cwd='/root/workspace',capture_output=True,text=True,timeout=timeout)
    raw=(rr.stdout or '')+'\n'+(rr.stderr or '')
    (raw_dir/f'第{ch}_{role}_v2.json').write_text(raw,encoding='utf-8')
    return raw

base_card=f'''# 第{ch}章精修任务卡V2
- V8锚点：第二卷《{title}》。{anchor}。
- 上章承接：承接第{ch-1}章行动后果。
- 本章必须发生：{focus}。
- 禁止发生：不提前解决后续谜题；不写成报告；不靠口号推进。
- 章末钩子：{hook}，牵引{next_ch}。
- 风格：物理反馈/行动链/短句；禁文艺比喻；技术解释进入动作。
'''
pre_common=f'''任务: 先审原版第{ch}章，给作者精修意见。输出≤500字，必须给“修改清单”。
V8任务卡:\n{base_card}
原版首段:\n{head}
原版章末:\n{tail}
'''
editor_pre=call('editor','角色: 网文编辑\n关注: 大纲对齐/章节功能/结构节奏/章末钩子/投稿风险\n'+pre_common)
military_pre=call('military','角色: 军事顾问\n关注: 行动链/战术/组织/装备可信度。无军事内容则写“无硬伤”。\n'+pre_common)
science_pre=call('science','角色: 科学顾问\n关注: 技术设定/科普可读性/术语是否进入行动。无硬伤则写“无硬伤”。\n'+pre_common)
card_text=base_card+f'''\n## 编辑写前意见\n{editor_pre[:900]}\n\n## 军事顾问写前意见\n{military_pre[:700]}\n\n## 科学顾问写前意见\n{science_pre[:700]}\n'''
card.write_text(card_text,encoding='utf-8')

cfg=yaml.safe_load(open('/root/.hermes/config.yaml',encoding='utf-8')) or {}; m=cfg.get('model') or {}
provider_name=m.get('provider') or 'cpa'
provider=(cfg.get('providers') or {}).get(provider_name,{})
base=(m.get('base_url') or provider.get('base_url') or 'http://43.135.181.17:8080/v1').rstrip('/')
key=m.get('api_key') or provider.get('api_key')
key_env=provider.get('key_env') or m.get('key_env')
if not key and key_env: key=os.environ.get(key_env,'')
model=m.get('default') or m.get('model') or provider.get('default_model') or provider.get('model') or 'gpt-5.5'
if not key:
    raise SystemExit(f'AUTHOR_FAIL no api_key for provider {provider_name}')
prompt=f'''你是《科武纪元》作者。按精修任务卡V2改第{ch}章，只输出正文。
硬约束：保留主线；首行“第{ch}章 {title}”；末行“（本章完）”；3200-5200中文字；不得解释。

{card_text[:3000]}

原版全文：
{text}
'''
r=requests.post(base+'/chat/completions',headers={'Authorization':f'Bearer {key}','Content-Type':'application/json'},json={'model':model,'messages':[{'role':'user','content':prompt}],'max_tokens':7500},timeout=300)
if not r.ok: raise SystemExit(f'AUTHOR_FAIL {r.status_code} {r.text[:300]}')
new=r.json()['choices'][0]['message']['content'].strip()
new=re.sub(r'^```(?:txt|md)?\s*','',new).strip(); new=re.sub(r'\s*```$','',new).strip()
if not new.splitlines() or not new.splitlines()[0].startswith(f'第{ch}章'): new=f'第{ch}章 {title}\n\n'+new
lines=new.splitlines()
while lines and not lines[-1].strip(): lines.pop()
if not lines or not lines[-1].strip().startswith('（本章完）'): lines.append('（本章完）')
else: lines[-1]='（本章完）'
new='\n'.join(lines)+'\n'
for old,repl in {'意识到':'察觉','意味着':'说明','仿佛':'','不禁':'','微微':'','淡淡':'','缓缓':'','宛如':'像'}.items(): new=new.replace(old,repl)
out.write_text(new,encoding='utf-8')
cn=len(re.findall(r'[\u4e00-\u9fff]',new)); nhead=new[:900]; ntail=new[-1100:]
post=f'''任务: 写后门禁第{ch}章。输出必须含英文 PASS 或 FAIL；若有必改/硬伤/不宜进入下一章则 FAIL。\n任务卡:\n{base_card}\n首段:\n{nhead}\n章末:\n{ntail}\n'''
editor_post=call('editor','角色: 网文编辑\n关注: 是否符合任务卡/大纲/结构/钩子/投稿风险。\n'+post)
reader_post=call('reader','角色: 普通网文读者\n关注: 看懂/顺/爽/AI味/想不想看下一章。\n'+post)
def passed(raw):
    if '"ok": true' not in raw or 'PASS' not in raw: return False
    return not any(w in raw for w in ['FAIL','必改','硬伤','不宜进入下一章','不能进入下一章','重写'])
ep=passed(editor_post); rp=passed(reader_post)
final=ep and rp and cn>=3000
rec=f'''# 第{ch}章 六角色外审记录

时间：2026-05-02
章节：第{ch}章《{title}》
原版：{orig}
改版：{out}

## 精修V2流程
- 写前：编辑 + 军事顾问 + 科学顾问审原版并给修改意见
- 作者：按任务卡改写
- 写后：编辑 + 读者双门禁

## 本地预检
- 字数：{cn}
- 首行：第{ch}章 {title}
- 末行：（本章完）

## 原始输出
- 编辑写前：raw/第{ch}_editor_v2.json
- 军事顾问写前：raw/第{ch}_military_v2.json
- 科学顾问写前：raw/第{ch}_science_v2.json
- 编辑写后：raw/第{ch}_editor_v2.json
- 读者写后：raw/第{ch}_reader_v2.json

## 门禁
- 编辑写后：{'PASS' if ep else 'REVIEW_NEEDED'}
- 读者写后：{'PASS' if rp else 'REVIEW_NEEDED'}

## 最终结论
{'PASS' if final else 'REVIEW_NEEDED'}
'''
review.write_text(rec,encoding='utf-8')
print(json.dumps({'chapter':ch,'chars':cn,'editor_pass':ep,'reader_pass':rp,'final_pass':final,'file':str(out),'card':str(card),'review':str(review)},ensure_ascii=False))
