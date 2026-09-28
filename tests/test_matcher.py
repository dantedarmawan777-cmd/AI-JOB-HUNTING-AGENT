"""
Unit tests for JobMatcher and MatcherEngine modules.
"""

from datetime import datetime, timezone
import pytest
from src.core.models import Job, ApplicationStatus, PlatformEnum
from src.matcher.matcher import JobMatcher, default_matcher
from src.matcher.profile_loader import load_candidate_profile, get_cv_path_for_language


@pytest.fixture
def matcher():
    return JobMatcher()


def test_candidate_profile_loading():
    profile = load_candidate_profile()
    assert profile.full_name == "Aditya Darmawan"
    assert profile.email == "dantedarmawan@yahoo.com"
    assert profile.phone == "+62 811-599-4948"
    assert profile.total_years_experience == 15
    assert len(profile.experience) >= 4

    # Test CV resolution
    cv_en = get_cv_path_for_language("EN", profile)
    assert cv_en is not None
    assert "EN" in str(cv_en)

    cv_id = get_cv_path_for_language("ID", profile)
    assert cv_id is not None
    assert "ID" in str(cv_id)


def test_strong_credit_risk_and_fintech_match(matcher):
    job = Job(
        platform=PlatformEnum.JOBSTREET,
        title="Senior Credit Risk Underwriting Specialist",
        company="Fintech SEA Capital",
        location="Jakarta",
        description="""
        We are seeking a Senior Credit Risk Specialist with extensive background in SME lending and digital underwriting.
        Responsibilities:
        - Perform financial statement analysis, cash flow verification, and DSCR debt capacity modeling.
        - Formulate, calibrate, and monitor risk scorecards for digital SME credit products.
        - Collaborate with product and engineering teams on automated risk decisioning engines.
        - Implement early warning systems to mitigate delinquency and minimize portfolio NPL rates.
        Requirements:
        - 5-10+ years of experience in credit underwriting, commercial banking, or digital FinTech lending.
        - Proven track record in structuring working capital facilities and borrower due diligence.
        """,
        url="https://jobstreet.co.id/job/cr-101",
        salary="IDR 25,000,000 - 35,000,000",
    )

    result = matcher.calculate_match(job)
    assert result.score >= 75, f"Expected match score >= 75, got {result.score}"
    assert result.recommended_action == "APPLY"
    assert len(result.matching_points) >= 3

    # Verify 2-sentence rationale structure
    sentences = [s.strip() for s in result.reasoning.split(".") if s.strip()]
    assert len(sentences) == 2, f"Rationale must be exactly 2 sentences, got {len(sentences)}: {result.reasoning}"
    assert "Aditya" in result.reasoning
    assert "Aspire SEA" in result.reasoning or "Maybank" in result.reasoning


def test_commercial_banking_sme_match(matcher):
    job = Job(
        platform=PlatformEnum.GLINTS,
        title="Commercial Banking Relationship Manager",
        company="PT Bank Danamon Indonesia, Tbk",
        location="Balikpapan",
        description="""
        Manage and grow SME and commercial banking loan portfolios.
        - Underwrite and structure working capital, trade finance, and term loan facilities.
        - Conduct on-site borrower due diligence, collateral appraisal, and legal perfection (Hak Tanggungan).
        - Prepare credit memorandums for regional credit committee presentations.
        - Monitor covenant compliance and prevent delinquency.
        """,
        url="https://glints.com/id/opportunities/jobs/sme-202",
        salary_min=25_000_000,
        salary_max=32_000_000,
    )

    result = matcher.calculate_match(job)
    assert result.score >= 75
    assert result.recommended_action == "APPLY"
    assert "Maybank" in result.reasoning or "commercial" in result.reasoning.lower()


def test_unrelated_job_low_score(matcher):
    job = Job(
        platform=PlatformEnum.KALIBRR,
        title="Senior Frontend React Engineer",
        company="Tech Corp",
        location="Jakarta",
        description="""
        Build beautiful user interfaces using React, TypeScript, Next.js, and Tailwind CSS.
        Experience with Redux, GraphQL, and Webpack is required.
        """,
        url="https://kalibrr.com/job/fe-303",
    )

    result = matcher.calculate_match(job)
    assert result.score < 50
    assert result.recommended_action == "SKIP"


def test_blacklisted_job_zero_score(matcher):
    job = Job(
        platform=PlatformEnum.JOBSTREET,
        title="Fresh Graduate Admin Kredit",
        company="PT Pinjol Ilegal",
        location="Jakarta",
        description="Tanpa pengalaman, bunga harian 2% tanpa BI checking.",
        url="https://jobstreet.co.id/job/bad-404",
    )

    result = matcher.calculate_match(job)
    assert result.score == 0
    assert result.recommended_action == "SKIP"
    assert "Excluded by safety filter" in result.reasoning


def test_match_and_update_job(matcher):
    job = Job(
        platform=PlatformEnum.LINKEDIN,
        title="Head of Credit Policy & Underwriting",
        company="SEA Digital Bank",
        location="Jakarta",
        description="""
        Lead credit policy and underwriting scorecards for digital SME lending and commercial products.
        Deep expertise in credit risk, financial spreading, DSCR, and team leadership required.
        10+ years experience.
        """,
        url="https://linkedin.com/jobs/view/999",
    )

    updated_job = matcher.match_and_update_job(job)
    assert updated_job.status == ApplicationStatus.SHORTLISTED
    assert updated_job.match_result is not None
    assert updated_job.match_result.score >= 75
