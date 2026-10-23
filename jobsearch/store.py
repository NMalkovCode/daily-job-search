"""The job record, the daily raw files and the seen-jobs store used for de-duplication.

A job is a plain dict (so the JSON files stay easy to read):
    key          "<source>:<id>", unique and stable, e.g. "li:4407801212", "reed:55012345"
    source       linkedin | reed | adzuna | greenhouse | lever | ashby | smartrecruiters | workable | workday
    title, company, location
    region       one of the countries in settings.json -> regions, e.g. "United Kingdom"
    link         the advert on the source site
    posted       YYYY-MM-DD when the source says, else ""
    salary       salary text given by the source (APIs only), else ""
    description  plain text
    query        the search that found it
    fingerprint  normalised company|title|country, see textutil.fingerprint
    also_on      [{"source", "key", "link"}] the same job found on other sites in the same run
"""
import datetime as dt
import json
import os
import re
import tempfile

from . import paths
from .textutil import fingerprint


def _one_line(text):
    return re.sub(r"\s+", " ", text or "").strip()


def make_job(source, key_prefix, source_id, title, company, location, region, link,
             description="", posted="", salary="", query=""):
    title, company = _one_line(title), _one_line(company)
    return {
        "key": f"{key_prefix}:{source_id}",
        "source": source,
        "title": title,
        "company": company,
        "location": re.sub(r"(?:\s*,)+\s*,", ",", _one_line(location)).strip(" ,"),  # "London, , UK"
        "region": region,
        "link": link,
        "posted": posted or "",
        "salary": salary or "",
        "description": description or "",
        "query": query,
        "fingerprint": fingerprint(company, title, region),
        "also_on": [],
    }


def write_json(path, data):
    """Write atomically, so a crash or Ctrl+C never leaves a half-written file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, prefix=path.name, suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=1, ensure_ascii=False)
    os.replace(tmp, path)


def read_json(path, default=None):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------- raw day files
def load_day(date):
    """{"date", "runs": [...], "jobs": [...]} for a day; an empty shell if nothing was fetched yet."""
    return read_json(paths.raw_file(date), {"date": date, "runs": [], "jobs": []})


def save_day(day):
    write_json(paths.raw_file(day["date"]), day)


def raw_dates():
    return sorted(p.stem for p in paths.RAW_DIR.glob("????-??-??.json"))


def find_jobs(keys, date=None, lookback_days=7):
    """Look jobs up by key in the given day's raw file, or in the most recent days."""
    wanted, found = set(keys), {}
    dates = [date] if date else raw_dates()[-lookback_days:][::-1]
    for d in dates:
        for job in load_day(d)["jobs"]:
            if job["key"] in wanted and job["key"] not in found:
                found[job["key"]] = dict(job, found_on=d)
        if len(found) == len(wanted):
            break
    return found


# ---------------------------------------------------------------- seen store
class Seen:
    """Every job key and fingerprint ever fetched, with the date it was first seen.

    keys          stops the same advert being fetched twice
    fingerprints  stops a repost (new id, same company + title) or the same job on
                  another site being treated as new within `repost_window_days`
    """

    def __init__(self, window_days):
        data = read_json(paths.SEEN_FILE, {"keys": {}, "fingerprints": {}})
        self.keys = data["keys"]
        self.fingerprints = data["fingerprints"]
        self.window = dt.timedelta(days=window_days)

    def has_key(self, key):
        return key in self.keys

    def repost_of(self, fp, today):
        """Date the same job was first seen, if that was inside the repost window."""
        first = self.fingerprints.get(fp)
        if first and dt.date.fromisoformat(today) - dt.date.fromisoformat(first) <= self.window:
            return first
        return None

    def add(self, key, fp, date):
        self.keys.setdefault(key, date)
        if fp:
            old = self.fingerprints.get(fp)
            # restart the window when a job reappears after it expired
            if not old or dt.date.fromisoformat(date) - dt.date.fromisoformat(old) > self.window:
                self.fingerprints[fp] = date

    def save(self):
        write_json(paths.SEEN_FILE, {"keys": self.keys, "fingerprints": self.fingerprints})
