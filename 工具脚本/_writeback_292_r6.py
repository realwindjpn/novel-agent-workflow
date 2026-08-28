#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""292 R6 定稿写回 + TXT 生成（主控确定性机械动作，不改正文语义）"""
import hashlib
import json
import os
import re
import shutil
import sys
import time

ROOT = "/root/workspace/\u79d1\u6b66\u7eaa\u5143"
SRC = os.path.join(ROOT, "\u4efb\u52a1\u8fd0\u884c\u6001/20260823_kewu_selfcycle_daily/output/candidate_292_r6.md")
NEW = os.path.join(ROOT, "\u65b0\u7248/\u7b2c292\u7ae0.md")
TXT = os.path.join(ROOT, "\u5df2\u6295\u7a3f/\u7b2c292\u7ae0.txt")
EXPECT_SHA = "383549126090ce1d510916a43ec37a29def9d4403d4db1584b6025cbf4fe4524"

AUTHOR_NOTE = (
    "\u4f5c\u8005\u6709\u8bdd\u8bf4\uff1a\n"
    "\u4e0a\u4e00\u7ae0\u5361\u5728\u7535\uff0c\u8fd9\u7ae0\u5c31\u5f97\u628a\u7535\u7684\u8d26\u7b97\u5b8c\u3002\u56db\u767e\u4e8c\u5341\u5343\u74e6\u7684\u7f3a\u53e3\uff0c"
    "\u56db\u6761\u73b0\u6210\u8def\u5b50\u9010\u6761\u5835\u6b7b\uff1a\u805a\u53d8\u6269\u5bb9\u5361\u5728\u6c1a\u2014\u2014\u79cd\u5b50\u91cf\u5dee\u4e94\u70b9\u56db\u514b\uff0c"
    "\u6708\u7403\u6c1a\u589e\u6b96\u6bef\u6708\u4ea7\u96f6\u70b9\u4e09\u514b\uff0c\u5341\u516b\u4e2a\u6708\uff1b\u7ef4\u751f\u6cf5\u662f\u4e09\u7528\u4e00\u5907\u7684\u6700\u4f4e\u6784\u578b\uff0c"
    "\u4e0d\u80fd\u52a8\uff1b\u76d1\u542c\u9635\u5217\u8981\u4e24\u65b9\u8054\u7b7e\uff1b\u9057\u8ff9\u6838\u5fc3\u662f\u4e00\u70b9\u516b\u5409\u74e6\u76f4\u6d41\uff0c"
    "\u786c\u63a5\u4ea4\u6d41\u6bcd\u7ebf\u70e7\u7a7f\u9006\u53d8\u6865\u3002\u5269\u4e0b\u7684\u53ea\u6709 L1 \u592a\u9633\u80fd\u9635\u5217\u3002\n"
    "\u94fe\u8def\u6570\u5b57\u662f\u53ef\u9006\u63a8\u7684\uff1a\u706b\u661f\u8f68\u9053\u592a\u9633\u5e38\u6570\u4e94\u767e\u4e5d\u5341\u74e6\u6bcf\u5e73\u65b9\u7c73\uff0c"
    "\u7838\u5316\u9553\u6548\u7387\u4e09\u5341\u4e00\uff0c\u622a\u83b7\u7387\u516d\u5341\u4e8c\u4e58\u6574\u6d41\u4e03\u5341\u56db\uff0c\u94fe\u8def\u603b\u6548\u7387\u56db\u5341\u516d\uff1b"
    "\u56db\u767e\u4e8c\u5341\u9664\u56db\u5341\u516d\uff0c\u9635\u5217\u7aef\u8981\u53d1\u4e5d\u767e\u4e00\u5341\u4e09\u5343\u74e6\uff0c\u52a0\u56db\u4e2a\u767e\u5206\u70b9\u4f59\u91cf\u5c31\u662f"
    "\u4e5d\u767e\u56db\u5341\u4e5d\u3002\u9762\u79ef\u4e94\u5343\u4e8c\u767e\u5e73\u65b9\u7c73\uff0c\u603b\u8d28\u91cf\u5341\u516d\u70b9\u4e5d\u5428\uff0c\u5206\u56db\u6bb5\u8fd0\u3002\n"
    "\u771f\u6b63\u60f3\u5199\u7684\u4e0d\u662f\u65b9\u6848\u672c\u8eab\uff0c\u662f\u8d26\u7b97\u5b8c\u4e4b\u540e\u90a3\u4e9b\u4eba\u3002\u8f68\u9053\u9632\u5fa1\u7684\u5907\u4ef6"
    "\u5ef6\u4e00\u4e2a\u6708\uff0c\u5357\u6bb5\u62e6\u622a\u7a7a\u7a97\u4e8c\u5341\u5929\uff1b\u4ea7\u7ebf\u8fd8\u5dee\u4e94\u5343\u4e09\u767e\u4e8c\u5341\u516d\u4ef6\u7684"
    "\u6b20\u8d26\uff0c\u5e76\u7f51\u4e4b\u540e\u4e5f\u8ffd\u4e0d\u5e73\u3002\u65b9\u6848\u7acb\u9879\u4e0d\u7b49\u4e8e\u95ee\u9898\u89e3\u51b3\uff0c\u53ea\u662f\u628a\u4ee3\u4ef7\u6362\u4e86"
    "\u4e00\u4e2a\u4f4d\u7f6e\u3002\u6563\u4f1a\u65f6\u90a3\u5f20\u6392\u671f\u8868\u60ac\u5728\u684c\u6cbf\u6ca1\u6389\u4e0b\u53bb\uff0c\u5c31\u662f\u8fd9\u4e2a\u610f\u601d\u3002\n"
)


def sha256_file(p):
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def cjk(t):
    return len(re.findall(r"[\u4e00-\u9fff]", t))


def fanqie_count(t):
    """番茄口径：去掉空白后的字符数"""
    return len(re.sub(r"\s", "", t))


out = {"utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}

src_sha = sha256_file(SRC)
out["source"] = {"file": SRC, "sha256": src_sha, "expect": EXPECT_SHA, "match": src_sha == EXPECT_SHA}
if src_sha != EXPECT_SHA:
    print(json.dumps(out, ensure_ascii=False, indent=2))
    sys.exit("SOURCE_SHA_MISMATCH")

body = open(SRC, encoding="utf-8").read()
out["source"]["cjk"] = cjk(body)
out["source"]["fanqie"] = fanqie_count(body)

# ---- 备份既有 ----
bk = {}
stamp = time.strftime("%Y%m%d_%H%M%S")
bkdir = os.path.join(ROOT, "\u5ba1\u6838\u8bb0\u5f55/\u5907\u4efd/292_r6_writeback_" + stamp)
for label, path in (("new_version", NEW), ("txt", TXT)):
    if os.path.exists(path):
        os.makedirs(bkdir, exist_ok=True)
        dst = os.path.join(bkdir, os.path.basename(path))
        shutil.copy2(path, dst)
        bk[label] = {"existed": True, "backup": dst, "old_sha256": sha256_file(path)}
    else:
        bk[label] = {"existed": False, "backup": None, "note": "NO_PRIOR_FILE"}
out["backup"] = bk

# ---- 写回新版（MD 源稿，与候选逐字一致）----
with open(NEW, "w", encoding="utf-8") as f:
    f.write(body)
out["new_version"] = {
    "file": NEW,
    "sha256": sha256_file(NEW),
    "identical_to_candidate": sha256_file(NEW) == src_sha,
    "cjk": cjk(open(NEW, encoding="utf-8").read()),
}

# ---- 生成 TXT（纯正文 + 作者说；去 wikilink / markdown）----
txt = body
txt = re.sub(r"\[\[([^\]|]+)\|([^\]]+)\]\]", r"\2", txt)
txt = re.sub(r"\[\[([^\]]+)\]\]", r"\1", txt)
txt = txt.replace("**", "")
txt = re.sub(r"\n{3,}", "\n\n", txt)
if not txt.endswith("\n"):
    txt += "\n"
txt = txt + "\n" + AUTHOR_NOTE
with open(TXT, "w", encoding="utf-8") as f:
    f.write(txt)

tt = open(TXT, encoding="utf-8").read()
body_only = tt.split("\u4f5c\u8005\u6709\u8bdd\u8bf4\uff1a")[0]
out["txt"] = {
    "file": TXT,
    "sha256": sha256_file(TXT),
    "first_line": tt.splitlines()[0],
    "body_last_line": [l for l in body_only.splitlines() if l.strip()][-1],
    "has_author_note": "\u4f5c\u8005\u6709\u8bdd\u8bf4\uff1a" in tt,
    "author_note_cjk": cjk(AUTHOR_NOTE),
    "body_cjk": cjk(body_only),
    "body_fanqie": fanqie_count(body_only),
    "wikilink": tt.count("[["),
    "markdown_bold": tt.count("**"),
    "triple_blank": bool(re.search(r"\n{3,}", tt)),
    "chapter_end_marker": tt.count("\uff08\u672c\u7ae0\u5b8c\uff09"),
}
print(json.dumps(out, ensure_ascii=False, indent=2))
with open(os.path.join(ROOT, "\u4efb\u52a1\u8fd0\u884c\u6001/20260823_kewu_selfcycle_daily/output/takeover_292/writeback_292_r6.json"), "w", encoding="utf-8") as f:
    json.dump(out, f, ensure_ascii=False, indent=2)
