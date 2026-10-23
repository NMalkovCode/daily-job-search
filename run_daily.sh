#!/usr/bin/env bash
# The daily run on macOS / Linux.
#   ./run_daily.sh         fetch + triage (skipped if already done today), then Claude does /daily-run
#   ./run_daily.sh fetch   fetch + triage only (for cron, e.g. "15 18 * * * /path/to/run_daily.sh fetch")
cd "$(dirname "$0")"
export PYTHONUTF8=1
if [ ! -x .venv/bin/python ]; then
  echo "Run ./setup.sh first."
  exit 1
fi
if [ "$1" = "fetch" ]; then
  mkdir -p data/logs
  exec .venv/bin/python -m jobsearch daily >> data/logs/scheduled.log 2>&1
fi

echo "=== 1/2  Fetch new jobs + triage  (20-40 min unless already done today) ==="
if ! .venv/bin/python -m jobsearch daily; then
  echo "Fetch or triage failed - see data/logs/ for details."
  exit 1
fi

echo
echo "=== 2/2  Choosing jobs and writing cover letters in Claude ==="
CLAUDE=$(command -v claude || true)
[ -z "$CLAUDE" ] && [ -x "$HOME/.local/bin/claude" ] && CLAUDE="$HOME/.local/bin/claude"
if [ -n "$CLAUDE" ]; then
  "$CLAUDE" "/daily-run"
else
  echo "The Claude Code command line was not found."
  echo "Open this folder in the Claude desktop app (Code tab) and type:   /daily-run"
fi
