from conftest import job, write_day
from jobsearch import paths, triage


def test_triage_ranks_and_rejects(project):
    write_day("2026-10-21", [
        job(1, title="Graduate Strategy Analyst", location="Dubai, United Arab Emirates"),
        job(2, title="Business Analyst", company="Hays", location="Leeds, United Kingdom", region="United Kingdom",
            description="Our client is a bank. 0-2 years of experience."),
        job(3, title="Data Analyst", description="UAE nationals only. Graduate role."),
        job(4, title="Operations Analyst", description="Requires 7+ years of experience in operations."),
    ])
    rows, rejected = triage.analyse("2026-10-21")
    assert [r["job"]["key"] for r in rows] == ["li:1", "li:2"]
    assert rows[1]["agency"] and rows[0]["points"] > rows[1]["points"]
    assert rejected == {"nationality": 1, "experience": 1}

    text = triage.write("2026-10-21").read_text(encoding="utf-8")
    assert "li:1 | DIRECT | Graduate Strategy Analyst" in text and "li:2 | AGENCY" in text
    assert paths.triage_file("2026-10-21").exists()
