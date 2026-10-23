"""Loads config/settings.json and API keys (config/secrets.json or environment variables)."""
import json
import os
from functools import lru_cache

from . import paths

# secret name -> environment variable that can be used instead of config/secrets.json
SECRET_ENV = {
    "reed_api_key": "REED_API_KEY",
    "adzuna_app_id": "ADZUNA_APP_ID",
    "adzuna_app_key": "ADZUNA_APP_KEY",
    "jooble_api_key": "JOOBLE_API_KEY",
}


@lru_cache(maxsize=None)
def settings():
    if not paths.SETTINGS_FILE.exists():
        raise FileNotFoundError("config/settings.json not found - run setup (it copies config/settings.example.json), "
                                "or copy that file yourself")
    return json.loads(paths.SETTINGS_FILE.read_text(encoding="utf-8"))


@lru_cache(maxsize=None)
def secrets():
    found = {}
    if paths.SECRETS_FILE.exists():
        found.update(json.loads(paths.SECRETS_FILE.read_text(encoding="utf-8")))
    for name, env in SECRET_ENV.items():
        if os.environ.get(env):
            found[name] = os.environ[env]
    return {k: v for k, v in found.items() if v}


def source_settings(name):
    return settings()["sources"].get(name, {})


def cv_options():
    """{cv id: file path relative to cv_root} from settings.json."""
    return settings()["candidate"]["cvs"]


def cv_path(cv_id):
    root = paths.ROOT / settings()["candidate"].get("cv_root", "cvs")
    return (root / cv_options()[cv_id]).resolve()
