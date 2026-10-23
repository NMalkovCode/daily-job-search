import pytest

from jobsearch import config
from jobsearch.filters import Filters
from jobsearch.textutil import detect_region, fingerprint, parse_salary, salary_label

F = Filters(config.settings())
UAE, UK = "United Arab Emirates", "United Kingdom"


def j(title="Business Analyst", description="", company="Acme"):
    return {"title": title, "company": company, "description": description}


# ---------------------------------------------------------------- de-duplication keys
@pytest.mark.parametrize("a, b", [
    (("Northwind Capital Group", "Technical Operations & AI Automation Analyst"),
     ("Northwind Capital Group LLC", "Technical Operations and AI Automation Analyst")),
    (("Acme Ltd", "Business Analyst (Hybrid)"), ("ACME Limited", "Business Analyst - Hybrid")),
    (("L'Oréal", "[UAE] Digital Graduate Trainee"), ("L'Oreal", "Digital Graduate Trainee")),
])
def test_same_job_same_fingerprint(a, b):
    assert fingerprint(*a, UAE) == fingerprint(*b, UAE)


def test_different_country_or_role_differs():
    assert fingerprint("Acme", "Analyst", UAE) != fingerprint("Acme", "Analyst", UK)
    assert fingerprint("Acme", "Data Analyst", UK) != fingerprint("Acme", "Pricing Analyst", UK)


@pytest.mark.parametrize("loc, region", [
    ("Dubai, Dubai, United Arab Emirates", UAE), ("Abu Dhabi Emirate", UAE), ("London Area, United Kingdom", UK),
    ("Sheffield (hybrid)", UK), ("Berlin, Germany", None), ("", None),
])
def test_detect_region(loc, region):
    assert detect_region(loc) == region


@pytest.mark.parametrize("text, label", [
    ("Salary: AED 30,000–35,000 per month", "AED 30k-35k/mo"),
    ("£28k - £32k plus bonus", "GBP 28k-32k/yr"),
    ("£55,000 - £60,000 (depending on experience)", "GBP 55k-60k/yr"),
    ("AED 12,000 monthly", "AED 12k/mo"),
    ("a £5 voucher and a $1.2bn fund", ""),
    ("Starting Salary: £5 4 ,000 + £7,000 signing bonus", ""),
    ("£2,500 per month", "GBP 2.5k/mo"),
])
def test_parse_salary(text, label):
    assert salary_label(parse_salary(text)) == label


# ---------------------------------------------------------------- experience
@pytest.mark.parametrize("text, years", [
    ("We need 5+ years of experience in banking.", 5),
    ("3-5 years of relevant experience", 3),
    ("2–4 years' professional experience", 2),
    ("8+ years building production software, including at least 1 year of agentic AI", 8),
    ("Minimum 4 years in consulting", 4),
    ("For over 50 years our firm has led the market. Graduates welcome.", None),
    ("29 days of holiday after 5 years' service", None),
    ("income protection for 5 years if you need it", None),
    ("2+ years of experience required; 5+ years preferred", 2),
    ("Experience: 0-2 years", None),
])
def test_required_years(text, years):
    assert F.required_years(text) == years


# ---------------------------------------------------------------- hard filters
@pytest.mark.parametrize("description, reason", [
    ("This role is open to UAE nationals only.", "nationality"),
    ("Requirements: United Arab Emirates nationality. Business degree.", "nationality"),
    ("As part of our Emiratisation programme we hire graduates.", "nationality"),
    ("Workforce Transformation Analyst [Part of Emiritization]", "nationality"),
    ("Mandatory: Emirati national holding Family Book, registered in NAFIS.", "nationality"),
    ("Fluent in Arabic and English.", "arabic"),
    ("You must hold active SC clearance.", "clearance"),
    ("Candidates must be able to obtain security clearance (SC). We welcome all applicants.", "clearance"),
    ("This is a commission-only role.", "pay"),
    ("Requires 6+ years of experience.", "experience"),
])
def test_rejects(description, reason):
    assert (F.reject_reason(j(description=description)) or "").startswith(reason)


@pytest.mark.parametrize("description", [
    "Arabic is a plus.",
    "No security clearance required.",
    "Generous benefits including our unpaid leave scheme.",
    "UAE nationals are encouraged to apply; open to all nationalities.",
    "Graduate role, 0-1 years of experience.",
])
def test_keeps(description):
    assert F.reject_reason(j(description=description)) is None


@pytest.mark.parametrize("title, ok", [
    ("Graduate Business Analyst", True), ("AI Automation Specialist", True), ("Junior Quantity Surveyor", False),
    ("Senior Data Analyst", False), ("Pricing Insight Lead", False), ("Lead Generation Analyst", True),
    ("Chief Operating Office - Full-Time Analyst", True), ("Chief Analyst", False), ("Финансовый аналитик", True),
    ("Nurse", False), ("Workforce Transformation Analyst [Part of Emiritization]", False),
    ("Junior Consultant – Advisory (UAE Nationals Only)", False),
])
def test_title_filter(title, ok):
    assert F.title_ok(title) is ok


def test_agency_detection():
    assert F.is_agency(j(company="Hays"))
    assert F.is_agency(j(company="Acme", description="Our client is a leading bank in Dubai."))
    assert not F.is_agency(j(company="Deloitte", description="Join our graduate scheme."))


def test_flags():
    flags = F.flags(j(description="Our graduate programme offers visa sponsorship. Python and SQL."))
    assert {"grad-scheme", "visa-offered", "python-sql"} <= set(flags)
