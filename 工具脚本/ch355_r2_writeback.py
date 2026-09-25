#!/usr/bin/env python3
"""把 ch355 R2 五席审稿结果写回审核记录目录（产物落盘 + 首行校验）。"""
import json
from pathlib import Path

OUT = Path("/root/workspace/科武纪元/审核记录/ch355_review_r2")
OUT.mkdir(parents=True, exist_ok=True)

RESULTS = {
    "editor": {
        "provider": "bmapi", "model": "gpt-5.6-sol", "duration_sec": 120.91,
        "text": """VERDICT: PASS
L111 | 虹膜扫描日志里有一条异常。毛细血管渗透压升高。 | 将虹膜扫描日志改为眼底或接口生理监测日志，或补一句检测原理 | 当前检测对象与指标的对应关系略跳，补足后技术逻辑更稳。
L123 | 屏幕上，谢云的接口温度曲线在缓慢下降。四个接口的读数从橙区往黄区挪。很慢。但在挪。 | 可补一处医疗组接管或降载动作 | 严重接口过载后的处置链更完整，也能强化林星辰停步观察的因果。
L130 | 第三次合拢的时候，小指没有跟上。它慢了半拍。他盯着那根小指看了两秒。然后它跟上了。 | 可让小指失同步再出现一次，或补一个短暂的动作代价 | 单次异常目前更像悬念提示，重复一次能增强神经损伤的连续性。
L132 | 视野右下角的那块模糊还在。比刚才大了一点。他眨了一下眼。 | 可补一句他确认模糊范围或避开操作界面 | 章末视觉损伤钩子成立，增加一个可观察反馈会更有落点。
"""},
    "structure": {
        "provider": "sensenova", "model": "glm-5.2", "duration_sec": 266.92,
        "text": """VERDICT: PASS

结构完整。三视角（林星辰/谢云/方宁）切换均以空行断开，转场干净；开篇钩子（L2 无名指抖）与结尾悬念（L114-L116 视野模糊扩大）首尾闭合，铁幕主节点离线（L57-L60）扣题"溃败"。数值链自洽：带宽87%→83%（L21/L75-L76）、72h（L18/L21）、432nm与六十三号档案咬合（L45/L50/L54）、四接口淤青三见一致（L20/L28/L109）。方宁右手护具（L34）承接354灼伤退线，谢云颅内侧毛细血管渗漏（L71）与虹膜日志渗透压异常（L93）互证，无矛盾。

非阻断建议：
1. L113 | 走到手腕的时候被接口的热度截住了 | 热度落点改"手背"以应L20"手背四个神经接口" | 接口定位前后统一
2. L39 | 南极节点的加密壳在剥落。轨道中继的路由表在重写 | 收线段可一笔带过"流云切众星"以落大纲锚点，否则确认后章承接 | 锚点覆盖核对
"""},
    "science_mil": {
        "provider": "chun-grok46", "model": "grok-4.6", "duration_sec": 39.23,
        "text": "VERDICT: PASS\n"},
    "reader": {
        "provider": "yezi-gemini", "model": "gemini-3.8-flash", "duration_sec": 29.79,
        "text": """VERDICT: PASS

追读评分：5分。第七卷收官节奏极稳，铁幕节点离线的情绪宣泄克制而有力，无瑕项目深空飞行器悬念留足，三人组身体代偿细节硬核扎实。

L54 | 四百三十二纳米。那条针一样的异常谱线，和六十三号档案里的发射峰，毛刺对毛刺，齿口咬合。峰值位置偏差不超过零点三纳米。线宽几乎一致。连边缘那几根细碎的次级峰都对上了，像两把锉刀的齿纹互相卡进去。 | 可考虑删去末尾「像两把锉刀的齿纹互相卡进去」 | 前半句「毛刺对毛刺，齿口咬合」已足够具象，锉刀比喻稍有叠床架屋，不改亦不阻断。

L81 | 方宁听见链路断了。 | 可保持现状 | 医疗舱视角的静止与无声极为克制，对比主控台震荡形成有力留白。
"""},
    "deai": {
        "provider": "sensenova2", "model": "glm-5.2", "duration_sec": 270.47,
        "note": "原席 yi-hydrogel/grok-4.7 fallback 链全挂，按配方换异 provider 补席",
        "text": """VERDICT: PASS

非阻断建议（5条，均可不改即过）：

L80|"第一遍是回答。第二遍是确认自己还在说话。"|删后句、留"说了两遍。"|叙述者拆解重复动机，偏解释腔；前文衰退已足传达。

L28/L109|"灯光穿过积液，青紫色变成一种脏兮兮的透"/"穿过积液，在皮肤底下投出四小块暗色的透"|L109换角度写淤青（形状/边缘/扩散）|同一"灯—积液—透"意象近复刻。

L92/L112|"他的声音比刚才慢半拍"/"它慢了半拍"|L112改"跟不上/迟一拍"|"慢半拍"两用于声与指，词复。

L23/L34/L72|"像玻璃上哈了一口气"/"像隔了一层水"/"像隔着一层没擦干净的水"|L34换非水系喻体（方宁系听觉）|"水/玻璃模糊"喻体三现，听觉与视觉混同。

L5|"左屏的加密壳剥落进度，中屏的路由表重写，右屏的生物遥测曲线"|三屏拆入眼跳动作逐屏写|工整三联排比，偏清单腔节奏。

判定依据：全文感官/物理锚点密（温、汗、皮、痛、积液、谱线、带宽），科学机制具体（432nm咬合、毛细管渗压、多普勒频移），动作链完整；无比喻空抒情、无设定直灌、无"不是…而是"公式、无拆否定句（L71"像刚哭过，但他没有哭"为喻后否定、L105"很慢。但在挪"为让步，均非先否定后揭底形状）、无AI高频词。上述5项为打磨级，不阻断。
"""},
}

report = {}
for seat, r in RESULTS.items():
    text = r["text"]
    first = text.strip().split("\n")[0].strip()
    ok = first in ("VERDICT: PASS", "VERDICT: FAIL")
    if not ok:
        raise SystemExit(f"{seat} 首行不合规: {first!r}")
    (OUT / f"{seat}.md").write_text(text, encoding="utf-8")
    meta = {k: v for k, v in r.items() if k != "text"}
    meta.update({"seat": seat, "verdict": first.split(": ")[1], "first_line_ok": True,
                 "chars": len(text)})
    (OUT / f"{seat}.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    report[seat] = meta
    print(f"{seat:12s} {meta['verdict']:5s} {r['provider']}/{r['model']:24s} {r['duration_sec']:6.1f}s 首行OK")

(OUT / "summary.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
npass = sum(1 for m in report.values() if m["verdict"] == "PASS")
print(f"\n五席 {npass}/5 PASS")
