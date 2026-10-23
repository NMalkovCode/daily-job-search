# Architecture

```
   sources (ats → reed → linkedin → adzuna → jooble)
            │  wanted(): new key? target country? relevant title? not a repost?
            ▼
   fetch ──► data/raw/<date>.json ◄──► data/state/seen.json
            │                           (keys + fingerprints, for de-duplication)
            ▼
   triage ─► data/triage/<date>.txt     hard filters + points, best first
            │
            ▼  Claude (/daily-run): reads the triage list, `show`s full adverts,
            │  researches companies, writes data/scored/<date>.json
            ▼
   validate ─► build ─► output/Cover Letters/<date>/*.docx
                    └─► output/Job Tracker.xlsx  (backup in data/backups/ first)
```

## Modules (`jobsearch/`)

| module | job |
|---|---|
| `__main__.py`, `commands.py` | the command line |
| `paths.py` | every file location |
| `config.py` | `settings.json`, `secrets.json` / environment variables |
| `store.py` | the job record, raw day files, the `Seen` store |
| `textutil.py` | name normalisation, fingerprints, region detection, salary parsing |
| `filters.py` | title filter, hard filters, experience parser, agency detection, flags |
| `fetch.py` | runs the sources, de-duplicates, saves progress |
| `sources/*.py` | one module per site: `ats` (9 employer-board systems), `reed`, `linkedin`, `adzuna`, `jooble` |
| `triage.py` | the ranked list |
| `scored.py` | the format and checks for Claude's picks |
| `letters.py` | Word letters, the edit guard, the weekly rotation |
| `tracker.py` | the Excel workbook |
| `http.py`, `log.py` | a shared HTTP session with retries; console + `data/logs/<date>.log` |

## The job record

The format is documented at the top of `store.py`. Its `key` is `<prefix>:<id>`:
- `li:4481556323` for LinkedIn
- `reed:…` for Reed
- `adz:…` for Adzuna
- `ats:greenhouse:celonis:12345` for an employer board

The key is unique and never changes.

`data/raw/<date>.json` looks like this:

```json
{"date": "2026-10-21",
 "runs": [{"started": "...", "finished": "...", "sources": {"linkedin": {"new": 592, "seen": 40, ...}}}],
 "jobs": [ {job}, ... ]}
```

## De-duplication

These are the rules, in order, inside `fetch.Context.wanted` and `fetch.run`:

1. **Same advert.** A `key` already in `seen.json` is skipped.
2. **Repost or the same job on another site.** The `fingerprint` is the normalised company,
   title and country:
   - legal suffixes (`Ltd`, `LLC`, `Group`, …), city names and noise words (`Hybrid`, `(m/f/d)`,
     `[UAE]`, …) are removed;
   - `&` becomes "and", accents are stripped.

   If the same fingerprint was first seen within `dedupe.repost_window_days` (30), the job is
   skipped. When the earlier copy is from today, the new site's link is added to its `also_on`.
3. **Source order.** Employer boards run first, then the sources with full adverts (Reed,
   LinkedIn), then the snippet-only aggregators (Adzuna, Jooble). The saved record therefore
   carries the best link and text.
4. **Already in the tracker.** `validate` refuses a pick that is already in the tracker from an
   earlier day, by key or by fingerprint.

Agencies re-advertise under their own name, so an agency copy of a direct job cannot be matched
automatically. Claude is told to look for the employer's own advert and use `direct_link`.

## Safety and recovery

**Fetch**
- Progress is written every 20 jobs, atomically (temp file + rename).
- A crash or Ctrl+C loses at most 20 jobs.
- The next `fetch` the same day resumes (saved jobs are already "seen").
- One failing source or employer board is logged and skipped; the others still run.

**Build**
1. Checks that Excel does not hold the tracker **before** it moves or writes anything.
2. Copies the old tracker to `data/backups/`.
3. Saves to a temp file and swaps it in.

**Letters** — the build stores a SHA-256 of every letter it writes in
`Cover Letters/<date>/.letters.json`. A file whose hash no longer matches was edited, so it is kept.

**Tracker**
- "All applications" is append-only.
- Rows are matched by the hidden-at-the-end `Key` column.

## LinkedIn

- Uses the public guest endpoints (`jobs-guest/jobs/api/...`), the same pages a logged-out
  browser sees.
- Searches run with `f_TPR=r86400` (last 24 h) and `f_E=1,2,3` (internship, entry, associate).
- Waits 2–4 s between search pages and 1.5–3 s between adverts.
- On HTTP 429/999 it backs off 20 s, 40 s and 60 s.
- Descriptions are only fetched for jobs that pass the title filter and are new, which saves
  about a third of the requests.
- This goes against LinkedIn's terms of use, and too many requests can get the IP blocked.
  Keep the volumes as they are.
