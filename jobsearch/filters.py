"""Rule-based checks shared by fetch and triage. All word lists live in config/settings.json -> "filters"."""
import re

from .textutil import clip

# A phrase does not count when it is negated just before it ("no security clearance required")
# or softened just after it ("Arabic is a plus", "UAE nationals are encouraged to apply").
_NEGATION_BEFORE = re.compile(r"\b(no|not|without|non|never|isn't|doesn't|don't)\b[\w\s,/-]{0,20}$")
_SOFT_AFTER = re.compile(r"^\W{0,3}(?:[\w-]+\W+){0,4}?(?:is |are |would be |will be )?(?:a |an |considered )?"
                         r"(plus|advantage|advantageous|preferred|desirable|bonus|nice to have|beneficial|"
                         r"encouraged)\b")

_YEARS = re.compile(r"\b(\d{1,2})\s*\+?\s*(?:(?:-|–|—|to)\s*\d{1,2}\s*\+?\s*)?(?:years?|yrs?)\b")
_YEARS_IS_REQUIREMENT_AFTER = re.compile(
    r"^['’]?\s*(?:of\s+)?(?:[\w-]+\s+){0,4}?(?:experience|exp\b|pqe)|"
    r"^['’]?\s*(?:of\s+)?(?:hands-on|relevant|proven|professional|industry|work|working|building|into\s|"
    r"in\s|with\s|across\s|delivering|leading|managing|post-qualification|track record|background)")
_YEARS_IS_REQUIREMENT_BEFORE = re.compile(
    r"(?:experience|minimum|min\.?|at least|requires?|required|must have|need|needs|you have|"
    r"you bring)\W*(?:of\s+)?(?:a\s+)?(?:approximately\s+|around\s+|over\s+)?$")
_YEARS_IS_PREFERRED = re.compile(r"^['’]?\s*(?:of\s+)?(?:[\w-]+\s+){0,3}?(?:is\s+|are\s+|would be\s+)?"
                                 r"(?:preferred|desirable|advantageous|an advantage|a plus|a bonus)\b")
_YEARS_IS_NOT_REQUIREMENT = re.compile(
    r"^\s*(?:ago|old|of (?:history|heritage|innovation|excellence|pioneering|growth|service|operation|"
    r"trading|success|leadership|existence)|in business|in the (?:industry|market|region|uae|uk|gcc)"
    r"|of (?:age|age or older))")
_COMPANY_AGE_BEFORE = re.compile(r"(?:founded|established|since|celebrat\w*|for over|for more than|"
                                 r"over the (?:past|last)|history of|legacy of|heritage of)\W*$")


def _rx(parts):
    return re.compile("|".join(f"(?:{p})" for p in parts), re.I) if parts else None


def _real_match(text, m):
    before, after = text[max(0, m.start() - 40):m.start()], text[m.end():m.end() + 40]
    return not _NEGATION_BEFORE.search(before) and not _SOFT_AFTER.search(after)


class Filters:
    def __init__(self, settings):
        f = settings["filters"]
        self.max_years = f.get("max_years_experience", 3)
        self.title_keep = _rx(f["title_keep"])
        self.title_exclude = _rx(f["title_exclude"])
        # keys starting with "_" are notes for people (e.g. "_readme_note"), not phrase lists
        self.reject = {reason: _rx(phrases) for reason, phrases in f["description_reject"].items()
                       if not reason.startswith("_")}
        self.agency_name = _rx(f["agency_names"])
        self.agency_phrase = _rx(f["agency_phrases"])
        self.flag_rx = {flag: _rx(phrases) for flag, phrases in f["flags"].items() if not flag.startswith("_")}

    # ---------------------------------------------------------------- title (cheap, before details)
    def title_ok(self, title):
        return bool(self.title_keep.search(title or "")) and not (
            self.title_exclude and self.title_exclude.search(title or ""))

    # ---------------------------------------------------------------- full job
    def required_years(self, text):
        """Years of experience the advert insists on, or None.

        Each requirement counts by its lower bound ("3-5 years" -> 3); an advert asking for
        "8+ years in software, incl. 1 year of AI" needs 8, so the largest requirement wins.
        Mentions marked preferred/ideally are ignored.
        """
        text = (text or "").lower()
        found = []
        for m in _YEARS.finditer(text):
            n = int(m.group(1))
            before, after = text[max(0, m.start() - 45):m.start()], text[m.end():m.end() + 80]
            if n == 0 or n > 15 or _YEARS_IS_NOT_REQUIREMENT.search(after) or _COMPANY_AGE_BEFORE.search(before):
                continue
            if _YEARS_IS_PREFERRED.search(after):
                continue
            if _YEARS_IS_REQUIREMENT_AFTER.search(after) or _YEARS_IS_REQUIREMENT_BEFORE.search(before):
                found.append(n)
        return max(found) if found else None

    def reject_reason(self, job):
        """Why the job breaks a hard filter (see config/profile.md), or None if it passes."""
        if not self.title_ok(job["title"]):
            return "title"
        text = f"{job['title']}\n{job.get('description') or ''}".lower()
        for reason, rx in self.reject.items():
            for m in rx.finditer(text):
                if _real_match(text, m):
                    return f"{reason}: “{clip(m.group(0), 40)}”"
        years = self.required_years(text)
        if years is not None and years > self.max_years:
            return f"experience: {years}+ years"
        return None

    def is_agency(self, job):
        desc = (job.get("description") or "")[:1500]
        return bool(self.agency_name.search(job["company"] or "") or self.agency_phrase.search(desc))

    def flags(self, job):
        text = f"{job['title']}\n{job.get('description') or ''}"
        return [flag for flag, rx in self.flag_rx.items()
                if any(_real_match(text.lower(), m) for m in rx.finditer(text.lower()))]
