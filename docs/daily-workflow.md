# Daily workflow

Commands below use the Windows path `.venv/Scripts/python`; on macOS / Linux use `.venv/bin/python`.

## The evening run

1. **Double-click `run_daily.bat`** (macOS / Linux: `./run_daily.sh`). It runs two steps.
2. **Step 1: fetch and triage.** This takes 20–40 minutes, most of it LinkedIn.
   - The step is skipped if today's fetch already finished (for example by the 18:15 scheduled
     task). You can close the window and run the file again later.
   - An interrupted fetch resumes where it stopped.
3. **Step 2: Claude** opens with `/daily-run`. Claude:
   - reads your rules (`config/profile.md`) and the ranked list;
   - reads the most promising adverts in full and picks 5–12;
   - researches each company;
   - writes the cover letters and builds the tracker;
   - shows you a summary table.

   It runs the project's commands and web searches without asking (allowed in
   `.claude/settings.json`). Anything else, it asks first.
4. The tracker opens when Claude finishes. Apply.

### Or: the control panel (`start_ui.bat`)

Double-click **`start_ui.bat`** (macOS / Linux: `./start_ui.sh`). It opens a local page (`http://127.0.0.1:8765`, served by `ui.py`)
with one **Start / Stop** button and the date and time of the previous run.
- Start runs the same steps as `run_daily.bat`: `daily` (fetch + triage), then `claude -p /daily-run`
  when the Claude Code CLI is installed (`%USERPROFILE%\.local\bin\claude.exe` is found even when it
  is not on PATH). Without the CLI it stops after triage and says to type `/daily-run` in the app.
- Tick **Fetch fresh jobs** to run `fetch --again` + `triage` instead of `daily`. Needed when today's
  fetch is already marked finished (e.g. after a partial `fetch --only ats`).
- The status line shows how long since the last output; after 2 minutes of silence it warns that
  the fetch is slow or the PC went to sleep. Keep the PC awake for the 30–60 minute run.
- Run history: `data/logs/ui_runs.json`. Opening the panel again replaces an older copy still
  running on the port (Windows otherwise lets two copies share it and split the clicks).

**No Claude Code command line?** Open this folder in the Claude desktop app (**Code** tab) and
type `/daily-run`. You can also give a date (`/daily-run 2026-10-21`) to redo or catch up on a
past day. Catching up does not fetch; it works with what was collected that day.

## The tracker: `output/Job Tracker.xlsx`

| sheet | what it is |
|---|---|
| **Today's applications** | today's picks with the reasons, salary, visa notes, CV, and links to the advert and the letter |
| **All applications** | every earlier pick. Each build moves the previous days' rows here and keeps your Status, Date applied and Notes |
| **Summary** | counts per status and the follow-ups that are due |

### What you fill in

| column | values |
|---|---|
| **Status** (drop-down) | To apply → Applied → Interview → Offer, or Rejected / No response / Withdrawn / Skipped |
| **Date applied** | the date you sent the application |
| **Notes** | anything you like |

**Follow up by** fills itself in: Date applied + 7 days. The Summary sheet and
`.venv/Scripts/python -m jobsearch status` list overdue follow-ups.

### Rules

- You may add your own columns or formatting to **All applications**. Rows there are only
  added, never rewritten.
- **Today's applications** is rebuilt on every build. Only Status, Date applied and Notes
  survive a rebuild.
- **Close Excel before a build.** If the file is open, the build stops safely and asks you to
  close it.
- A copy of the tracker is saved in `data/backups/` before every build. The last 20 are kept.

## Cover letters

- Each day's letters are saved in `output/Cover Letters/<date>/` as Word files, and the tracker
  links to them.
- **Edit freely.** A letter you changed is never overwritten. To get a fresh one from Claude,
  delete the file and ask Claude to rebuild.
- Save your PDF next to the .docx. Every 7 days, older dated folders move into
  `Previous Cover Letters/` as `<date> - <file>`. Every file moves, including PDFs. Nothing is
  deleted, and the tracker links follow the files.

## Useful commands

Run these from this folder in a terminal, or ask Claude to run them:

```
.venv/Scripts/python -m jobsearch status     # today's progress, follow-ups due
.venv/Scripts/python -m jobsearch doctor     # check setup, API keys, CV files
.venv/Scripts/python -m jobsearch show li:4481556323   # read one advert
.venv/Scripts/python -m jobsearch fetch --again        # look for jobs posted since the last fetch
```

## Changing what you get

Tell Claude in plain words. For example:
- "skip internships"
- "more pricing roles"
- "add Kearney's careers site"
- "my new CV is ..."

Claude updates `config/profile.md`, `config/settings.json` or `config/companies.json`. See
[configuration.md](configuration.md).
