"""Reed.co.uk Jobseeker API (UK only). Free key: https://www.reed.co.uk/developers/jobseeker

Auth is HTTP Basic with the key as the user name and an empty password.
Search results carry a short description; the full one needs a second request per job.
"""
import datetime as dt

from .. import http
from ..store import make_job
from ..textutil import html_to_text, target_region

NAME, PREFIX, NEEDS = "reed", "reed", ("reed_api_key",)
SEARCH = "https://www.reed.co.uk/api/1.0/search"
DETAIL = "https://www.reed.co.uk/api/1.0/jobs/{}"


def _date(text):
    """Reed dates are dd/mm/yyyy."""
    try:
        return dt.datetime.strptime(text, "%d/%m/%Y").date().isoformat()
    except (TypeError, ValueError):
        return ""


def _salary(r):
    low, high = r.get("minimumSalary"), r.get("maximumSalary")
    if not low and not high:
        return ""
    cur = {"GBP": "£"}.get(r.get("currency") or "GBP", r.get("currency") or "")
    return f"{cur}{low:,.0f}" + (f" - {cur}{high:,.0f}" if high and high != low else "") + " per annum"


def fetch(ctx):
    uk = target_region("gb")
    if uk is None:  # Reed is UK-only
        return
    auth = (ctx.secrets["reed_api_key"], "")
    oldest = dt.date.fromisoformat(ctx.date) - dt.timedelta(days=ctx.cfg.get("max_age_days", 2))
    picked = {}
    for query in ctx.settings["searches"]["simple"]:
        r = http.get(SEARCH, auth=auth, params={
            "keywords": query, "resultsToTake": min(100, ctx.cfg.get("results_per_search", 100))})
        results = r.json().get("results", []) if r else []
        for item in results:
            key = f"{PREFIX}:{item['jobId']}"
            posted = _date(item.get("date"))
            if key in picked or (posted and dt.date.fromisoformat(posted) < oldest):
                continue
            if ctx.wanted(key, item.get("jobTitle"), item.get("employerName"), uk, item.get("jobUrl", "")):
                picked[key] = dict(item, _query=query, _posted=posted)
        http.pause(0.5, 1)
    ctx.log(f"  {len(picked)} new and relevant -> fetching descriptions")
    for key, item in picked.items():
        r = http.get(DETAIL.format(item["jobId"]), auth=auth)
        full = r.json() if r else {}
        yield make_job(NAME, PREFIX, item["jobId"], item.get("jobTitle"), item.get("employerName"),
                       item.get("locationName") or uk, uk,
                       full.get("jobUrl") or item.get("jobUrl", ""),
                       description=html_to_text(full.get("jobDescription") or item.get("jobDescription", "")),
                       posted=item["_posted"], salary=_salary(item) or _salary(full), query=item["_query"])
        http.pause(0.3, 0.8)
