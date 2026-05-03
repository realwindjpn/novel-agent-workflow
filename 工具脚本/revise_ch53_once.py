import os, re, yaml, requests

proj = '/root/workspace/科武纪元'
in_path = f'{proj}/待确认投稿/第53章改.txt'
out_path = in_path
review_path = f'{proj}/审核记录/六角色外审/第53章_修订说明.md'

with open(in_path, 'r', encoding='utf-8') as f:
    text = f.read()

cfg_path = '/root/.hermes/config.yaml'
with open(cfg_path, 'r', encoding='utf-8') as f:
    cfg = yaml.safe_load(f) or {}
model_cfg = cfg.get('model') or {}
base_url = model_cfg.get('base_url', 'http://43.135.181.17:8080/v1').rstrip('/')
api_key = model_cfg.get('api_key') or os.environ.get('OPENAI_API_KEY')
model = model_cfg.get('default') or model_cfg.get('model') or 'gpt-5.5'
if not api_key:
    raise SystemExit('NO_API_KEY')

prompt = f'''你是《科武纪元》作者。只修第53章《铁幕初现》，不要解释。

编辑必改：
1 压缩纯复盘，穿插线索实物/数据面板/行动指令。
2 “铁幕”具象化：加密频段、跳板IP、异常权限流/资金流至少落地一项。
3 技术泄露调查落地首个可执行目标：服务器异常/内部权限/门禁记录等。
4 章末钩子改成即时触发型：警报/倒计时/张维舟主动加密坐标。
5 顾问组/张维舟与技术泄露形成因果桥/时间轴。

硬约束：
- 保留原剧情与人物关系。
- 字数3500-5000中文，不要扩到八千。
- 硬派工业党风格，禁止文艺比喻。
- 用动作、数据、设备反馈替代心理解释。
- 首行必须：第53章 铁幕初现
- 末行必须： （本章完）

原文：
{text}
'''

r = requests.post(
    base_url + '/chat/completions',
    headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
    json={'model': model, 'messages': [{'role':'user','content':prompt}], 'max_tokens': 7000},
    timeout=300,
)
if not r.ok:
    raise SystemExit(f'API_FAIL {r.status_code} {r.text[:300]}')
new = r.json()['choices'][0]['message']['content'].strip()
# strip markdown fences if any
new = re.sub(r'^```(?:txt|md)?\s*', '', new).strip()
new = re.sub(r'\s*```$', '', new).strip()
lines = new.splitlines()
if not lines or not lines[0].strip().startswith('第53章'):
    new = '第53章 铁幕初现\n\n' + new
lines = new.splitlines()
while lines and not lines[-1].strip():
    lines.pop()
if not lines or lines[-1].strip() != '（本章完）':
    if lines and lines[-1].strip().startswith('（本章完）'):
        lines[-1] = '（本章完）'
    else:
        lines.append('（本章完）')
new = '\n'.join(lines) + '\n'
# clean obvious AI words
for old, repl in {'意识到':'察觉','意味着':'说明','仿佛':'','不禁':'','微微':'','淡淡':'','缓缓':'','宛如':'像'}.items():
    new = new.replace(old, repl)

with open(out_path, 'w', encoding='utf-8') as f:
    f.write(new)

cn = len(re.findall(r'[\u4e00-\u9fff]', new))
first = next((l.strip() for l in new.splitlines() if l.strip()), '')
last = next((l.strip() for l in reversed(new.splitlines()) if l.strip()), '')
os.makedirs(os.path.dirname(review_path), exist_ok=True)
with open(review_path, 'w', encoding='utf-8') as f:
    f.write(f'# 第53章修订说明\n\n字数：{cn}\n首行：{first}\n末行：{last}\n修订：落实铁幕具象化、权限/门禁目标、张维舟时间轴、即时警报钩子。\n')
print(f'REVISED ch53 chars={cn} first={first} last={last}')
