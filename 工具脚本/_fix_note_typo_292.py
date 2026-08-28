#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""292 TXT 作者说确定性错字修复：砸化镓 -> 砷化镓。不动正文。"""
import hashlib
import re

TXT = "/root/workspace/\u79d1\u6b66\u7eaa\u5143/\u5df2\u6295\u7a3f/\u7b2c292\u7ae0.txt"
MARK = "\u4f5c\u8005\u6709\u8bdd\u8bf4\uff1a"
BAD = "\u7838\u5316\u9553"   # 砸化镓
GOOD = "\u7837\u5316\u9553"  # 砷化镓

t = open(TXT, encoding="utf-8").read()
head, sep, note = t.partition(MARK)
assert sep, "MARK_NOT_FOUND"
body_sha_before = hashlib.sha256(head.encode("utf-8")).hexdigest()
n = note.count(BAD)
note_fixed = note.replace(BAD, GOOD)
out = head + MARK + note_fixed
with open(TXT, "w", encoding="utf-8") as f:
    f.write(out)

t2 = open(TXT, encoding="utf-8").read()
h2, _, n2 = t2.partition(MARK)
print("replaced", n)
print("body_sha_unchanged", hashlib.sha256(h2.encode("utf-8")).hexdigest() == body_sha_before)
print("bad_remaining_in_file", t2.count(BAD))
print("good_in_note", n2.count(GOOD))
print("note_len", len(n2.strip()))
print("txt_sha256", hashlib.sha256(t2.encode("utf-8")).hexdigest())
print("body_cjk", len(re.findall(r"[\u4e00-\u9fff]", h2)))
