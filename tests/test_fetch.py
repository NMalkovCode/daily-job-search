"""fetch.run with fake sources: de-duplication, resume, same-day behaviour."""
import types

import pytest

from conftest import job
from jobsearch import fetch, paths
from jobsearch.store import Seen, load_day


def fake_source(name, jobs, fail_after=None):
    def run(ctx):
        for n, j in enumerate(jobs):
            if fail_after is not None and n == fail_after:
                raise RuntimeError("site changed")
            if ctx.wanted(j["key"], j["title"], j["company"], j["region"], j["link"]):
                yield dict(j, source=name)
    return types.SimpleNamespace(NAME=name, fetch=run)


@pytest.fixture
def sources(monkeypatch, project):
    def use(**mods):
        monkeypatch.setattr(fetch, "SOURCES", mods)
        for name in mods:
            monkeypatch.setitem(fetch.config.settings()["sources"], name, {"enabled": True})
    return use


def test_same_job_on_two_sites_is_saved_once(sources):
    a = job(1, company="Acme Ltd")
    b = job(2, company="ACME Limited", source="reed", prefix="reed")
    sources(ats=fake_source("ats", [a]), reed=fake_source("reed", [b]))
    day = fetch.run()
    assert [j["key"] for j in day["jobs"]] == ["li:1"]
    assert day["jobs"][0]["also_on"][0]["key"] == "reed:2"


def test_second_run_same_day_is_skipped_unless_again(sources):
    sources(ats=fake_source("ats", [job(1)]))
    fetch.run()
    sources(ats=fake_source("ats", [job(1), job(3, title="Pricing Analyst")]))
    assert len(fetch.run()["jobs"]) == 1
    assert len(fetch.run(again=True)["jobs"]) == 2


def test_reposts_and_irrelevant_titles_are_dropped(sources):
    seen = Seen(30)
    seen.add("li:old", job(9)["fingerprint"], paths.today())
    seen.save()
    sources(ats=fake_source("ats", [job(10), job(11, title="Head of Sales"), job(12, region="Germany")]))
    day = fetch.run()
    assert day["jobs"] == []


def test_broken_source_keeps_progress_and_others_run(sources):
    jobs = [job(n, title=f"Data Analyst {n}") for n in range(5)]
    sources(ats=fake_source("ats", jobs, fail_after=3), reed=fake_source("reed", [job(99, title="Strategy Analyst")]))
    day = fetch.run()
    assert len(day["jobs"]) == 4
    run = load_day(paths.today())["runs"][-1]
    assert "site changed" in run["sources"]["ats"]["error"] and run["finished"]
    assert Seen(30).has_key("li:2")
