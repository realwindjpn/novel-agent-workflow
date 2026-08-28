#!/usr/bin/env bash
# 302 四审并行投递：跨 provider 跨族，避主控 claude-opus-5 同族
set -u
PY=/root/.hermes/hermes-agent/.venv/bin/python3
DC=/root/workspace/scripts/direct_model_call.py
D=/root/workspace/科武纪元/任务运行态/20260828_kewu_selfcycle_daily
R=$D/output/reviews_302_r1

cd "$D" || exit 1

run() {  # provider model prompt out tag
  $PY "$DC" --provider "$1" --model "$2" \
      --prompt-file "$R/$3" --output "$R/$4" \
      --max-tokens 16384 --timeout 700 --json > "$R/${5}_call.json" 2>&1 &
}

run chun-grok46      grok-4.6       reader_prompt.md    reader_review.md    reader
run yi-hydrogel      grok-4.6       structure_prompt.md structure_review.md structure
run wechat-glm       GLM-5.2        editor_prompt.md    editor_review.md    editor
run aliyun-qwen38    qwen3.8-max    science_prompt.md   science_review.md   science

wait
echo "=== 四审回收 ==="
for tag in reader structure editor science; do
  st=$($PY -c "
import json,pathlib
p=pathlib.Path('$R/${tag}_call.json')
try:
    d=json.loads(p.read_text(encoding='utf-8'))
    print(d.get('status'), d.get('provider'), d.get('requested_model'), str(d.get('error'))[:80])
except Exception as e:
    print('PARSE_FAIL', e)
")
  v=$(head -1 "$R/${tag}_review.md" 2>/dev/null || echo "无产物")
  printf "%-11s %-58s %s\n" "$tag" "$st" "$v"
done
