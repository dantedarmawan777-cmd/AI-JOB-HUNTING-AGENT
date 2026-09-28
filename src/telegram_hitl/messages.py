"""
Telegram message formatting and inline keyboard builder.
Formats job alerts, match summaries, and interactive HITL buttons.
"""

from __future__ import annotations

from typing import List, Optional
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from src.core.models import ApplicationStatus, Job


def format_job_alert(job: Job) -> str:
    """
    Format rich Markdown message for Telegram job notification.
    """
    score = job.match_result.score if job.match_result else 0
    score_emoji = "🟢" if score >= 85 else ("🟡" if score >= 70 else "🔴")

    platform_tag = f"#{job.platform.value.upper()}"
    salary_str = job.get_display_salary()

    lines = [
        f"🎯 *NEW JOB MATCH: {score_emoji} {score}% FIT*",
        f"━━━━━━━━━━━━━━━━━━━━━━",
        f"🏢 *Company:* {job.company}",
        f"💼 *Role:* {job.title}",
        f"📍 *Location:* {job.location}",
        f"💰 *Salary:* {salary_str}",
        f"🏷 *Platform:* {platform_tag}",
        f"📄 *Selected CV:* `{job.cv_language}`",
    ]

    if job.match_result:
        mr = job.match_result
        if mr.matching_points:
            lines.append("\n✨ *Key Matching Strengths:*")
            for pt in mr.matching_points[:4]:
                lines.append(f"  • {pt}")

        if mr.missing_points:
            lines.append("\n⚠️ *Gaps / Review Notes:*")
            for pt in mr.missing_points[:2]:
                lines.append(f"  • {pt}")

        if mr.reasoning:
            lines.append(f"\n💡 *Recommendation:* _{mr.reasoning}_")

    lines.append(f"\n🆔 *Job ID:* `{job.id}`")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("⚡ *HITL Enforcement: Requires explicit approval before auto-applying.*")

    return "\n".join(lines)


def build_job_action_keyboard(job: Job) -> InlineKeyboardMarkup:
    """
    Construct interactive Telegram Inline Keyboard for Human-in-the-Loop decision.
    """
    # CV toggle button text
    next_lang = "ID" if job.cv_language == "EN" else "EN"
    cv_btn_text = f"📄 CV: {job.cv_language} (Switch to {next_lang})"

    keyboard = [
        [
            InlineKeyboardButton(
                text="✅ Approve & Auto-Apply",
                callback_data=f"approve_{job.id}",
            ),
            InlineKeyboardButton(
                text="❌ Skip",
                callback_data=f"reject_{job.id}",
            ),
        ],
        [
            InlineKeyboardButton(
                text=cv_btn_text,
                callback_data=f"toggle_cv_{job.id}_{next_lang}",
            ),
            InlineKeyboardButton(
                text="🔗 Open Listing",
                url=job.url,
            ),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


def format_status_message(stats: dict) -> str:
    """Format bot statistics overview message."""
    lines = [
        "📊 *Job Hunting Agent - Pipeline Status*",
        "━━━━━━━━━━━━━━━━━━━━━━",
        f"📁 *Total Jobs Tracked:* {stats.get('total', 0)}",
        f"⭐ *Average Match Score:* {stats.get('avg_match_score', 0)}%",
        "",
        "📌 *By Status:*",
    ]

    status_dict = stats.get("by_status", {})
    status_emojis = {
        "discovered": "🔍 Discovered",
        "shortlisted": "⏳ Shortlisted (Pending HITL)",
        "approved": "✅ Approved",
        "submitting": "⚙️ Submitting (Playwright)",
        "submitted": "🚀 Submitted",
        "rejected": "❌ Skipped/Rejected",
        "failed": "⚠️ Failed",
        "interview_invited": "🎉 Interview Invited",
    }

    for st_key, st_label in status_emojis.items():
        count = status_dict.get(st_key, 0)
        lines.append(f"  • {st_label}: *{count}*")

    lines.append("")
    lines.append("🌐 *By Platform:*")
    platform_dict = stats.get("by_platform", {})
    for p_key, count in platform_dict.items():
        lines.append(f"  • {p_key.capitalize()}: *{count}*")

    lines.append("━━━━━━━━━━━━━━━━━━━━━━")
    return "\n".join(lines)
