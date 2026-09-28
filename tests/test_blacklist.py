"""
Unit tests for BlacklistFilter module.
"""

from datetime import datetime, timezone, timedelta
import pytest

from src.matcher.blacklist import BlacklistFilter, ExclusionResult
from src.core.models import Job, ApplicationStatus, PlatformEnum


@pytest.fixture
def blacklist():
    return BlacklistFilter(max_job_age_days=14)


def test_junior_title_exclusion(blacklist):
    junior_titles = [
        "Fresh Graduate Credit Analyst",
        "Magang Credit Risk",
        "Internship Underwriting",
        "Admin Kredit Cabang Tarakan",
        "Telemarketing Pinjaman",
        "Customer Service Representative",
        "Desk Collection Officer",
        "Junior Staff Administrasi",
        "Entry Level Account Officer",
        "Management Trainee Banking",
    ]

    for title in junior_titles:
        is_jr, reason, pat = blacklist.is_junior_position(title)
        assert is_jr is True, f"Failed to filter out junior title: {title}"
        assert reason is not None
        assert pat is not None


def test_senior_title_allowed(blacklist):
    senior_titles = [
        "Senior Credit Risk Analyst",
        "Head of Underwriting",
        "Credit Risk Manager",
        "Commercial Banking Relationship Manager",
        "SME Lending Specialist",
        "Risk Policy Lead",
    ]

    for title in senior_titles:
        is_jr, reason, _ = blacklist.is_junior_position(title)
        assert is_jr is False, f"Erroneously blacklisted senior title: {title} (reason: {reason})"


def test_senior_title_with_junior_mentions_in_jd(blacklist):
    """A Senior Manager who will mentor interns or junior staff should NOT be excluded."""
    title = "Senior Credit Risk Manager"
    desc = "Responsibilities include mentoring junior staff and guiding interns in credit assessment."
    is_jr, reason, _ = blacklist.is_junior_position(title, desc)
    assert is_jr is False, f"Erroneously excluded senior manager mentoring juniors: {reason}"


def test_predatory_pinjol_exclusion(blacklist):
    bad_companies = [
        "Pinjol Ilegal Sejahtera",
        "Dana Kilat Online",
        "Rupiah Super P2P",
        "Kantong Darurat Finansial",
    ]

    for comp in bad_companies:
        is_pred, reason, _ = blacklist.is_predatory_pinjol(comp)
        assert is_pred is True, f"Failed to blacklist predatory company: {comp}"

    # Test scam descriptions
    scam_descs = [
        "Dibutuhkan analis kredit tanpa BI checking dan tanpa SLIK bunga harian 2%",
        "Lowongan kerja joki pinjol dan jasa hapus data pinjol",
        "Buka rekening bank dapat komisi harian Rp 500rb",
        "Wajib membayar biaya administrasi pelatihan sebelum kerja",
    ]

    for desc in scam_descs:
        is_pred, reason, _ = blacklist.is_predatory_pinjol("PT XYZ Fintech", desc)
        assert is_pred is True, f"Failed to blacklist scam description: {desc}"


def test_legitimate_bank_not_predatory(blacklist):
    legit = [
        ("PT Bank Maybank Indonesia, Tbk", "Commercial banking SME loan origination"),
        ("PT Bank Central Asia, Tbk", "Corporate credit risk evaluation"),
        ("Aspire SEA", "Digital SME business term loan underwriting"),
    ]
    for comp, desc in legit:
        is_pred, reason, _ = blacklist.is_predatory_pinjol(comp, desc)
        assert is_pred is False, f"Erroneously flagged legit entity: {comp}"


def test_posting_age_and_status(blacklist):
    ref_time = datetime(2026, 9, 28, 12, 0, 0, tzinfo=timezone.utc)

    # 1. More than 14 days old (e.g. 15 days ago)
    is_exp, reason, _ = blacklist.is_expired_or_closed(
        posted_date="15 days ago",
        reference_date=ref_time
    )
    assert is_exp is True
    assert "exceeds maximum allowable threshold" in reason

    # 2. 3 weeks ago
    is_exp, reason, _ = blacklist.is_expired_or_closed(
        posted_date="3 weeks ago",
        reference_date=ref_time
    )
    assert is_exp is True

    # 3. Explicit old date
    is_exp, reason, _ = blacklist.is_expired_or_closed(
        posted_date="2026-09-01T00:00:00Z",
        reference_date=ref_time
    )
    assert is_exp is True

    # 4. Fresh posting (3 days ago)
    is_exp, reason, _ = blacklist.is_expired_or_closed(
        posted_date="3 days ago",
        reference_date=ref_time
    )
    assert is_exp is False

    # 5. Closed status
    is_exp, reason, _ = blacklist.is_expired_or_closed(
        status="closed",
        reference_date=ref_time
    )
    assert is_exp is True

    # 6. Description contains closed text
    is_exp, reason, _ = blacklist.is_expired_or_closed(
        description="This job is closed and no longer accepting applications.",
        reference_date=ref_time
    )
    assert is_exp is True


def test_full_job_evaluation(blacklist):
    ref_time = datetime(2026, 9, 28, 12, 0, 0, tzinfo=timezone.utc)

    valid_job = Job(
        platform=PlatformEnum.JOBSTREET,
        title="Senior Credit Analyst",
        company="PT Bank Permata, Tbk",
        location="Jakarta",
        description="Underwrite commercial and SME loan proposals.",
        posted_date="2 days ago",
        url="https://jobstreet.co.id/job/123",
    )
    result = blacklist.evaluate(valid_job, reference_date=ref_time)
    assert result.is_excluded is False

    junior_job = Job(
        platform=PlatformEnum.JOBSTREET,
        title="Telemarketing Kredit",
        company="PT Sales Indo",
        location="Jakarta",
        description="Menawarkan pinjaman via telepon.",
        posted_date="1 day ago",
        url="https://jobstreet.co.id/job/456",
    )
    result_jr = blacklist.evaluate(junior_job, reference_date=ref_time)
    assert result_jr.is_excluded is True
    assert result_jr.category == "junior"
