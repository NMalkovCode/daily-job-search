"""Parsers of each source, fed with canned responses (no network)."""

import pytest

from conftest import Resp
from jobsearch import config, fetch
from jobsearch.filters import Filters
from jobsearch.sources import ats, linkedin
from jobsearch.store import Seen

CARD = """<li><div class="base-card" data-entity-urn="urn:li:jobPosting:4412345678">
<h3 class="base-search-card__title">
      Graduate Business Analyst
    </h3><h4 class="base-search-card__subtitle"><a>Acme Analytics</a></h4>
<span class="job-search-card__location">Dubai, Dubai, United Arab Emirates</span>
<time class="job-search-card__listdate" datetime="2026-10-21">1 hour ago</time></div></li>"""
DETAIL = """<div class="show-more-less-html__markup">About the role<br>Entry level. Python.</div>
<ul><li class="description__job-criteria-item"><h3 class="description__job-criteria-subheader">Seniority level</h3>
<span class="description__job-criteria-text">Entry level</span></li></ul>"""


def test_linkedin_parsers():
    cards = linkedin.parse_cards(CARD, "United Arab Emirates")
    assert cards == [{"id": "4412345678", "title": "Graduate Business Analyst", "company": "Acme Analytics",
                      "location": "Dubai, Dubai, United Arab Emirates", "posted": "2026-10-21"}]
    text, details = linkedin.parse_detail(DETAIL)
    assert "Entry level. Python." in text and details == {"seniority": "Entry level"}


@pytest.fixture
def ctx(project):
    settings = config.settings()
    day = {"date": "2026-10-21", "runs": [], "jobs": []}
    return fetch.Context("ats", settings, Filters(settings), Seen(30), day, {}, lambda m: None)


def test_greenhouse_and_lever(ctx, monkeypatch):
    responses = {
        "boards-api.greenhouse.io": {"jobs": [
            {"id": 1, "title": "Graduate Strategy Analyst", "location": {"name": "London, UK"},
             "first_published": "2026-10-20T10:00:00Z", "absolute_url": "https://gh/1",
             "content": "&lt;p&gt;Graduate role&lt;/p&gt;"},
            {"id": 2, "title": "Graduate Strategy Analyst", "location": {"name": "Berlin"},
             "first_published": "2026-10-20", "absolute_url": "https://gh/2", "content": ""},
            {"id": 3, "title": "Data Analyst", "location": {"name": "Dubai"},
             "first_published": "2026-01-01", "absolute_url": "https://gh/3", "content": ""},
        ]},
        "api.lever.co": [
            {"id": "abc", "text": "AI Automation Analyst", "categories": {"location": "Dubai"},
             "createdAt": 1792454400000, "hostedUrl": "https://lever/abc", "descriptionPlain": "Automate things."},
        ],
    }
    monkeypatch.setattr(ats.http, "get", lambda url, **kw: Resp(next(v for k, v in responses.items() if k in url)))
    monkeypatch.setattr(ats.http, "pause", lambda *a: None)
    monkeypatch.setattr(ats, "companies", lambda: [{"company": "Acme", "ats": "greenhouse", "id": "acme"},
                                                   {"company": "Beta", "ats": "lever", "id": "beta"}])
    jobs = list(ats.fetch(ctx))
    assert [(j["key"], j["region"]) for j in jobs] == [("ats:greenhouse:acme:1", "United Kingdom"),
                                                       ("ats:lever:beta:abc", "United Arab Emirates")]
    assert jobs[0]["description"] == "Graduate role" and jobs[0]["source"] == "greenhouse"


def test_workday_resolves_multi_location_from_detail(ctx, monkeypatch):
    listing = {"jobPostings": [{"title": "Graduate Analyst", "externalPath": "/job/Dubai/Graduate-Analyst_R123",
                                "locationsText": "2 Locations", "postedOn": "Posted Yesterday"}]}
    detail = {"jobPostingInfo": {"jobDescription": "<p>Join us</p>", "location": "Dubai",
                                 "country": {"descriptor": "United Arab Emirates"}}}
    monkeypatch.setattr(ats.http, "post", lambda url, **kw: Resp(listing))
    monkeypatch.setattr(ats.http, "get", lambda url, **kw: Resp(detail))
    monkeypatch.setattr(ats.http, "pause", lambda *a: None)
    monkeypatch.setitem(ctx.cfg, "search_terms", ["graduate"])
    monkeypatch.setattr(ats, "companies", lambda: [{"company": "BigBank", "ats": "workday", "id": "bigbank",
                                                   "wd": 3, "site": "Careers"}])
    [j] = list(ats.fetch(ctx))
    assert j["region"] == "United Arab Emirates" and j["posted"] == "2026-10-20" and j["description"] == "Join us"
    assert j["link"] == "https://bigbank.wd3.myworkdayjobs.com/Careers/job/Dubai/Graduate-Analyst_R123"


RSS = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:tt="https://teamtailor.com/locations"><channel>
<item><title>Graduate Commercial Analyst</title><description>&lt;p&gt;Join our team&lt;/p&gt;</description>
<pubDate>Tue, 20 Oct 2026 10:00:00 +0400</pubDate><link>https://acme.teamtailor.com/jobs/8066036-graduate</link>
<tt:locations><tt:location><tt:city>Dubai</tt:city><tt:country>United Arab Emirates</tt:country></tt:location></tt:locations>
</item>
<item><title>Graduate Commercial Analyst</title><description>x</description>
<pubDate>Tue, 20 Oct 2026 10:00:00 +0400</pubDate><link>https://acme.teamtailor.com/jobs/8066037-cairo</link>
<tt:locations><tt:location><tt:city>Cairo</tt:city><tt:country>Egypt</tt:country></tt:location></tt:locations>
</item></channel></rss>"""


def run_board(ctx, monkeypatch, company, get=None, post=None):
    if get:
        monkeypatch.setattr(ats.http, "get", get)
    if post:
        monkeypatch.setattr(ats.http, "post", post)
    monkeypatch.setattr(ats.http, "pause", lambda *a: None)
    monkeypatch.setattr(ats, "companies", lambda: [company])
    return list(ats.fetch(ctx))


def test_teamtailor(ctx, monkeypatch):
    resp = type("R", (), {"content": RSS})()
    [j] = run_board(ctx, monkeypatch, {"company": "Acme", "ats": "teamtailor", "id": "acme"}, get=lambda url, **kw: resp)
    assert j["key"] == "ats:teamtailor:acme:8066036" and j["posted"] == "2026-10-20"
    assert j["location"] == "Dubai, United Arab Emirates" and j["description"] == "Join our team"


def test_pinpoint_and_oracle(ctx, monkeypatch):
    pin = {"data": [{"id": "1", "title": "Business Development Analyst", "url": "https://tabby.pinpointhq.com/p/1",
                     "location": {"city": "Dubai", "name": "United Arab Emirates"}, "description": "<p>BD</p>"}]}
    [j] = run_board(ctx, monkeypatch, {"company": "Tabby", "ats": "pinpoint", "id": "tabby"}, get=lambda url, **kw: Resp(pin))
    assert j["region"] == "United Arab Emirates" and j["description"] == "BD"

    reqs = {"items": [{"requisitionList": [
        {"Id": "27400", "Title": "Graduate Analyst", "PostedDate": "2026-10-21", "PrimaryLocation": "Dubai",
         "PrimaryLocationCountry": "AE"},
        {"Id": "27401", "Title": "Graduate Analyst", "PostedDate": "2026-10-21", "PrimaryLocation": "Itasca, IL",
         "PrimaryLocationCountry": "US"}]}]}
    detail = {"items": [{"ExternalDescriptionStr": "<p>About the role</p>"}]}
    monkeypatch.setitem(ctx.cfg, "search_terms", ["graduate"])
    [j] = run_board(ctx, monkeypatch, {"company": "DP World", "ats": "oracle", "id": "host.example", "site": "CX_1"},
                    get=lambda url, **kw: Resp(detail if "Details" in url else reqs))
    assert j["location"] == "Dubai, United Arab Emirates" and j["description"] == "About the role"
    assert j["link"] == "https://host.example/hcmUI/CandidateExperience/en/sites/CX_1/job/27400"


def test_api_sources(ctx, monkeypatch):
    from jobsearch.sources import adzuna, jooble, reed
    monkeypatch.setattr(ctx, "secrets", {"reed_api_key": "k", "adzuna_app_id": "i", "adzuna_app_key": "k",
                                         "jooble_api_key": "k"})
    monkeypatch.setitem(ctx.settings["searches"], "simple", ["graduate analyst"])
    for m in (reed, adzuna, jooble):
        monkeypatch.setattr(m.http, "pause", lambda *a: None)

    reed_search = {"results": [{"jobId": 55, "jobTitle": "Graduate Analyst", "employerName": "Acme",
                                "locationName": "Leeds", "date": "21/10/2026", "jobUrl": "https://reed/55",
                                "minimumSalary": 28000, "maximumSalary": 32000, "currency": "GBP"}]}
    reed_detail = {"jobDescription": "<p>Full advert</p>", "jobUrl": "https://reed/55"}
    monkeypatch.setattr(reed.http, "get", lambda url, **kw: Resp(reed_detail if "/jobs/" in url else reed_search))
    [j] = list(reed.fetch(ctx))
    assert j["key"] == "reed:55" and j["description"] == "Full advert" and j["salary"] == "£28,000 - £32,000 per annum"

    adz = {"results": [{"id": "77", "title": "<strong>Pricing</strong> Analyst", "company": {"display_name": "Beta"},
                        "location": {"display_name": "London"}, "redirect_url": "https://adzuna/77",
                        "description": "Snippet", "created": "2026-10-21T08:00:00Z", "salary_min": 30000,
                        "salary_is_predicted": "1"}]}
    monkeypatch.setattr(adzuna.http, "get", lambda url, **kw: Resp(adz))
    [j] = list(adzuna.fetch(ctx))
    assert j["title"] == "Pricing Analyst" and j["salary"] == "" and j["posted"] == "2026-10-21"

    jb = {"jobs": [{"id": 123, "title": "Strategy Analyst", "company": "Gamma", "location": "Dubai",
                    "snippet": "Short text", "link": "https://jooble.org/desc/123", "updated": "2026-10-21T00:00:00"}]}
    monkeypatch.setitem(ctx.cfg, "hosts", {"United Arab Emirates": "ae.jooble.org"})
    monkeypatch.setattr(jooble.http, "post", lambda url, **kw: Resp(jb))
    [j] = list(jooble.fetch(ctx))
    assert j["key"] == "jb:123" and j["region"] == "United Arab Emirates"
