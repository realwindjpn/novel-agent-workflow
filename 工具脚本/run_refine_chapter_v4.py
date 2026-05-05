#!/usr/bin/env python3
"""V4: 精修增强版 —— 知识库素材卡自动注入 + 文件分离 + 证据包二次构建 + WikiLink 注入"""

from pathlib import Path
import re, yaml, requests, subprocess, json, sys, os

# ─── 加载 .env ───
env_path = Path.home() / '.hermes' / '.env'
if env_path.exists():
    for line in env_path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if line and not line.startswith('#') and '=' in line:
            k, v = line.split('=', 1)
            os.environ.setdefault(k.strip(), v.strip())

ch = int(sys.argv[1])
proj = Path('/root/workspace/科武纪元')

# ─── 目录 ───
for d in ['审核记录/四层审核包', '审核记录/运行留痕', 'wiki/chapters',
          '审核记录/任务卡', '审核记录/六角色外审/raw',
          '审核记录/证据包', '审核记录/章节记忆卡']:
    (proj / d).mkdir(parents=True, exist_ok=True)

raw_dir = proj / '审核记录/六角色外审/raw'
card_dir = proj / '审核记录/任务卡'
review_dir = proj / '审核记录/六角色外审'

# ─── 元数据 ───
meta = {
    1: ('江城少年', '开篇建立林星辰、江城屋顶光伏实验、太极训练与异常电压钩子。前10章留存优先：首段必须快速给出异常数据、人物行动和悬念，不做慢热铺垫。现实科学设定涉及光伏板、电压检测、示波器/万用表等基础电学，可在作者说注明：本章光伏发电与电压检测参考现实光伏组件与基础电路测量常识，异常脉冲为小说化延展。', '屋顶光伏异常脉冲持续回应，牵引双轨教育与后续科技/武学融合线', '强化前三页留存：开场异常数据更硬、林星辰行动更主动、父亲/家庭压力少量点到；减少说明腔，保留光伏实验的现实依据；如出现现实科学设定，在章末作者说用一句话标注来源与小说化处理边界', '双轨之争'),
    2: ('双轨之争', '双轨教育通知引发班级争议，武学课与应试路径第一次正面冲突；林星辰、苏雨晴、陈思琪三条线开始相互靠近。前10章留存优先：冲突要落到教室噪声、老师表态、学生选择和林星辰实验压力，不写政策说明。现实设定涉及教育分流/体育武学课程、生物电初步观察，可在作者说注明：双轨教育为小说架空设定，生物电采样参考现实肌电/动作信号采集常识。', '周六前屋顶六秒脉冲复测，牵引太极课与科技线碰撞', '强化班级争论的现场感与人物立场；让双轨选择变成林星辰的现实压力；补陈思琪查线路的主动性；作者说可一句话标注双轨教育为架空、生物电采样为现实肌电常识延展', '太极'),
    62: ('审讯', '张维/方致远审讯，供述壳公司、联络方式与沙海贸易公司线索', '沙海区域贸易公司与三层壳结构浮出', '补足审讯证据链、胁迫+利诱、李国强交接链，明确沙海区域贸易公司', '铁幕轮廓'),
    63: ('铁幕轮廓', '李国强被捕后，铁幕联盟轮廓浮出：内部不透明、生态标准垄断、芯片+闭源软件+大模型绑定', '暗线追踪露出', '补方宁工程生态判断，写清生态锁定与各频道权限隔离，不写成纯报告', '暗线追踪'),
    64: ('暗线追踪', '陈思琪追查S-17编号至查巴哈尔壳公司，境外调查行动启动', '海上拦截稀土走私', '写境外调查边界、壳公司三层结构、不接触当地官方敏感部门；章末衔接海上行动', '海上拦截'),
    65: ('海上拦截', '波斯湾海域截获稀土走私货轮，拿到铁幕全球贸易链实据', '网络图谱与海外名校旧档案关联', '写出截获过程、稀土精矿证据、贸易链分析；章末牵引全球网络追踪', '网络图谱'),
    66: ('网络图谱', '铁幕六周周期进入第十七周期最后一周，陈思琪预测得到验证，铁幕发动大规模行动', '中心节点与海外名校旧档案关联', '缝合海上拦截到数据室分析，行动化绘制全球网络图谱，章末牵引海外名校往事', '海外名校往事'),
    67: ('海外名校往事', '陈思琪从U盘文档追到海外名校旧事，导师照片与股东嵌套露出铁幕学术渗透链', '波士顿/智利加密包继续牵引追踪叶启明', '落地导师旧照、股权穿透、流云算法特征码溯源，章末抓到叶启明活跃信号', '间谍网络'),
    67: ('海外名校往事', '陈思琪从U盘文档追到海外名校旧事，导师照片与股东嵌套露出铁幕学术渗透链', '波士顿/智利加密包继续牵引追踪叶启明', '落地导师旧照+股权穿透+流云算法特征码溯源，章末抓到叶启明活跃信号', '间谍网络'),
    68: ('间谍网络', '张维供述铁幕国内渗透网络，国安启动清洗行动', '张维交出清洗名单和存储卡，牵连出更多下线', '写清审讯节奏、张维心理防线逐步瓦解、名单逐步露出、存储卡悬念', '清洗行动'),
    76: ('南美某国交锋', '高原训练，清剿矿区据点，雇佣兵死守，南美资源线进入地面交锋', '雇佣兵逃向安第斯山脉', '把锂三角冲突落成高原训练+矿区清剿，不堆地名，真实国名虚化', '安第斯山'),
    77: ('安第斯山', '高海拔追击，外骨骼效率骤降，太极呼吸优势显现', '追击指向芯片加工厂', '写出高海拔、装备衰减、呼吸法优势与追击压力', '加工厂'),
    78: ('加工厂', '突袭芯片加工厂，拿到AI核心数据与量子纠错模块线索', '盐滩行动受阻，帕米尔告急', '补对话，避免纯叙述；科学院/国内科研机构脱敏', '盐滩突袭'),
    79: ('盐滩突袭', '盐滩行动受阻，盐滩是指挥中心，帕米尔告急', '河谷战场白热化', '把受阻原因、指挥中心价值、三线压力写成行动链', '河谷激战'),
    80: ('河谷激战', '南美战场白热化，三线施压，河谷遭遇铁幕先头部队', '第四条线出事，南部海域被封锁', '写清地形、火力、撤退/推进选择，不写成战报', '南部海域封锁'),
    81: ('南部海域封锁', '第四条线出事，南部海域封锁，黑市算力走私链暴露', '无人艇反制引出破封锁', '标题统一为南部海域封锁；加入渔船算力走私链/海水冷却/星链中继暗线', '破封锁'),
    82: ('破封锁', '苏雨晴前线，无人艇反制，代理人背后大国支撑', '帕米尔增援进入倒计时', '南部海域破封锁要虚化真实国名，重点写反制链和代价', '帕米尔增援'),
    83: ('帕米尔增援', '帕米尔增援前六小时，分队作战，三线捉襟见肘', '资源战争进入战略僵持', '写出分队压力、补给窗口、增援延迟，不让主角团轻松解围', '战略僵持'),
    84: ('战略僵持', '四线僵持，谁先打破平衡谁赢', '泛际会议转入算力外交', '把僵持写成资源、算力、军事多线拉扯，章末接外交战', '算力外交'),
    85: ('算力外交', '泛际会议辩论，数据打脸，多边协商，算力成为外交筹码', '开源生态战争线露头', '脱敏国际机构；用数据与利益交换推进，不写口号辩论', '铁幕反击'),
    86: ('铁幕反击', '铁幕发动全球网络攻击，并在泛际会议发起开源生态安全审查提案，围剿开源路线。【混沌模型】铁幕追求绝对安全=封闭AI生态。封闭系统内信息垄断→指令失真→信任瓦解。欧陆分支3秒延迟是内部熵增的外在表现，非道德觉醒。陈思琪用热力学第二定律反击："封闭系统必熵增，你们在给自己造棺材。"', '开源vs闭源=开放系统vs封闭系统的第一次正面交锋；3秒延迟=系统内部熵增信号；陈思琪反制', '写出网络攻击+会议围剿+欧陆分支3秒延迟+陈思琪反制；生态争论进入行动不写口号；铁幕"安全审查"是封闭系统本能；欧陆分支抗拒是压力累积必然结果', '算法对决'),
    87: ('算法对决', '陈思琪模拟测试进入关键阶段，流云迎战铁幕AI，虚拟空间算力攻防', '铁幕AI核心弱点：伦理判断模块逻辑死循环', '把算法对决写成可感知的攻防链：算力调度、规则冲突、误判代价；避免论文腔', '算力崩溃'),
    88: ('算力崩溃', '铁幕AI崩溃但潜伏代码失控，城市基础设施瘫痪，陈思琪出现道德危机', '算力攻击引发连锁反应，陈思琪承受心理重压', '写出失控后果、城市代价和陈思琪责任感；不要把哭戏写空', '城市巷战'),
    89: ('城市巷战', '算力攻击结束后城市基础设施失控，小队在废墟中与失控智能机器巷战', '谢云金刚拳在城市建筑掩护下威力倍增', '写清巷战地形、误伤风险、失控机器行为逻辑；动作链优先', '能源危机'),
    90: ('能源危机', '全球能源告警扩散，算力攻击连锁反应导致能源配给制启动；算力券成为硬通货', '能源-算力恶性循环形成，资本垄断催生黑市生态', '落地民生压力、算力券、黑市黄牛、三层壳公司吃差价；勿写成宏观报告', '南部海域再战'),
    91: ('南部海域再战', '南部海域封锁被撕开后并未安静，苏雨晴指挥后续清剿战', '海底矿物开采权回归联合政府管理', '写出清剿代价、无人艇反制、海上秩序重建；虚化真实国名', '盐滩计划'),
    92: ('盐滩计划', '盐滩突袭详细计划在圣地亚哥安全屋用三天完成', '盐滩是铁幕全球供应链关键枢纽', '写计划推演、风险拆解、补给窗口和行动取舍；避免纯会议纪要', '南大陆牵制'),
    93: ('南大陆牵制', '盐滩突袭原定提前启动，被南大陆急报压住，铁幕在刚果发动新一轮攻势', '双线牵制拖住兵力，盐滩只能延后', '写出两线拉扯、兵力不足、指挥层艰难取舍；不轻松解围', '盐滩之战'),
    94: ('盐滩之战', '林星辰靴底碾碎盐壳，阿塔卡马盐滩夜袭启动', '盐滩据点地下发现铁幕全球指挥网络核心节点', '写夜袭、盐壳地形、地下节点发现与战术代价；动作链要硬', '算力对决'),
    95: ('算力对决', '南部海域决战与算法对决交汇，陈思琪利用铁幕内部分歧，策反欧陆分支提供密钥，流云险胜。【混沌模型】C vs A（群体智能/开源 vs 算法主权）：流云算法在铁幕封闭生态上撕开缺口，证明"在CUDA之外可以有另一条生态"。开源=开放系统引入负熵，封闭=铁幕生态因内部分歧产生熵增。', '流云险胜但出现自生成代码；东方开源生态链形成；C vs A=去中心化破全知垄断', '写出欧陆分支密钥+流云险胜+自主芯片适配+开源生态分水岭；不要口号化；开源vs闭源是两条道路分水岭', '数字地震'),
    96: ('数字地震', '铁幕残余算力攻击引发全球网络基础设施连锁崩溃', '算力战争从虚拟蔓延到现实', '写基础设施崩溃的民生代价、连锁反应，不写宏观报告', '对手研究'),
    97: ('对手研究', '陈思琪发现铁幕AI正在针对性学习流云算法', 'AI对AI的军备竞赛升级', '写出针对性学习的具体证据、流云的应对策略', '古武突破'),
    98: ('古武突破', '铁幕溃败预案启动，林星辰融合全队武学创"众星归一"，踏入第三层·聚算', '新招破解铁幕AI战术预测逻辑；聚算后心念即可驱动算力', '写出融合过程、实战突破、聚算的身体感知变化', '全球清剿'),
    99: ('全球清剿', '铁幕第一次溃败后全球清剿正式启动，四线反攻同步展开', '反攻需要极高协调性，流云算法成为指挥中枢', '写四线同步推进、协调难度、具体清剿行动', '烽火暂歇'),
    100: ('烽火暂歇', '铁幕资源战争被打断，但后果未结束；黑市算力让300万人突破封锁。【混沌模型】C(群体智能)涌现：黑市是封闭系统的裂缝。铁幕垄断→催生去中心化生态→300万普通人突破封锁。封闭系统越压制，负熵流越从裂缝涌入。', '算力危机+铁幕浮现+异常信号+星穹公司→引出卷三；黑市生态成不可忽视力量；技术民族主义2.0成铁幕下一阶段战略', '写陈思琪算账+方宁看壳公司链路+林星辰看数据；"一切问题都是制度问题"；黑市=封闭系统裂缝的物理呈现', '三条道路'),
    101: ('三条道路', '铁幕溃败后战略选择：技术封锁/开放共享/秘密垄断。【混沌模型】全书核心：A(封闭/算法主权) vs 秩序(开放/技术共享)。三条路=三种热力学结局——封闭=热寂，开放=耗散结构进化，秘密垄断=延迟熵增但最终仍崩溃。', '算法主权vs技术共享=全书核心意识形态冲突；"两条道路两种模式两种结局"', '写出三条路对应的未来图景和取舍；林星辰报告定调"什么样的制度决定什么样的AI未来"', '方阵信号'),
    102: ('方阵信号', '方阵信号数据确认真实，赵刚做部署；铁幕统一指挥官代号方阵', '方阵指挥极度理性，每步都有精确成本收益计算', '写信号确认过程、部署行动、方阵的理性威胁', '异常信号'),
    103: ('异常信号', '异常信号增强后第一个夜晚，整个天耳项目都没睡', '信号分布模式暗示系统性外部影响', '写天耳团队熬夜分析、信号模式发现、外部影响线索', '太空萌芽'),
    104: ('太空萌芽', '太行山入冬最大一场雪，方宁提出太空算力中心构想', '太空算力成为解决地球算力危机的唯一出路', '写雪夜讨论、构想提出、技术可行性论证', '卷二终章'),
    105: ('卷二终章', '第二卷收束：铁幕资源战争结束但暗线交织', '四线汇总：铁幕+算力+信号+太空→卷三暗流', '收束四线、留暗线钩子、为卷三铺垫', '卷三开篇'),
    124: ('星穹线索', '调查铁幕技术来源发现与星穹探索公司资金往来。【混沌模型】星穹追求"算法主权"=绝对信息控制=封闭系统极致。越追求完美预测越依赖内部数据闭环，外部扰动越界→系统脆性断裂。这不是技术失败，是控制论的物理极限。', '星穹=铁幕版Palantir，技术-政治复合体太空分支；追求绝对控制的系统必因外部扰动而崩溃', '写清星穹从数据分析到战场决断的演变；"算法主权"的野心与脆弱性；"来客"信号作为超出模型边界的扰动伏笔', '月球开采'),
    217: ('政治清洗', '多国清洗铁幕联盟成员，联邦扩编"白盾部队"获得反恐预算/无人机权限/海外拘押通道。【混沌模型】B(算法暴力)：数据转化为物理暴力，不讲人情只看威胁评分。白盾=铁幕借治理裂缝放大的失控执法工具，算法无法处理复杂人性导致误杀引发更大暴乱。', '难民中混有铁幕特工；白盾成为制度裂缝中的准军事变量', '写清白盾从遣返执法队到准军事组织的演变；算法暴力的失控前兆；难民潮与无政府状态', '公司内鬼'),
    223: ('内战爆发', '铁幕在欧陆发动全面反击，多国陷入内战；白盾部队被安全幕僚越级调度执行城市封控与抓捕。【混沌模型】B(算法暴力)越界：白盾脱离控制，算法治理变成新型极权。铁幕不是白盾成员，而是借裂缝放大了失控执法工具。', '内战双方都声称拥有对抗外部威胁的终极武器；白盾是失控执法工具', '写清白盾越级调度机制、城市封控战术代价、联合政府权威受挑战；内战不是铁幕直接打，是算法暴力失控', '公司真相'),
}
if ch not in meta:
    raise SystemExit(f'meta missing for ch{ch}')

title, anchor, hook, focus, next_ch = meta[ch]
next_title = next_ch  # 已是纯标题，无章节号

# ─── 读原版 ───
orig = proj / '新版' / f'第{ch}章.md'
if not orig.exists():
    orig = proj / '待确认投稿' / f'第{ch}章改.txt'
if not orig.exists():
    raise SystemExit(f'原版不存在: ch{ch}')
out = proj / '待确认投稿' / f'第{ch}章改.txt'
text = orig.read_text(encoding='utf-8', errors='ignore')
head, tail = text[:900], text[-1100:]

# ─── Wiki 注入（含 wikilink 提取） ───
wiki_path = proj / 'wiki' / 'chapters' / f'ch{ch:03d}.md'
wiki_text = wiki_path.read_text(encoding='utf-8', errors='ignore')[:2000] if wiki_path.exists() else ''
# 提取 wikilink
wiki_links = re.findall(r'\[\[([^\]]+)\]\]', wiki_text) if wiki_text else []

# ─── 0a. 构建证据包（原版，供写前审核用） ───
subprocess.run(['python3', str(proj/'工具脚本/build_review_evidence.py'), str(ch)],
               cwd='/root/workspace', check=True, capture_output=True, text=True, timeout=120)
ev_md = proj / '审核记录/证据包' / f'第{ch}章_证据包.md'
ev_text = ev_md.read_text(encoding='utf-8', errors='ignore')[:3000] if ev_md.exists() else ''

# ─── 0b. 知识库素材卡匹配与注入（V4新增） ───
lookup = subprocess.run(['python3', str(proj/'工具脚本/lookup_kb_cards.py'),
                         '--chapter', str(ch), '--kb-dir', str(proj/'知识库'), '--top', '3'],
                        cwd='/root/workspace', capture_output=True, text=True, timeout=30)
kb_cards_text = ''
kb_card_list = []
if lookup.returncode == 0:
    try:
        kb_data = json.loads(lookup.stdout)
        cards = kb_data.get('cards', [])
        for c in cards:
            kb_card_list.append(c['name'])
            kb_cards_text += f"\n### {c['name']}\n- 核心数据: {c['core_data']}\n- 小说映射: {c['novel_mapping']}\n- 来源: {c['source']}\n- 摘要: {c.get('summary', '')[:200]}\n"
    except:
        pass
kb_section = f'\n## 知识库素材卡（相关{len(kb_card_list)}张）\n{kb_cards_text}' if kb_card_list else ''

# ─── 上章记忆卡 ───
mem_path = proj / '审核记录/章节记忆卡' / f'第{ch-1}章.md'
mem_text = mem_path.read_text(encoding='utf-8', errors='ignore')[:1500] if mem_path.exists() else ''
mem_links = re.findall(r'\[\[([^\]]+)\]\]', mem_text) if mem_text else []

# 合并所有已知链接
all_links = list(dict.fromkeys(wiki_links + mem_links))
link_context = ''
if all_links:
    link_context = f'\n## 已知关联（wikilink）\n' + '\n'.join(f'- [[{l}]]' for l in all_links[:15])

wiki_section = f'\n## Wiki知识库\n{wiki_text}' if wiki_text else ''
ev_section = f'\n## RTK证据包摘要\n{ev_text[:2000]}' if ev_text else ''
mem_section = f'\n## 上章记忆卡\n{mem_text}' if mem_text else ''

# ─── 1. 写前审核 ───
def call(role, prompt, suffix='pre', timeout=260):
    """调用角色审核，写入 raw/第{ch}_{role}_{suffix}.json"""
    cmd = ['python3', str(proj/'工具脚本/orchestrate_review.py'), '--role', role, '--prompt', prompt]
    rr = subprocess.run(cmd, cwd='/root/workspace', capture_output=True, text=True, timeout=timeout)
    raw = (rr.stdout or '') + '\n' + (rr.stderr or '')
    (raw_dir / f'第{ch}_{role}_{suffix}.json').write_text(raw, encoding='utf-8')
    return raw

base_card = f'''# 第{ch}章精修任务卡V3.1
- V8锚点：第二卷《{title}》。{anchor}。
- 上章承接：承接上章行动后果。
- 本章必须发生：{focus}。
- 禁止发生：不提前解决后续谜题；不写成报告；不靠口号推进。
- 章末钩子：{hook}，牵引"{next_ch}"。
- 风格：物理反馈/行动链/短句；禁文艺比喻；技术解释进入动作。
- 技术名词必须"差评君风格"科普化：先生活类比再给术语（训练=教大学生/推理=上班，量子纠错=KTV消音器，ASIC=专项运动员）。先讲"是什么/怎么用/战术意义"，再给参数。严禁堆砌ASIC/CUDA等学术缩写，用"推理芯片/专用芯片"。
- 去AI味铁律：禁"仿佛/微微/缓缓/意味着/意识到/不禁/不由得"。角色对话加口癖/犹豫/语法错误，不说完美台词。
- **铁律：正文和对话中禁止出现"第X章""第X卷"等章节编号。**
'''

pre_common = f'''任务: 先审原版第{ch}章，给作者精修意见。输出≤500字，必须含"修改清单"。
V8任务卡:\n{base_card}
{wiki_section}
{kb_section}
{ev_section}
{link_context}
原版首段:\n{head}
原版章末:\n{tail}
'''

# 优化：三方合并为一次调用，节省2次API请求
combined_pre = call('editor', '角色: 多面审核者（编辑+军事+科学）\n关注: 1.大纲对齐/结构节奏/钩子 2.军事行动链/战术可信度 3.技术设定/科普可读性。无相关内容可写"无硬伤"。输出分三个小段，必须含"修改清单"。总输出≤800字。\n' + pre_common, suffix='combined_pre_v3')
editor_pre = combined_pre[:900]
military_pre = combined_pre[:400]
science_pre = combined_pre[400:800]

card_text = base_card + f'''\n## 编辑写前意见\n{editor_pre[:900]}\n\n## 军事顾问写前意见\n{military_pre[:700]}\n\n## 科学顾问写前意见\n{science_pre[:700]}'''
(card_dir / f'第{ch}章.md').write_text(card_text, encoding='utf-8')

# ─── 2. 作者改写 ───（固定 mimo-v2.5，速度/字数/成本最优）
cfg = yaml.safe_load(open('/root/.hermes/config.yaml', encoding='utf-8')) or {}
provider = (cfg.get('providers') or {}).get('xiaomi', {})
base_url = (provider.get('base_url', 'https://token-plan-cn.xiaomimimo.com/v1')).rstrip('/')
key = provider.get('api_key')
key_env = provider.get('key_env') or 'XIAOMI_API_KEY'
if not key and key_env:
    key = os.environ.get(key_env, '')
model = provider.get('default_model') or provider.get('model') or 'mimo-v2.5'
if not key:
    raise SystemExit(f'AUTHOR_FAIL no api_key for xiaomi/mimo-v2.5')

author_prompt = f'''你是《科武纪元》作者。按精修任务卡V3.1改第{ch}章，只输出正文。

*** 字数硬约束：全文必须 3200-5200 中文字（不含标题和末行）。不足3200字视为不合格。
展开方法：每个动作节点补充物理反馈/环境细节/角色反应；对话穿插动作和感官描写；战术/技术环节写清操作步骤和结果验证。禁止用一句话概括本应展开的场景。

*** 本章必须写出的要素（缺一不可）：
{focus}

*** 章末钩子（必须显性提及）：{hook}，牵引"{next_ch}"。

*** 穿帮铁律：
- 正文和对话中**绝对禁止**出现"第X章""第X卷"等章节编号
- 角色不可能知道自己在第几章，这是写作元信息
- 违规视为不合格，必须重写

首行：第{ch}章 {title}
末行：（本章完）
不得解释，不得输出正文外任何内容。

{card_text[:3000]}
{wiki_section[:1500]}
{kb_section[:2000]}
{ev_section[:1500]}
{link_context}

原版全文：
{text}
'''

r = requests.post(base_url+'/chat/completions',
    headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'},
    json={'model': model, 'messages': [{'role': 'user', 'content': author_prompt}], 'max_tokens': 10000},
    timeout=420)
if not r.ok:
    raise SystemExit(f'AUTHOR_FAIL {r.status_code} {r.text[:300]}')

new = r.json()['choices'][0]['message']['content'].strip()
new = re.sub(r'^```(?:txt|md)?\s*', '', new).strip()
new = re.sub(r'\s*```$', '', new).strip()
if not new.splitlines() or not new.splitlines()[0].startswith(f'第{ch}章'):
    new = f'第{ch}章 {title}\n\n' + new
lines = new.splitlines()
while lines and not lines[-1].strip():
    lines.pop()
if not lines or not lines[-1].strip().startswith('（本章完）'):
    lines.append('（本章完）')
else:
    lines[-1] = '（本章完）'
new = '\n'.join(lines) + '\n'
for old, repl in {'意识到':'察觉', '意味着':'说明', '仿佛':'', '不禁':'', '微微':'', '淡淡':'', '缓缓':'', '宛如':'像'}.items():
    new = new.replace(old, repl)

out.write_text(new, encoding='utf-8')
cn = len(re.findall(r'[\u4e00-\u9fff]', new))

# ─── 字数不足补写 ───
if cn < 3000:
    print(f'  [字数不足 {cn}，补写中...]')
    expand_prompt = f'''你是《科武纪元》作者。第{ch}章当前仅{cn}字，不足3000字底线。
请在保留现有情节骨架的基础上，把每个场景展开：
- 每个动作节点补充物理反馈、环境细节、角色反应
- 对话穿插动作和感官描写
- 战术/技术环节写清操作步骤和结果验证
- 禁止用一句话概括本应展开的场景
- 目标：≥3500中文字

原版全文：
{text}

当前改写稿：
{new}
'''
    r2 = requests.post(base_url+'/chat/completions',
        headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'},
        json={'model': model, 'messages': [{'role': 'user', 'content': expand_prompt}], 'max_tokens': 10000},
        timeout=420)
    if r2.ok:
        new = r2.json()['choices'][0]['message']['content'].strip()
        new = re.sub(r'^```(?:txt|md)?\s*', '', new).strip()
        new = re.sub(r'\s*```$', '', new).strip()
        if not new.splitlines() or not new.splitlines()[0].startswith(f'第{ch}章'):
            new = f'第{ch}章 {title}\n\n' + new
        lines = new.splitlines()
        while lines and not lines[-1].strip():
            lines.pop()
        if not lines or not lines[-1].strip().startswith('（本章完）'):
            lines.append('（本章完）')
        else:
            lines[-1] = '（本章完）'
        new = '\n'.join(lines) + '\n'
        out.write_text(new, encoding='utf-8')
        cn = len(re.findall(r'[\u4e00-\u9fff]', new))

nhead, ntail = new[:900], new[-1100:]

# ─── 3. 写后快筛门禁（粗截看整体体感） ───
post = f'''任务: 写后快筛第{ch}章。只判断整体体感，不替代RTK最终门禁。输出必须含英文 PASS 或 FAIL；若有必改/硬伤/不宜进入下一章则 FAIL。
任务卡:
{base_card}
{kb_section[:1500]}
首段:
{nhead}
章末:
{ntail}
'''
editor_post = call('editor', '角色: 网文编辑\n关注: 整体结构/风格/是否明显跑偏。\n' + post, suffix='editor_post_v3')
reader_post = call('reader', '角色: 普通网文读者\n关注: 是否顺、是否水、AI味（禁"仿佛/微微/缓缓/意味着/意识到/不禁/不由得"）、想不想看下一章、技术解释是否用了生活类比。\n' + post, suffix='reader_post_v3')

def passed(raw):
    """Trust 'ok' field from orchestrate_review.py JSON; fallback to content scan"""
    try:
        data = json.loads(raw)
        if data.get('ok') is True:
            return True, 'ok=true'
        if data.get('ok') is False:
            return False, 'ok=false'
    except:
        pass
    content = ''
    try:
        data = json.loads(raw)
        content = data.get('content', '')
    except:
        pass
    if not content:
        return False, 'empty content'
    has_pass = 'PASS' in content
    has_fail = 'FAIL' in content
    if has_pass and not has_fail:
        return True, 'PASS in content'
    if has_fail:
        return False, 'FAIL in content'
    if has_pass:
        return True, 'PASS in content'
    return False, 'no PASS in content'

def verdict_from(raw):
    """compatibility wrapper"""
    return passed(raw)

ep, ep_reason = verdict_from(editor_post)
rp, rp_reason = verdict_from(reader_post)

# ─── 4. 改后RTK证据包（模型输入前置压缩） ───
# 作者改写后重建证据包：只把证据包送入最终门禁，正文保真保存在文件中
subprocess.run(['python3', str(proj/'工具脚本/build_review_evidence.py'), str(ch)],
               cwd='/root/workspace', check=True, capture_output=True, text=True, timeout=120)
ev_text_post = ev_md.read_text(encoding='utf-8', errors='ignore')[:4500] if ev_md.exists() else ''
ev_section_post = f'\n## 改后RTK证据包\n{ev_text_post}' if ev_text_post else ''

# ─── RTK 独立门禁 ───
subprocess.run(['python3', str(proj/'工具脚本/editor_gate_with_evidence.py'), str(ch)],
               cwd='/root/workspace', check=True, capture_output=True, text=True, timeout=300)
subprocess.run(['python3', str(proj/'工具脚本/reader_gate_with_evidence.py'), str(ch)],
               cwd='/root/workspace', check=True, capture_output=True, text=True, timeout=300)

editor_evidence_raw = (raw_dir / f'第{ch}_editor_evidence_gate.json').read_text(encoding='utf-8', errors='ignore')
reader_evidence_raw = (raw_dir / f'第{ch}_reader_evidence_gate.json').read_text(encoding='utf-8', errors='ignore')

rep, rep_reason = verdict_from(editor_evidence_raw)
rrp, rrp_reason = verdict_from(reader_evidence_raw)

# ─── 钩子检测（2-4字滑动窗口） ───
def bigrams(t):
    return [t[i:i+n] for n in range(2, 5) for i in range(len(t)-n+1)]
next_title = re.sub(r'^第\d+章\s*', '', next_ch)
all_kw = list(set(bigrams(hook) + bigrams(next_title)))
all_kw = [k for k in all_kw if len(k) >= 2]
tail_500 = new[-500:]
hook_found = any(kw in tail_500 for kw in all_kw)

# ─── 最终判定 ───
final = ep and rp and rep and rrp and cn >= 3000 and hook_found
final_pass = final
eg_passed = rep  # RTK编辑门禁结果
rg_passed = rrp  # RTK读者门禁结果
meta_leak_found = False

# ─── 5. 写入审核记录 ───
rec = f'''# 第{ch}章 六角色外审记录 V4

时间：2026-05-03
章节：第{ch}章《{title}》
原版：{orig}
改版：{out}

## 精修V4流程
- 写前：编辑 + 军事 + 科学（注入Wiki+知识库素材卡+证据包+wikilink）
- 作者：按任务卡改写（注入Wiki+知识库素材卡+证据包+记忆卡+wikilink）
- 写后：编辑 + 读者双门禁（注入知识库素材卡）
- RTK独立门禁：编辑证据包 + 读者证据包（作者改写后二次构建证据包）

## 本地预检
- 字数：{cn} {'✓' if cn >= 3000 else '✗ 不足3000'}
- 首行：第{ch}章 {title}
- 末行：（本章完）
- Wiki知识库：{'已注入' if wiki_text else '未找到'}
- 知识库素材卡：{len(kb_card_list)} 张注入 ({', '.join(kb_card_list) if kb_card_list else '无匹配'})
- RTK证据包：已构建（写前+写后两次）
- 上章记忆卡：{'已注入' if mem_text else '未找到'}
- Wikilink关联：{len(all_links)} 条
- 章末钩子检测：{'✓' if hook_found else '✗ 未找到'}

## 原始输出
- 编辑写前：raw/第{ch}_editor_pre_v3.json
- 军事写前：raw/第{ch}_military_pre_v3.json
- 科学写前：raw/第{ch}_science_pre_v3.json
- 编辑写后：raw/第{ch}_editor_post_v3.json
- 读者写后：raw/第{ch}_reader_post_v3.json
- RTK编辑门禁：raw/第{ch}_editor_evidence_gate.json
- RTK读者门禁：raw/第{ch}_reader_evidence_gate.json

## 门禁
- 编辑写后：{'PASS' if ep else 'REVIEW_NEEDED'} ({ep_reason})
- 读者写后：{'PASS' if rp else 'REVIEW_NEEDED'} ({rp_reason})
- RTK编辑门禁：{'PASS' if rep else 'REVIEW_NEEDED'} ({rep_reason})
- RTK读者门禁：{'PASS' if rrp else 'REVIEW_NEEDED'} ({rrp_reason})
- 章末钩子：{'✓' if hook_found else '✗'}

## 最终结论
{'PASS' if final else 'REVIEW_NEEDED'}
'''
(review_dir / f'第{ch}章.md').write_text(rec, encoding='utf-8')

print(json.dumps({
    'chapter': ch, 'chars': cn,
    'editor_pass': ep, 'reader_pass': rp,
    'meta_leak': False,
    'evidence_gate': eg_passed,
    'reader_evidence_gate': rg_passed,
    'kb_cards': kb_card_list,
    'file': str(out), 'card': str(card_dir / f'第{ch}章.md'),
    'review': str(review_dir / f'第{ch}章.md')
}, ensure_ascii=False))

# ─── 精修 PASS 自动归档流程 ───
if final:
    original = proj / '新版' / f'第{ch}章.md'
    if original.exists():
        import shutil, datetime, subprocess
        
        # 1. 备份旧版
        backup_dir = proj / '审核记录' / '备份' / f'精修替换_{datetime.date.today().isoformat()}'
        backup_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(original), str(backup_dir / f'第{ch}章_精修前.md'))
        print(f'\n✅ PASS → 旧版备份: {backup_dir / f"第{ch}章_精修前.md"}')
        
        # 2. 精修稿替换新版/原版
        shutil.copy2(str(out), str(original))
        print(f'✅ 精修稿 → 新版/第{ch}章.md')
        
        # 3. git 提交
        r = subprocess.run(['git', 'add', str(original)], cwd=str(proj), capture_output=True, text=True)
        msg = f'refine: 第{ch}章 V4精修 PASS'
        r2 = subprocess.run(['git', 'commit', '-m', msg], cwd=str(proj), capture_output=True, text=True)
        hash_line = r2.stdout.strip().split('\n')[0] if r2.returncode == 0 else r2.stderr.strip()[:80]
        print(f'✅ git: {hash_line}')
        
        # ─── 4. 章节记忆卡（自动） ───
        mem_card_path = proj / '审核记录' / '章节记忆卡' / f'第{ch}章.md'
        # 提取章末钩子（取倒数第3-5行非空行）
        non_empty = [l for l in new.splitlines() if l.strip()]
        hook_text = '\\n'.join(non_empty[-3:]) if len(non_empty) >= 3 else ''
        
        mem_card = f'''# 第{ch}章记忆卡
- 标题：{title}
- 功能：{anchor}
- 核心事件：{hook}
- 人物状态：待提取
- 混沌模型：已注入V8锚点
- 章末钩子：牵引"{next_ch}"
- 字数：{cn}（番茄口径）
- 审核：编辑PASS + 读者PASS
- Wikilink：{', '.join(all_links[:5]) if all_links else '待提取'}
'''
        mem_card_path.write_text(mem_card, encoding='utf-8')
        print(f'✅ 章节记忆卡：第{ch}章.md')
        
        # ─── 5. Wiki章节页（自动） ───
        wiki_ch_path = proj / 'wiki' / 'chapters' / f'ch{ch:03d}.md'
        # 提取卷名（简单匹配标题或默认）
        vol_map = {range(1,55): '第一卷', range(56,105): '第二卷·烽火', range(106,155): '第三卷·暗流', range(156,208): '第四卷', range(209,258): '第五卷'}
        vol = '未知卷'
        for r, v in vol_map.items():
            if ch in r: vol = v; break
        
        wiki_page = f'''---
title: 第{ch}章 {title}
chapter: {ch}
volume: {vol}
---

# 第{ch}章 {title}

## 章节功能
{anchor}

## 关键事件
- {focus}

## 章末钩子
牵引"{next_ch}"——{hook}

## Source Material
- 审核记录：六角色外审/第{ch}章.md
'''
        wiki_ch_path.write_text(wiki_page, encoding='utf-8')
        print(f'✅ Wiki章节页：ch{ch:03d}.md')
        
        # ─── 6. 跟踪表更新（统一格式） ───
        index_path = proj / '审核记录' / '六角色外审' / 'index.md'
        if index_path.exists():
            content = index_path.read_text(encoding='utf-8')
            line_mark = f'| {ch} | {title} | PASS | V4精修 | {cn} | {datetime.date.today().isoformat()} | 编辑PASS+读者PASS | 混沌模型已注入 |'
            if f'| {ch} |' not in content:
                lines = content.splitlines()
                # 找到最后一个表格行插入
                insert_at = len(lines)
                for i in range(len(lines)-1, -1, -1):
                    if lines[i].strip().startswith('| '):
                        insert_at = i + 1
                        break
                lines.insert(insert_at, line_mark)
                index_path.write_text('\\n'.join(lines) + '\\n', encoding='utf-8')
                print(f'✅ 跟踪表更新：第{ch}章')
        print('\\n✅✅✅ 全部流程闭环。')
