import json, sys
from pathlib import Path
import importlib.util
spec = importlib.util.spec_from_file_location('scan', '/root/workspace/科武纪元/工具脚本/kewu_deai_hard_gate_scan.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
r = m.scan_file(Path('/root/workspace/科武纪元/新版/第339章.md'))
print(json.dumps({k: r[k] for k in ('verdict','score','hit_count','hard_count')}, ensure_ascii=False))
for h in r['hits']:
    print(h['line'], h['type'], '|', h['text'][:120])
