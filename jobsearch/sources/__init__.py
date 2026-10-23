"""Job sources. Each module has NAME, PREFIX (start of the job key), NEEDS (secret names)
and fetch(ctx) -> iterator of job dicts (see store.make_job).

Order matters: when the same job is on several sites, the first source to save it owns the
record and later ones are added to its `also_on`. Employer boards go first so the main link
points at the employer's own advert; sources with full descriptions (Reed, LinkedIn) come
before the aggregators that only give a snippet (Adzuna, Jooble).
"""
from . import adzuna, ats, jooble, linkedin, reed

SOURCES = {m.NAME: m for m in (ats, reed, linkedin, adzuna, jooble)}


def missing_secrets(module, secrets):
    return [name for name in getattr(module, "NEEDS", ()) if not secrets.get(name)]
