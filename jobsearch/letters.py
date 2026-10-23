"""Cover letters as Word files in output/Cover Letters/<date>/, and the weekly clean-up.

Rotation: once the oldest dated folder is 7+ days old, every dated folder except today's is
emptied into "Previous Cover Letters" as "<date> - <file name>". ALL files move (the .docx
and any PDF saved next to it), nothing is deleted, and the tracker links are updated.
"""
import datetime as dt
import hashlib
import json
import re
import shutil
import unicodedata

from docx import Document
from docx.shared import Cm, Pt

from . import config, paths

ROTATE_AFTER_DAYS = 7
MANIFEST = ".letters.json"
_DATED = re.compile(r"\d{4}-\d{2}-\d{2}")


def file_name(job):
    """'<title> - <company>.docx', ASCII-safe so the Excel links never break."""
    name = f"{job['title']} - {job['company']}"
    name = name.replace("–", "-").replace("—", "-").replace("’", "'")
    name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    name = re.sub(r'[\\/:*?"<>|]+', "", name)
    return re.sub(r"\s+", " ", name).strip()[:120] + ".docx"


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save_all(date, picks):
    """Write every pick's letter. -> {job key: path relative to output/}.

    A letter already edited by hand in Word is never overwritten: the build remembers the hash
    of each file it wrote (in .letters.json) and only replaces files that still match.
    """
    folder = paths.LETTERS_DIR / date
    folder.mkdir(parents=True, exist_ok=True)
    manifest_file = folder / MANIFEST
    manifest = json.loads(manifest_file.read_text(encoding="utf-8")) if manifest_file.exists() else {}
    links, kept = {}, []
    for job in picks:
        path = folder / file_name(job)
        if path.exists() and manifest.get(path.name) != _sha(path):
            kept.append(path.name)
        else:
            _write_docx(path, job["cover_letter"])
            manifest[path.name] = _sha(path)
        links[job["key"]] = path.relative_to(paths.OUTPUT_DIR).as_posix()
    manifest_file.write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    for name in kept:
        print(f"Kept the existing letter (edited by hand or made earlier; delete it to regenerate): {name}")
    return links


def _write_docx(path, letter):
    doc = Document()
    for section in doc.sections:
        section.left_margin = section.right_margin = Cm(2.5)
        section.top_margin = section.bottom_margin = Cm(2.2)
    normal = doc.styles["Normal"]
    normal.font.name, normal.font.size = "Calibri", Pt(11)
    normal.paragraph_format.space_after = Pt(8)
    for para in re.split(r"\n\s*\n", letter.strip()):
        doc.add_paragraph(re.sub(r"\s*\n\s*", " ", para.strip()))
    signature = config.settings()["candidate"]["signature"]
    sign = doc.add_paragraph(signature[0])
    sign.paragraph_format.space_after = Pt(0)
    for line in signature[1:]:
        doc.add_paragraph(line).paragraph_format.space_after = Pt(0)
    doc.save(path)


def rotate(today):
    """Move old dated folders into Previous Cover Letters. -> {old relative path: new relative path}."""
    root, prev = paths.LETTERS_DIR, paths.PREVIOUS_LETTERS_DIR
    if not root.exists():
        return {}
    dated = sorted(p for p in root.iterdir() if p.is_dir() and _DATED.fullmatch(p.name) and p.name != today)
    if not dated or (dt.date.fromisoformat(today) - dt.date.fromisoformat(dated[0].name)).days < ROTATE_AFTER_DAYS:
        return {}
    prev.mkdir(parents=True, exist_ok=True)
    moved = {}
    for folder in dated:
        (folder / MANIFEST).unlink(missing_ok=True)
        for f in sorted(folder.rglob("*")):
            if not f.is_file():
                continue
            target = prev / f"{folder.name} - {f.name}"
            n = 2
            while target.exists():
                target = prev / f"{folder.name} - {f.stem} ({n}){f.suffix}"
                n += 1
            shutil.move(str(f), str(target))
            moved[f.relative_to(paths.OUTPUT_DIR).as_posix()] = target.relative_to(paths.OUTPUT_DIR).as_posix()
        if not any(p.is_file() for p in folder.rglob("*")):
            shutil.rmtree(folder)
    print(f"Moved {len(moved)} files from {len(dated)} dated folders into 'Previous Cover Letters'")
    return moved
