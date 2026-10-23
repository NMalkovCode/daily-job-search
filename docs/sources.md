# Job sources

Commands below use the Windows path `.venv/Scripts/python`; on macOS / Linux use `.venv/bin/python`.

Sources run in the order below, which matters for de-duplication. When one job is on several
sites, the first source to save it owns the record, and the others are listed in its `also_on`:
1. Employer boards go first, so the record points at the employer's own advert.
2. Sources with full descriptions come next.
3. Aggregators that only give a snippet come last.

| order | source | covers | key needed | notes |
|---|---|---|---|---|
| 1 | `ats` (employer boards) | any country, **direct employers only** | no | the boards in `config/companies.json` (the example has 43 UK + UAE employers) |
| 2 | `reed` | UK | free | Reed.co.uk Jobseeker API, full descriptions |
| 3 | `linkedin` | any country | no | public guest search, last 24 h, entry/associate/internship levels |
| 4 | `adzuna` | UK, US, most of Europe, CA, AU, NZ, IN, SG, ZA, BR, MX | free | aggregates many boards; ~500-character snippet. **No UAE.** |
| 5 | `jooble` | many countries (one host each, set in `settings.json`) | free | aggregates many boards, including Bayt and GulfTalent, which block direct access; snippet + redirect link |

Run one source only: `.venv/Scripts/python -m jobsearch fetch --again --only ats`.
`status` shows what each source found in the last fetch.

## API keys (optional, free)

Put the keys in `config/secrets.json`. Setup creates the file. Environment variables
`REED_API_KEY`, `ADZUNA_APP_ID`, `ADZUNA_APP_KEY` and `JOOBLE_API_KEY` work too. A source
without its key is simply skipped.

**Jooble** (most useful where other APIs are missing, e.g. the UAE)
1. Fill in the form at <https://jooble.org/api/about>.
2. The key arrives by e-mail.
3. Put it in `"jooble_api_key"`, and give each country its host in `settings.json → sources.jooble.hosts`
   (e.g. `"United Kingdom": "uk.jooble.org"`, `"United Arab Emirates": "ae.jooble.org"`).
4. Its code follows Jooble's published API format but has not run with a live key yet. After
   the first fetch, check `status`: "jooble N new" with N > 0 means it works.

**Reed**
1. Register at <https://www.reed.co.uk/developers/jobseeker>.
2. The key arrives by e-mail.
3. Put it in `"reed_api_key"`.

**Adzuna**
1. Register at <https://developer.adzuna.com/signup>.
2. Copy the **Application ID** into `"adzuna_app_id"` and the **Application Key** into
   `"adzuna_app_key"`.
3. The free tier is plenty: about 13 requests per run.

Check with `.venv/Scripts/python -m jobsearch doctor`.

## Employer boards: `config/companies.json`

```json
{"company": "Celonis", "ats": "greenhouse", "id": "celonis"}
{"company": "BigBank", "ats": "workday", "id": "bigbank", "wd": 3, "site": "Careers"}
{"company": "Old Co", "ats": "lever", "id": "oldco", "enabled": false}
```

| `ats` | `id` is | how to find it |
|---|---|---|
| `greenhouse` | board slug | careers links like `job-boards.greenhouse.io/<id>` |
| `lever` | slug (`"eu": true` for EU-hosted boards) | `jobs.lever.co/<id>` (`jobs.eu.lever.co` → eu) |
| `ashby` | slug | `jobs.ashbyhq.com/<id>` |
| `smartrecruiters` | company identifier (case-sensitive) | `jobs.smartrecruiters.com/<id>/...` |
| `workable` | account slug | `apply.workable.com/<id>/` |
| `workday` | tenant, plus `wd` (number) and `site` | `<id>.wd<wd>.myworkdayjobs.com/<site>` |
| `pinpoint` | subdomain | `<id>.pinpointhq.com` |
| `teamtailor` | subdomain, or the custom careers domain | `<id>.teamtailor.com` (Chalhoub: `careers.chalhoubgroup.com`) |
| `oracle` | host, plus `site` (e.g. `CX_1`) | `<host>/hcmUI/CandidateExperience/en/sites/<site>/...` |

**Extra fields:**
- `"countries": ["ae"]`: SmartRecruiters only, limits the query to some countries. Talabat, for
  example, is read from Delivery Hero's board with `ae` only.
- `"region"`: a note for people. The code does not use it.

**How a board is read**
- A job is kept only if it is in a target country, has a relevant title, and was posted in the
  last `sources.ats.max_age_days` (3) days.
- Pinpoint gives no date, so its listed jobs count as current; the seen store keeps each one once.
- Boards list every level, and there is no equivalent of LinkedIn's experience filter. So
  `sources.ats.extra_title_exclude` also drops Manager (unless graduate/trainee/junior),
  Staff, Head, Business Partner, Architect and "II/III" titles.
- Workday and Oracle boards hold thousands of jobs, so they are searched instead of read in
  full:
  - The search uses the terms in `sources.ats.search_terms`, with 2 pages of 20 per term on Workday.
  - Workday is also limited to the target countries through its country filter.
- A board that fails (renamed, moved) is logged as `ERROR` and skipped. Fix its entry or set
  `"enabled": false`.

**Boards in `companies.example.json` (UK and UAE employers, checked live on 2026-10-21).** Replace them with
the employers you care about.
- **UAE:**
  - Fintech and start-ups: Careem, Tamara, Talabat (Delivery Hero), Ziina, Tabby, Property Finder,
    Dubizzle/Bayut.
  - Large employers: Aldar, Masdar, Chalhoub Group, DP World.
  - Global firms with Dubai roles: Mastercard (Launch Program), JLL (graduate analysts), Marsh McLennan
    (Oliver Wyman), FTI Consulting, Accenture.
- **UK:**
  - Banks and finance: BlackRock, MUFG, Deutsche Bank, Barclays, LSEG (incl. graduates), Wise,
    Monzo, OakNorth, GoCardless.
  - Consulting: Baringa, PA Consulting, Celonis.
  - Engineering and energy: Rolls-Royce (incl. early careers), Octopus Energy, Centrica.
  - Tech and AI: Deliveroo, Palantir, Faculty, Quantexa, ElevenLabs, Synthesia, Wayve,
    Tractable, PolyAI, IQVIA.

**Adding an employer.** Open the company's careers page, click a job, and read the address bar
against the table above. Or ask Claude: "add <company> to the employer boards". It finds the
board and tests it with `fetch --again --only ats`.

## Adding a new kind of site

Create `jobsearch/sources/<name>.py` with:

```python
NAME, PREFIX = "mysite", "ms"     # PREFIX starts every job key: "ms:<id>"
NEEDS = ("mysite_api_key",)       # optional: secrets it needs

def fetch(ctx):
    for item in ...:              # use jobsearch.http.get/post (retries built in)
        key = f"{PREFIX}:{item_id}"
        if not ctx.wanted(key, title, company, region, link):   # seen / repost / title / country
            continue
        yield make_job(NAME, PREFIX, item_id, title, company, location, region, link,
                       description=text, posted="YYYY-MM-DD", query=query)
```

Then:
1. Register it in `jobsearch/sources/__init__.py`. Mind the order: direct sources go before aggregators.
2. Add `"mysite": {"enabled": true}` to `settings.json → sources`.
3. Add a parser test with a canned response in `tests/test_sources.py`.

Call `ctx.wanted()` **before** any per-job request, so seen and irrelevant jobs cost nothing.

## Sites considered and not used (UK + UAE, checked 2026-10-21)

**UAE job boards**

| site | why not |
|---|---|
| Bayt, Naukrigulf, Indeed UAE, Dubizzle jobs | bot protection (Cloudflare / Akamai / Incapsula) blocks plain requests. Jooble covers part of them. |
| GulfTalent | answered once, then Cloudflare challenges; its robots.txt bans AI crawlers |
| Laimoon | jobs section discontinued |
| Hays UAE | needs JavaScript and a token |
| Michael Page UAE/UK | reachable, but it is an agency with mostly mid/senior roles. It could be added later as a source if wanted. |

**Aggregator APIs**

| API | why not |
|---|---|
| Careerjet | needs a publisher account tied to a website |
| JSearch (RapidAPI), SerpApi | paid or account-based; not tested |
| Indeed Publisher API | retired |

**Employers with no usable board**

| where | employers |
|---|---|
| UAE | Noon, Kitopi, Anghami, Sarwa, Baraka, Huspy, G42, Majid Al Futtaim, Emaar, e&, Mubadala |
| UK | Revolut, Starling, Kearney, L.E.K., OC&C, Arup, KPMG, Deloitte UK, PwC, Mott MacDonald, Siemens Energy |

The reasons for these employers vary: bot protection, a careers site that loads with JavaScript,
or an empty or stale board. LinkedIn still covers them.

## Slow boards

Some Workday boards (Accenture) answer HTTP 429 after a few requests and recover after about 90 seconds.
Add `"slow": true` to that company in `config/companies.json`: the fetch then waits 45 s, 90 s and 135 s
before giving up on a request and pauses 3-5 s between pages (Accenture takes about 3-4 minutes).

## Sources switched off

Reed, Adzuna and Jooble are `"enabled": false` in `config/settings.json → sources` because no API keys
are set. After adding the keys to `config/secrets.json`, set `"enabled": true` again.
