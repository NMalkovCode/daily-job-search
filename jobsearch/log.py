"""Print to the console and append to data/logs/<date>.log."""
import datetime as dt

from . import paths


class Log:
    def __init__(self, date):
        paths.LOG_DIR.mkdir(parents=True, exist_ok=True)
        self.file = paths.LOG_DIR / f"{date}.log"

    def __call__(self, message):
        print(message, flush=True)
        self.write(f"{dt.datetime.now():%H:%M:%S} {message}")

    def write(self, text):
        with self.file.open("a", encoding="utf-8") as f:
            f.write(text.rstrip() + "\n")
