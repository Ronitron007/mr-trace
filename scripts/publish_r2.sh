#!/usr/bin/env bash
# Rebuild the REAL-data mr-trace snapshot and upload it to the private R2 bucket behind the mr-trace-viewer Worker.
# Needs an env file (default /workspace/mr-trace-notes/r2-upload.env, mode 600, never committed) with
#   MR_TRACE_UPLOAD_URL=https://<worker>/upload
#   MR_TRACE_UPLOAD_TOKEN=<upload secret>
# Refuses to upload if the snapshot contains anything that looks like a key or token.
set -euo pipefail
ENV_FILE="${MR_TRACE_ENV:-/workspace/mr-trace-notes/r2-upload.env}"
cd "$(dirname "$0")/.."
# shellcheck disable=SC1090
set -a; . "$ENV_FILE"; set +a
out="$(mktemp --suffix=.html)"; trap 'rm -f "$out"' EXIT
python3 -m mrtrace build -o "$out" >/dev/null
python3 - "$out" <<'PY'
import sys
from mrtrace import scrub
hits = [m.group(0)[:12] + "…" for m in scrub.SECRET.finditer(open(sys.argv[1]).read())]
if hits:
    sys.exit(f"refusing to upload: {len(hits)} secret-looking strings, e.g. {hits[:3]}")
PY
resp="$(curl -sS --fail-with-body -X PUT -H "Authorization: Bearer ${MR_TRACE_UPLOAD_TOKEN}" \
  -H "Content-Type: text/html" --data-binary @"$out" "$MR_TRACE_UPLOAD_URL")"
echo "$(date '+%d %b %H:%M %Z') uploaded snapshot: $resp"
