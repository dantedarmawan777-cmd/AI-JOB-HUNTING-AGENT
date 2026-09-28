"""
Unit tests for Core modules (Logger, Models, Database).
"""

import asyncio
import os
import tempfile
from pathlib import Path
import pytest

from src.core.logger import get_logger
from src.core.models import (
    ApplicationStatus,
    Job,
    MatchResult,
    PlatformEnum,
    ScreeningQuestion,
    ScreeningQuestionType,
)
from src.core.database import Database


def test_logger() -> None:
    logger = get_logger("test_module")
    assert logger is not None
    logger.info("Test log info message")
    logger.debug("Test log debug message")


def test_job_model_id_generation() -> None:
    job = Job(
        platform=PlatformEnum.JOBSTREET,
        title="Senior Credit Risk Manager",
        company="PT Bank Maybank Indonesia",
        location="Jakarta",
        url="https://id.jobstreet.com/id/job/123456",
        salary="IDR 25.000.000 - 35.000.000",
    )
    assert job.id.startswith("job_")
    assert job.status == ApplicationStatus.DISCOVERED
    assert job.cv_language == "EN"


@pytest.mark.asyncio
async def test_database_crud() -> None:
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp_dir:
        db_path = Path(tmp_dir) / "test_jobs.db"
        test_db = Database(db_path=db_path)
        await test_db.init_async()

        # 1. Create Job
        job = Job(
            platform=PlatformEnum.GLINTS,
            title="Commercial Credit Underwriter",
            company="Aspire SEA",
            location="Jakarta",
            url="https://glints.com/id/opportunities/jobs/test-underwriter",
            salary="IDR 30,000,000",
            description="Underwriting SME and commercial loan portfolios.",
            status=ApplicationStatus.SHORTLISTED,
            match_result=MatchResult(
                score=92,
                reasoning="Perfect fit for SME underwriting.",
                matching_points=["Underwriting", "Commercial banking"],
                missing_points=[],
            ),
            screening_questions=[
                ScreeningQuestion(
                    question="Years of credit experience?",
                    question_type=ScreeningQuestionType.NUMBER,
                    answer="15",
                )
            ],
        )

        saved_job = await test_db.save_job(job)
        assert saved_job.id == job.id

        # 2. Query Job
        fetched_job = await test_db.get_job_by_id(job.id)
        assert fetched_job is not None
        assert fetched_job.title == "Commercial Credit Underwriter"
        assert fetched_job.match_result is not None
        assert fetched_job.match_result.score == 92
        assert len(fetched_job.screening_questions) == 1
        assert fetched_job.screening_questions[0].answer == "15"

        # 3. Check Duplicate Exists
        assert await test_db.job_exists(job.url) is True
        assert await test_db.job_exists("https://unknown-url.com") is False

        # 4. Update Status with Audit Log
        updated = await test_db.update_job_status(
            job.id,
            ApplicationStatus.APPROVED,
            notes="Approved by user in HITL test",
        )
        assert updated is True

        job_after_update = await test_db.get_job_by_id(job.id)
        assert job_after_update.status == ApplicationStatus.APPROVED

        # 5. Check Pending Approvals and Stats
        pending = await test_db.get_pending_approvals()
        assert len(pending) == 0  # Since it was approved

        approved = await test_db.get_approved_jobs()
        assert len(approved) == 1

        stats = await test_db.get_statistics()
        assert stats["total"] == 1
        assert stats["by_status"]["approved"] == 1
        assert stats["by_platform"]["glints"] == 1
        assert stats["avg_match_score"] == 92.0


if __name__ == "__main__":
    test_logger()
    test_job_model_id_generation()
    asyncio.run(test_database_crud())
    print("All core tests passed!")
