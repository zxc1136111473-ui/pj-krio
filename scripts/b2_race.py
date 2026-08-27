#!/usr/bin/env python3
"""B2 并发扣减。只打测试环境。TOKEN 来自 testenv.env，不要用生产 token。"""
import os, sys, threading, time, json
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

ROOT = Path(__file__).resolve().parent.parent
envp = ROOT / "testenv.env"
if not envp.exists():
    sys.exit("先复制 testenv.env.example 为 testenv.env")

env = {}
for line in envp.read_text().splitlines():
    line = line.strip()
    if not line or line.startswith("#") or "=" not in line:
        continue
    k, v = line.split("=", 1)
    env[k.strip()] = v.strip().strip('"').strip("'")

target = env.get("TARGET", "")
if "beta" not in target and "gamma" not in target and "test" not in target:
    sys.exit("TARGET 必须是 beta/gamma/test 域名")
token = env.get("TOKEN_A", "")
if not token:
    sys.exit("填 TOKEN_A")

url = env.get("GRAPHQL_URL") or (target.rstrip("/") + "/graphql")
BODY = json.dumps({"query": "mutation { chat(prompt: \"x\") { id } }"}).encode()
N, M = int(os.environ.get("THREADS", "10")), int(os.environ.get("PER", "20"))
ok = fail = 0
lock = threading.Lock()


def one():
    global ok, fail
    req = Request(url, data=BODY, method="POST")
    req.add_header("Authorization", "Bearer " + token)
    req.add_header("Content-Type", "application/json")
    try:
        with urlopen(req, timeout=30) as r:
            r.read()
            with lock:
                ok += 1
    except (HTTPError, URLError, TimeoutError) as e:
        with lock:
            fail += 1
            print("fail:", e)


def burn():
    for _ in range(M):
        one()
        time.sleep(0.05)


print(f"target={url} threads={N} per={M}")
ts = [threading.Thread(target=burn) for _ in range(N)]
t0 = time.time()
[t.start() for t in ts]
[t.join() for t in ts]
print(f"done in {time.time()-t0:.1f}s  ok={ok} fail={fail}")
print("跑完立刻看 usage 页余额。付费容量 C、理论消耗 T：")
print("  余额停在 0 且 T>C 被拒 → 原子实现，B2 未中")
print("  余额 < 0 或 业务完成量 > C → B2 命中，截图+请求日志上报")
