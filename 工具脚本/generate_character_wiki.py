#!/usr/bin/env python3
import re, json, pathlib, urllib.request, yaml, os, sys
HOME=pathlib.Path.home()
ENV=HOME/'.hermes/.env'; CFG=HOME/'.hermes/config.yaml'
BASE=pathlib.Path('/root/workspace/科武纪元')
OUT=BASE/'wiki/characters'
OUT.mkdir(parents=True, exist_ok=True)
if ENV.exists():
    for line in ENV.read_text(encoding='utf-8',errors='ignore').splitlines():
        line=line.strip()
        if not line or line.startswith('#') or '=' not in line: continue
        k,v=line.split('=',1); os.environ.setdefault(k.strip(),v.strip().strip('"').strip("'"))
c=yaml.safe_load(CFG.read_text(encoding='utf-8')) or {}
p=(c.get('providers') or {}).get('cpa') or (c.get('providers') or {}).get('custom') or {}
base=(p.get('base_url') or '').rstrip('/')
key=p.get('api_key') or os.environ.get(p.get('key_env',''),'')
if not key: raise SystemExit('missing key')
outline_text = (BASE/'科武纪元大纲 V8_完整版.md').read_text(encoding='utf-8')
# Extract first 70 chapters summary
chapters_text = []
lines = outline_text.splitlines()
for line in lines:
    if re.match(r'第\d+章', line) and int(re.search(r'第(\d+)', line).group(1)) <= 72:
        chapters_text.append(line.strip())
context = '\n'.join(chapters_text[:70])

entities = [
    ('林星辰', '主角', '江城少年班，太极传人，生物电/武学 AI 核心，擅长推演与抗压'),
    ('苏雨晴', '女角/导师', '太极传人，外骨骼同步率问题，传统与现代的冲突，外冷内热'),
    ('谢云', '队友/战力', '金刚拳，外骨骼高同步，直爽，战斗主力'),
    ('陈思琪', '科研/智囊', '算法天才，实验室负责人，算力推演，理性至上'),
    ('方宁', '队长/军方', '沉稳，大局观，联合政府与少年班的桥梁'),
    ('赵刚', '军方/通报', '负责情报通报，连接外部局势与小队'),
    ('李梦瑶', '队友/辅助', '黑客/网络专家，负责信息战与算力黑市线索'),
]

def chat(prompt):
    req=urllib.request.Request(base+'/chat/completions',data=json.dumps({'model':'gpt-5.5','messages':[{'role':'user','content':prompt}],'max_tokens':4096},ensure_ascii=False).encode(),headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'})
    raw=urllib.request.urlopen(req,timeout=120).read().decode('utf-8','ignore')
    j=json.loads(raw)
    return j.get('choices',[{}])[0].get('message',{}).get('content','')

sys.path.insert(0, '/root/workspace/vector-memory')
from vecmem import VectorMemory
vm = VectorMemory()

for name, role, summary in entities:
    file_path = OUT/f'{name}.md'
    if file_path.exists(): 
        print(f'{name} already exists')
        continue
    
    prompt = f'''角色：Wiki 编纂员
任务：基于以下前 70 章大纲片段和角色简介，生成 {name} 的 Wiki 人物页。
要求：Markdown 格式，包含：
1. 基本信息（身份、阵营、能力）。
2. 核心人设（性格关键词、行为逻辑）。
3. 前 70 章剧情轨迹（按卷/阶段总结）。
4. 关键关系（与其他角色的羁绊/冲突）。
5. 混沌模型映射（该角色代表哪种熵增/熵减动力）。

大纲片段：
{context[:3000]}

简介：{role}，{summary}。

输出：'''
    content = chat(prompt)
    if not content: continue
    
    file_path.write_text(content, encoding='utf-8')
    vm.add(domain='novel', title=f'{name}_人物维基', content=content, tags=['人物', name, role], source='wiki_characters_gen')
    print(f'Generated {name}.md and added to vector-memory')

print('Done')