"""Employers' own job boards through the public APIs of their applicant-tracking systems.

No key needed. These are DIRECT adverts, which the candidate prefers over agencies.
The company list lives in config/companies.json:
    {"company": "Celonis", "ats": "greenhouse", "id": "celonis"}
    {"company": "BlackRock", "ats": "workday", "id": "blackrock", "wd": 1, "site": "BlackRock_Professional"}
Supported "ats": greenhouse, lever, ashby, smartrecruiters, workable, workday, teamtailor, pinpoint,
oracle. The formats were checked against live boards on 2026-10-21.
"""
import datetime as dt
import email.utils
import html
import json
import re
import time
import xml.etree.ElementTree as ET

from .. import http, paths
from ..store import make_job
from ..textutil import COUNTRIES, country_name, detect_region, html_to_text

NAME, PREFIX = "ats", "ats"
COMPANIES_FILE = paths.CONFIG_DIR / "companies.json"


def _iso(value):
    """ISO string / epoch ms / None -> YYYY-MM-DD or ""."""
    if value in (None, ""):
        return ""
    if isinstance(value, (int, float)):
        return dt.datetime.fromtimestamp(value / 1000, dt.timezone.utc).date().isoformat()
    return str(value)[:10]


_MULTI = re.compile(r"\d+\s+locations", re.I)
_SENIOR_LEVELS = {"mid_senior_level", "director", "executive"}  # SmartRecruiters experienceLevel ids


def _get(url, **kw):
    """Employer APIs either answer or not: retry once after 5 s, never LinkedIn-style long waits."""
    return http.get(url, **{"tries": 2, "backoff": 5, **kw})


def _post(url, **kw):
    return http.post(url, **{"tries": 2, "backoff": 5, **kw})


def _with_country(location, code):
    """Add the country name so region detection works when only a code is given."""
    name = country_name(code)
    return f"{location}, {name}" if name and name not in (location or "") else location


# ---------------------------------------------------------------- one function per ATS
# Each yields dicts: id, title, location, posted, link, text (plain description) or detail (callable -> text)

def greenhouse(c, ctx):
    r = _get(f"https://boards-api.greenhouse.io/v1/boards/{c['id']}/jobs", params={"content": "true"})
    for j in (r.json().get("jobs", []) if r else []):
        yield {"id": j["id"], "title": j.get("title"), "location": (j.get("location") or {}).get("name", ""),
               "posted": _iso(j.get("first_published") or j.get("updated_at")), "link": j.get("absolute_url"),
               "text": html_to_text(html.unescape(j.get("content") or ""))}


def lever(c, ctx):
    host = "api.eu.lever.co" if c.get("eu") else "api.lever.co"
    r = _get(f"https://{host}/v0/postings/{c['id']}", params={"mode": "json"})
    for j in (r.json() if r else []):
        cats = j.get("categories") or {}
        locations = [cats.get("location") or ""] + (cats.get("allLocations") or [])
        lists = "\n".join(f"{x.get('text', '')}\n{html_to_text(x.get('content', ''))}" for x in j.get("lists") or [])
        location = _with_country("; ".join(loc for loc in locations if loc), j.get("country"))
        yield {"id": j["id"], "title": j.get("text"), "location": location,
               "posted": _iso(j.get("createdAt")), "link": j.get("hostedUrl"),
               "text": "\n\n".join(filter(None, [j.get("descriptionPlain"), lists, j.get("additionalPlain")]))}


def ashby(c, ctx):
    r = _get(f"https://api.ashbyhq.com/posting-api/job-board/{c['id']}")
    for j in (r.json().get("jobs", []) if r else []):
        if j.get("isListed") is False:
            continue
        places = [j.get("location") or ""] + [s.get("location", "") for s in j.get("secondaryLocations") or []]
        country = ((j.get("address") or {}).get("postalAddress") or {}).get("addressCountry", "")
        location = "; ".join(p for p in places + [country] if p)
        yield {"id": j["id"], "title": j.get("title"), "location": location,
               "posted": _iso(j.get("publishedAt")), "link": j.get("jobUrl"),
               "text": j.get("descriptionPlain") or html_to_text(j.get("descriptionHtml"))}


def smartrecruiters(c, ctx):
    default = [COUNTRIES[r][0] for r in ctx.regions if r in COUNTRIES]  # the target countries' codes
    for country in c.get("countries", default):
        r = _get(f"https://api.smartrecruiters.com/v1/companies/{c['id']}/postings",
                     params={"limit": 100, "country": country})
        for j in (r.json().get("content", []) if r else []):
            if (j.get("experienceLevel") or {}).get("id") in _SENIOR_LEVELS:
                continue
            loc = j.get("location") or {}
            ref = j.get("ref")

            def detail(ref=ref):
                d = _get(ref)
                sections = ((d.json().get("jobAd") or {}).get("sections") or {}) if d else {}
                return "\n\n".join(html_to_text(s.get("text", "")) for s in sections.values() if isinstance(s, dict))

            yield {"id": j["id"], "title": j.get("name"),
                   "location": _with_country(loc.get("fullLocation") or loc.get("city") or "", loc.get("country") or country),
                   "posted": _iso(j.get("releasedDate")),
                   "link": f"https://jobs.smartrecruiters.com/{c['id']}/{j['id']}", "detail": detail}


def workable(c, ctx):
    r = _get(f"https://apply.workable.com/api/v1/widget/accounts/{c['id']}", params={"details": "true"})
    for j in (r.json().get("jobs", []) if r else []):
        loc = ", ".join(filter(None, [j.get("city"), j.get("state"), j.get("country")]))
        yield {"id": j.get("shortcode") or j.get("id"), "title": j.get("title"), "location": loc,
               "posted": _iso(j.get("published_on") or j.get("created_at")), "link": j.get("url"),
               "text": html_to_text(j.get("description"))}


_WD_POSTED = re.compile(r"posted\s+(today|yesterday|(\d+)\+?\s+days?\s+ago)", re.I)


def _wd_facets(facets):
    """Workday nests facets; flatten to [(facetParameter, values)]."""
    out = []
    for f in facets or []:
        values = f.get("values") or []
        if values and "facetParameter" in values[0]:
            out += _wd_facets(values)
        else:
            out.append((f.get("facetParameter"), values))
    return out


def workday(c, ctx):
    """Big employers: searched with a few terms, limited to the target countries through the country facet."""
    base = f"https://{c['id']}.wd{c.get('wd', 1)}.myworkdayjobs.com"
    api = f"{base}/wday/cxs/{c['id']}/{c['site']}"
    headers = {"Origin": base, "Referer": f"{base}/en-US/{c['site']}"}
    today = dt.date.fromisoformat(ctx.date)
    # a few boards (Accenture) answer 429 after a handful of requests and recover after ~90 s;
    # companies.json can give them "slow": true to wait longer between and after requests
    slow = {"tries": 4, "backoff": 45} if c.get("slow") else {}
    pause = (3, 5) if c.get("slow") else (0.5, 1)

    # the facet name differs per employer (locationCountry, Location_Country, Country...)
    first = _post(f"{api}/jobs", headers=headers, **slow,
                  json={"appliedFacets": {}, "limit": 1, "offset": 0, "searchText": ""})
    if first is None:
        raise RuntimeError("board did not answer (rate-limited or moved)")
    applied = {}
    for param, values in _wd_facets(first.json().get("facets")):
        ids = [v["id"] for v in values if v.get("id") and detect_region(v.get("descriptor", ""))]
        if param and "country" in param.lower() and ids:
            applied = {param: ids}
            break

    seen_paths = set()
    for term in ctx.cfg.get("search_terms", ["graduate", "analyst"]):
        for page in range(ctx.cfg.get("workday_pages", 2)):
            r = _post(f"{api}/jobs", headers=headers, **slow,
                      json={"appliedFacets": applied, "limit": 20, "offset": 20 * page, "searchText": term})
            if r is None:
                raise RuntimeError(f"board stopped answering at search '{term}'")
            postings = r.json().get("jobPostings", [])
            for j in postings:
                path = j.get("externalPath")
                if not path or path in seen_paths:
                    continue
                seen_paths.add(path)
                m = _WD_POSTED.search(j.get("postedOn") or "")
                days = 0 if m and m.group(1).lower() == "today" else 1 if m and m.group(1).lower() == "yesterday" \
                    else int(m.group(2)) if m else 99
                info = {}

                def detail(path=path, info=info):
                    d = _get(f"{api}{path}", headers=headers, **slow)
                    info.update((d.json().get("jobPostingInfo") or {}) if d else {})
                    return html_to_text(info.get("jobDescription", ""))

                yield {"id": path.rsplit("_", 1)[-1], "title": j.get("title"), "location": j.get("locationsText", ""),
                       "posted": (today - dt.timedelta(days=days)).isoformat(), "link": f"{base}/{c['site']}{path}",
                       "detail": detail, "info": info}
            http.pause(*pause)
            if len(postings) < 20:
                break


_TT = "{https://teamtailor.com/locations}"


def teamtailor(c, ctx):
    """RSS feed; `id` is the subdomain or a custom careers domain (careers.chalhoubgroup.com)."""
    host = c["id"] if "." in c["id"] else f"{c['id']}.teamtailor.com"
    r = _get(f"https://{host}/jobs.rss")
    if not r:
        return
    for item in ET.fromstring(r.content).iter("item"):
        places = [", ".join(filter(None, [loc.findtext(f"{_TT}city"), loc.findtext(f"{_TT}country")]))
                  for loc in item.iter(f"{_TT}location")]
        link = item.findtext("link") or ""
        posted = item.findtext("pubDate")
        number = re.search(r"/jobs/(\d+)", link)
        yield {"id": number.group(1) if number else item.findtext("guid"), "title": item.findtext("title"), "location": "; ".join(p for p in places if p),
               "posted": email.utils.parsedate_to_datetime(posted).date().isoformat() if posted else "",
               "link": link, "text": html_to_text(item.findtext("description"))}


def pinpoint(c, ctx):
    """No posting date in the feed, so every listed job counts as current (seen-store keeps it once)."""
    r = _get(f"https://{c['id']}.pinpointhq.com/postings.json")
    for j in (r.json().get("data", []) if r else []):
        loc = j.get("location") or {}
        parts = [j.get("description"), j.get("key_responsibilities"), j.get("skills_knowledge_expertise"), j.get("benefits")]
        yield {"id": j["id"], "title": j.get("title"), "location": ", ".join(filter(None, [loc.get("city"), loc.get("name")])),
               "posted": "", "link": j.get("url"), "text": "\n\n".join(html_to_text(p) for p in parts if p)}


def oracle(c, ctx):
    """Oracle Recruiting Cloud (e.g. DP World). `id` is the host, `site` the site number (CX_1)."""
    base = f"https://{c['id']}/hcmRestApi/resources/latest"
    site, seen_ids = c.get("site", "CX_1"), set()
    for term in ctx.cfg.get("search_terms", ["graduate", "analyst"]):
        r = _get(f"{base}/recruitingCEJobRequisitions", params={
            "onlyData": "true", "expand": "requisitionList",
            "finder": f"findReqs;siteNumber={site},limit=50,offset=0,keyword={term},sortBy=POSTING_DATES_DESC"})
        items = (r.json().get("items") or [{}]) if r else [{}]
        for j in items[0].get("requisitionList") or []:
            if j["Id"] in seen_ids:
                continue
            seen_ids.add(j["Id"])

            def detail(job_id=j["Id"]):
                d = _get(f"{base}/recruitingCEJobRequisitionDetails", params={
                    "expand": "all", "onlyData": "true", "finder": f'ById;Id="{job_id}",siteNumber={site}'})
                info = ((d.json().get("items") or [{}])[0]) if d else {}
                return "\n\n".join(html_to_text(info.get(k)) for k in (
                    "ExternalDescriptionStr", "ExternalResponsibilitiesStr", "ExternalQualificationsStr") if info.get(k))

            yield {"id": j["Id"], "title": j.get("Title"),
                   "location": _with_country(j.get("PrimaryLocation") or "", j.get("PrimaryLocationCountry")),
                   "posted": _iso(j.get("PostedDate")),
                   "link": f"https://{c['id']}/hcmUI/CandidateExperience/en/sites/{site}/job/{j['Id']}", "detail": detail}
        http.pause(0.5, 1)


ADAPTERS = {f.__name__: f for f in (greenhouse, lever, ashby, smartrecruiters, workable, workday,
                                    teamtailor, pinpoint, oracle)}


# ---------------------------------------------------------------- common loop
def companies():
    if not COMPANIES_FILE.exists():
        return []
    return [c for c in json.loads(COMPANIES_FILE.read_text(encoding="utf-8"))["companies"]
            if c.get("enabled", True)]


def fetch(ctx):
    oldest = dt.date.fromisoformat(ctx.date) - dt.timedelta(days=ctx.cfg.get("max_age_days", 3))
    # boards list every level; LinkedIn's experience filter has no equivalent here
    extra = ctx.cfg.get("extra_title_exclude") or []
    too_senior = re.compile("|".join(f"(?:{p})" for p in extra), re.I) if extra else None
    for c in companies():
        adapter = ADAPTERS.get(c["ats"])
        if adapter is None:
            ctx.log(f"  {c['company']}: unknown ats '{c['ats']}' in config/companies.json")
            continue
        count, started = 0, time.monotonic()
        try:
            for j in adapter(c, ctx):
                if j["posted"] and dt.date.fromisoformat(j["posted"]) < oldest:
                    continue
                if too_senior and too_senior.search(j["title"] or ""):
                    ctx.stats["title"] += 1
                    continue
                key = f"{PREFIX}:{c['ats']}:{c['id']}:{j['id']}"
                region, text = detect_region(j["location"]), j.get("text")
                if region is None and _MULTI.search(j["location"] or "") and not ctx.seen.has_key(key) \
                        and ctx.filters.title_ok(j["title"]):
                    # Workday shows "3 Locations"; the countries are only on the detail page
                    text = j["detail"]()
                    info = j.get("info") or {}
                    region = detect_region(f"{info.get('location', '')} {(info.get('country') or {}).get('descriptor', '')}")
                if not ctx.wanted(key, j["title"], c["company"], region, j["link"]):
                    continue
                if text is None:
                    text = j["detail"]()
                yield make_job(c["ats"], PREFIX, f"{c['ats']}:{c['id']}:{j['id']}", j["title"], c["company"],
                               j["location"], region, j["link"], description=text, posted=j["posted"],
                               query=f"{c['ats']} board")
                count += 1
        except Exception as e:  # one company's board changing must not stop the rest
            ctx.log(f"  {c['company']}: ERROR {type(e).__name__}: {e}")
        seconds = time.monotonic() - started
        if count or seconds > 60:
            ctx.log(f"  {c['company']}: {count} new ({seconds:.0f} s)")
        http.pause(0.3, 0.8)
