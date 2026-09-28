"""
Unit tests for Telegram HITL messages and keyboard builders.
"""

from src.core.models import Job, MatchResult, PlatformEnum
from src.telegram_hitl.messages import (
    build_job_action_keyboard,
    format_job_alert,
    format_status_message,
)


def test_telegram_message_and_keyboard_formatting() -> None:
    job = Job(
        platform=PlatformEnum.JOBSTREET,
        title="Credit Risk Policy Lead",
        company="PT Bank CIMB Niaga Tbk",
        location="Jakarta",
        salary="IDR 30.000.000 - 42.000.000",
        url="https://id.jobstreet.com/id/job/889900",
        cv_language="EN",
        match_result=MatchResult(
            score=95,
            reasoning="Outstanding fit for Senior Credit Risk Underwriting.",
            matching_points=[
                "15+ years banking track record",
                "Deep DSCR & SME credit policy expertise",
            ],
            missing_points=[],
            recommended_action="APPLY",
        ),
    )

    # 1. Format Alert
    alert_text = format_job_alert(job)
    assert "Credit Risk Policy Lead" in alert_text
    assert "PT Bank CIMB Niaga Tbk" in alert_text
    assert "95% FIT" in alert_text
    assert "Strict Human Approval" in alert_text or "HITL Enforcement" in alert_text

    # 2. Build Keyboard
    kb = build_job_action_keyboard(job)
    assert kb is not None
    assert len(kb.inline_keyboard) == 2

    # Row 1: Approve and Skip
    row1 = kb.inline_keyboard[0]
    assert row1[0].text == "✅ Approve & Auto-Apply"
    assert row1[0].callback_data == f"approve_{job.id}"
    assert row1[1].text == "❌ Skip"
    assert row1[1].callback_data == f"reject_{job.id}"

    # Row 2: CV Toggle and Listing URL
    row2 = kb.inline_keyboard[1]
    assert "CV: EN" in row2[0].text
    assert row2[0].callback_data == f"toggle_cv_{job.id}_ID"
    assert row2[1].url == job.url


def test_status_message_formatting() -> None:
    stats = {
        "total": 12,
        "avg_match_score": 88.5,
        "by_status": {
            "discovered": 5,
            "shortlisted": 3,
            "approved": 2,
            "submitted": 2,
        },
        "by_platform": {
            "jobstreet": 7,
            "glints": 5,
        },
    }

    msg = format_status_message(stats)
    assert "Total Jobs Tracked:* 12" in msg
    assert "88.5%" in msg
    assert "Jobstreet: *7*" in msg
    assert "Glints: *5*" in msg


if __name__ == "__main__":
    test_telegram_message_and_keyboard_formatting()
    test_status_message_formatting()
    print("All Telegram HITL tests passed!")
