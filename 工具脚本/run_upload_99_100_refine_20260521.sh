#!/usr/bin/env bash
set -euo pipefail
cd /root/workspace/科武纪元
export KEWU_AUTHOR_ROUTE=mimo-v2.5-pro
python3 工具脚本/run_refine_chapter_v4.py 99
python3 工具脚本/run_refine_chapter_v4.py 100
