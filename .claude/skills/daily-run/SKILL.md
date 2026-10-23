---
name: daily-run
description: Do the day's job screening for the candidate. Fetch and triage new jobs, pick the best 5-12, research the companies, write cover letters, validate, then build the Excel tracker and letters. Use when the user types /daily-run or asks for today's (or a given day's) job search, shortlist or cover letters.
argument-hint: "[YYYY-MM-DD]"
allowed-tools:
  - Bash(.venv/Scripts/python -m jobsearch *)
  - PowerShell(.venv/Scripts/python -m jobsearch *)
  - Bash(.venv/bin/python -m jobsearch *)
  - WebSearch
  - WebFetch
  - Read
  - Edit(/data/scored/**)
---

# Daily run

Date: `$ARGUMENTS`. If it is empty, use today's date (YYYY-MM-DD). Below, `<date>` means that
date. Talk to the user in the language they write in. Every file you write is in English.

Run the CLI exactly as `.venv/Scripts/python -m jobsearch <command>` on Windows (works in both
PowerShell and Git Bash) or `.venv/bin/python -m jobsearch <command>` on macOS/Linux. Both are
pre-approved.

If `config/profile.md` is missing or still the template (`<Your name>`), stop and help the user
set up first (see CLAUDE.md → First run).

## 1. Data ready?

1. Run `status`.
2. If `<date>` is today and the fetch is missing or "NOT finished", run `daily` **in the
   background**. It takes 20–40 minutes, mostly LinkedIn.
   - Tell the user it is running.
   - Wait for it to finish. Do not poll faster than every few minutes.
   - For a past date, never fetch. Work with what exists.
3. If `data/triage/<date>.txt` is missing, run `triage <date>`.

## 2. Choose

1. Read `config/profile.md` in full. It holds the rules: priorities, hard filters, the agency
   policy, CV choice, salary targets and the cover-letter guide.
2. Read the triage file.
   - The top section is sorted by rough points: read all of it.
   - Skim the one-liners below the cut for anything the points undervalued.
3. Shortlist about 15–20 candidates. Read their full adverts in batches of about five:
   `show <key> <key> ...`.
4. Drop any job that breaks a hard filter in the full text (experience, nationality, language,
   clearance, pay — as listed in `config/profile.md`). `show` prints `NOTE: fails hard filter` when the script already spotted one.
5. Recommend **5–12**, following the location priority in `config/profile.md`. Prefer DIRECT
   employers, and include at most 2 agency jobs.
6. If a job is a duplicate of one already shortlisted, skip it. Validation also catches this.

## 3. Research each pick

Use web search to find:
- The company's values or mission, and one or two recent news items. The letter uses these.
- **Agency or job-board adverts only**: the real employer and its own advert. If you find the
  advert on the employer's careers site, set `direct_link`, `company` and `source_type: "Direct"`.
  Copy URLs from search results only. Never construct or guess a URL.

## 4. Write `data/scored/<date>.json`

Follow `docs/scored-format.md`. In short, it is a JSON list with one object per job you read:
- **Recommended**: all fields, including `cover_letter`.
- **Read but rejected**: only `key`, `recommend: false`, `fit_score` and `why`. Rejecting a job
  is useful history.

Rules:
- Copy `key` exactly from the triage or `show` output. Do not write links for the advert itself;
  the build takes them from the raw data.
- `cv` is an id from `config/settings.json → candidate.cvs`.
- Cover letters: follow the guide in `config/profile.md` (about 300 words, no sign-off: the
  build adds the signature).
  Use earlier `data/scored/*.json` letters as tone examples.

## 5. Validate and build

1. Run `validate <date>`. Fix every ERROR in the JSON. Judge each WARNING and fix it if it is
   real; "CV file not found" means the user has to copy their CVs into `cvs/`, so just tell them.
2. Run `build <date>`. If it says the tracker is open in Excel, ask the user to close it, then
   run it again.

## 6. Report to the user

- A short table of the picks: fit, title, company, city, Direct/Agency, salary verdict, CV.
- Anything they must do: missing CV files, deadlines soon, warnings you could not resolve.
- Remind them that they apply themselves. They should set **Status** (and **Date applied**) in the
  tracker; the rows move to "All applications" automatically on the next build.

## Never

- Apply, sign in anywhere, message employers or recruiters, or submit any form.
- Invent or edit links, change `data/raw/` or `data/state/`, or show the keys in `config/secrets.json`.
- Overwrite a cover letter the user edited. The build keeps edited files; to regenerate one, ask
  them first, then delete it.
