# Daily Job Search: notes for Claude

This is a personal job-screening tool for **one candidate: the user of this copy**. Who they
are, what they want and how to choose for them is in `config/profile.md` (their copy of
`config/profile.example.md`). Every evening:
1. Scripts collect new adverts and rank them.
2. **You** pick the best 5–12, research the companies and write cover letters.
3. Scripts build an Excel tracker and Word letters.

The candidate applies themselves. They may not be a developer: talk to them plainly, in the
language they write in. Everything in the repository is in English.

## First run: help the user set up

If `config/profile.md` is missing or still contains `<Your name>`, or `candidate.name` in
`config/settings.json` is still `Your Name`, setup is not finished. Before any daily run:
1. If `config/*.json` / `profile.md` are missing, ask them to run setup (`setup.bat` on Windows,
   `./setup.sh` on macOS/Linux), which copies the `*.example` files.
2. Read their CVs in `cvs/` (ask them to copy them there first).
3. Fill in `config/profile.md` with them: experience and numbers from the CVs, target roles,
   countries in priority order, salary targets, deal-breakers. Ask what the CVs cannot tell you.
   Claim nothing that is not on a CV or confirmed by them.
4. In `config/settings.json`: `candidate` (name, signature, CV list), `regions`, `searches`,
   `triage.salary_targets`, and the filters/flags that fit them (see `docs/configuration.md`).
5. Optionally adjust `config/companies.json` to employers they care about (see `docs/sources.md`).
6. Run `doctor`, then the tests.

These config files are git-ignored. Never move personal details into tracked files.

## The daily job

`/daily-run [YYYY-MM-DD]`, defined in `.claude/skills/daily-run/SKILL.md`, is the whole
procedure. `run_daily.bat` / `run_daily.sh` fetch first and then open Claude with that command.
The rules for choosing jobs are in `config/profile.md`; read it before choosing.

## Commands

Use this exact form. It is pre-approved in `.claude/settings.json`:

```
.venv/Scripts/python -m jobsearch <command>      # Windows (PowerShell or Git Bash)
.venv/bin/python -m jobsearch <command>          # macOS / Linux
```

| command | does |
|---|---|
| `daily` | fetch (if not done today) + triage |
| `fetch [--again] [--only linkedin,ats]` | new jobs from all sources → `data/raw/<today>.json` (20–40 min, run in background) |
| `triage [DATE]` | hard filters + ranking → `data/triage/<DATE>.txt` |
| `show KEY [KEY ...]` | full adverts |
| `validate [DATE]` | check `data/scored/<DATE>.json` |
| `build [DATE]` | validate → cover letters → tracker |
| `status` | today's progress, follow-ups due |
| `doctor` | installation, config, API keys, CV files |

Tests: `.venv/Scripts/python -m pytest` (or `.venv/bin/python -m pytest`). They use their own
settings in `tests/fixtures/`, not the user's.

## Layout

```
config/*.example.*      shared templates (tracked in git)
config/settings.json    the user's searches, countries, filters, weights, sources, CV list, signature
config/profile.md       the user's profile + selection rules (for you)
config/companies.json   employer job boards (Greenhouse, Lever, Workday, ...)
config/secrets.json     API keys (never shared)
jobsearch/              the Python package (sources/ = one module per job site)
data/raw/               everything fetched, per day          (written by scripts only)
data/triage/            ranked shortlist per day, for you
data/scored/            YOUR output per day: picks + cover letters
data/state/seen.json    every job ever seen, for de-duplication (scripts only)
data/backups/           tracker copy before each build
output/                 Job Tracker.xlsx + Cover Letters/  (the user's working files)
cvs/                    the user's CV files
docs/                   how everything works (start at docs/README.md)
```

## Rules

- **Never** apply for a job, sign in to any site, contact employers or recruiters, or submit forms.
- **Links:** never type or guess one. Advert links come from the raw data through `key`.
  `direct_link` must be copied from a search result.
- Do not edit `data/raw/` or `data/state/` by hand. The scripts own them; the settings deny it.
- **The tracker:**
  - The user writes in it: Status, Date applied, Notes, and any columns they add.
  - Never rebuild "All applications" from scratch. Never delete their rows.
  - If the tracker is open in Excel, the build stops: ask them to close it.
- **Cover letters:**
  - A letter they edited is never overwritten; the build keeps it.
  - Delete one only with their OK.
- **API keys** in `config/secrets.json`: never print them or copy them elsewhere.
- **LinkedIn** is scraped from its public guest pages. Keep the polite delays in
  `sources/linkedin.py`. Do not raise volumes or add parallel requests: an IP block would stop
  the main source.
- **Personal data:** CVs, letters, `config/` copies, `data/` and `output/` are personal and
  git-ignored. Never commit them or copy their contents into tracked files (code, docs, tests,
  the `*.example` templates).

## Changing the code

- **Filters and weights** live in `config/settings.json` (regex lists). After changing them:
  1. Run the tests.
  2. Run `triage` on a past day and compare the kept/rejected counts.
  3. Check that earlier picks in `data/scored/` still pass.
- **Countries:** `settings.json → regions`. Built-in country patterns are in
  `textutil.COUNTRIES`; `region_patterns` adds or overrides one.
- **A new job site:** add a module to `jobsearch/sources/` (see `docs/sources.md`), then
  register it in `sources/__init__.py` and `settings.example.json → sources`.
- **De-duplication** works on `fingerprint` (company + title + country) for 30 days plus the
  per-site `key`. See `docs/architecture.md`.
- **Style:** small modules, plain dicts for jobs, comments only where the reason is not obvious.
  Keep `docs/` in step with any behaviour change.
