#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""确定性核对：远端草稿正文 == 本地 TXT 正文去标题行；并核对作者说模块是否在页。"""
import json
import re
from pathlib import Path

R = Path(
    "/root/workspace/\u79d1\u6b66\u7eaa\u5143/\u4efb\u52a1\u8fd0\u884c\u6001/20260823_kewu_selfcycle_daily/output/takeover_292/draft_remote_body_292.txt"
)
L = Path("/root/workspace/\u79d1\u6b66\u7eaa\u5143/\u5df2\u6295\u7a3f/\u7b2c292\u7ae0.txt")

remote = R.read_text(encoding="utf-8")
local = L.read_text(encoding="utf-8")
local_body = local.split("\u4f5c\u8005\u6709\u8bdd\u8bf4\uff1a")[0]
lines = [l for l in local_body.splitlines()]
assert lines[0].startswith("\u7b2c292\u7ae0"), lines[0]
local_no_title = "\n".join(lines[1:])


def norm(s):
    return re.sub(r"\s", "", s)


nr, nl = norm(remote), norm(local_no_title)
out = {
    "remote_norm_len": len(nr),
    "local_no_title_norm_len": len(nl),
    "exact_match_excluding_title": nr == nl,
    "remote_cjk": len(re.findall(r"[\u4e00-\u9fff]", remote)),
    "local_no_title_cjk": len(re.findall(r"[\u4e00-\u9fff]", local_no_title)),
    "title_line": lines[0],
    "chapter_end_once": nr.count("\uff08\u672c\u7ae0\u5b8c\uff09") == 1,
    "no_dup_first_para": nr.count("\u4f1a\u8bae\u5ba4\u7684\u6295\u5f71\u5c4f\u6302\u5728\u5317\u5899") == 1,
}
if nr != nl:
    for i, (a, b) in enumerate(zip(nr, nl)):
        if a != b:
            out["first_diff_index"] = i
            out["remote_ctx"] = nr[max(0, i - 40):i + 40]
            out["local_ctx"] = nl[max(0, i - 40):i + 40]
            break
print(json.dumps(out, ensure_ascii=False, indent=2))
Path(
    "/root/workspace/\u79d1\u6b66\u7eaa\u5143/\u4efb\u52a1\u8fd0\u884c\u6001/20260823_kewu_selfcycle_daily/output/takeover_292/draft_body_confirm_292.json"
).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
