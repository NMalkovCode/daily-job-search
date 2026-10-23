"""One shared HTTP session with polite retries."""
import random
import time

import requests

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/141.0 Safari/537.36",
    "Accept-Language": "en-GB,en;q=0.9",
}
RETRY_STATUS = {429, 500, 502, 503, 504, 999}  # 999 = LinkedIn's "slow down"

_session = None


def session():
    global _session
    if _session is None:
        _session = requests.Session()
        _session.headers.update(HEADERS)
    return _session


def request(method, url, tries=4, backoff=20, **kw):
    """Response on HTTP 200, None on any other final status. Network errors are retried too."""
    kw.setdefault("timeout", 25)
    for attempt in range(tries):
        try:
            r = session().request(method, url, **kw)
        except requests.RequestException:
            r = None
        if r is not None and r.status_code == 200:
            return r
        if r is not None and r.status_code not in RETRY_STATUS:
            return None
        if attempt < tries - 1:
            time.sleep(backoff * (attempt + 1))
    return None


def get(url, **kw):
    return request("GET", url, **kw)


def post(url, **kw):
    return request("POST", url, **kw)


def pause(low, high):
    time.sleep(random.uniform(low, high))
