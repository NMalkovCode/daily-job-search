"""Text helpers: normalising names for de-duplication, region detection, salary parsing."""
import re
import unicodedata

from bs4 import BeautifulSoup

# Words that do not change which job it is ("Analyst - Hybrid" == "Analyst").
_TITLE_NOISE = {
    "hybrid", "remote", "onsite", "on", "site", "full", "time", "fulltime", "part", "permanent",
    "contract", "temporary", "fixed", "term", "ftc", "m", "f", "d", "x", "w", "uk", "uae", "the",
    "job", "role", "position", "opportunity", "immediate", "start", "urgent", "hiring",
}
_COMPANY_SUFFIXES = {
    "ltd", "limited", "plc", "llc", "l", "c", "llp", "inc", "incorporated", "corp", "corporation",
    "co", "company", "gmbh", "ag", "sa", "bv", "fz", "fze", "fzco", "fzc", "fzllc", "dmcc", "pjsc",
    "group", "holding", "holdings", "uk", "uae", "me", "middle", "east", "international", "global",
    "the", "in",
}
_CITY_WORDS = {"london", "dubai", "abu", "dhabi", "manchester", "birmingham", "edinburgh", "glasgow",
               "leeds", "bristol", "sharjah", "england", "scotland"}

# Countries the region detection knows: name -> (ISO code, regex of the name and its main cities).
# settings.json -> "regions" lists the ones to search. A country missing here still works (its own
# name is matched), and settings.json -> "region_patterns" can add or override a pattern.
COUNTRIES = {
    "United Kingdom": ("gb", r"united kingdom|\buk\b|\bgbr?\b|great britain|england|scotland|wales|northern ireland|"
                             r"london|manchester|birmingham|edinburgh|glasgow|leeds|bristol|liverpool|sheffield|"
                             r"cambridge|oxford|reading|nottingham|newcastle|cardiff|belfast|southampton|"
                             r"milton keynes|aberdeen|coventry|leicester|brighton|guildford|surrey|kent|essex|"
                             r"hertfordshire|berkshire|yorkshire|lancashire|hampshire|cheshire"),
    "United Arab Emirates": ("ae", r"united arab emirates|\buae\b|dubai|abu dhabi|sharjah|ajman|ras al|fujairah|"
                                   r"umm al|al ain|emirate"),
    "Ireland": ("ie", r"(?<!northern )\bireland\b|dublin|cork|galway|limerick"),
    "United States": ("us", r"united states|\busa?\b|new york|san francisco|los angeles|chicago|boston|seattle|"
                            r"austin|washington,? d\.?c|atlanta|denver|miami|dallas|houston|philadelphia|"
                            r"san jose|san diego"),
    "Canada": ("ca", r"canada|toronto|vancouver|montreal|ottawa|calgary"),
    "Australia": ("au", r"australia|sydney|melbourne|brisbane|adelaide|canberra"),
    "New Zealand": ("nz", r"new zealand|auckland|wellington|christchurch"),
    "Germany": ("de", r"germany|deutschland|berlin|munich|münchen|hamburg|frankfurt|cologne|köln|stuttgart|"
                      r"düsseldorf"),
    "France": ("fr", r"france|paris|lyon|marseille|toulouse|lille"),
    "Netherlands": ("nl", r"netherlands|nederland|amsterdam|rotterdam|the hague|utrecht|eindhoven"),
    "Switzerland": ("ch", r"switzerland|zurich|zürich|geneva|basel|lausanne"),
    "Spain": ("es", r"spain|españa|madrid|barcelona|valencia"),
    "Singapore": ("sg", r"singapore"),
    "India": ("in", r"\bindia\b|bengaluru|bangalore|mumbai|delhi|hyderabad|pune|chennai|gurugram|gurgaon|noida"),
    "Saudi Arabia": ("sa", r"saudi arabia|\bksa\b|riyadh|jeddah|dammam"),
    "Qatar": ("qa", r"qatar|doha"),
}
_CODE_ALIASES = {"uk": "gb"}


def _settings():
    from . import config  # imported here: config is loaded lazily and only when a region is needed
    return config.settings()


def region_code(region):
    """Two-letter code of a country name ("United Kingdom" -> "gb"); unknown names -> lower-case name."""
    return COUNTRIES.get(region, (None,))[0] or (region or "").lower()


def country_name(code):
    """'ae' / 'GB' / 'uk' -> the country name used in settings.json, or None."""
    code = _CODE_ALIASES.get((code or "").lower(), (code or "").lower())
    return next((name for name, (c, _) in COUNTRIES.items() if c == code), None)


def target_region(code):
    """The searched country with this code (e.g. "gb" for the UK-only APIs), or None if it is not searched."""
    name = country_name(code)
    return name if name in _settings()["regions"] else None


def _words(text):
    text = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode().lower()
    text = text.replace("&", " and ")
    return re.sub(r"[^a-z0-9]+", " ", text).split()


def norm_company(name):
    words = [w for w in _words(name) if w not in _COMPANY_SUFFIXES and w not in _CITY_WORDS]
    return " ".join(words) or " ".join(_words(name))


def norm_title(title):
    title = re.sub(r"\[[^\]]*\]|\([^)]*\)", " ", title or "")  # "[UAE]", "(m/f/d)", "(Hybrid)"
    words = [w for w in _words(title) if w not in _TITLE_NOISE and w not in _CITY_WORDS]
    return " ".join(words) or " ".join(_words(title))


def fingerprint(company, title, region):
    """Same company + same job title + same country = the same job, whichever site it came from."""
    return f"{norm_company(company)}|{norm_title(title)}|{region_code(region)}"


def detect_region(location):
    """Map a free-text location to one of the target countries (settings.json -> regions), or None.

    The countries are tried in the order they are listed in settings.json.
    """
    if not location:
        return None
    settings = _settings()
    extra = settings.get("region_patterns") or {}
    for name in settings["regions"]:
        pattern = extra.get(name) or COUNTRIES.get(name, (None, None))[1] or re.escape(name)
        if re.search(pattern, location, re.I):
            return name
    return None


def html_to_text(html):
    if not html:
        return ""
    text = BeautifulSoup(html, "html.parser").get_text("\n", strip=True)
    return re.sub(r"\n{3,}", "\n\n", text)


def clip(text, n):
    text = re.sub(r"\s+", " ", text or "").strip()
    return text if len(text) <= n else text[: n - 1] + "…"


# ---------------------------------------------------------------- salary
_MONEY = re.compile(
    r"(?P<cur>£|gbp|€|eur|aed|dhs?|\$|usd)\s?(?P<a>\d[\d,]*(?:\.\d+)?)\s?(?P<ak>k)?"
    r"(?:\s?(?:-|–|to)\s?(?:£|gbp|€|eur|aed|dhs?|\$|usd)?\s?(?P<b>\d[\d,]*(?:\.\d+)?)\s?(?P<bk>k)?)?"
    r"(?:\s?(?P<per>per annum|per year|a year|/year|/yr|p\.?a\.?|annually|per month|a month|/month|"
    r"/mo|monthly|pcm))?",
    re.I,
)


def _amount(num, k):
    value = float(num.replace(",", ""))
    return value * 1000 if k else value


def parse_salary(text):
    """First salary found in text -> dict(currency, low, high, period) or None.

    period is "year" or "month"; when the advert does not say, it is guessed from the size.
    """
    for m in _MONEY.finditer(text or ""):
        cur = m.group("cur").lower()
        cur = {"£": "GBP", "gbp": "GBP", "$": "USD", "usd": "USD", "€": "EUR", "eur": "EUR"}.get(cur, "AED")
        low = _amount(m.group("a"), m.group("ak"))
        high = _amount(m.group("b"), m.group("bk")) if m.group("b") else low
        if low < 500 or high < low:  # "£5 voucher", "$1.2bn" etc.
            continue
        per = (m.group("per") or "").lower()
        if "month" in per or per in ("/mo", "pcm"):
            period = "month"
        elif per:
            period = "year"
        elif cur == "AED":  # UAE pay is quoted per month
            period = "month" if high < 80000 else "year"
        elif high < 10000:  # "£7,000 signing bonus", "$500 allowance": not a salary
            continue
        else:
            period = "year"
        return {"currency": cur, "low": low, "high": high, "period": period}
    return None


def salary_label(s):
    if not s:
        return ""
    def fmt(v):
        if v >= 10000:
            return f"{v / 1000:.0f}k"
        return f"{v / 1000:.1f}".rstrip("0").rstrip(".") + "k" if v >= 1000 else f"{v:.0f}"
    rng = fmt(s["low"]) if s["low"] == s["high"] else f"{fmt(s['low'])}-{fmt(s['high'])}"
    return f"{s['currency']} {rng}/{'mo' if s['period'] == 'month' else 'yr'}"
