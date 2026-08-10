#!/usr/bin/env python3
"""
kewu_domain_ontology.py  v1  (2026-07-10)

科武纪元 采集领域本体配置。
九稳定域 + 戴森球能力树 + 大纲章节映射。

不改小说正文/大纲。仅服务于素材采集评分与查询路由。
"""
from __future__ import annotations

import re

from typing import Any

# ═══════════════════════════════════════════════
# 1. 九大稳定域
# ═══════════════════════════════════════════════

STABLE_DOMAINS: dict[str, dict[str, Any]] = {
    'frontier_tech': {
        'label': '前沿科技',
        'query_keywords': [
            '量子计算', '量子通信', '量子纠错', 'quantum computing', 'quantum error correction',
            '脑机接口', 'BCI', 'brain computer interface', 'neural interface',
            '核聚变', '可控核聚变', 'fusion energy', 'ITER', 'EAST',
            '拓扑量子', 'topological qubit', '离子阱', 'trapped ion',
            '光量子', 'photonic quantum', '超导量子', 'superconducting qubit',
            '具身智能', 'embodied AI', '人形机器人', 'humanoid robot',
        ],
        'outline_chapters': [261, 375, 376, 381, 225, 226],
        'tech_institution_chars': ['量子密钥', 'QKD', '纠错码', '拓扑保护'],
        'plot_threads': ['量子主权', '后量子密码', '算力跃迁'],
        'weight': 1.0,
    },
    'geopolitics': {
        'label': '地缘政治',
        'query_keywords': [
            '出口管制', 'export control', 'export controls', '制裁', 'sanctions',
            'BIS', 'entity list', '实体清单', '贸易摩擦', 'trade friction',
            '台海', 'Taiwan Strait', '南海', 'South China Sea',
            '北约', 'NATO', '地缘博弈', 'geopolitics',
            '铁幕', 'iron curtain', '算法主权', 'algorithm sovereignty',
            '军售', 'arms sales', '武器禁运', 'arms embargo',
            '贸易战', 'trade war', '关税战',
        ],
        'outline_chapters': [63, 86, 140, 145, 183, 184, 206, 207, 208, 306, 307],
        'tech_institution_chars': ['BIS', 'EAR', 'CFIUS', 'Wassenaar'],
        'plot_threads': ['铁幕封锁', '标准制定阴谋', '联盟控制权', '白盾扩编'],
        'weight': 1.0,
    },
    'biology': {
        'label': '生物',
        'query_keywords': [
            '基因编辑', 'CRISPR', 'gene editing', '基因治疗', 'gene therapy',
            '合成生物学', 'synthetic biology', '脑科学', 'neuroscience',
            '干细胞', 'stem cell', '太空生物', 'space biology',
            '生物传感器', 'biosensor', '生物安全', 'biosecurity',
            '深空生物', 'deep space biology', '辐射损伤', 'radiation damage',
        ],
        'outline_chapters': [370, 371, 373, 375],
        'tech_institution_chars': ['CRISPR-Cas9', '干细胞培养', '辐射防护'],
        'plot_threads': ['太空生物样本', '深空辐射', '基因改造伦理'],
        'weight': 0.8,
    },
    'space': {
        'label': '太空',
        'query_keywords': [
            '航天', 'space', '运载火箭', 'launch vehicle', '可重复使用', 'reusable',
            '长征', 'Long March', '首飞', 'maiden flight', 'first flight',
            '月球', 'moon', 'lunar', '月面', 'lunar surface', '月壤', 'lunar regolith',
            '深空', 'deep space', '火星', 'Mars', '登月', 'lunar landing',
            '空间站', 'space station', '天宫', 'Tiangong',
            '商业航天', 'commercial space', '卫星', 'satellite',
            '氦-3', 'helium-3', '月球基地', 'lunar base',
            '垂直返回', 'vertical landing', '海上捕获', 'sea capture',
            'Artemis', 'Starship', 'SLS',
        ],
        'outline_chapters': [156, 169, 220, 221, 359, 370, 371, 373, 375, 381],
        'tech_institution_chars': ['CNSA', 'NASA', 'ESA', 'SpaceX', 'CALT'],
        'plot_threads': ['月面绞肉机', '氦-3争夺', '轨道防御', '双向封锁', '深空回响'],
        'weight': 1.0,
    },
    'aviation': {
        'label': '航空',
        'query_keywords': [
            '无人机', 'drone', 'UAV', '蜂群', 'swarm', '忠诚僚机', 'loyal wingman',
            '战斗机', 'fighter jet', 'NGAD', 'CCA', '协同作战', 'collaborative combat',
            'FPV', '巡飞弹', 'loitering munition', '反无人机', 'counter-drone',
            '高超音速', 'hypersonic', '超视距', 'beyond visual range',
            '电子战', 'electronic warfare', 'EW', '雷达', 'radar',
            'F-35', '歼-20', 'J-20', '运-20', 'Y-20',
            'C919', '适航', 'airworthiness', 'ARJ21', '大飞机',
        ],
        'outline_chapters': [36, 110, 115, 184, 306, 308, 310],
        'tech_institution_chars': ['OODA', 'JADC2', 'DMO', 'AESA'],
        'plot_threads': ['蜂群夜袭', '忠诚僚机', '电子压制', 'HPM微波反制'],
        'weight': 0.9,
    },
    'ai': {
        'label': '人工智能',
        'query_keywords': [
            '人工智能', 'artificial intelligence', 'AI', '大模型', 'LLM', 'large language model',
            'AGI', '通用人工智能', 'AI安全', 'AI safety', 'AI对齐', 'AI alignment',
            '机器学习', 'machine learning', '深度学习', 'deep learning',
            '强化学习', 'reinforcement learning', 'RLHF',
            'AI芯片', 'AI chip', 'GPU', 'NPU', 'ASIC',
            '智能体', 'agent', 'agentic', '多模态', 'multimodal',
            'AI治理', 'AI governance', '算法审计', 'algorithm audit',
        ],
        'outline_chapters': [63, 78, 86, 95, 101, 184, 212, 225, 356, 357],
        'tech_institution_chars': ['CUDA', 'Transformer', 'RLHF', 'MoE'],
        'plot_threads': ['算力主权', '残缺阵列训练', '硬反馈闭环', 'AI伦理', '技术共和国'],
        'weight': 1.0,
    },
    'military': {
        'label': '军事',
        'query_keywords': [
            '军事', 'military', '国防', 'defense', 'national defense',
            '导弹', 'missile', '弹道导弹', 'ballistic missile', '反卫星', 'ASAT',
            '网络战', 'cyber warfare', '信息战', 'information warfare',
            '太空战', 'space warfare', '轨道战', 'orbital combat',
            '无人系统', 'unmanned systems', '自主武器', 'autonomous weapons',
            '外骨骼', 'exoskeleton', '军用外骨骼', 'military exoskeleton',
            'C4ISR', '指挥链', 'command chain', 'OODA',
            'JADC2', '分布式作战', 'distributed operations',
        ],
        'outline_chapters': [36, 110, 115, 184, 217, 223, 306, 307, 308, 310, 371],
        'tech_institution_chars': ['JADC2', 'DMO', 'CEC', 'TTNT'],
        'plot_threads': ['多域指挥摩擦', '火力审批卡', '联络官', '白盾部队'],
        'weight': 0.9,
    },
    'materials': {
        'label': '材料',
        'query_keywords': [
            '新材料', 'advanced materials', '材料科学', 'materials science',
            '碳纤维', 'carbon fiber', '石墨烯', 'graphene',
            '超材料', 'metamaterial', '二维材料', '2D materials',
            '半导体材料', 'semiconductor materials', '光刻', 'lithography',
            '稀土', 'rare earth', '稀有矿物', 'rare minerals',
            '高温合金', 'superalloy', '陶瓷基', 'CMC',
            '镓', 'gallium', '锗', 'germanium', '氮化镓', 'GaN',
            '钴', 'cobalt', '锂', 'lithium',
        ],
        'outline_chapters': [19, 20, 26, 31, 34, 63, 86, 95, 308],
        'tech_institution_chars': ['炉温', '张力', '缺陷率', '批次'],
        'plot_threads': ['材料先打烂再用', '供应链断裂', '稀有矿争夺'],
        'weight': 0.8,
    },
    'energy': {
        'label': '能源',
        'query_keywords': [
            '能源', 'energy', '聚变', 'fusion', '核聚变', 'nuclear fusion',
            '太阳能', 'solar', '光伏', 'photovoltaic',
            '储能', 'energy storage', '电池', 'battery', '固态电池', 'solid state battery',
            '氢能', 'hydrogen', '氢燃料电池', 'fuel cell',
            '电力', 'power grid', '电网', 'smart grid',
            '算力能耗', 'computing energy', '数据中心', 'data center',
            '散热', 'cooling', '热管理', 'thermal management',
            '兰道极限', 'Landauer limit', '兰道下限', 'Landauer bound',
        ],
        'outline_chapters': [37, 41, 90, 209, 216, 370, 373],
        'tech_institution_chars': ['EAST', 'ITER', '兰道常数', '热力学极限'],
        'plot_threads': ['算力=电/热/水', '聚变之火', '散热不可突破兰道下限', '能源绑定算力'],
        'weight': 0.9,
    },
    'foundational_science': {
        'label': '基础科学',
        'query_keywords': [
            '数学', 'mathematics', 'math', '定理', 'theorem', '猜想', 'conjecture',
            '证明', 'proof', '基础科学', 'foundational science', '黎曼猜想', 'Riemann',
            '费马大定理', 'Fermat', '哥德尔', 'Gödel', 'Godel', '数论', 'number theory',
            '拓扑', 'topology', '代数', 'algebra', '几何', 'geometry', 'P vs NP',
            '千禧年难题', 'Millennium Prize',
        ],
        'outline_chapters': [261, 375, 376, 381, 406, 420, 456],
        'dyson_tree': ['quantum_computing', 'dyson_construction'],
        'tech_institution_chars': ['形式化证明', '可计算性', '复杂性理论', '数学基础'],
        'plot_threads': ['理论突破', '算力边界', '基础理论驱动工程跃迁'],
        'weight': 1.0,
    },
}

# ═══════════════════════════════════════════════
# 2. 戴森球能力树（卷六-卷十）
# ═══════════════════════════════════════════════

DYSON_SPHERE_CAPABILITY_TREE: dict[str, dict[str, Any]] = {
    'material_science': {
        'label': '戴森球材料',
        'level': 'foundation',
        'keywords': [
            '碳纤维', 'carbon fiber', '超材料', 'metamaterial',
            '太空材料', 'space materials', '辐射防护材料', 'radiation shielding',
            '耐高温', 'high temperature resistant', '轻量化', 'lightweight',
            '太空制造', 'space manufacturing', '在轨组装', 'on-orbit assembly',
        ],
        'outline_chapters': [256, 282, 293, 306, 375, 406, 456],
        'depends_on': [],
        'tech_constraints': ['批次缺陷', '张力约束', '炉温控制', '良率'],
    },
    'orbital_mechanics': {
        'label': '轨道调度',
        'level': 'foundation',
        'keywords': [
            '轨道', 'orbit', '轨道力学', 'orbital mechanics',
            '拉格朗日点', 'Lagrange point', 'L1', 'L2',
            '地月空间', 'cislunar', '月轨', 'lunar orbit',
            '轨道碎片', 'orbital debris', '太空交通', 'space traffic',
            'Δv', 'delta-v', '霍曼转移', 'Hohmann transfer',
            '可重复使用', 'reusable', '运载火箭', 'launch vehicle',
            '垂直返回', 'vertical landing', '海上捕获', 'sea capture',
            '首飞', 'maiden flight', '发射', 'launch',
        ],
        'outline_chapters': [169, 220, 359, 371, 406, 456],
        'depends_on': [],
        'tech_constraints': ['燃料预算', '窗口限制', '通信延迟'],
    },
    'energy_harvesting': {
        'label': '能量采集',
        'level': 'core',
        'keywords': [
            '太阳能采集', 'solar harvesting', '太空太阳能', 'space solar power',
            '无线能量传输', 'wireless power transfer', '微波输电', 'microwave power',
            '光伏阵列', 'solar array', '聚光器', 'concentrator',
            '戴森云', 'Dyson swarm', '戴森环', 'Dyson ring',
            '太阳能', 'solar power', '光伏发电',
        ],
        'outline_chapters': [406, 420, 440, 456, 470, 485],
        'depends_on': ['material_science', 'orbital_mechanics'],
        'tech_constraints': ['传输效率', '散热极限', '规模成本'],
    },
    'quantum_computing': {
        'label': '量子算力',
        'level': 'core',
        'keywords': [
            '量子计算', 'quantum computing', '量子纠错', 'quantum error correction',
            '量子网络', 'quantum network', '量子中继', 'quantum repeater',
            '拓扑量子', 'topological quantum', '量子比特', 'qubit',
            '量子优越性', 'quantum advantage', '量子霸权', 'quantum supremacy',
        ],
        'outline_chapters': [261, 375, 376, 381, 406, 420, 456],
        'depends_on': ['energy_harvesting'],
        'tech_constraints': ['纠错开销', '退相干时间', '测控链路'],
    },
    'consciousness_interface': {
        'label': '意识接口',
        'level': 'advanced',
        'keywords': [
            '脑机接口', 'BCI', 'brain computer interface',
            '意识上传', 'consciousness upload', '神经链接', 'neural link',
            '算力共振', 'computing resonance', '意识外放', 'consciousness projection',
            '零信息擦除', 'zero information erasure',
        ],
        'outline_chapters': [355, 405, 455, 485, 495, 500],
        'depends_on': ['quantum_computing'],
        'tech_constraints': ['人性锚点', '经脉异变', '精神消耗'],
    },
    'dyson_construction': {
        'label': '戴森球工程',
        'level': 'ultimate',
        'keywords': [
            '戴森球', 'Dyson sphere', '戴森云', 'Dyson swarm',
            '恒星工程', 'stellar engineering', '卡尔达肖夫', 'Kardashev',
            '行星级算力', 'planetary computing', '恒星共振', 'stellar resonance',
            '零界', 'zero boundary', '文明分岔', 'civilization branching',
        ],
        'outline_chapters': [256, 406, 420, 440, 456, 470, 485, 495, 500],
        'depends_on': ['energy_harvesting', 'quantum_computing', 'consciousness_interface'],
        'tech_constraints': ['恒星绑定', '人性弱化', '宇宙级连锁'],
    },
    # 2026-08-09 修复: 战略资源/循环利用域, 覆盖锂电池回收、稀土、关键矿产等
    # 当前事件(如新华社《探秘一块锂电池的"重生"之旅》)匹配 南美锂战/氦-3开采 等章节,
    # 却因 Dyson 树缺节点被判 NO_DYSON_TREE_MATCH 归档, 致 DOMESTIC_OFFICIAL_P0_ZERO。
    'strategic_materials': {
        'label': '战略资源',
        'level': 'foundation',
        'keywords': [
            '电池', '锂电池', '动力电池', 'battery', 'lithium', '锂',
            '回收', '再生', '资源化', '循环利用', '供应链', '产业链',
            '退役', '稀土', '关键矿产', '战略资源', '矿产资源',
            'resource recovery', 'battery recycling', 'critical minerals',
            'rare earth', 'strategic resources', 'resource security',
        ],
        'outline_chapters': [75, 157, 20, 31, 37, 63, 78, 86, 95, 101],
        'depends_on': [],
        'tech_constraints': ['回收率', '提炼纯度', '供应链韧性'],
    },
}

# ═══════════════════════════════════════════════
# 3. 噪声/降级域
# ═══════════════════════════════════════════════

NOISE_DOMAINS: dict[str, dict[str, Any]] = {
    'generic_pop_science': {
        'label': '泛科普',
        'keywords': [
            '科普', 'popular science', '趣味知识', 'fun facts',
            '冷知识', 'trivia', '你不知道的', 'did you know',
            '生活小常识', 'daily tips', '养生', 'health tips',
        ],
        'degrade_to': 'NOISE',
        'reason': 'GENERIC_POP_SCIENCE',
    },
    'entertainment': {
        'label': '娱乐',
        'keywords': [
            '明星', 'celebrity', '八卦', 'gossip', '综艺', 'variety show',
            '演唱会', 'concert', '票房', 'box office', '影视', 'movie',
            '网红', 'influencer', '直播', 'livestream', '带货', 'e-commerce',
            '电竞', 'esports', '游戏', 'gaming',
        ],
        'degrade_to': 'NOISE',
        'reason': 'ENTERTAINMENT_CONTENT',
    },
    'consumer_review': {
        'label': '消费评测',
        'keywords': [
            '评测', 'review', '开箱', 'unboxing', '对比测试', 'comparison test',
            '性价比', 'cost effective', '值不值得买', 'worth buying',
            '推荐', 'recommendation', '种草', 'product suggestion',
            '购物', 'shopping', '折扣', 'discount', '优惠', 'deal',
        ],
        'degrade_to': 'NOISE',
        'reason': 'CONSUMER_REVIEW',
    },
    'stale_news': {
        'label': '旧闻',
        'keywords': [],  # 由时间判断，非关键词
        'degrade_to': 'NOISE',
        'reason': 'STALE_NEWS',
        'max_age_days_domestic': 180,
        'max_age_days_overseas': 14,
    },
}

# ═══════════════════════════════════════════════
# 4. 评分权重模型
# ═══════════════════════════════════════════════

SCORING_WEIGHTS: dict[str, float] = {
    'domain_relevance': 3.0,       # 命中稳定域关键词数
    'outline_chapter_hit': 2.0,    # 命中大纲章节映射
    'tech_institution': 1.5,       # 命中技术-制度关键词
    'character_plot': 1.5,         # 命中人物-情节映射
    'source_authority': 2.0,       # 来源权威度（官方/学术/媒体）
    'timeliness': 1.0,             # 时效性（当日+3, 本周+2, 本月+1）
    'credibility': 1.0,            # 可信度（一手源+2, 二手+1, discovery+0）
    'dedup_penalty': -2.0,         # 重复度惩罚
    'noise_penalty': -5.0,         # 噪声惩罚（泛科普/娱乐/消费评测/旧闻）
}

# 来源权威度映射
SOURCE_AUTHORITY: dict[str, float] = {
    'domestic_official': 1.0,
    'overseas_official': 0.9,
    'academic': 1.0,
    'domestic_discovery': 0.4,
    'overseas_discovery': 0.4,
}

# 时效性衰减
TIMELINESS_DECAY: dict[str, float] = {
    'same_day': 1.0,
    'same_week': 0.7,
    'same_month': 0.4,
    'older': 0.1,
}

# ═══════════════════════════════════════════════
# 5. 动态实体抽取配置
# ═══════════════════════════════════════════════

ENTITY_PATTERNS: dict[str, dict[str, Any]] = {
    'model_designation': {
        'label': '型号',
        'patterns': [
            r'[A-Z]{1,5}[-–]\d{1,4}[A-Z]?',  # F-35, J-20, CZ-10B, NGAD
            r'长征[一二三四五六七八九十百]+[甲乙丙丁]?',
            r'Long\s+March\s+\d+[A-Z]?',
            r'第[一二三四五六七八九十]+代',
            r'Mk\.?\s*\d+',
            r'Type\s+\d+',
        ],
        'generate_followup': True,
    },
    'organization': {
        'label': '组织',
        'patterns': [
            r'(?:中国|美国|欧洲|日本|俄罗斯|印度)(?:航天|军事|科技|能源|量子)(?:局|院|部|集团|公司|中心|研究所)',
            r'(?:NASA|ESA|CNSA|DARPA|CALT|SIA|IEEE|BIS)',
            r'(?:华为|中芯|台积电|三星|英特尔|英伟达|AMD|高通)(?:集团|公司)?',
            r'(?:SpaceX|Blue Origin|Northrop|Lockheed|Raytheon|Boeing)',
            r'[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+\s+(?:Inc|Corp|Ltd|LLC|Company|Technologies|Systems)\.?',
        ],
        'generate_followup': True,
    },
    'person': {
        'label': '人物',
        'patterns': [
            r'(?:习近平|拜登|特朗普|普京|泽连斯基|马克龙|默茨)',
            r'(?:黄仁勋|马斯克|扎克伯格|奥特曼|阿尔特曼)',
            r'(?:沈逸|高志凯)',
        ],
        'generate_followup': False,  # 人物不生成二次查询（避免噪声）
    },
}

# ═══════════════════════════════════════════════
# 6. 查询组合模板
# ═══════════════════════════════════════════════

TEMPORAL_KEYWORDS: dict[str, list[str]] = {
    'today': ['今天', '今日', 'today', 'latest', '最新', '刚刚', 'breaking'],
    'this_week': ['本周', 'this week', '近期', 'recently'],
    'this_month': ['本月', 'this month', '最近', 'recent'],
}

EVENT_SEMANTIC_TEMPLATES: list[dict[str, Any]] = [
    {
        'template': '{domain_kw} {temporal} {event}',
        'description': '域×时间×事件三元组合',
        'priority': 1,
    },
    {
        'template': 'site:{official_domain} {domain_kw} {temporal}',
        'description': '域官方源定向查询',
        'priority': 2,
    },
    {
        'template': '{domain_kw} 突破 最新 进展',
        'description': '域突破发现',
        'priority': 3,
    },
]

# 官方源域名映射（域→推荐 site: 域名）
DOMAIN_OFFICIAL_SITES: dict[str, list[str]] = {
    'frontier_tech': ['cas.cn', 'iop.cas.cn', 'arxiv.org', 'nature.com'],
    'geopolitics': ['xinhuanet.com', 'people.com.cn', 'mfa.gov.cn', 'state.gov'],
    'biology': ['nih.gov', 'nature.com', 'cas.cn', 'pubmed.ncbi.nlm.nih.gov'],
    'space': ['cnsa.gov.cn', 'cmse.gov.cn', 'calt.com', 'nasa.gov', 'esa.int'],
    'aviation': ['mod.gov.cn', 'defense.gov', 'darpa.mil'],
    'ai': ['miit.gov.cn', 'most.gov.cn', 'arxiv.org', 'anthropic.com'],
    'military': ['mod.gov.cn', 'defense.gov', 'darpa.mil'],
    'materials': ['cas.cn', 'stdaily.com', 'nature.com'],
    'energy': ['energy.gov', 'cas.cn', 'most.gov.cn'],
    'foundational_science': ['arxiv.org', 'nature.com', 'ams.org', 'maa.org'],
}


def _keyword_matches(text_lower: str, keyword: str) -> bool:
    """中文按子串匹配；英文和缩写必须匹配完整词组。"""
    keyword_lower = keyword.lower()
    if re.search(r'[\u4e00-\u9fff]', keyword):
        return keyword_lower in text_lower
    return re.search(r'\b' + re.escape(keyword_lower) + r'\b', text_lower) is not None


def get_domain_for_keywords(text: str) -> list[tuple[str, float]]:
    """返回文本命中的域列表及命中数。"""
    text_lower = text.lower()
    results: list[tuple[str, float]] = []
    for domain_id, domain in STABLE_DOMAINS.items():
        hits = sum(1 for kw in domain['query_keywords'] if _keyword_matches(text_lower, kw))
        if hits > 0:
            results.append((domain_id, hits * domain.get('weight', 1.0)))
    results.sort(key=lambda x: -x[1])
    return results


def get_outline_chapters_for_domain(domain_id: str) -> list[int]:
    """返回域对应的大纲章节号列表。"""
    domain = STABLE_DOMAINS.get(domain_id, {})
    return list(domain.get('outline_chapters', []))


def get_dyson_tree_for_chapter(chapter: int) -> list[str]:
    """返回章节号对应的戴森球能力树节点。"""
    nodes: list[str] = []
    for node_id, node in DYSON_SPHERE_CAPABILITY_TREE.items():
        if chapter in node.get('outline_chapters', []):
            nodes.append(node_id)
    return nodes


def is_noise_domain(text: str) -> tuple[bool, str]:
    """检查文本是否属于噪声域。返回 (is_noise, reason)。"""
    text_lower = text.lower()
    for noise_id, noise in NOISE_DOMAINS.items():
        if noise_id == 'stale_news':
            continue  # 旧闻由时间判断
        hits = sum(1 for kw in noise['keywords'] if _keyword_matches(text_lower, kw))
        if hits >= 2:  # 需要至少2个噪声关键词命中
            return True, noise['reason']
    return False, ''
