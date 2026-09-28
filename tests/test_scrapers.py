"""
Unit tests for Scrapers (JobStreet, Glints, Kalibrr, Base).
"""

import pytest
from src.core.models import PlatformEnum
from src.scrapers.base import BaseScraper
from src.scrapers.jobstreet import JobStreetScraper
from src.scrapers.glints import GlintsScraper
from src.scrapers.kalibrr import KalibrrScraper


def test_salary_parser() -> None:
    # Test Indonesian Rupiah ranges
    raw, s_min, s_max, curr = BaseScraper.parse_salary("IDR 25.000.000 - 35.000.000 per month")
    assert s_min == 25000000.0
    assert s_max == 35000000.0
    assert curr == "IDR"

    # Test abbreviation (jt)
    raw, s_min, s_max, curr = BaseScraper.parse_salary("Rp 20 jt - 30 jt")
    assert s_min == 20000000.0
    assert s_max == 30000000.0
    assert curr == "IDR"

    # Test SGD
    raw, s_min, s_max, curr = BaseScraper.parse_salary("SGD 6,000 - 8,500")
    assert s_min == 6000.0
    assert s_max == 8500.0
    assert curr == "SGD"

    # Test None/empty
    raw, s_min, s_max, curr = BaseScraper.parse_salary("")
    assert s_min is None
    assert s_max is None


def test_jobstreet_api_parser() -> None:
    scraper = JobStreetScraper()
    mock_api_items = [
        {
            "id": "7891011",
            "title": "Senior Credit Risk Analyst",
            "advertiser": {"description": "PT FinTech Nusantara"},
            "locationHierarchy": {"city": "Jakarta Pusat"},
            "salary": "IDR 28.000.000 - 38.000.000",
            "listingDate": "2026-09-20",
            "teaser": "Seeking experienced credit risk analyst with commercial banking background.",
            "bulletPoints": [
                "Underwriting SME loan applications",
                "DSCR and financial spreading analysis",
            ],
            "workType": "Full-time",
        }
    ]

    jobs = scraper._parse_api_jobs(mock_api_items)
    assert len(jobs) == 1
    job = jobs[0]
    assert job.title == "Senior Credit Risk Analyst"
    assert job.company == "PT FinTech Nusantara"
    assert job.location == "Jakarta Pusat"
    assert job.platform == PlatformEnum.JOBSTREET
    assert job.salary_min == 28000000.0
    assert job.salary_max == 38000000.0
    assert "Underwriting SME loan applications" in job.description


def test_glints_parser() -> None:
    scraper = GlintsScraper()
    mock_glints_items = [
        {
            "id": "glints-12345",
            "title": "Head of Credit Underwriting",
            "company": {"name": "PT Modal Pintar Indonesia"},
            "cities": [{"name": "Jakarta"}],
            "country": {"name": "Indonesia"},
            "minSalary": 35000000,
            "maxSalary": 45000000,
            "currency": "IDR",
            "isRemote": True,
            "slug": "head-of-credit-underwriting-glints-12345",
            "description": "<p>Lead underwriting team for business term loans and credit lines.</p>",
            "createdAt": "2026-09-22T08:00:00Z",
        }
    ]

    jobs = scraper._parse_glints_jobs(mock_glints_items)
    assert len(jobs) == 1
    job = jobs[0]
    assert job.title == "Head of Credit Underwriting"
    assert job.company == "PT Modal Pintar Indonesia"
    assert "Remote" in job.location
    assert job.platform == PlatformEnum.GLINTS
    assert job.salary_min == 35000000.0
    assert job.salary_max == 45000000.0
    assert "Lead underwriting team" in job.description


def test_kalibrr_parser() -> None:
    scraper = KalibrrScraper()
    mock_kalibrr_items = [
        {
            "id": 99887,
            "name": "Commercial Banking Relationship Manager",
            "company_name": "PT Bank Mega Tbk",
            "company_slug": "bank-mega",
            "slug": "commercial-banking-relationship-manager-99887",
            "google_location": {"address_components": {"city": "Tarakan"}},
            "salary_min": 22000000,
            "salary_max": 30000000,
            "salary_currency": "IDR",
            "job_description": "Managing commercial loan portfolios and borrower due diligence.",
            "qualifications": "Bachelor degree, minimum 5 years experience.",
        }
    ]

    jobs = scraper._parse_kalibrr_jobs(mock_kalibrr_items)
    assert len(jobs) == 1
    job = jobs[0]
    assert job.title == "Commercial Banking Relationship Manager"
    assert job.company == "PT Bank Mega Tbk"
    assert job.location == "Tarakan"
    assert job.platform == PlatformEnum.KALIBRR
    assert "borrower due diligence" in job.description


def test_linkedin_parser() -> None:
    from src.scrapers.linkedin import LinkedInScraper
    scraper = LinkedInScraper()
    assert scraper.platform == PlatformEnum.LINKEDIN
    assert scraper.name == "LinkedIn"


if __name__ == "__main__":
    test_salary_parser()
    test_jobstreet_api_parser()
    test_glints_parser()
    test_kalibrr_parser()
    test_linkedin_parser()
    print("All scraper tests passed!")

