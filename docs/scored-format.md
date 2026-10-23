# `data/scored/<date>.json`: Claude's daily picks

A JSON list with one object per job Claude read in full. Title, company, location and the
advert link are **not** written here. The build copies them from `data/raw/` using `key`, so a
link can never be mistyped.

## Recommended job

```json
{
  "key": "li:4481556323",
  "recommend": true,
  "fit_score": 9,
  "source_type": "Direct",
  "why": "Close match with the automation work in my current role ... Risk: small boutique.",
  "cv": "technical",
  "salary": "Est. AED 12,000–18,000/month (boutique firm, junior, Dubai).",
  "meets_target": "Borderline – top of the range meets the Dubai target",
  "visa_notes": "Employer must sponsor the UAE visa; confirm early.",
  "deadline": "2026-11-15",
  "cover_letter": "Dear Hiring Team,\n\nI am applying for ...\n\n...",

  "title": "optional: a cleaner title",
  "company": "optional: the real employer when the advert was posted by a job board or agency",
  "direct_link": "optional: the employer's own advert, copied from a search result"
}
```

## Fields

| field | type | rule |
|---|---|---|
| `key` | text | exactly as in the triage file or `show` output |
| `recommend` | true/false | |
| `fit_score` | whole number 0–10 | after the −2 agency penalty |
| `source_type` | text | starts with `Direct` or `Agency` (e.g. `Agency – Lorien (employer undisclosed)`) |
| `why` | text | salary, growth, future-proofing against AI, profile fit, main risk |
| `cv` | text | an id from `settings.json → candidate.cvs` |
| `salary` | text | estimated range + basis |
| `meets_target` | text | starts with `Yes`, `No` or `Borderline` |
| `visa_notes` | text | |
| `cover_letter` | text | ~300 words, paragraphs separated by a blank line, **no sign-off** (the build adds the signature; a sign-off you leave in is removed) |
| `deadline` | `YYYY-MM-DD` | optional |
| `title`, `company` | text | optional display overrides |
| `direct_link` | URL | optional; shown as "Employer site" in the tracker |

## Read but not recommended

```json
{"key": "li:4480476452", "recommend": false, "fit_score": 4, "why": "Needs 5 years of SAP experience."}
```

These rows never reach the tracker. They are a record of what was considered.

## Checks (`validate`)

**Errors.** These stop the build:
- a missing or wrong-type field;
- a key that is not in the raw data;
- the same job twice in the file;
- a job already in the tracker from an earlier day (by key, or by the same company + title + country);
- an unknown `cv` id;
- a bad `source_type`;
- an empty letter or a leftover placeholder such as `[Company]`;
- a `direct_link` that is not a URL.

**Warnings.** Shown but not blocking:
- a CV file that is not in `cvs/`;
- a letter outside 200–400 words, or one that never names the company;
- more than 2 agency jobs;
- fewer than 5 or more than 12 picks;
- an odd `meets_target` or `deadline`.
