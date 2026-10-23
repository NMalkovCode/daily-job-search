#!/usr/bin/env bash
# Opens the control panel (Start/Stop button + last run time) in your browser.
cd "$(dirname "$0")"
if [ ! -x .venv/bin/python ]; then
  echo "Run ./setup.sh first."
  exit 1
fi
exec .venv/bin/python ui.py
