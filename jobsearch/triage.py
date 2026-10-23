"""Hard filters + ranking -> data/triage/<date>.txt, the compact list the AI reads first.

The points only decide the ORDER of the list (best guesses on top, so the AI reads less);
the AI makes the actual choice. Weights are in config/settings.json -> "triage".
"""
import re
from collections import Counter

from . import config, paths
from .filters import Filters
from .store import load_day
from .textutil import clip, parse_salary, salary_label

LEGEND = """\
# Columns: points | key | DIRECT/AGENCY | title | company | location | yrs (min. experience asked) |
#          salary (as advertised; meets/below = vs target) | flags | posted | sources | opening of the advert
# Read a full advert:  .venv/Scripts/python -m jobsearch show <key> [<key> ...]"""


def _salary_verdict(sal, job, targets):
    """'meets' / 'below' / '' when it cannot be told.

    targets: [{"currency", "per_year", optional "region", optional "location"}], first match wins,
    so put city-specific targets before the general one for the same currency.
    """
    if not sal:
        return ""
    yearly = sal["high"] * (12 if sal["period"] == "month" else 1)
    loc = job["location"].lower()
    for t in targets:
        if t.get("currency") != sal["currency"] or t.get("region", job["region"]) != job["region"]:
            continue
        if t.get("location") and t["location"].lower() not in loc:
            continue
        return "meets" if yearly >= t["per_year"] else "below"
    return ""


def _points(job, agency, flags, verdict, cfg):
    title, loc = job["title"].lower(), job["location"].lower()
    p = sum(w for word, w in cfg["title_points"].items() if re.search(word, title))
    p += max([w for city, w in cfg["city_points"].items() if city in loc] or [0])
    p += sum(cfg["flag_points"].get(f, 0) for f in flags)
    p += cfg["agency_points"] if agency else 0
    p += cfg["salary_points"].get(verdict, 0)
    return round(p, 1)


def analyse(date):
    """Rows for every job that passes the hard filters (best first) and the rejection counts."""
    settings = config.settings()
    cfg, filters = settings["triage"], Filters(settings)
    rows, rejected = [], Counter()
    for job in load_day(date)["jobs"]:
        reason = filters.reject_reason(job)
        if reason:
            rejected[reason.split(":")[0]] += 1
            continue
        agency, flags = filters.is_agency(job), filters.flags(job)
        sal = parse_salary(job.get("salary")) or parse_salary(job.get("description"))
        verdict = _salary_verdict(sal, job, cfg["salary_targets"])
        rows.append({
            "job": job, "agency": agency, "flags": flags, "years": filters.required_years(job.get("description")),
            "salary": salary_label(sal) + (f" ({verdict})" if verdict else ""),
            "points": _points(job, agency, flags, verdict, cfg),
        })
    rows.sort(key=lambda r: -r["points"])
    return rows, rejected


def _line(r, snippet_chars):
    j = r["job"]
    sources = ",".join([j["source"]] + [a["source"] for a in j.get("also_on", [])])
    seniority = (j.get("details") or {}).get("seniority", "")
    fields = [
        f"{r['points']:>4}", j["key"], "AGENCY" if r["agency"] else "DIRECT", j["title"], j["company"],
        j["location"], f"yrs:{r['years'] if r['years'] is not None else '-'}", f"sal:{r['salary'] or '-'}",
        f"flags:{','.join(r['flags']) or '-'}" + (f",seniority={seniority}" if seniority else ""),
        f"posted:{j.get('posted') or '-'}", sources, clip(j.get("description"), snippet_chars),
    ]
    return " | ".join(f.replace("|", "/") for f in fields)  # "|" separates columns


def write(date):
    cfg = config.settings()["triage"]
    rows, rejected = analyse(date)
    total = len(rows) + sum(rejected.values())
    top, rest = rows[: cfg["top_n"]], rows[cfg["top_n"]:]
    lines = [
        f"# Triage {date}: {len(rows)} of {total} jobs pass the hard filters; top {len(top)} in full, the rest as one-liners.",
        "# Rejected by hard filters: " + (", ".join(f"{k} {v}" for k, v in rejected.most_common()) or "none"),
        LEGEND, "",
    ]
    lines += [_line(r, cfg["snippet_chars"]) for r in top]
    if rest:
        lines += ["", f"## Below the cut ({len(rest)}): points | key | D/A | title | company | location"]
        lines += [f"{r['points']:>4} | {r['job']['key']} | {'A' if r['agency'] else 'D'} | {r['job']['title']} | "
                  f"{r['job']['company']} | {r['job']['location']}" for r in rest]
    out = paths.triage_file(date)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"{len(rows)} of {total} jobs kept -> data/triage/{date}.txt "
          f"(rejected: {dict(rejected.most_common()) or 'none'})")
    return out
