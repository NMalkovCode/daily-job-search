"""Command line: .venv/Scripts/python -m jobsearch <command> [options]

  fetch [--again] [--only a,b]   collect new jobs from all sources -> data/raw/<today>.json
  triage [DATE]                  hard filters + ranking -> data/triage/<DATE>.txt
  daily                          fetch (if not done today) + triage: the scripted half of the day
  show KEY [KEY ...] [--date D]  print full adverts for the AI to read
  validate [DATE]                check data/scored/<DATE>.json (the AI's picks)
  build [DATE]                   validate, write cover letters, update the Excel tracker
  status                         what has been done today, follow-ups due
  doctor                         check the installation, keys, CV files
DATE defaults to today (YYYY-MM-DD).
"""
import argparse
import sys

from . import commands


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):  # Windows consoles default to cp1252
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    p = argparse.ArgumentParser(prog="jobsearch", description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    sub = p.add_subparsers(dest="command", required=True)
    f = sub.add_parser("fetch")
    f.add_argument("--again", action="store_true", help="fetch again even if today's fetch finished")
    f.add_argument("--only", help="comma-separated source names, e.g. linkedin,ats")
    for name in ("triage", "validate", "build"):
        sub.add_parser(name).add_argument("date", nargs="?")
    sub.add_parser("daily")
    s = sub.add_parser("show")
    s.add_argument("keys", nargs="+")
    s.add_argument("--date")
    s.add_argument("--chars", type=int, default=6000, help="max description length per job")
    sub.add_parser("status")
    sub.add_parser("doctor")
    args = p.parse_args(argv)
    return commands.run(args)


if __name__ == "__main__":
    sys.exit(main())
