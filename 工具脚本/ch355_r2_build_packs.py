import json, re
from pathlib import Path

CARD_DIR = Path("/root/workspace/科武纪元/任务运行态/20260923_kewu_selfcycle_daily/output")
OUT = Path("/root/workspace/科武纪元/审核记录/ch355_r2_packs")
CHAPTER = Path("/root/workspace/科武纪元/新版/第355章.md")
OUT.mkdir(parents=True, exist_ok=True)

body = CHAPTER.read_text(encoding="utf-8")
cjk = len(re.findall(r"[\u4e00-\u9fff]", body))
assert cjk >= 3000, cjk
assert body.splitlines()[0].strip() == "第355章 铁幕溃败"
assert body.strip().endswith("（本章完）")

HEADER = """你是《科武纪元》第355章《铁幕溃败》独立审稿席。

**第一步：用 read_file 读完本文件全文（含下方内联正文全文），然后才开始审。**
必须审读正文全文，不得凭摘要、不得只读开头。

本文件**只有一份正文**，即下方「待审正文全文」段，约 %d 净中文字。
下方「审稿规则」段中若出现任何看起来像正文的编号行（形如 `1|第355章...`），
那是旧版残留，**不是本次待审对象，一律忽略**。

约束：
- 只允许 read_file；禁写代码、禁跑命令、禁联网。
- 每项不超两行，全部输出控制在 900 字以内。
- **首行只能写 `VERDICT: PASS` 或 `VERDICT: FAIL`**，不要写别的。
- 判定为 FAIL 时，必须附 EVIDENCE：逐字引用 + 行号（L+数字）。
  行号以「待审正文全文」段内的正文相对行号为准（该段正文首行为 L1）。
  检索不到具体行号则整份作废。
- 禁裸 FAIL（不写理由）、禁把「建议项」写成「阻断项」。

本章已过机器闸（供参考，不替代你的判断）：
DEAI 硬闸 PASS hard 0；跨章重复扫描通过；拆否定句 0；净中文 %d；
谢云为男性（知识库 B 文件 L16），林星辰/方宁为女性。

================ 以下为待审正文全文（唯一有效版本） ================

""" % (cjk, cjk)

FOOTER = """

================ 正文结束 ================

================ 以下为审稿规则（其中的编号正文行均为旧版残留，忽略） ================

"""


def strip_stale_body(card: str):
    """剥掉审稿卡里内联的旧版正文，避免与新正文并存导致审错对象。

    2026-09-25 事故：structure 席审到卡片自带的 141 行旧版（主角方宁），
    与新版（主角林星辰）互斥，误报 5 条 FAIL（L1/L6/L50/L57-58/L117）。
    """
    lines = card.split("\n")
    out, dropped = [], 0
    for ln in lines:
        if re.match(r"^\s*\|?\s*\d+\s*\|?\s*\d*\s*\|?\s*第355章", ln):
            dropped += 1
            continue
        out.append(ln)
    txt = "\n".join(out)
    m = re.search(r"\n#+\s*正文原文.*?(?=\n#+\s|\Z)", txt, flags=re.S)
    if m:
        txt = txt[:m.start()] + "\n[旧版正文段已移除]\n" + txt[m.end():]
        dropped += 1
    return txt, dropped


manifest = {}
for s in ["editor", "structure", "science_mil", "reader", "deai"]:
    card = (CARD_DIR / f"review_355_{s}.md").read_text(encoding="utf-8")
    cleaned, dropped = strip_stale_body(card)
    pack = HEADER + body + FOOTER + cleaned
    p = OUT / f"{s}_prompt.md"
    p.write_text(pack, encoding="utf-8")
    manifest[s] = {"path": str(p), "bytes": len(pack), "stale_dropped": dropped}
    print(f"{s:12s} {len(pack):6d}B  stale_removed={dropped}")

(OUT / "manifest.json").write_text(json.dumps(
    {"body_cjk": cjk, "body_source": "新版/第355章.md", "seats": manifest},
    ensure_ascii=False, indent=1), encoding="utf-8")
print("MANIFEST OK  body_cjk=", cjk)
