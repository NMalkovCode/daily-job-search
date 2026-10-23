"""Configurable countries: region detection, salary targets, country-aware sources."""
import pytest

from conftest import Resp
from jobsearch import config, triage
from jobsearch.sources import adzuna, reed
from jobsearch.textutil import country_name, detect_region, region_code, target_region


@pytest.fixture
def regions(monkeypatch):
    def use(names, patterns=None):
        monkeypatch.setitem(config.settings(), "regions", names)
        monkeypatch.setitem(config.settings(), "region_patterns", patterns or {})
    return use


def test_detection_follows_settings(regions):
    regions(["Germany", "Ireland"])
    assert detect_region("Munich, Bavaria") == "Germany"
    assert detect_region("Dublin, County Dublin, Ireland") == "Ireland"
    assert detect_region("Belfast, Northern Ireland") is None  # the UK is not searched
    assert detect_region("London, United Kingdom") is None


def test_unknown_country_and_custom_pattern(regions):
    regions(["Portugal"])
    assert detect_region("Lisbon") is None and detect_region("Lisbon, Portugal") == "Portugal"
    regions(["Portugal"], {"Portugal": "portugal|lisbon|porto"})
    assert detect_region("Lisbon") == "Portugal"
    assert region_code("Portugal") == "portugal" and region_code("Germany") == "de"


def test_country_codes(regions):
    assert country_name("UK") == country_name("gb") == "United Kingdom" and country_name("zz") is None
    regions(["Germany"])
    assert target_region("gb") is None and target_region("de") == "Germany"


def test_salary_targets_first_match_wins():
    targets = [{"currency": "GBP", "location": "london", "per_year": 50000},
               {"currency": "GBP", "per_year": 30000},
               {"currency": "EUR", "region": "Germany", "per_year": 45000}]
    sal = {"currency": "GBP", "low": 40000, "high": 40000, "period": "year"}
    uk = {"region": "United Kingdom", "location": "London, England"}
    assert triage._salary_verdict(sal, uk, targets) == "below"
    assert triage._salary_verdict(sal, dict(uk, location="Leeds"), targets) == "meets"
    eur = {"currency": "EUR", "low": 4000, "high": 4000, "period": "month"}
    assert triage._salary_verdict(eur, {"region": "Germany", "location": "Berlin"}, targets) == "meets"
    assert triage._salary_verdict(eur, {"region": "France", "location": "Paris"}, targets) == ""


def test_api_sources_follow_regions(regions, monkeypatch, project):
    from jobsearch import fetch
    from jobsearch.filters import Filters
    from jobsearch.store import Seen
    regions(["Germany"])
    settings = config.settings()
    ctx = fetch.Context("adzuna", settings, Filters(settings), Seen(30), {"date": "2026-10-21"}, {}, lambda m: None)
    ctx.secrets = {"adzuna_app_id": "i", "adzuna_app_key": "k", "reed_api_key": "k"}
    monkeypatch.setitem(settings["searches"], "simple", ["analyst"])
    urls = []
    data = {"results": [{"id": "1", "title": "Data Analyst", "company": {"display_name": "Acme"},
                         "location": {"display_name": "Berlin"}, "redirect_url": "https://a/1",
                         "salary_min": 50000, "salary_max": 60000}]}
    monkeypatch.setattr(adzuna.http, "get", lambda url, **kw: urls.append(url) or Resp(data))
    monkeypatch.setattr(adzuna.http, "pause", lambda *a: None)
    [j] = list(adzuna.fetch(ctx))
    assert "/jobs/de/search/" in urls[0] and j["region"] == "Germany" and j["salary"].startswith("€50,000")
    assert list(reed.fetch(ctx)) == []  # Reed is UK-only and the UK is not searched
