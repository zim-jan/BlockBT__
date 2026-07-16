import json
import time
import urllib.request

base = "http://127.0.0.1:8000"

r = urllib.request.urlopen(base + "/api/health")
print("HEALTH:", json.loads(r.read()))

body = json.dumps(
    {
        "name": "SMA Phase2 E2E",
        "parameters": {"sma_fast": 10, "sma_slow": 30, "initial_capital": 10000},
    }
).encode()
req = urllib.request.Request(
    base + "/api/strategies/", data=body, headers={"Content-Type": "application/json"}
)
strat = json.loads(urllib.request.urlopen(req).read())
sid = strat["data"]["id"]
print(f"STRATEGY id={sid} name={strat['data']['name']}")

body2 = json.dumps({"strategy_id": sid}).encode()
req2 = urllib.request.Request(
    base + "/api/backtest/", data=body2, headers={"Content-Type": "application/json"}
)
job = json.loads(urllib.request.urlopen(req2).read())
jid = job["data"]["job_id"]
print(f"JOB id={jid} status={job['data']['status']}")

for i in range(8):
    time.sleep(5)
    res = json.loads(urllib.request.urlopen(base + f"/api/backtest/{jid}").read())
    s = res["data"]["status"]
    print(f"POLL {i + 1}: {s}")
    if s in ("COMPLETED", "FAILED"):
        d = res["data"]
        print(f"  return%={d['total_return_pct']}")
        print(f"  sharpe={d['sharpe_ratio']}")
        print(f"  maxDD={d['max_drawdown_pct']}")
        print(f"  trades={d['num_trades']}")
        print(f"  final_capital={d['final_capital']}")
        if d.get("error_message"):
            print(f"  ERROR: {d['error_message']}")
        break
