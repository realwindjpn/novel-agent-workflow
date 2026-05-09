from pathlib import Path
import subprocess,json,re,sys
ch=int(sys.argv[1])
proj=Path('/root/workspace/科武纪元')
subprocess.run(['python3',str(proj/'工具脚本/build_review_evidence.py'),str(ch)],cwd='/root/workspace',check=True,capture_output=True,text=True)
md=proj/'审核记录/证据包'/f'第{ch}章_证据包.md'
review=proj/'审核记录/六角色外审'/f'第{ch}章.md'
raw_dir=proj/'审核记录/六角色外审/raw'; raw_dir.mkdir(parents=True,exist_ok=True)
full=md.read_text(encoding='utf-8',errors='ignore')
def section(name,limit=1800):
    marker='## '+name
    i=full.find(marker)
    if i<0: return ''
    j=full.find('\n## ',i+1)
    return full[i:j if j>0 else len(full)][:limit]
# MiniMax 读者模型长证据包容易返回非JSON/解析失败；读者门禁优先尾段+钩子+任务卡，保持短输入。
parts=[]
for name,lim in [('本地预检',300),('任务卡摘录',700),('尾段行号',2200),('证据地图：章末钩子',800),('证据地图：大纲锚点',500)]:
    s=section(name,lim)
    if s: parts.append(s)
pkg='\n\n'.join(parts)
prompt=f'''你是网文读者门禁。只看证据包，判断本章是否想继续看下一章。

RTK证据包：
{pkg[:4500]}

第一行必须且只能输出 PASS 或 FAIL（大写英文），不得有前缀、标点、修饰。
PASS=看得懂/顺/爽/AI味轻/章末想看下一章。FAIL=看不懂/AI味重/结构断裂/无追读欲。
第二行起可写≤3条理由。
章末钩子允许语义等效表达，不要求原文匹配。
'''
cmd=['python3',str(proj/'工具脚本/orchestrate_review.py'),'--role','reader','--prompt',prompt]
rr=subprocess.run(cmd,cwd='/root/workspace',capture_output=True,text=True,timeout=240)
raw=(rr.stdout or '')+'\n'+(rr.stderr or '')
(raw_dir/f'第{ch}_reader_evidence_gate.json').write_text(raw,encoding='utf-8')
m=re.search(r'"content"\s*:\s*"(.*?)"\s*,\s*"tokens_used"',raw,re.S)
s=(m.group(1) if m else raw).replace('\\n','\n')
# MiniMax may emit <think>...</think> before the actual verdict.
s2=re.sub(r'<think>.*?</think>','',s,flags=re.S).strip()
first=next((x.strip() for x in s2.splitlines() if x.strip()),'')
# 中文模型正向表达
positive_en = any(k in s2 for k in ['PASS', 'pass'])
positive_zh = any(k in s2 for k in [
    '没问题','通过','合格','想继续看','想追','追读','很好','不错','想看下一章',
    '继续看下一章','继续阅读','可进入','完整度达标','悬念设置好',
    '值得看','可以进入','节奏好','结构完整','没有大问题'
])
# 负向阻断
negative = any(k in first for k in ['FAIL','失败','不合格','重写','看不懂','AI味重','无追读欲','不想看','不推荐']) or \
           any(k in s2 for k in ['重写全文','方向性错误','严重跑题'])
ok = '"ok": true' in raw and (positive_en or positive_zh) and not negative
old=review.read_text(encoding='utf-8',errors='ignore') if review.exists() else f'# 第{ch}章 六角色外审记录\n'
review.write_text(old+f'''\n\n## RTK证据包读者门禁（2026-05-02）\n- 证据包：审核记录/证据包/第{ch}章_证据包.md\n- 原始输出：raw/第{ch}_reader_evidence_gate.json\n- 结论：{'PASS' if ok else 'REVIEW_NEEDED'}\n\n## 当前门禁汇总\n- 编辑证据包：见 raw/第{ch}_editor_evidence_gate.json\n- 读者证据包：{'PASS' if ok else 'REVIEW_NEEDED'}\n''',encoding='utf-8')
print(json.dumps({'chapter':ch,'reader_evidence_pass':ok,'evidence':str(md),'review':str(review)},ensure_ascii=False))
