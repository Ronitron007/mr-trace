# Proposals for mr (not applied; mr is Goosebump's repo)

1. `mr-task-title-and-caller.patch` (applies cleanly to mr `main` at 94e404c, checked with `git apply --check`).
   - `title`: first line of the task text (≤120 chars). Today `title` is always `null`, so most jobs show up as "code task in repo".
   - `caller`: `$MR_CALLER` (each bot sets it, e.g. `MR_CALLER=goosebump mr run …`), else the parent process name. Answers "which agent ran this job".
2. Write a `role:"step_start"` record (task, role, rung, model, started_at) before each rung, so the live view
   doesn't have to read the process table.
3. Run cursor rungs with `--output-format stream-json` (as router-logging-spec D-L3 already suggests). That gives
   tool calls with timestamps and a partial trace when a run crashes.
