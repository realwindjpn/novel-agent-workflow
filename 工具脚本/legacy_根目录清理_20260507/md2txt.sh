#!/bin/bash
# MD→番茄投稿TXT：压缩连续空行为单空行，去除markdown符号
# 用法: ./md2txt.sh 第40章.md
SRC="$1"
NAME=$(basename "$SRC" .md)
OUT="已投稿/${NAME}.txt"

sed 's/^$//' "$SRC" | tr -s '\n' | \
  sed 's/^[#`*>~]//; s/[*_~]//g' \
  > "$OUT"

echo "→ $OUT ($(wc -c < "$OUT") bytes)"
