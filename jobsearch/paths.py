"""Every file and folder the project reads or writes, in one place."""
import datetime as dt
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

CONFIG_DIR = ROOT / "config"
SETTINGS_FILE = CONFIG_DIR / "settings.json"  # your copies of the *.example files (setup creates them)
SECRETS_FILE = CONFIG_DIR / "secrets.json"
PROFILE_FILE = CONFIG_DIR / "profile.md"

DATA_DIR = ROOT / "data"
RAW_DIR = DATA_DIR / "raw"          # raw/<date>.json      - everything fetched that day
TRIAGE_DIR = DATA_DIR / "triage"    # triage/<date>.txt    - ranked shortlist for the AI
SCORED_DIR = DATA_DIR / "scored"    # scored/<date>.json   - the AI's picks and cover letters
STATE_DIR = DATA_DIR / "state"
SEEN_FILE = STATE_DIR / "seen.json"  # every job ever fetched, for de-duplication
BACKUP_DIR = DATA_DIR / "backups"   # tracker copies made before each build
LOG_DIR = DATA_DIR / "logs"

OUTPUT_DIR = ROOT / "output"
TRACKER_FILE = OUTPUT_DIR / "Job Tracker.xlsx"
LETTERS_DIR = OUTPUT_DIR / "Cover Letters"
PREVIOUS_LETTERS_DIR = LETTERS_DIR / "Previous Cover Letters"


def today():
    return dt.date.today().isoformat()


def raw_file(date):
    return RAW_DIR / f"{date}.json"


def triage_file(date):
    return TRIAGE_DIR / f"{date}.txt"


def scored_file(date):
    return SCORED_DIR / f"{date}.json"
