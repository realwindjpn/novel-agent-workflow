#!/usr/bin/env python3
import requests,re,json,pathlib,html,datetime,hashlib
from urllib.parse import quote
ROOT=pathlib.Path('/root/workspace/科武纪元')
rawdir=ROOT/'硬科学素材/采集_20260526/raw'; rawdir.mkdir(parents=True,exist_ok=True)
carddir=ROOT/'时事素材/素材卡/2026-05-27'; carddir.mkdir(parents=True,exist_ok=True)
kbdir=ROOT/'知识库/芯片算力'; kbdir.mkdir(parents=True,exist_ok=True)
queries=[
 '"多层电子系统的时间缩放理论" "何庭波"',
 '"多层电子系统的时间缩微理论" "何庭波"',
 '"韬定律" "何庭波" "观察者网"',
 '"韬定律" "上海证券报"',
 '"韬定律" "腾讯新闻"',
 '"韬定律" "微博" "华为"',
 '"韬定律" "微信公众号" "华为"',
 '"Tau Scaling Law" "Huawei" "ISCAS 2026"',
]
headers={'User-Agent':'Mozilla/5.0 AppleWebKit/537.36 Chrome/124 Safari/537.36','Accept-Language':'zh-CN,zh;q=0.9'}
results=[]
for q in queries:
    r=requests.get('https://www.bing.com/search?q='+quote(q)+'&setlang=zh-cn&cc=CN',headers=headers,timeout=25)
    blocks=re.findall(r'<li class="b_algo".*?</li>',r.text,re.S)
    for b in blocks:
        m=re.search(r'<h2[^>]*>\s*<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>',b,re.S) or re.search(r'<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>',b,re.S)
        if not m: continue
        href=html.unescape(m.group(1)); title=html.unescape(re.sub('<.*?>','',m.group(2))).strip()
        sn=re.search(r'<p[^>]*>(.*?)</p>',b,re.S); desc=html.unescape(re.sub('<.*?>','',sn.group(1))).strip() if sn else ''
        blob=(title+' '+desc+' '+href).lower()
        if any(k.lower() in blob for k in ['韬定律','何庭波','tau scaling','logicfolding','hi-one','iscas 2026','多层电子系统']):
            results.append({'query':q,'title':title,'url':href,'desc':desc[:800]})
# dedupe
seen=set(); ded=[]
for x in results:
    if x['url'] in seen: continue
    seen.add(x['url']); ded.append(x)
results=ded
pages=[]
for x in results[:25]:
    try:
        rr=requests.get(x['url'],headers=headers,timeout=25)
        txt=re.sub('<script.*?</script>|<style.*?</style>','',rr.text,flags=re.S)
        txt=html.unescape(re.sub('<[^>]+>',' ',txt)); txt=re.sub(r'\s+',' ',txt).strip()
        pages.append({'source':x,'status':rr.status_code,'len':len(txt),'text':txt[:12000]})
    except Exception as e:
        pages.append({'source':x,'error':str(e)})
raw=(rawdir/'tao_official_social_collect_20260527.json')
raw.write_text(json.dumps({'queries':queries,'results':results,'pages':pages},ensure_ascii=False,indent=2),encoding='utf-8')
# classify evidence
primary=[]; secondary=[]; social=[]
for x in results:
    u=x['url']; t=x['title']
    if any(d in u for d in ['guancha.cn','cnstock.com','thepaper.cn','qq.com','sina.com.cn','ithome.com']): secondary.append(x)
    elif any(d in u for d in ['mp.weixin.qq.com','weibo.com']): social.append(x)
    else: secondary.append(x)
# card
obs=[r for r in results if 'guancha.cn' in r['url'] or '观察' in r['title']]
qq=[r for r in results if 'qq.com' in r['url']]
cnstock=[r for r in results if 'cnstock' in r['url'] or '上海证券报' in r['title']]
sina=[r for r in results if 'sina' in r['url'] or '财经头条' in r['title']]
now=datetime.datetime.now().isoformat(timespec='seconds')
card=f'''# 素材卡：华为“韬（τ）定律”与多层电子系统时间缩放理论（补证）

- 采集时间：{now}
- 主题域：芯片算力 / 算法主权 / 工程替代路径
- 可信度：secondary+（多家公开媒体转载/解读；未取得华为官网或论文预发布平台原始PDF，暂不升primary）
- 原始采集：`{raw}`

## 已命中来源

### 核心转载/全文线索
'''
for x in (obs+qq+sina+cnstock)[:10]:
    card+=f'- {x["title"]}\n  - {x["url"]}\n  - 摘要：{x.get("desc","")[:240]}\n'
card+='''
## 事实摘录

- 公开资料称，华为何庭波围绕“多层电子系统的时间缩放理论”阐述“韬（τ）定律”。核心不是继续单纯追求二维几何缩微，而是通过多层电子系统、逻辑折叠（LogicFolding）等方式降低有效互连延迟/信号传播时间。
- 相关解读把它描述为摩尔定律式“尺寸缩微”之外的工程路径：在先进制程受限时，通过三维堆叠、逻辑重排、光/电互连、系统级协同优化，提高等效算力密度。
- 已命中腾讯新闻/观察者网/新浪财经头条/上海证券报/IT之家/澎湃等公开渠道；其中“何庭波万字论文，详述华为‘韬定律’”与“华为‘韬 (τ)定律’论文全文”是后续追华为原文或预发布平台原文的关键入口。

## 对《科武纪元》的可用性

- 可用于“芯片主权”线：从追先进制程，转为系统级算力密度、互连延迟、三维堆叠和工程折中。
- 可用于“制度/供应链”线：封锁环境下，技术路线不只靠单点突破，而靠架构、封装、EDA、制造协同。
- 小说表达宜落成动作链：工程师不说“突破摩尔定律”，而是拿延迟预算、键合间距、散热余量、良率曲线和供应链替代件做选择。

## 风险与边界

- 暂未抓到华为官网、IEEE官方论文全文、中国科学院科技论文预发布平台原始页。
- 不得写成“已被学界公认为新定律”；只能写“华为提出/公开阐述的工程理论或路线”。
- 微博/微信公众号官方号仍需下一轮定向抓取；本轮Bing未稳定返回官方社媒原文。
'''
card_path=carddir/'素材卡_华为韬定律_多层电子系统时间缩放_补证_20260527.md'
card_path.write_text(card,encoding='utf-8')
kb_path=kbdir/card_path.name
kb_path.write_text(card,encoding='utf-8')
print(json.dumps({'results':len(results),'pages':len(pages),'raw':str(raw),'card':str(card_path),'kb':str(kb_path),'top':[{'title':x['title'],'url':x['url']} for x in results[:10]]},ensure_ascii=False,indent=2))
