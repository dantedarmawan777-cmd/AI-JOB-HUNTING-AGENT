"""
Telegram HITL Bot Service.
Sets up Telegram application, handlers, and notification dispatching.
"""

from __future__ import annotations

import asyncio
from typing import Optional
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from config import config
from src.core.database import db
from src.core.logger import get_logger
from src.core.models import Job
from src.telegram_hitl.handlers import (
    approve_command_handler,
    callback_query_handler,
    gemini_chat_handler,
    interval_command_handler,
    pending_handler,
    reject_command_handler,
    scrape_command_handler,
    start_handler,
    status_handler,
)
from src.telegram_hitl.messages import build_job_action_keyboard, format_job_alert

logger = get_logger(__name__)


class TelegramHitlBot:
    """Human-in-the-loop Telegram Bot Service."""

    def __init__(self, token: Optional[str] = None, default_chat_id: Optional[str] = None) -> None:
        self.token = token or config.telegram_bot_token
        self.chat_id = default_chat_id or config.telegram_chat_id
        self._app: Optional[Application] = None
        self._is_running = False

    def build_application(self) -> Application:
        """Construct the python-telegram-bot application with all handlers registered."""
        if not self.token:
            logger.warning("TELEGRAM_BOT_TOKEN is not configured in .env. Bot features will operate in mock mode.")
            return None

        app = Application.builder().token(self.token).build()

        # Command Handlers
        app.add_handler(CommandHandler("start", start_handler))
        app.add_handler(CommandHandler("help", start_handler))
        app.add_handler(CommandHandler("status", status_handler))
        app.add_handler(CommandHandler("pending", pending_handler))
        app.add_handler(CommandHandler("scrape", scrape_command_handler))
        app.add_handler(CommandHandler("interval", interval_command_handler))
        app.add_handler(CommandHandler("approve", approve_command_handler))
        app.add_handler(CommandHandler("reject", reject_command_handler))


        # Callback Query Handler for Inline Buttons
        app.add_handler(CallbackQueryHandler(callback_query_handler))

        # Natural Language Conversational Handler via Gemini AI
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, gemini_chat_handler))

        return app

    async def start(self) -> None:
        """Start polling loop for incoming Telegram user approvals."""
        if not self.token:
            logger.warning("Telegram Bot cannot start: No token provided.")
            return

        try:
            self._app = self.build_application()
            if not self._app:
                return

            logger.info("Starting Telegram HITL Bot polling...")
            await self._app.initialize()
            await self._app.start()
            await self._app.updater.start_polling(drop_pending_updates=True)
            self._is_running = True
            logger.info("Telegram HITL Bot successfully polling.")
        except Exception as e:
            logger.error("Error starting Telegram bot (will keep Web Dashboard active): %s", e)
            self._is_running = False

    async def stop(self) -> None:
        """Gracefully shutdown Telegram bot."""
        if self._app and self._is_running:
            try:
                logger.info("Stopping Telegram HITL Bot...")
                if self._app.updater and self._app.updater.running:
                    await self._app.updater.stop()
                await self._app.stop()
                await self._app.shutdown()
            except Exception as e:
                logger.warning("Error stopping Telegram bot: %s", e)
            finally:
                self._is_running = False

    async def send_job_alert(self, job: Job, target_chat_id: Optional[str | int] = None) -> bool:

        """
        Send a job opportunity card with inline approval/rejection buttons to Telegram.
        """
        dest_chat = target_chat_id or self.chat_id
        if not dest_chat or not self.token:
            logger.debug(
                "Skipping Telegram alert for job %s (chat_id: %s, token configured: %s)",
                job.id, bool(dest_chat), bool(self.token)
            )
            return False

        if not self._app:
            self._app = self.build_application()

        msg_text = format_job_alert(job)
        keyboard = build_job_action_keyboard(job)

        try:
            bot_instance = self._app.bot
            await bot_instance.send_message(
                chat_id=dest_chat,
                text=msg_text,
                reply_markup=keyboard,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True,
            )
            logger.info("Sent Telegram alert for shortlisted job: %s (%s)", job.title, job.company)
            await db.record_event(
                job_id=job.id,
                event_type="TELEGRAM_ALERT_SENT",
                notes=f"Sent to chat {dest_chat}",
            )
            return True
        except Exception as e:
            logger.error("Failed to send Telegram alert for job %s: %s", job.id, e)
            return False


# Global Telegram HITL Bot Instance
telegram_bot = TelegramHitlBot()
