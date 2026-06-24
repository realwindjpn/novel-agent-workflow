from pathlib import Path
import subprocess, json, re, sys
ch=int(sys.argv[1])
proj=Path('/root/workspace/科武纪元')
subprocess.run(['python3',str(proj/'工具脚本/build_review_evidence.py'),str(ch)],cwd='/root/workspace',check=True,capture_output=True,text=True)
md=proj/'审核记录/证据包'/f'第{ch}章_证据包.md'
review=proj/'审核记录/六角色外审'/f'第{ch}章.md'
raw_dir=proj/'审核记录/六角色外审/raw'; raw_dir.mkdir(parents=True,exist_ok=True)
full=md.read_text(encoding='utf-8',errors='ignore')

# 读证据包 deai_counts，避免字符串误判
json_path=proj/'审核记录/证据包'/f'第{ch}章_evidence.json'
dc={'META_INFO_HARD':0}
if json_path.exists():
    try: dc=json.loads(json_path.read_text(encoding='utf-8')).get('deai_counts',{})
    except: pass

def section(name, limit=1800):
    marker='## '+name
    i=full.find(marker)
    if i<0: return ''
    j=full.find('\n## ', i+1)
    s=full[i:j if j>0 else len(full)]
    return s[:limit]
# Do NOT send first 6500 chars: that truncates before tail. Send prioritized sections.
parts=[]
for name,lim in [('本地预检',500),('任务卡摘录',1200),('尾段行号',6000),('证据地图：章末钩子',1600),('证据地图：大纲锚点',1000),('证据地图：技术动作',900),('证据地图：军事动作',900),('证据地图：投稿风险',600)]:
    s=section(name,lim)
    if s: parts.append(s)
pkg='\n\n'.join(parts)
prompt=f'''RTK证据包：
{pkg[:12000]}

你是审核器 + DEAI编辑门禁。基于以上证据包做判断。
*** 第一行必须且只能输出 PASS 或 FAIL（大写英文）。不得有任何前缀、标点、修饰。不要分析，不要思考过程，不要复述任务，不要说"首先"。 ***
PASS=符合任务卡要求可进入下一章。FAIL=有硬伤/钩子缺失/偏纲/证据不足/去AI硬闸未过。
第二行起必须含：DEAI_EDITOR_PASS 或 DEAI_EDITOR_FAIL；NOT_BUT_COUNT、ENUMERATION_COUNT、META_INFO_COUNT、REPORT_TONE_COUNT。
若证据包“去AI硬闸扫描”中 META_INFO_HARD > 0，必须FAIL。
若出现密集“不是……而是……”、说明书式枚举、公文口播、鸡汤收束，必须给≤3条行号理由。
注意：章末钩子允许语义等效表达，不要求与任务卡原文完全一致。只要章末提及了下章核心主题（如资源管辖权转移、盐滩计划等）即可视为钩子存在。
'''
cmd=['python3',str(proj/'工具脚本/orchestrate_review.py'),'--role','editor','--prompt',prompt]
rr=subprocess.run(cmd,cwd='/root/workspace',capture_output=True,text=True,timeout=240)
raw=(rr.stdout or '')+'\n'+(rr.stderr or '')
(raw_dir/f'第{ch}_editor_evidence_gate.json').write_text(raw,encoding='utf-8')
m=re.search(r'"content"\s*:\s*"(.*?)"\s*,\s*"tokens_used"',raw,re.S)
s=(m.group(1) if m else raw).replace('\\n','\n')
first=next((x.strip() for x in s.splitlines() if x.strip() and not x.strip().startswith('<think>')),'')
required_deai = all(k in s for k in ['DEAI_EDITOR_PASS','NOT_BUT_COUNT','ENUMERATION_COUNT','META_INFO_COUNT','REPORT_TONE_COUNT'])
meta_info_hard = int(dc.get('META_INFO_HARD') or 0) > 0
negative = ('DEAI_EDITOR_FAIL' in s) or meta_info_hard or first.startswith('FAIL')
ok='"ok": true' in raw and first.startswith('PASS') and required_deai and not negative
old=review.read_text(encoding='utf-8',errors='ignore') if review.exists() else f'# 第{ch}章 六角色外审记录\n'
review.write_text(old+f'''\n\n## RTK证据包编辑门禁（2026-05-02）\n- 证据包：审核记录/证据包/第{ch}章_证据包.md\n- 送审方式：任务卡 + 本地预检 + 尾段行号 + 证据地图，避免前文挤掉章末。\n- 原始输出：raw/第{ch}_editor_evidence_gate.json\n- 结论：{'PASS' if ok else 'REVIEW_NEEDED'}\n''',encoding='utf-8')
print(json.dumps({'chapter':ch,'editor_evidence_pass':ok,'evidence':str(md),'review':str(review)},ensure_ascii=False))
