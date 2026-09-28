"""
Telegram bot command and callback query handlers.
Enforces strict Human-in-the-Loop approval before any auto-fill execution.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Optional
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from config import config
from src.core.database import db
from src.core.gemini_assistant import gemini_assistant
from src.core.logger import get_logger
from src.core.models import ApplicationStatus
from src.telegram_hitl.messages import (
    build_job_action_keyboard,
    format_job_alert,
    format_status_message,
)

logger = get_logger(__name__)


def is_authorized(update: Update) -> bool:
    """Verify incoming user matches allowed Telegram handle."""
    if not config.allowed_user:
        return True
    user = update.effective_user
    if not user:
        return False
    username = (user.username or "").replace("@", "").lower()
    return username == config.allowed_user.lower()


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command and capture active chat ID."""
    if not update.effective_message:
        return

    # Auto-record chat ID if not set
    if update.effective_chat:
        config.telegram_chat_id = str(update.effective_chat.id)

    if not is_authorized(update):
        await update.effective_message.reply_text("⛔ Akses ditolak. Bot ini khusus untuk pengguna terotorisasi.")
        return

    welcome_text = (
        f"🤖 *Antigravity Job Copilot & HITL Gateway Aktif!*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Halo Bos @{config.allowed_user}! Bot ini memantau lowongan kerja Credit Risk & Underwriting, "
        f"melakukan AI Resume Screening, dan mengeksekusi lamaran dengan *Human-in-the-Loop Approval*.\n\n"
        f"*Fitur & Perintah:*\n"
        f"• 💬 *Chat Langsung:* Tanya lowongan, minta evaluasi CV, atau minta buatin cover letter via Gemini AI.\n"
        f"• `/status` - Lihat metrik & progres pipeline lamaran\n"
        f"• `/pending` - Lihat lowongan shortlisted yang menunggu approval\n"
        f"• `/approve <id>` - Setujui lowongan untuk auto-apply\n"
        f"• `/reject <id>` - Skip / tolak lowongan\n\n"
        f"⚙️ *Mode:* `{'Dry Run (Simulasi Aman)' if config.dry_run else 'Live Submission'}` | 🎯 *Min Fit:* `{config.min_match_score}%`\n"
    )
    await update.effective_message.reply_text(
        welcome_text,
        parse_mode=ParseMode.MARKDOWN,
    )


async def gemini_chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle free-form natural language chat using Gemini AI Assistant."""
    if not update.effective_message or not update.effective_message.text:
        return

    if update.effective_chat:
        config.telegram_chat_id = str(update.effective_chat.id)

    if not is_authorized(update):
        await update.effective_message.reply_text("⛔ Akses ditolak. Bot ini khusus untuk pengguna terotorisasi.")
        return

    user_text = update.effective_message.text.strip()
    logger.info("Received chat from @%s: '%s'", update.effective_user.username if update.effective_user else "unknown", user_text)

    # Send typing indicator
    try:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    except Exception:
        pass

    try:
        reply = await gemini_assistant.chat(user_text)
        await update.effective_message.reply_text(
            reply,
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
        )
    except Exception as e:
        logger.error("Error in gemini_chat_handler: %s", e, exc_info=True)
        await update.effective_message.reply_text(
            f"⚠️ Maaf Bos, ada kendala saat memproses jawaban: `{str(e)}`",
            parse_mode=ParseMode.MARKDOWN,
        )


async def status_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /status command."""
    if not update.effective_message:
        return

    stats = await db.get_statistics()
    msg = format_status_message(stats)
    await update.effective_message.reply_text(msg, parse_mode=ParseMode.MARKDOWN)


async def pending_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /pending command to display unapproved shortlisted jobs."""
    if not update.effective_message:
        return

    pending_jobs = await db.get_pending_approvals(limit=10)
    if not pending_jobs:
        await update.effective_message.reply_text(
            "✅ *No pending jobs awaiting approval.* All caught up!",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    await update.effective_message.reply_text(
        f"📋 Found *{len(pending_jobs)}* job(s) awaiting your approval:",
        parse_mode=ParseMode.MARKDOWN,
    )

    for job in pending_jobs:
        msg_text = format_job_alert(job)
        keyboard = build_job_action_keyboard(job)
        await update.effective_message.reply_text(
            msg_text,
            reply_markup=keyboard,
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
        )


async def approve_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /approve <job_id> command."""
    if not update.effective_message:
        return

    args = context.args
    if not args:
        await update.effective_message.reply_text(
            "⚠️ Usage: `/approve <job_id>`",
            parse_mode=ParseMode.MARKDOWN,
        )
        return

    job_id = args[0].strip()
    job = await db.get_job_by_id(job_id)
    if not job:
        await update.effective_message.reply_text(f"❌ Job with ID `{job_id}` not found.", parse_mode=ParseMode.MARKDOWN)
        return

    await db.update_job_status(job.id, ApplicationStatus.APPROVED, notes="Approved via /approve command")
    await update.effective_message.reply_text(
        f"✅ Job *{job.title}* at *{job.company}* marked as APPROVED for auto-apply.",
        parse_mode=ParseMode.MARKDOWN,
    )
    # Trigger background worker
    asyncio.create_task(trigger_playwright_execution(job.id, context.bot, update.effective_chat.id))


async def reject_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /reject <job_id> command."""
    if not update.effective_message:
        return

    args = context.args
    if not args:
        await update.effective_message.reply_text("⚠️ Usage: `/reject <job_id>`", parse_mode=ParseMode.MARKDOWN)
        return

    job_id = args[0].strip()
    job = await db.get_job_by_id(job_id)
    if not job:
        await update.effective_message.reply_text(f"❌ Job with ID `{job_id}` not found.", parse_mode=ParseMode.MARKDOWN)
        return

    await db.update_job_status(job.id, ApplicationStatus.REJECTED, notes="Rejected via /reject command")
    await update.effective_message.reply_text(
        f"❌ Job *{job.title}* at *{job.company}* marked as REJECTED.",
        parse_mode=ParseMode.MARKDOWN,
    )


async def callback_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handle Telegram inline keyboard button presses.
    Enforces human approval before triggering Playwright worker.
    """
    query = update.callback_query
    if not query:
        return

    await query.answer()
    data = query.data or ""
    chat_id = query.message.chat_id if query.message else None

    # 1. APPROVE & AUTO-APPLY
    if data.startswith("approve_"):
        job_id = data.replace("approve_", "", 1)
        job = await db.get_job_by_id(job_id)
        if not job:
            await query.edit_message_text(f"❌ Error: Job `{job_id}` not found in database.")
            return

        # Update status to APPROVED
        await db.update_job_status(
            job.id,
            ApplicationStatus.APPROVED,
            notes="Approved via Telegram HITL inline button",
        )

        orig_text = query.message.text if query.message else ""
        action_notice = (
            f"\n\n━━━━━━━━━━━━━━━━━━━━━━\n"
            f"✅ *APPROVED by Human Operator!*\n"
            f"🚀 *Queued for Playwright Auto-Apply worker (CV: {job.cv_language})*..."
        )
        try:
            await query.edit_message_text(
                text=orig_text + action_notice,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True,
            )
        except Exception:
            pass

        # Trigger background Playwright execution
        if chat_id and context.bot:
            asyncio.create_task(trigger_playwright_execution(job.id, context.bot, chat_id))

    # 2. REJECT / SKIP
    elif data.startswith("reject_"):
        job_id = data.replace("reject_", "", 1)
        job = await db.get_job_by_id(job_id)
        if not job:
            await query.edit_message_text(f"❌ Error: Job `{job_id}` not found in database.")
            return

        await db.update_job_status(
            job.id,
            ApplicationStatus.REJECTED,
            notes="Rejected via Telegram HITL inline button",
        )

        orig_text = query.message.text if query.message else ""
        action_notice = "\n\n━━━━━━━━━━━━━━━━━━━━━━\n❌ *SKIPPED / REJECTED by Human Operator.*"
        try:
            await query.edit_message_text(
                text=orig_text + action_notice,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True,
            )
        except Exception:
            pass

    # 3. TOGGLE CV LANGUAGE (EN <-> ID)
    elif data.startswith("toggle_cv_"):
        parts = data.split("_")
        if len(parts) >= 4:
            job_id = parts[2]
            new_lang = parts[3].upper()
            job = await db.get_job_by_id(job_id)
            if job:
                job.cv_language = new_lang
                await db.update_job_cv_language(job.id, new_lang)
                new_keyboard = build_job_action_keyboard(job)
                new_msg = format_job_alert(job)
                try:
                    await query.edit_message_text(
                        text=new_msg,
                        reply_markup=new_keyboard,
                        parse_mode=ParseMode.MARKDOWN,
                        disable_web_page_preview=True,
                    )
                except Exception as e:
                    logger.debug("Failed to edit CV toggle message: %s", e)


async def trigger_playwright_execution(job_id: str, bot: Any, chat_id: int | str) -> None:
    """
    Background executor triggered strictly after human operator approval.
    Runs Playwright worker, captures screenshots, updates DB, and notifies Telegram.
    """
    from src.execution.auto_fill import auto_fill_engine

    logger.info("Human approval received for job %s. Starting Playwright auto-fill...", job_id)
    job = await db.get_job_by_id(job_id)
    if not job:
        logger.error("Cannot execute auto-apply: Job %s not found", job_id)
        return

    # Update status to SUBMITTING
    await db.update_job_status(job.id, ApplicationStatus.SUBMITTING, notes="Playwright execution started")

    try:
        # Execute Auto-Fill Engine
        result = await auto_fill_engine.execute_job_application(job)

        # Notify Telegram with Result and Screenshot
        if result.success:
            status_text = (
                f"🎉 *APPLICATION SUCCESSFULLY EXECUTED!*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🏢 *Company:* {job.company}\n"
                f"💼 *Role:* {job.title}\n"
                f"📄 *Submitted CV:* `{job.cv_language}`\n"
                f"⚙️ *Mode:* `{'Dry Run (Pre-submit review)' if result.dry_run else 'Live Submission Completed'}`\n"
                f"🕒 *Timestamp:* `{result.submitted_at.strftime('%Y-%m-%d %H:%M:%S UTC')}`\n"
            )
            if result.answers_submitted:
                status_text += "\n📝 *Answers Auto-Filled:*\n"
                for q, a in list(result.answers_submitted.items())[:5]:
                    status_text += f"  • _{q[:40]}..._: *{a}*\n"

            if result.screenshot_path and Path(result.screenshot_path).exists():
                with open(result.screenshot_path, "rb") as photo_file:
                    await bot.send_photo(
                        chat_id=chat_id,
                        photo=photo_file,
                        caption=status_text,
                        parse_mode=ParseMode.MARKDOWN,
                    )
            else:
                await bot.send_message(chat_id=chat_id, text=status_text, parse_mode=ParseMode.MARKDOWN)

        else:
            fail_text = (
                f"⚠️ *APPLICATION EXECUTION WARNING / MANUAL ACTION NEEDED*\n"
                f"━━━━━━━━━━━━━━━━━━━━━━\n"
                f"🏢 *Company:* {job.company}\n"
                f"💼 *Role:* {job.title}\n"
                f"❗ *Reason:* {result.error_message or 'Unknown error during form fill'}\n"
                f"🔗 *Listing URL:* {job.url}\n\n"
                f"_Please review the attached screenshot or complete application manually if required._"
            )
            if result.screenshot_path and Path(result.screenshot_path).exists():
                with open(result.screenshot_path, "rb") as photo_file:
                    await bot.send_photo(
                        chat_id=chat_id,
                        photo=photo_file,
                        caption=fail_text,
                        parse_mode=ParseMode.MARKDOWN,
                    )
            else:
                await bot.send_message(chat_id=chat_id, text=fail_text, parse_mode=ParseMode.MARKDOWN)

    except Exception as e:
        logger.error("Exception during auto-fill execution for job %s: %s", job_id, e, exc_info=True)
        await db.update_job_status(job.id, ApplicationStatus.FAILED, notes=f"Execution error: {str(e)}")
        await bot.send_message(
            chat_id=chat_id,
            text=f"❌ *Auto-Apply Error for {job.title} at {job.company}:*\n`{str(e)}`",
            parse_mode=ParseMode.MARKDOWN,
        )
