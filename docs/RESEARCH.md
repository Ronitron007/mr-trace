# Outside research: how others draw agent and workflow traces (Oct 2026)

| Tool | View | What works | What doesn't, for mr |
|---|---|---|---|
| LangSmith | Trace tree + waterfall; Trajectory / Turns / Details panels ([docs](https://docs.langchain.com/langsmith/view-traces)) | A flat "trajectory" for reading, and details only on click: skim first, drill second | Organised around chat threads and nested runs. mr's unit is a ladder of attempts, not a conversation |
| Langfuse | Tree, Timeline (responsive, fits the whole trace on screen) and agent Graph with Aggregated vs Expanded modes ([agent graphs](https://langfuse.com/docs/observability/features/agent-graphs), [timeline](https://langfuse.com/changelog/2026-08-28-responsive-timeline)) | "See the shape first, then zoom". Colour carries the step type, and a deterministic layout puts things in the same place every time | The graph needs typed observations. For a linear cascade, the aggregated graph collapses into a line |
| Arize Phoenix / AX | Span tree + agent graph / path from `graph.node.id` attributes ([agent trajectory](https://arize.com/docs/ax/instrument/agent-trajectory)); eval results and annotations attached to spans ([Phoenix LLM traces](https://arize.com/docs/phoenix/tracing/llm-traces)) | Agent-level "logical flow map" kept separate from span detail | Built for multi-agent handoffs. mr has one agent climbing a ladder |
| Honeycomb trace waterfall ([docs](https://docs.honeycomb.io/reference/honeycomb-ui/query/trace-waterfall)) | Waterfall with a trace summary and a mini-waterfall/minimap above it for orientation | A small overview strip above the detail tells you where to look before you read any spans | Generic spans, so there's no rung or cost meaning |
| Jaeger / OTel waterfall | Nested horizontal bars on a time axis | Read like a profiler: gaps between child spans are your own code, which here means mr's checks | No idea of a "rung" or "price", and retries look like noise |
| Temporal UI | Compact (ordered, not to scale), Timeline (to scale, red for failure, retry icon with attempt number) and Full History ([blog](https://temporal.io/blog/the-dark-magic-of-workflow-exploration)) | Event *groups* turn many low-level events into one meaningful bar; red/green outcome colour; attempt counter | Activities aren't ranked by cost, so you can't see an "escalation" |
| Coding-agent runtimes ([Gump](https://gump.build/), [Plan Forge dashboard](https://planforge.software/dashboard.html), [Glanceable](https://glanceable.com/)) | Per-step gate results, "escalate: claude-sonnet" lines, a promotion-chain badge, a board of tiles with blocked/failed runs on top | The closest to mr: gates, retries and escalations are the main story, and failures rise to the top | Mostly text logs or cards, with no picture of where the time went |
| Git graph (git log --graph, Temporal's full-history style) | Lanes and merges | Familiar to developers | Fakes branches for a sequential process (spike A) |
| Flame graphs | Stacked call depth | Great for CPU stacks | Depth isn't the question here, cost is |

## Takeaways applied

1. **Shape first, details on demand** (Langfuse timeline, LangSmith trajectory → details). Board → ladder → cards.
2. **Group low-level events into a meaningful unit** (Temporal event groups). One bar is one model session, not one tool call.
3. **Make the y axis mean something.** No tool above ranks steps by price. For mr the rung *is* the story, so y = rung.
4. **Colour carries the outcome** (Temporal). Red failed, green accepted, blue plan, violet review, amber needs a human.
5. **Small multiples for "many runs at once"** (Tufte; Glanceable's board). Every board row has the same mini-ladder.
6. **Words, not codes.** Every failure class is shown with its meaning and what mr does next.
7. **Summary above the detail** (Honeycomb's trace summary / mini-waterfall). The board has a summary strip of model sessions per rung, failures by class and accepted direct vs after escalating, computed over the jobs currently listed.
8. **Verdicts on the step** (Phoenix's eval annotations on spans). Each step card carries mr's H/D/A/C signal chips and the failure class with its meaning.

## Added after Instinct's review (31 Oct 2026)

Instinct (the reviewing bot) suggested these. All are in the viewer now:

- Per board row: a two-tone bar for model time vs mr's own checks (grey = unlogged time on a killed job), with a tooltip giving the split.
- A shorter fallback headline when data is missing ("Review: accepted · 37s"), never "?" or "–".
- Free vs unmeasured cost: "free" = mr measured zero; "n/a" = mr wrote no cost (falls back to tokens if it has them).
- A shape tag: "mostly planning", "mostly retries" (attempts that were thrown away) or "mostly mr checks", shown when one part is ≥ 50% of a job that ran at least 30 s.
- The highest rung reached, as a label beside each mini-ladder.
- The summary strip (takeaway 7).
