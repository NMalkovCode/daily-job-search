"""The AI's daily output, data/scored/<date>.json, and the checks run on it before the build.

The AI writes ONLY its judgement. Title, company, location and links are copied from the raw
data by `key`, so a link can never be mistyped. See docs/scored-format.md for the fields.
"""
import json
import re

from . import config, paths, tracker
from .store import find_jobs

FIELDS = {  # name: (type, required)
    "key": (str, True),
    "recommend": (bool, True),
    "fit_score": (int, True),
    "source_type": (str, True),
    "why": (str, True),
    "cv": (str, True),
    "salary": (str, True),
    "meets_target": (str, True),
    "visa_notes": (str, True),
    "cover_letter": (str, True),
    "deadline": (str, False),
    "direct_link": (str, False),
    "title": (str, False),      # cleaner title / the real employer when the advert was posted
    "company": (str, False),    # by a job board or agency; links still come from the raw data
}
NOT_RECOMMENDED_NEEDS = {"key", "recommend", "fit_score", "why"}
LETTER_WORDS = (200, 400)      # warn outside this range; the target is ~300
PICKS_PER_DAY = (5, 12)
MAX_AGENCY_PER_DAY = 2
_SIGN_OFF = re.compile(r"\n\s*(kind regards|best regards|warm regards|regards|yours sincerely|yours faithfully|"
                       r"sincerely|many thanks)\b[\s\S]*$", re.I)
_PLACEHOLDER = re.compile(r"\[[A-Z][^\]]{0,40}\]|\{[a-z_]+\}|\bXXX\b|lorem ipsum|<insert", re.I)


def strip_sign_off(letter):
    """The build adds the signature from settings.json, so drop any the AI wrote."""
    return _SIGN_OFF.sub("", letter.strip()).rstrip()


def load(date):
    path = paths.scored_file(date)
    if not path.exists():
        raise FileNotFoundError(f"data/scored/{date}.json does not exist yet - the AI writes it during /daily-run")
    return json.loads(path.read_text(encoding="utf-8"))


def validate(date):
    """-> (errors, warnings, picks). picks = recommended entries merged with their raw job, best first."""
    errors, warnings = [], []
    try:
        entries = load(date)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        return [str(e)], [], []
    if not isinstance(entries, list):
        return ["The file must be a JSON list of objects"], [], []

    cvs = config.cv_options()
    jobs = find_jobs([e.get("key") for e in entries if isinstance(e, dict)], lookback_days=7)
    earlier = tracker.listed_before(date)  # {key or fingerprint: date} already in the tracker
    picks, used = [], set()

    for n, e in enumerate(entries, 1):
        where = f"entry {n} ({e.get('key', '?') if isinstance(e, dict) else '?'})"
        if not isinstance(e, dict):
            errors.append(f"{where}: must be an object")
            continue
        for name, (typ, required) in FIELDS.items():
            if name not in e:
                # a job read but not recommended only needs the reason
                if required and (e.get("recommend") is not False or name in NOT_RECOMMENDED_NEEDS):
                    errors.append(f"{where}: missing '{name}'")
            elif not isinstance(e[name], typ) or (typ is int and isinstance(e[name], bool)):
                errors.append(f"{where}: '{name}' must be {typ.__name__}")
        for name in set(e) - set(FIELDS):
            warnings.append(f"{where}: unknown field '{name}' is ignored")
        if errors and errors[-1].startswith(where):
            continue

        job = jobs.get(e["key"])
        if job is None:
            errors.append(f"{where}: key not found in data/raw (last 7 days) - copy keys from the triage file")
            continue
        fp = job["fingerprint"]
        if e["key"] in used or fp in used:
            errors.append(f"{where}: the same job appears twice in this file")
        used.update([e["key"], fp])
        if not 0 <= e["fit_score"] <= 10:
            errors.append(f"{where}: fit_score must be 0-10")
        if not e["recommend"]:
            continue

        if e["key"] in earlier or fp in earlier:
            errors.append(f"{where}: already in the tracker from {earlier.get(e['key']) or earlier.get(fp)}")
        if e["cv"] not in cvs:
            errors.append(f"{where}: cv '{e['cv']}' is not one of {', '.join(cvs)} (config/settings.json)")
        elif not config.cv_path(e["cv"]).exists():
            warnings.append(f"{where}: CV file not found: {config.cv_path(e['cv'])}")
        if not re.match(r"(Direct|Agency)\b", e["source_type"]):
            errors.append(f"{where}: source_type must start with 'Direct' or 'Agency'")
        if not re.match(r"(Yes|No|Borderline)\b", e["meets_target"]):
            warnings.append(f"{where}: meets_target should start with Yes / No / Borderline")
        if e.get("deadline") and not re.fullmatch(r"\d{4}-\d{2}-\d{2}", e["deadline"]):
            warnings.append(f"{where}: deadline should be YYYY-MM-DD")
        if e.get("direct_link") and not re.match(r"https?://", e["direct_link"]):
            errors.append(f"{where}: direct_link must be a full http(s) URL")

        letter = strip_sign_off(e["cover_letter"])
        words = len(letter.split())
        if not letter:
            errors.append(f"{where}: cover_letter is empty")
        elif not LETTER_WORDS[0] <= words <= LETTER_WORDS[1]:
            warnings.append(f"{where}: cover letter has {words} words (aim for ~300)")
        if _PLACEHOLDER.search(letter):
            errors.append(f"{where}: cover letter still has a placeholder: {_PLACEHOLDER.search(letter).group(0)}")
        company = e.get("company") or job["company"]
        first_word = (company.split() or [""])[0].lower()
        if e["source_type"].startswith("Direct") and first_word not in letter.lower():
            warnings.append(f"{where}: cover letter never names the company ({company})")
        picks.append({**job, **e, "cover_letter": letter, "posted_by": job["company"]})

    agency = sum(1 for p in picks if p["source_type"].startswith("Agency"))
    if agency > MAX_AGENCY_PER_DAY:
        warnings.append(f"{agency} agency jobs recommended (rule: at most {MAX_AGENCY_PER_DAY} per day)")
    if picks and not PICKS_PER_DAY[0] <= len(picks) <= PICKS_PER_DAY[1]:
        warnings.append(f"{len(picks)} jobs recommended (usual range {PICKS_PER_DAY[0]}-{PICKS_PER_DAY[1]})")
    picks.sort(key=lambda p: -p["fit_score"])
    return errors, warnings, picks


def report(date):
    errors, warnings, picks = validate(date)
    for w in warnings:
        print(f"WARNING  {w}")
    for e in errors:
        print(f"ERROR    {e}")
    print(f"{len(picks)} recommended, {len(errors)} errors, {len(warnings)} warnings")
    return not errors
