import json, sys, urllib.request, websocket

PORT = sys.argv[1]
PREF = sys.argv[2]
EXPR = sys.argv[3]

BASE = f"http://127.0.0.1:{PORT}"
lst = json.load(urllib.request.urlopen(f"{BASE}/json/list"))
tab = None
for t in lst:
    if t["id"].startswith(PREF.upper()) and t.get("type") == "page":
        tab = t
        break
if tab is None:
    raise SystemExit(f"NO_TAB {PREF} on {PORT}")
try:
    urllib.request.urlopen(f"{BASE}/json/activate/{tab['id']}").read()
except Exception:
    pass
ws = websocket.create_connection(tab["webSocketDebuggerUrl"], suppress_origin=True, timeout=180)
ws.send(json.dumps({"id": 1, "method": "Runtime.evaluate",
                    "params": {"expression": EXPR, "awaitPromise": True, "returnByValue": True}}))
while True:
    m = json.loads(ws.recv())
    if m.get("id") == 1:
        print(m.get("result", {}).get("result", {}).get("value"))
        break
