"""LinkedIn public (logged-out) job search. No login, no applying.

Search results come 10 per page; every new job then needs one more request for its
description. Requests are spaced out to stay polite; a full run takes ~20-40 minutes.
"""
import re

from bs4 import BeautifulSoup

from .. import http
from ..store import make_job
from ..textutil import detect_region

NAME, PREFIX = "linkedin", "li"
SEARCH = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
DETAIL = "https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{}"


def _text(el, selector):
    found = el.select_one(selector)
    return found.get_text(strip=True) if found else ""


def parse_cards(html, region):
    """Search-result HTML -> list of dicts with id, title, company, location, posted."""
    cards = []
    for li in BeautifulSoup(html, "html.parser").select("li"):
        urn_el = li if li.get("data-entity-urn") else li.select_one("[data-entity-urn]")
        m = re.search(r"(\d+)$", urn_el.get("data-entity-urn", "")) if urn_el else None
        if not m:
            continue
        posted = li.select_one("time")
        cards.append({
            "id": m.group(1),
            "title": _text(li, ".base-search-card__title"),
            "company": _text(li, ".base-search-card__subtitle"),
            "location": _text(li, ".job-search-card__location") or region,
            "posted": posted.get("datetime", "") if posted else "",
        })
    return cards


def parse_detail(html):
    """Job page HTML -> (description text, {"seniority": .., "employment_type": ..})."""
    soup = BeautifulSoup(html, "html.parser")
    desc = soup.select_one(".show-more-less-html__markup")
    details = {}
    for item in soup.select(".description__job-criteria-item"):
        head = item.select_one(".description__job-criteria-subheader")
        val = item.select_one(".description__job-criteria-text")
        if head and val:
            name = head.get_text(strip=True).lower().replace(" level", "").replace(" ", "_")
            details[name] = val.get_text(strip=True)
    return (desc.get_text("\n", strip=True) if desc else ""), details


def fetch(ctx):
    cfg = ctx.cfg
    cards = {}
    for region in ctx.regions:
        for query in ctx.settings["searches"]["boolean"]:
            found = 0
            for start in range(0, cfg.get("max_results_per_search", 100), 10):
                r = http.get(SEARCH, params={
                    "keywords": query, "location": region, "start": start,
                    "f_TPR": f"r{int(cfg.get('posted_within_hours', 24)) * 3600}",
                    "f_E": cfg.get("experience_levels", "1,2,3"),
                })
                page = parse_cards(r.text, region) if r else []
                if not page:
                    break
                for c in page:
                    found += 1
                    if c["id"] not in cards:
                        cards[c["id"]] = dict(c, region=detect_region(c["location"]) or region, query=query)
                http.pause(2, 4)
            ctx.log(f"  {region} | {query[:60]}: {found} results")

    todo = [c for c in cards.values()
            if ctx.wanted(f"{PREFIX}:{c['id']}", c["title"], c["company"], c["region"])]
    ctx.log(f"  {len(cards)} unique results, {len(todo)} new and relevant -> fetching descriptions")
    for i, c in enumerate(todo, 1):
        r = http.get(DETAIL.format(c["id"]))
        description, details = parse_detail(r.text) if r else ("", {})
        job = make_job(NAME, PREFIX, c["id"], c["title"], c["company"], c["location"], c["region"],
                       f"https://www.linkedin.com/jobs/view/{c['id']}/", description=description,
                       posted=c["posted"], query=c["query"])
        if details:
            job["details"] = details
        if i % 50 == 0:
            ctx.log(f"  descriptions: {i}/{len(todo)}")
        yield job
        http.pause(1.5, 3)
