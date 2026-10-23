"""Jooble API (many countries, one host per country). Aggregates many boards, including ones such as
Bayt and GulfTalent that block plain HTTP. Free key: request form at https://jooble.org/api/about

Results carry a short snippet only; `link` is Jooble's redirect to the original advert, which
Claude can open when a job is shortlisted. Endpoint per country is in settings.json.
Written to Jooble's published API format; not yet run with a live key (see docs/sources.md).
"""
import datetime as dt
import hashlib

from .. import http
from ..store import make_job
from ..textutil import detect_region, html_to_text

NAME, PREFIX, NEEDS = "jooble", "jb", ("jooble_api_key",)


def _id(item):
    raw = str(item.get("id") or item.get("link") or "")
    return raw if raw.isdigit() else hashlib.sha1(raw.encode()).hexdigest()[:16]


def fetch(ctx):
    key = ctx.secrets["jooble_api_key"]
    since = (dt.date.fromisoformat(ctx.date) - dt.timedelta(days=ctx.cfg.get("max_age_days", 2))).isoformat()
    for region, host in ctx.cfg.get("hosts", {}).items():
        if region not in ctx.regions:
            continue
        for query in ctx.settings["searches"]["simple"]:
            r = http.post(f"https://{host}/api/{key}", json={
                "keywords": query, "location": ctx.cfg.get("locations", {}).get(region, ""),
                "page": "1", "ResultOnPage": str(ctx.cfg.get("results_per_search", 50)), "datecreatedfrom": since})
            for item in (r.json().get("jobs", []) if r else []):
                job_id = _id(item)
                loc = item.get("location") or ""
                job_region = detect_region(loc) or region
                if not ctx.wanted(f"{PREFIX}:{job_id}", item.get("title"), item.get("company"), job_region,
                                  item.get("link", "")):
                    continue
                yield make_job(NAME, PREFIX, job_id, html_to_text(item.get("title")), item.get("company"), loc,
                               job_region, item.get("link", ""), description=html_to_text(item.get("snippet")),
                               posted=(item.get("updated") or "")[:10], salary=item.get("salary") or "", query=query)
            http.pause(1, 2)
