"""mr-trace CLI.

  python3 -m mrtrace serve [--port 8765]          live page that follows mr as jobs run
  python3 -m mrtrace build [-o mr-trace.local.html]   one self-contained HTML snapshot
  python3 -m mrtrace demo  [-o docs/index.html]       scrubbed snapshot safe to publish
  python3 -m mrtrace show <task-id>                   the plain-English story in the terminal
"""
from __future__ import annotations

import argparse
import json
import os
import sys

from . import load, narrate, render, scrub, serve


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="mrtrace")
    p.add_argument("--home", default=load.MR_HOME, help="mr home (default /home/box/mr or $MR_HOME)")
    sp = p.add_subparsers(dest="cmd", required=True)
    s = sp.add_parser("serve"); s.add_argument("--port", type=int, default=8765); s.add_argument("--host", default="127.0.0.1")
    b = sp.add_parser("build"); b.add_argument("-o", "--out", default="mr-trace.local.html")
    d = sp.add_parser("demo"); d.add_argument("-o", "--out", default="docs/index.html"); d.add_argument("--json", default="docs/demo-traces.json")
    sh = sp.add_parser("show"); sh.add_argument("task")
    a = p.parse_args(argv)
    if a.cmd == "serve":
        serve.serve(a.home, a.host, a.port)
        return 0
    traces = load.build_traces(a.home)
    if a.cmd == "build":
        _write(a.out, render.page(render.payload(traces)))
    elif a.cmd == "demo":
        clean = scrub.scrub_traces(traces)
        data = render.payload(clean)
        bad = scrub.find_secrets(data)
        blob = json.dumps(data, default=str)
        leaks = [x for t in traces for x in (t.get("title"), t.get("why"), t.get("task")) if x and len(str(x)) >= 12
                 and not str(x).startswith("t-") and str(x) in blob]
        if leaks:
            print(f"refusing: {len(leaks)} real task titles/labels survived scrubbing", file=sys.stderr)
            return 3
        if bad:
            print(f"refusing: {len(bad)} secret-looking strings survived scrubbing", file=sys.stderr)
            return 2
        _write(a.out, render.page(data))
        _write(a.json, json.dumps(clean, indent=1, default=str))
    elif a.cmd == "show":
        t = next((x for x in traces if x["task"] == a.task), None)
        if not t:
            print("no such task", file=sys.stderr)
            return 1
        print(f"{t['task']}  {t.get('title') or ''}\n{narrate.headline(t)}")
        for i, st in enumerate(t["steps"], 1):
            print(f"  {i}. {narrate.step_line(st)}")
    return 0


def _write(path: str, text: str) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    print("wrote", path)


if __name__ == "__main__":
    sys.exit(main())
