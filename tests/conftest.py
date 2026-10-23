import json
from pathlib import Path

import pytest

from jobsearch import config, paths
from jobsearch.store import make_job, save_day

# The tests use their own fixed settings (UAE + UK), never the user's config/settings.json.
paths.SETTINGS_FILE = Path(__file__).parent / "fixtures" / "settings.json"
config.settings.cache_clear()


@pytest.fixture
def project(tmp_path, monkeypatch):
    """Point every data/output path at a temp folder; config/ stays the real one (read-only)."""
    data, out = tmp_path / "data", tmp_path / "output"
    for name, value in {
        "DATA_DIR": data, "RAW_DIR": data / "raw", "TRIAGE_DIR": data / "triage", "SCORED_DIR": data / "scored",
        "STATE_DIR": data / "state", "SEEN_FILE": data / "state" / "seen.json", "BACKUP_DIR": data / "backups",
        "LOG_DIR": data / "logs", "OUTPUT_DIR": out, "TRACKER_FILE": out / "Job Tracker.xlsx",
        "LETTERS_DIR": out / "Cover Letters", "PREVIOUS_LETTERS_DIR": out / "Cover Letters" / "Previous Cover Letters",
    }.items():
        monkeypatch.setattr(paths, name, value)
    return tmp_path


def job(n, title="Graduate Business Analyst", company="Acme Analytics", location="Dubai, United Arab Emirates",
        region="United Arab Emirates", source="linkedin", prefix="li", description=None):
    return make_job(source, prefix, str(n), title, company, location, region, f"https://example.com/jobs/{n}",
                    description=description or "Entry level role, 0-2 years of experience. Python and SQL.")


LETTER = ("Dear Hiring Team,\n\nI am applying for the Graduate Business Analyst role at Acme Analytics. "
          + "My work automating quotes and pricing at a growing engineering firm taught me a lot. " * 12
          + "\n\nI would welcome the chance to talk.\n\nKind regards,\nAlex Example")


def pick(key, **extra):
    entry = {"key": key, "recommend": True, "fit_score": 8, "source_type": "Direct", "why": "Good fit.",
             "cv": "consulting", "salary": "AED 15-18k/month", "meets_target": "Yes",
             "visa_notes": "Employer sponsors the visa.", "cover_letter": LETTER}
    entry.update(extra)
    return entry


def write_day(date, jobs):
    save_day({"date": date, "runs": [{"started": None, "finished": "test", "sources": {}}], "jobs": jobs})


def write_scored(date, entries):
    paths.SCORED_DIR.mkdir(parents=True, exist_ok=True)
    paths.scored_file(date).write_text(json.dumps(entries), encoding="utf-8")


class Resp:
    """A canned HTTP response for the source parsers."""

    def __init__(self, data):
        self.data = data

    def json(self):
        return self.data
