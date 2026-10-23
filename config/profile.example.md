# Candidate profile and selection rules

<!--
  This is a TEMPLATE. setup copies it to config/profile.md - edit that copy, not this file.
  Replace everything in <angle brackets> and delete what does not apply to you.
  Tip: you can ask Claude to fill it in for you: open the folder in Claude Code and say
  "Read my CVs in cvs/ and fill in config/profile.md with me".
  Claude reads config/profile.md before choosing jobs every day, so the better it is,
  the better the picks and cover letters.
-->

The AI reads this file every day before choosing jobs (`/daily-run`). Keep it up to date: new
experience, a new CV, a changed salary target or priority all belong here. Machine-checked
values (CV list, signature, filter words) live in `config/settings.json`.

## Candidate

**<Your name>**. <Degree, university, years, grade>. <Other qualifications>.
<Optional: LinkedIn / GitHub / portfolio links>

<One or two sentences: the angle you want employers to see, e.g. "an analyst who also builds the
tools: finds the business problem and writes the code that fixes it".>

Every claim below must be on your current CVs (`cvs/`). The AI must not claim anything that is
not here or on a CV.

- **<Employer>**, <City> (<start> – <end>): <job title>.
  - <Achievement with a number, e.g. "automated monthly reporting: -80% manual time">
  - <Achievement>
- **<Employer>**, <City> (<start> – <end>): <job title>.
  - <Achievement>
- **<Project / society / volunteering>**: <one line on what you did and the result>.
- **Skills**: <programming languages, tools, methods>.
- **Not my skills**: <tools you do NOT have, so the AI flags roles that require them>.
- **Languages**: <e.g. English (native), Spanish (fluent)>.
- **Right to work**:
  - <Country>: <e.g. citizen / Graduate visa until 2028 / needs sponsorship>.
  - <Country>: <...>

## Target roles

- <e.g. Data analysis>
- <e.g. Business or strategy consulting>
- <e.g. Commercial, pricing or operations analyst>
- <Other good fits>

<Company size or industry preferences, if any.>

## Priority

1. **<First country / city>**
2. **<Second>**

When two jobs are close, the higher-priority location wins.

## What a good job looks like

Judge the **daily work in the advert**, not the title, the company's brand or the industry.

- <What you want to do every day, e.g. "build models and dashboards and present the insight">
- <Growth signs you value: structured graduate programme, exposure to senior leaders, training budget>
- <Pay, location, hybrid/remote preferences>

Examples of jobs you would rate excellent (optional, but they help a lot):
- **<Job title, company>**: <why it is a great fit>.

## Traps (reject or score low)

Things that look plausible to a keyword search but are a bad fit for you, for example:
- **Sales in disguise.** "Consultant" titles whose work is cold calling, targets or commission.
- **Admin and coordination.** Meeting minutes, status reports, data entry, document collation.
- <A field or qualification you do not have, e.g. "a professional accounting qualification required">
- **Suspicious adverts.** The company name does not match the content, emoji-template posts.
  Skip unless the real employer is verifiable.

## Hard filters (reject)

The scripts already drop most of these (`config/settings.json → filters`). Re-check every pick
against the full advert.

- Senior roles, or roles that need more than <3> years of experience.
- <Nationality or security-clearance requirements you cannot meet>.
- <Languages you do not speak that are mandatory>.
- Unpaid, commission-only, or pure cold-calling sales.

## How to choose (daily)

1. Start from the top of `data/triage/<date>.txt`. The list is sorted by rough points, but the
   points are only a guess. Also skim the one-liners below the cut.
2. Shortlist about 15–20 candidates. Read their full adverts with the `show` command.
3. Recommend the best **5–12**, in the priority order above.
4. **Prefer DIRECT employers.** Take 2 points off an agency job's fit score. Recommend an agency
   job only when it is clearly better than the direct options, and at most **2 per day**.
5. For an agency job, or one reposted by a job board, try to find the real employer and its
   own advert. Put that URL in `direct_link` (copied from a search result, never typed), the
   real employer in `company`, and mark the job `Direct`.
6. Research every pick briefly: the company's values and recent news. The cover letter uses
   this research.

## Fields to write per job

See `docs/scored-format.md` for the exact JSON.

- **fit_score** (0–10): overall fit, after the agency penalty.
- **why**: two to four sentences covering salary, growth, how future-proof the role is, profile
  fit and the main risk.
- **cv**: one id from `config/settings.json → candidate.cvs`:
  - `general`: <when to use it>
  - `technical`: <when to use it>
- **salary**: an estimated range for the location, with the basis (advertised, typical, etc.).
- **meets_target**: starts with `Yes`, `No – below target` or `Borderline`, plus a short reason.
- **visa_notes**: right-to-work points for this job.
- **deadline** (optional): `YYYY-MM-DD`, only when the advert states one.
- **cover_letter**: see below.

## Salary target

<Your minimum gross salary per location, and the reasoning if you like, e.g.:>

| Location | Minimum gross per year |
|---|---|
| <London> | <£35,000> |
| <Elsewhere in the UK> | <£28,000> |

The same numbers go in `settings.json → triage.salary_targets` (they drive the `meets` /
`below` hint in the triage file).

## Cover letters

- About **300 words** (250–350). <UK / US> English.
- Address the hiring team or the named recruiter. Use the role title as advertised.
- **Structure**:
  1. Why this role at this company, using one specific detail from your research.
  2. The most relevant evidence from my experience, with numbers.
  3. Why the company appeals: its values, recent news, the team.
  4. A short close (availability, relocation if relevant).
- **Angle**: <your strongest story and numbers, in order of preference>.
- **Tone**: confident, specific, no clichés. Never invent experience or skills. Use the letters in
  `data/scored/*.json` (field `cover_letter`) as tone examples once there are some.
- Do **not** add a sign-off or contact details. The build adds the signature from
  `settings.json → candidate.signature`.
