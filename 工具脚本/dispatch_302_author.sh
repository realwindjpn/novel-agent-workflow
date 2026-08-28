#!/usr/bin/env bash
# 302 网页 Qwen 作者席投递：新建项目内对话 + 冷启动 + 3 连重试
set -u
cd /root/workspace/工具/web_agents_qwen || exit 1

PY=/root/.hermes/hermes-agent/.venv/bin/python3
TASK=/root/workspace/科武纪元/任务运行态/20260828_kewu_selfcycle_daily
PROMPT=$TASK/output/AUTHOR_302_PROMPT.md
OUT=$TASK/output/qwen_302_r1_raw.md
STATE=$TASK/output/qwen_state_302.json
LOG=$TASK/output/qwen_302_r1.log
PROJ="https://chat.qwen.ai/p/18dab9a0-fea0-490f-abc2-aff83b85ee04"

for i in 1 2 3; do
  echo "=== ATTEMPT $i $(date +%H:%M:%S) ===" | tee -a "$LOG"
  $PY scripts/qwen_submit_chapter.py \
      --prompt-file "$PROMPT" \
      --output "$OUT" \
      --state-file "$STATE" \
      --profile-dir .qwen-browser-profile \
      --project-url "$PROJ" \
      --new-session \
      --skip-role \
      --take-last \
      --preferred-model qwen3.8-max \
      --min-chars 3000 \
      --timeout 1500 \
      --cdp-url "" >> "$LOG" 2>&1
  rc=$?
  echo "attempt $i rc=$rc" | tee -a "$LOG"
  if [ -s "$OUT" ]; then
    chars=$($PY -c "import pathlib,re;t=pathlib.Path('$OUT').read_text(encoding='utf-8');print(len(re.findall(r'[\u4e00-\u9fff]',t)))")
    echo "attempt $i recovered cjk=$chars" | tee -a "$LOG"
    if [ "$chars" -ge 3000 ]; then
      echo "SUCCESS attempt=$i cjk=$chars" | tee -a "$LOG"
      exit 0
    fi
  fi
  echo "attempt $i insufficient, retry after 20s" | tee -a "$LOG"
  sleep 20
done
echo "ALL_3_ATTEMPTS_FAILED" | tee -a "$LOG"
exit 1
