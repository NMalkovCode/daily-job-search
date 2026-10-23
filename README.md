# Daily Job Search

[![tests](https://github.com/NMalkovCode/daily-job-search/actions/workflows/tests.yml/badge.svg)](https://github.com/NMalkovCode/daily-job-search/actions/workflows/tests.yml)
![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)
![Windows | macOS | Linux](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

**An AI job-hunting assistant that runs every evening: it finds new jobs, picks the ones that
fit *you*, and writes the cover letters.** Built around [Claude Code](https://claude.com/claude-code).

Every evening it collects the day's new job adverts, filters and ranks them, and then Claude
picks the best handful for you, researches each company and writes a tailored cover letter.
You get an Excel tracker and ready-to-edit Word letters. **You apply yourself**: the tool never
signs in anywhere, applies or contacts anyone.

```
 LinkedIn · employer job boards · Reed · Adzuna · Jooble
                    │  collect (20-40 min, polite)
                    ▼
     de-duplicate ─► hard filters ─► rank by your rules        (Python, no AI)
                    │
                    ▼  /daily-run in Claude Code
     read the best adverts ─► research employers ─► pick 5-12 ─► write cover letters
                    │
                    ▼
     output/Job Tracker.xlsx  +  output/Cover Letters/<date>/*.docx
```

## What it does

1. **Collects** new adverts from:
   - LinkedIn's public job search (no login);
   - employers' own job boards (Greenhouse, Lever, Ashby, SmartRecruiters, Workable, Workday,
     Teamtailor, Pinpoint, Oracle) for any companies you list;
   - optionally, with free API keys: Reed (UK), Adzuna (UK, US, most of Europe and more) and
     Jooble (many countries).

   Jobs already seen, reposts and the same job on two sites are dropped.
2. **Filters and ranks** them with rules you control: seniority, years of experience, phrases
   that rule a job out for you (clearance, nationality, language…), agencies vs direct employers,
   salary vs your target.
3. **Claude** reads the shortlist, opens the most promising adverts, picks the best 5–12,
   researches each company and writes a ~300-word cover letter based on *your* profile.
4. **Builds** `output/Job Tracker.xlsx` (statuses, follow-ups, links to adverts, CVs and
   letters) and the Word cover letters.

## What you need

- **Python 3.10+** ([python.org](https://www.python.org/downloads/); on Windows tick
  "Add python.exe to PATH").
- **Claude Code**, the command line or the Claude desktop app (Code tab), with a Claude
  subscription or API key. The fetching and filtering work without it; choosing jobs and
  writing letters need it.
- Windows, macOS or Linux.

## Quick start

1. **Download** this repository (green **Code** button → *Download ZIP*, or `git clone`).
2. **Run setup** once:
   - Windows: double-click `setup.bat`.
   - macOS / Linux: `./setup.sh` in a terminal (if it says "permission denied":
     `chmod +x *.sh` first).

   It creates a Python environment, installs the packages and creates **your own config files**
   from the templates: `config/settings.json`, `config/profile.md`, `config/companies.json`,
   `config/secrets.json`. These are git-ignored, so your details stay on your computer.
3. **Copy your CV(s) into `cvs/`** (PDF or Word).
4. **Tell it who you are.** The easiest way: open this folder in Claude Code and say
   > Help me set up: read my CVs in cvs/ and fill in config/profile.md and config/settings.json with me.

   Claude asks about your target roles, countries, salary and deal-breakers and fills in the
   files. Or edit them yourself:
   - `config/profile.md`: your experience, target roles, priorities, salary, what a good job
     looks like, cover-letter style. This is what Claude reads every day.
   - `config/settings.json`: your name and signature, CV files, **countries** (`regions`),
     **search terms**, filters and salary targets. See [docs/configuration.md](docs/configuration.md).
   - `config/companies.json`: employers whose job boards to check. The example list is UK and UAE
     employers; replace it with your own (see [docs/sources.md](docs/sources.md)).
5. **Check**: `.venv/Scripts/python -m jobsearch doctor` (Windows) or
   `.venv/bin/python -m jobsearch doctor` (macOS / Linux).
6. **Every day**: run `run_daily.bat` / `./run_daily.sh`, or `start_ui.bat` / `./start_ui.sh`
   for a small panel with a Start/Stop button.
   - It fetches and ranks the jobs (20–40 min, mostly LinkedIn; skipped if already done today).
   - Then it starts Claude Code with `/daily-run`. In the desktop app instead, open this folder
     in the **Code** tab and type `/daily-run`.
7. **Open `output/Job Tracker.xlsx`** and apply. Set **Status** and **Date applied** as you go.

Optional: free API keys in `config/secrets.json` add more jobs (see [docs/sources.md](docs/sources.md)).
On Windows, `schedule_fetch.bat` makes the fetch run automatically at 18:15; on macOS / Linux use
cron with `./run_daily.sh fetch`.

## Folders

| folder | what is in it | in git? |
|---|---|---|
| `config/` | `*.example.*` templates, plus your own copies | templates only |
| `cvs/` | your CV files | no |
| `output/` | **your working files**: the tracker and `Cover Letters/<date>/` | no |
| `data/` | fetched adverts, triage lists, Claude's picks, de-duplication state, backups, logs | no |
| `jobsearch/` | the Python code | yes |
| `docs/` | documentation | yes |
| `tests/` | automated tests (`python -m pytest`) | yes |

## Documentation

Start with [docs/README.md](docs/README.md). Most useful:
- [daily workflow](docs/daily-workflow.md)
- [configuration](docs/configuration.md)
- [job sources and API keys](docs/sources.md)
- [troubleshooting](docs/troubleshooting.md)

For Claude, the project rules are in [CLAUDE.md](CLAUDE.md) and the daily procedure is in
[.claude/skills/daily-run/SKILL.md](.claude/skills/daily-run/SKILL.md).

## Good to know

- **LinkedIn**: the tool reads LinkedIn's public, logged-out job pages slowly and politely.
  Automated access is against LinkedIn's terms of use and too many requests can get your IP
  temporarily blocked; keep the delays as they are and use it at your own risk. You can switch it
  off in `settings.json → sources.linkedin.enabled`.
- **Your data stays local.** CVs, letters, the tracker and your config are git-ignored. If you
  fork this repository, check `git status` before every commit.
- Claude's cover letters are drafts: read and edit each one before you send it.

## Contributing

Bug reports, new job sources and more built-in countries are welcome: see
[CONTRIBUTING.md](CONTRIBUTING.md). Please never paste your CV, profile or API keys into an issue.

## License

MIT, see [LICENSE](LICENSE).
