# Configuration

All settings are plain text files in `config/`. Claude can edit them for you; ask in plain words.

Each file comes as a shared template (`*.example.*`, tracked in git). Setup copies it to your own
file, which is **git-ignored**, so your details never end up on GitHub:

| your file | from template | what |
|---|---|---|
| `profile.md` | `profile.example.md` | **who you are and how to choose**: experience, target roles, priorities, hard filters, agency policy, CV guide, salary table, cover-letter guide. Claude reads it every day. |
| `settings.json` | `settings.example.json` | machine settings (below) |
| `companies.json` | `companies.example.json` | employer job boards to check (see [sources.md](sources.md)) |
| `secrets.json` | `secrets.example.json` | API keys |

If you change a template later (e.g. after pulling a new version), your own copy is not touched.
Compare the two and copy across what you want.

## `settings.json`

Keys that start with `_` (`_readme`, `_readme_note`, …) are notes and are ignored.

### `candidate`
- `name`, `signature`: the lines added under every cover letter.
- `cv_root` + `cvs`: the CV files Claude may choose from, as `id → path`.
  - Paths are relative to `cv_root`. The default is the project's `cvs/` folder. It may be an
    absolute path such as `C:/Users/you/Documents/CVs`; use forward slashes.
  - Adding a CV: add a line here **and** describe when to use it in `profile.md`.

### `regions` and `region_patterns`
The countries searched, most important first, e.g. `["United Kingdom", "Ireland"]`.

- LinkedIn runs every query once per country, using the name as the location.
- Each job's free-text location ("Manchester Area", "Dubai, UAE") is mapped to one of these
  countries; jobs elsewhere are dropped. The patterns for these are built in (`textutil.py →
  COUNTRIES`): United Kingdom, United Arab Emirates, Ireland, United States, Canada, Australia,
  New Zealand, Germany, France, Netherlands, Switzerland, Spain, Singapore, India, Saudi Arabia,
  Qatar.
- Any other country works too, but only its name is recognised. Add its cities in
  `region_patterns`, which also overrides a built-in pattern:
  ```json
  "regions": ["Portugal"],
  "region_patterns": {"Portugal": "portugal|lisbon|lisboa|porto|braga"}
  ```

### `searches`
- `boolean`: LinkedIn queries. They support `AND`, `OR`, quotes and brackets.
- `simple`: plain keyword queries for Reed, Adzuna and Jooble.

### `filters`
All entries are case-insensitive **regular expressions**. In JSON, `\b` (word boundary) is
written `\\b`.

| key | effect |
|---|---|
| `title_keep` | the title must match one of these to be considered at all. Applied before descriptions are downloaded, which saves time. |
| `title_exclude` | the title must match none (senior, lead, director, nationals only, …) |
| `description_reject` | named groups of phrases that reject a job, e.g. `nationality`, `clearance`, `pay`. Add your own, e.g. `"language": ["fluent in german", "native french"]`. A phrase is ignored if negated just before ("**no** security clearance required") or softened just after ("German **is a plus**"). |
| `max_years_experience` | 3 = reject adverts that require 4+ years. The parser takes each requirement's lower bound ("3–5 years" → 3), uses the largest requirement, ignores "preferred" ones, company age ("for over 50 years") and benefits ("after 5 years' service"). |
| `agency_names`, `agency_phrases` | mark a job AGENCY (by company name, or "our client is…" in the advert) |
| `flags` | tags shown in the triage list, e.g. `grad-scheme`, `visa-offered`, `needs-long-term-rtw`, `cold-calling`, `builder` (hands-on build/automation work), `admin-heavy`. Add your own; give them points in `triage.flag_points`. |

**After changing filters:**
1. Run the tests: `.venv/Scripts/python -m pytest` (macOS / Linux: `.venv/bin/python`).
2. Run `triage <a past date>` and compare the kept/rejected counts on the first two lines of the
   triage file.

### `dedupe`
`repost_window_days` (30): how long a company + title + country counts as the same job.

### `triage`
Points that **only sort** the list. Claude makes the choice.

| key | effect |
|---|---|
| `title_points`, `city_points`, `flag_points` | regex/word → points |
| `agency_points` | −2 for agency jobs (the rule in `profile.md`) |
| `salary_points` + `salary_targets` | +1 if the advertised salary meets your target, −1 if below |
| `top_n` | how many jobs are listed in full; the rest are one-liners |

`salary_targets` is a list; the first entry that matches the salary's currency (and the
optional `region` and `location` word) is used, so put city-specific targets first:

```json
"salary_targets": [
  {"currency": "GBP", "location": "london", "per_year": 35000},
  {"currency": "GBP", "per_year": 28000},
  {"currency": "AED", "region": "United Arab Emirates", "per_year": 180000}
]
```

Currencies recognised in adverts: GBP (£), USD ($), EUR (€) and AED.

### `sources`
One block per source: `enabled` plus its own limits. See [sources.md](sources.md).
