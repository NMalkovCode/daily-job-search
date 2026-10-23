"""Runs every enabled source, drops jobs already seen (or reposted, or found on another site)
and saves the new ones to data/raw/<today>.json.

Progress is saved every 20 jobs, so an interrupted run loses almost nothing: running
`fetch` again the same day resumes where it stopped (already-saved jobs are skipped).
"""
import datetime as dt
import traceback

from . import config, paths
from .filters import Filters
from .log import Log
from .sources import SOURCES, missing_secrets
from .store import Seen, load_day, save_day
from .textutil import fingerprint

SAVE_EVERY = 20


class Context:
    """What a source needs: its settings, keys, and `wanted()` to skip jobs before costly requests."""

    def __init__(self, name, settings, filters, seen, day, by_fp, log):
        self.name = name
        self.settings = settings
        self.cfg = settings["sources"].get(name, {})
        self.secrets = config.secrets()
        self.regions = settings["regions"]
        self.filters = filters
        self.seen = seen
        self.date = day["date"]
        self.by_fp = by_fp
        self.log = log
        self.stats = {"new": 0, "seen": 0, "duplicate": 0, "title": 0, "region": 0}

    def wanted(self, key, title, company, region, link=""):
        """True if the job is new, in a target country and has a relevant title."""
        if region not in self.regions:
            self.stats["region"] += 1
            return False
        if self.seen.has_key(key):
            self.stats["seen"] += 1
            return False
        if not self.filters.title_ok(title):
            self.stats["title"] += 1
            return False
        fp = fingerprint(company, title, region)
        if self.seen.repost_of(fp, self.date):
            self.stats["duplicate"] += 1
            original = self.by_fp.get(fp)
            if original is not None and link and all(a["key"] != key for a in original["also_on"]):
                original["also_on"].append({"source": self.name, "key": key, "link": link})
            return False
        return True


def run(again=False, only=None):
    settings = config.settings()
    date = paths.today()
    log = Log(date)
    day = load_day(date)
    if day["runs"] and day["runs"][-1].get("finished") and not again:
        log(f"Already fetched today ({len(day['jobs'])} jobs in data/raw/{date}.json). "
            f"Use `fetch --again` to look for jobs posted since then.")
        return day

    seen = Seen(settings["dedupe"]["repost_window_days"])
    filters = Filters(settings)
    by_fp = {j["fingerprint"]: j for j in day["jobs"]}
    run_info = {"started": dt.datetime.now().isoformat(timespec="seconds"), "finished": None, "sources": {}}
    day["runs"].append(run_info)

    for name, module in SOURCES.items():
        cfg = settings["sources"].get(name, {})
        if (only and name not in only) or not cfg.get("enabled", False):
            continue
        missing = missing_secrets(module, config.secrets())
        if missing:
            log(f"[{name}] skipped: no API key ({', '.join(missing)} in config/secrets.json)")
            run_info["sources"][name] = {"skipped": "no API key"}
            continue
        log(f"[{name}] fetching...")
        ctx = Context(name, settings, filters, seen, day, by_fp, log)
        error = None
        try:
            for job in module.fetch(ctx):
                twin = by_fp.get(job["fingerprint"])
                if twin is not None:  # same job twice in one run (e.g. two ids on one site)
                    twin["also_on"].append({"source": name, "key": job["key"], "link": job["link"]})
                    seen.add(job["key"], None, date)
                    ctx.stats["duplicate"] += 1
                    continue
                day["jobs"].append(job)
                by_fp[job["fingerprint"]] = job
                seen.add(job["key"], job["fingerprint"], date)
                ctx.stats["new"] += 1
                if ctx.stats["new"] % SAVE_EVERY == 0:
                    save_day(day)
                    seen.save()
        except KeyboardInterrupt:
            save_day(day)
            seen.save()
            log("Interrupted - progress saved. Run fetch again to continue.")
            raise
        except Exception as e:  # one broken source must not stop the others
            error = f"{type(e).__name__}: {e}"
            log(f"[{name}] ERROR {error}")
            log.write(traceback.format_exc())
        save_day(day)
        seen.save()
        run_info["sources"][name] = dict(ctx.stats, error=error)
        s = ctx.stats
        log(f"[{name}] {s['new']} new | skipped: {s['seen']} seen before, {s['duplicate']} duplicates/reposts, "
            f"{s['title']} irrelevant titles, {s['region']} other countries")

    run_info["finished"] = dt.datetime.now().isoformat(timespec="seconds")
    save_day(day)
    log(f"Saved {len(day['jobs'])} jobs -> data/raw/{date}.json")
    return day
