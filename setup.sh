#!/usr/bin/env bash
# One-time setup on macOS / Linux: creates .venv, installs the packages, creates your config files, checks everything.
set -e
cd "$(dirname "$0")"
echo "=== Daily Job Search - setup ==="

PY=$(command -v python3 || command -v python || true)
if [ -z "$PY" ]; then
  echo "Python was not found. Install Python 3.10 or newer (https://www.python.org/downloads/), then run ./setup.sh again."
  exit 1
fi
if [ ! -x .venv/bin/python ]; then
  echo "Creating the virtual environment .venv ..."
  "$PY" -m venv .venv
fi
echo "Installing packages ..."
.venv/bin/python -m pip install --disable-pip-version-check -q --upgrade pip
.venv/bin/python -m pip install --disable-pip-version-check -q -r requirements.txt

# Your own copies of the example files. They are git-ignored, so your details stay private.
for pair in settings.example.json:settings.json secrets.example.json:secrets.json \
            companies.example.json:companies.json profile.example.md:profile.md; do
  src="config/${pair%%:*}"; dst="config/${pair##*:}"
  if [ ! -e "$dst" ]; then
    cp "$src" "$dst"
    echo "Created $dst from $src - fill it in."
  fi
done

echo
.venv/bin/python -m jobsearch doctor || true
echo
echo "Setup finished. Next:"
echo " 1. Fill in config/profile.md and the \"candidate\" part of config/settings.json"
echo "    (or open this folder in Claude Code and ask it to help - see README.md)."
echo " 2. Copy your CV files into the cvs/ folder (see cvs/README.md)."
echo " 3. Optional: add free API keys to config/secrets.json (see docs/sources.md)."
echo " 4. Every day: ./run_daily.sh (or ./start_ui.sh for a Start/Stop panel)."
