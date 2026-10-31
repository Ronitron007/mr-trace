"""Spikes A (git graph), B (flow DAG), C (ladder/waterfall) on the same real mr tasks."""
import html, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from mrtrace import load

TASKS = sys.argv[1:] or ["t-2919b3e9", "t-e1b3bf5d", "t-110ef5eb"]
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
os.makedirs(OUT, exist_ok=True)
traces = {t["task"]: t for t in load.build_traces()}
MERMAID = '<script type="module">import mermaid from "https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs";mermaid.initialize({startOnLoad:true,theme:"neutral",gitGraph:{mainBranchName:"task"}});</script>'

def lbl(s):
    return f"{s['role'][0].upper()}:{s['rung']}"

def gitgraph(t):
    L = ["gitGraph", f'  commit id: "route {t["route"]}/{t["difficulty"]}"']
    branch = "task"
    for i, s in enumerate(t["steps"]):
        if s["role"] == "implementer":
            nb = f"a{s['attempt']}-{s['rung']}"
            L.append(f'  branch "{nb}"'); L.append(f'  checkout "{nb}"'); branch = nb
            typ = "HIGHLIGHT" if s["ok"] else "REVERSE"
            L.append(f'  commit id: "{lbl(s)} {int(s["wall_s"] or 0)}s {s["failure_class"] or "ok"}" type: {typ}')
        else:
            typ = "NORMAL" if s["ok"] else "REVERSE"
            L.append(f'  commit id: "{lbl(s)} {int(s["wall_s"] or 0)}s {"ok" if s["ok"] else "fail"}" type: {typ}')
        if s["role"] == "implementer" and s["ok"]:
            L.append('  checkout "task"'); L.append(f'  merge "{branch}"'); branch = "task"
    L.append(f'  commit id: "END {t["status"]}"')
    return "\n".join(L)

def flow(t):
    L = ["flowchart LR", f'  R(["route: {t["route"]}/{t["difficulty"]}<br/>ladder {" → ".join(t["ladder"])}"])']
    prev = "R"
    for i, s in enumerate(t["steps"]):
        nid = f"S{i}"
        txt = f'{s["role"]}<br/><b>{s["rung"]}</b> {s["model"]}<br/>{int(s["wall_s"] or 0)}s · {s["failure_class"] or s["decision"]}'
        L.append(f'  {nid}["{txt}"]')
        L.append(f'  {prev} --> {nid}')
        L.append(f'  style {nid} fill:{"#d8f0dc" if s["ok"] else "#f7d6d0"}')
        prev = nid
    L.append(f'  E((({t["status"]})))'); L.append(f'  {prev} --> E')
    return "\n".join(L)

def ladder_svg(t, W=900):
    steps = t["steps"]
    rungs = sorted({s["rung"] for s in steps}, key=load.rung_rank)
    t0 = t["t0"]; t1 = t["t1"] or max(s["t1"] for s in steps)
    span = max(t1 - t0, 1)
    rowh, left = 34, 90
    H = rowh * len(rungs) + 50
    x = lambda ts: left + (ts - t0) / span * (W - left - 20)
    y = lambda r: 20 + (len(rungs) - 1 - rungs.index(r)) * rowh
    out = [f'<svg width="{W}" height="{H}" font-family="sans-serif" font-size="11">']
    for r in rungs:
        out.append(f'<text x="8" y="{y(r)+18}">{r}</text><line x1="{left}" x2="{W-20}" y1="{y(r)+rowh-4}" y2="{y(r)+rowh-4}" stroke="#eee"/>')
    prev = None
    for s in steps:
        x0, x1 = x(s["t0"]), max(x(s["t1"]), x(s["t0"]) + 3)
        col = {"implementer": "#3b7", "planner": "#58a", "reviewer": "#a7c"}.get(s["role"], "#999")
        if not s["ok"]:
            col = "#d54"
        out.append(f'<rect x="{x0}" y="{y(s["rung"])+4}" width="{x1-x0}" height="{rowh-12}" rx="3" fill="{col}"><title>{html.escape(json.dumps({k:s[k] for k in ("role","model","wall_s","decision","failure_class")}))}</title></rect>')
        out.append(f'<text x="{x0+3}" y="{y(s["rung"])+20}" fill="white">{s["role"][0].upper()}</text>')
        if prev and prev["role"] == "implementer" and s["role"] == "implementer":
            out.append(f'<path d="M{x(prev["t1"])} {y(prev["rung"])+rowh/2} L{x0} {y(s["rung"])+rowh/2}" stroke="#333" fill="none" stroke-dasharray="3 2"/>')
        prev = s
    for e in t["events"]:
        if e["t"]:
            out.append(f'<circle cx="{x(e["t"])}" cy="{H-18}" r="4" fill="{"#e90" if e["kind"]=="guard" else "#69c"}"><title>{html.escape(e["label"])}</title></circle>')
    out.append(f'<text x="{left}" y="{H-2}">0</text><text x="{W-60}" y="{H-2}">{int(span)}s</text></svg>')
    return "".join(out)

for name, fn, kind in (("A-gitgraph", gitgraph, "mermaid"), ("B-flow", flow, "mermaid"), ("C-ladder", ladder_svg, "svg")):
    parts = [f"<html><head><meta charset=utf-8><title>{name}</title>{MERMAID if kind=='mermaid' else ''}</head><body style='font-family:sans-serif;background:#fff'>"]
    for tid in TASKS:
        t = traces[tid]
        parts.append(f"<h3>{tid} · {t['status']}</h3>")  # no task text: these images are published
        parts.append(f'<pre class="mermaid">{html.escape(fn(t))}</pre>' if kind == "mermaid" else fn(t))
    parts.append("</body></html>")
    open(os.path.join(OUT, name + ".html"), "w").write("\n".join(parts))
    print("wrote", name)
