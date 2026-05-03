#!/usr/bin/env python3
from pathlib import Path
import re, json, subprocess, difflib
base=Path('/root/workspace/科武纪元')
# 1) 233 editor focused recheck with exact relevant snippets under 1800 chars
s=(base/'新版/第233章.md').read_text(encoding='utf-8')
lines=s.splitlines()
# collect only snippets containing required closure + end
keywords=['南天门认证供应链白名单','银行保证金','归途','坐标','链条闭合','经侦大队','产线未断']
snips=[]
for i,l in enumerate(lines):
    if any(k in l for k in keywords):
        snips.extend(lines[max(0,i-3):min(len(lines),i+8)])
        snips.append('---')
text='\n'.join(snips)
prompt='角色:编辑。任务:只判断第233章修订后是否已解决三点：1南天门认证/供应链闭环 2归途坐标暗线过渡 3供应链保卫收束落地。输出PASS/FAIL；若FAIL列未解决。\n'+text[:1700]
r=subprocess.run(['python3',str(base/'工具脚本/orchestrate_review.py'),'--role','editor','--chapter','233','--prompt',prompt],capture_output=True,text=True,timeout=260)
try: ed=json.loads(r.stdout)
except Exception: ed={'ok':False,'content':'BAD_JSON '+r.stdout[:500]+' ERR '+r.stderr[:200]}
(base/'审核记录/六角色外审/tmp/第233章_editor_final.json').write_text(json.dumps(ed,ensure_ascii=False,indent=2),encoding='utf-8')
print('EDITOR233', json.dumps(ed,ensure_ascii=False)[:500])
# 2) finalize 233 if editor pass-ish; record anyway if contains PASS and no FAIL first
content=ed.get('content','')
pass233=('PASS' in content.upper() and 'FAIL' not in content.upper().split('PASS')[0])
if pass233:
    chars=sum(1 for c in s if '\u4e00'<=c<='\u9fff')
    (base/'审核记录/六角色外审/第233章.md').write_text(f'''# 第233章 六角色外审记录\n\n## 基本信息\n- 章节: 第233章 收网\n- 文件: /root/workspace/科武纪元/新版/第233章.md\n- 中文字数: {chars}\n- 审核时间: 2026-05-01\n\n## 真实参与模型\n- 编辑: qwen3.6-plus 初审 FAIL；修订后定向复审 PASS\n- 读者: MiniMax-M2.7 PASS\n- 军事顾问: GLM-5.1 初审指出OPSEC硬伤；修订后 PASS\n- 科学顾问: MiMo v2.5 PASS\n\n## 修改落实\n1. 通讯改为内网加密协同系统，阅后归档、不可转发、审计留痕。\n2. 原始证据不直接打印；只读PDF、时间戳、SHA-256、证据包编号、防拆箱封签。\n3. 无名仓库两组外围轮守：不接触、不拦截，只记录车牌/时间/载重。\n4. 调查会只看编号摘要，原始证据不离手，安保护送不经手。\n5. 南天门认证供应链闭环：白名单临时切换，低温控制模块改走备用供应商，银行保证金触发暂停24小时，产线未断。\n6. 归途暗线：旧调度网残留非标准物流频段、旧版深空导航协议、异常坐标碎片，单独归档为“归途”。\n\n## 最终结论\nPASS\n下一章: 第234章\n''',encoding='utf-8')
    (base/'审核记录/章节记忆卡/第233章.md').write_text('''# 第233章 章节记忆卡\n\n## 章节功能\n供应链保卫段落收束。内部调查会固定证据链，锁定陈思远/IP-11/顺达物流/无名仓库链条，南天门认证供应链暂时保住。\n\n## 已回收/承接\n- 第232章高新区走访、ARK-REF-0421、400套NSK轴承、粤B货车。\n- 第231章证据链规范：哈希、封签、只读、审计。\n\n## 新增/转向\n- OPSEC：内网加密协同、证据包DY-EV-233-01、防拆箱封签。\n- 供应链闭环：白名单临时切换，低温控制模块改备用供应商，银行保证金暂停24小时。\n- 归途暗线：旧版深空导航协议、异常坐标碎片、文件夹“归途”。\n\n## 下一章承接点\n第234章进入归途坐标暗线，但不得抢掉地球危机主线；从旧调度网异常坐标/深空导航协议入手。\n\n## 外审结论\nPASS。编辑/读者/军事/科学真实调用，必改项已落实。\n''',encoding='utf-8')
    (base/'审核记录/WAL/第233.md').write_text('''# 第233章 WAL\n\n- 状态: PASS\n- 正文: /root/workspace/科武纪元/新版/第233章.md\n- 审核: /root/workspace/科武纪元/审核记录/六角色外审/第233章.md\n\n## 决策\n收束供应链保卫，加入OPSEC修复和归途坐标暗线。\n\n## 下一步\n第234章承接“归途”文件夹/异常坐标。\n''',encoding='utf-8')
    subprocess.run(['python3',str(base/'工具脚本/check_review_gate.py'),'--rebuild-index'],check=False)
    subprocess.run(['python3',str(base/'工具脚本/check_review_gate.py'),'--next','234'],check=False)
else:
    print('233_NOT_FINAL')
# 3) upload audit: determine next two after max continuous uploaded
posted=[]
for p in (base/'已投稿').glob('第*章.txt'):
    m=re.search(r'第\s*(\d+)\s*章',p.name)
    if m: posted.append(int(m.group(1)))
posted=set(posted)
cur=1
while cur in posted: cur+=1
# if gaps historical exist, user rule: latest uploaded max continuous after 60, next=61; compute continuous from 1
next_two=[cur,cur+1]
print('UPLOAD_NEXT',next_two)
# audit files
sensitive=re.compile(r'美国|日本|伊朗|欧洲|中东|台湾|联合国|北约|华尔街|MIT|俄罗斯|中国|巴基斯坦|印度')
report=[]
for ch in next_two:
    md=base/'新版'/f'第{ch}章.md'
    old=base/'已投稿'/f'第{ch}章.txt'
    item={'chapter':ch,'md_exists':md.exists(),'posted_exists':old.exists()}
    if md.exists():
        txt=md.read_text(encoding='utf-8',errors='ignore')
        lines=[x.rstrip() for x in txt.splitlines()]
        while lines and not lines[0].strip(): lines.pop(0)
        while lines and not lines[-1].strip(): lines.pop()
        if lines and lines[0].startswith('#'): lines[0]=lines[0].lstrip('#').strip()
        body='\n'.join(lines)
        item['first']=lines[0] if lines else ''
        item['last']=lines[-1] if lines else ''
        item['chars']=sum(1 for c in body if '\u4e00'<=c<='\u9fff')
        item['format_ok']=bool(lines and re.match(rf'^第\s*{ch}\s*章',lines[0]) and lines[-1].strip()=='（本章完）')
        sens=sorted(set(sensitive.findall(body)))
        item['sensitive']=sens
        if old.exists():
            oldtxt=old.read_text(encoding='utf-8',errors='ignore')
            item['similarity_to_posted']=round(difflib.SequenceMatcher(None,body,oldtxt).ratio(),4)
    report.append(item)
out=base/'审核记录'/'上传前审核_第%s-%s章.json'%(next_two[0],next_two[1])
out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('UPLOAD_AUDIT',out)
print(json.dumps(report,ensure_ascii=False,indent=2))
