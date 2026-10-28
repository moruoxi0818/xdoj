# -*- coding: utf-8 -*-
"""命令行入口（网页控制台请用 server.py）

  python auto.py --contest 310 --list
  python auto.py --contest 310 --problem 509
  python auto.py --contest 310 --range 39-44
  python auto.py --contest 310 --all --dry
"""

import argparse
import os
import sys
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from ai.solver import load_env      # noqa: E402
from engine import Engine           # noqa: E402
from oj.client import OJError       # noqa: E402


def log(*a):
    print(time.strftime("[%H:%M:%S]"), *a, flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--contest", type=int, default=310)
    ap.add_argument("--problem", type=int)
    ap.add_argument("--range", help="题目列表序号区间，如 39-44")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--dry", action="store_true", help="只生成，不提交")
    ap.add_argument("--retry", type=int, default=1)
    ap.add_argument("--delay", type=int, default=5)
    ap.add_argument("--wait", type=int, default=10)
    ap.add_argument("--poll", type=int, default=15)
    ap.add_argument("--include-ac", action="store_true")
    args = ap.parse_args()

    eng = Engine(lambda e: log(e.get("msg", "")) if e.get("type") == "log" else None)
    cfg = load_env()

    if args.list:
        ps = eng.list_problems(args.contest)
        for i, p in enumerate(ps, 1):
            print(f"  {i:>3} {p['pid']:>6}  {'√' if p['ac'] else ' '}  {p['title']}")
        return 0

    oj = eng.connect(args.contest)
    ps = oj.problems()
    if args.problem:
        pids = [args.problem]
    elif args.range:
        a, b = args.range.split("-")
        pids = [p["pid"] for p in ps[int(a) - 1:int(b)]]
    elif args.all:
        pids = [p["pid"] for p in ps]
    else:
        log("用 --list / --problem / --range / --all 指定题目")
        return 1

    res = eng.run(args.contest, pids, retry=args.retry, dry=args.dry,
                  delay=args.delay, wait=args.wait, poll=args.poll,
                  skip_ac=not args.include_ac)
    return 0 if res and all(r["verdict"] in ("正确", "已通过") for r in res) else 2


if __name__ == "__main__":
    try:
        sys.exit(main())
    except OJError as e:
        log("接口错误:", e)
        sys.exit(1)
