"""Adzuna API. Free app_id + app_key: https://developer.adzuna.com

Adzuna aggregates many boards and employer sites in the countries below (no UAE). Each target
country it covers is searched. Descriptions are a ~500-character extract; the full advert is
behind `redirect_url`.
"""
from .. import http
from ..store import make_job
from ..textutil import COUNTRIES, html_to_text

NAME, PREFIX, NEEDS = "adzuna", "adz", ("adzuna_app_id", "adzuna_app_key")
SEARCH = "https://api.adzuna.com/v1/api/jobs/{country}/search/{page}"
# country code -> salary prefix (as parse_salary reads it, where it can)
COUNTRY_CURRENCY = {"gb": "£", "us": "$", "de": "€", "fr": "€", "nl": "€", "es": "€", "it": "€", "at": "€",
                    "be": "€", "ca": "CAD ", "au": "AUD ", "nz": "NZD ", "in": "INR ", "sg": "SGD ", "ch": "CHF ",
                    "pl": "PLN ", "br": "BRL ", "mx": "MXN ", "za": "ZAR "}


def _salary(item, cur):
    low, high = item.get("salary_min"), item.get("salary_max")
    if not low or str(item.get("salary_is_predicted")) == "1":
        return ""  # Adzuna's own estimate, not the employer's figure
    return f"{cur}{low:,.0f}" + (f" - {cur}{high:,.0f}" if high and high != low else "") + " per annum"


def fetch(ctx):
    per_page = min(50, ctx.cfg.get("results_per_search", 50))
    for region in ctx.regions:
        country = COUNTRIES.get(region, (None,))[0]
        if country not in COUNTRY_CURRENCY:
            continue
        for query in ctx.settings["searches"]["simple"]:
            r = http.get(SEARCH.format(country=country, page=1), params={
                "app_id": ctx.secrets["adzuna_app_id"], "app_key": ctx.secrets["adzuna_app_key"],
                "what": query, "max_days_old": ctx.cfg.get("max_age_days", 2), "results_per_page": per_page,
                "sort_by": "date", "content-type": "application/json"})
            for item in (r.json().get("results", []) if r else []):
                key = f"{PREFIX}:{item['id']}"
                company = (item.get("company") or {}).get("display_name", "")
                if not ctx.wanted(key, item.get("title"), company, region, item.get("redirect_url", "")):
                    continue
                yield make_job(NAME, PREFIX, item["id"], html_to_text(item.get("title")), company,
                               (item.get("location") or {}).get("display_name", region), region,
                               item.get("redirect_url", ""), description=html_to_text(item.get("description", "")),
                               posted=(item.get("created") or "")[:10],
                               salary=_salary(item, COUNTRY_CURRENCY[country]), query=query)
            http.pause(1, 2)
