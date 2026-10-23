# Troubleshooting

Run `.venv/Scripts/python -m jobsearch doctor` first (`.venv/bin/python` on macOS / Linux). It checks Python, the packages, the
config files, the API keys, the CV files and whether the tracker is open.

| symptom | cause / fix |
|---|---|
| "Run setup.bat first." / "Run ./setup.sh first." | `.venv` is missing. Run setup. Do this again after moving the folder to another PC, because `.venv` is machine-specific. |
| "Python was not found" | Install Python 3.10+ from python.org and tick "Add python.exe to PATH". |
| "The tracker is open in Excel" | Close the workbook (check the taskbar) and run the build again. Nothing was changed. |
| `run_daily.bat` says the Claude Code command line was not found | Use the desktop app: open the folder in the Code tab and type `/daily-run`. Or install the CLI (`irm https://claude.ai/install.ps1 \| iex` in PowerShell). |
| A fetch takes very long or LinkedIn finds 0 results | LinkedIn is slowing requests down (HTTP 429/999). The script waits and retries. If it keeps happening, fetch later. Never lower the delays in `sources/linkedin.py`. |
| "[reed] skipped: no API key" | Expected until you add a key to `config/secrets.json` (see [sources.md](sources.md)). |
| One employer shows `ERROR` during fetch | Its job board changed address. Fix or disable that entry in `config/companies.json` (`"enabled": false`). The other sources still run. |
| The fetch was interrupted (closed window, sleep, no internet) | Run it again. The same day resumes, and jobs already saved are skipped. `status` shows "NOT finished" until then. |
| `validate` lists errors | Claude fixes them during `/daily-run`. When editing by hand, see [scored-format.md](scored-format.md). |
| A cover-letter link in Excel does not open | The letter was moved or renamed by hand. The links are relative to `output/`, so keep the folder structure as it is. |
| "Kept the existing letter" | The .docx was edited after it was generated (or came from the old version). Delete it if you want a new one. |
| Strange characters in the console | `run_daily.bat` sets UTF-8. In your own terminal, run `set PYTHONUTF8=1` first. |
| Need an older tracker | `data/backups/` holds the last 20 versions, one per build. |
