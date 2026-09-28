"""
Main entry point for Job Hunting Automation Agent.
Provides CLI interface for scraping, Telegram HITL daemon, single-job execution, and pipeline analytics.
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from typing import Optional

# Configure UTF-8 stdout for Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from config import config
from src.core.database import db
from src.core.logger import get_logger
from src.core.models import ApplicationStatus
from src.dashboard.server import run_dashboard_server
from src.execution.auto_fill import auto_fill_engine
from src.execution.playwright_worker import playwright_worker
from src.scrapers.manager import scraper_manager
from src.telegram_hitl.bot import telegram_bot

logger = get_logger("job_agent_main")


async def run_scraper_cycle() -> None:
    """Run single cycle of all scrapers and broadcast alerts to Telegram."""
    logger.info("Initiating full job scraping and matching cycle...")
    shortlisted_jobs = await scraper_manager.run_all()
    logger.info("Scraper cycle identified %d shortlisted jobs.", len(shortlisted_jobs))

    # Broadcast shortlisted jobs to Telegram for Human Approval
    for job in shortlisted_jobs:
        await telegram_bot.send_job_alert(job)
        # Polite pause between Telegram notifications
        await asyncio.sleep(1.0)


async def execute_application(job_id: str, cv_language: Optional[str] = None) -> None:
    """Execute Playwright application for a single job ID."""
    job = await db.get_job_by_id(job_id)
    if not job:
        logger.error("Job ID '%s' not found in database.", job_id)
        return

    logger.info("Executing application for Job '%s' at '%s'...", job.title, job.company)
    res = await auto_fill_engine.execute_job_application(job, cv_language=cv_language)
    logger.info(
        "Application result - Success: %s, Status: %s, Screenshot: %s",
        res.success, res.status.value, res.screenshot_path
    )


async def display_stats() -> None:
    """Print pipeline stats to console."""
    stats = await db.get_statistics()
    print("\n========================================")
    print("      JOB HUNTING PIPELINE STATS        ")
    print("========================================")
    print(f"Total Jobs Discovered: {stats.get('total', 0)}")
    print(f"Average Match Score:   {stats.get('avg_match_score', 0)}%\n")

    print("--- By Status ---")
    for st, count in stats.get("by_status", {}).items():
        print(f"  • {st.upper():<16}: {count}")

    print("\n--- By Platform ---")
    for plat, count in stats.get("by_platform", {}).items():
        print(f"  • {plat.capitalize():<16}: {count}")
    print("========================================\n")


async def run_daemon(poll_interval_hours: int = 4) -> None:
    """Run full automation daemon with Web Dashboard, Telegram HITL, and periodic scraping."""
    logger.info("Starting Job Hunting Automation Daemon & Web Dashboard...")

    # 1. Start Web Dashboard HTTP Server (for Railway Public Networking)
    dashboard_runner = await run_dashboard_server(host=config.host, port=config.port)

    # 2. Start Telegram HITL Bot
    await telegram_bot.start()

    try:
        while True:
            try:
                await run_scraper_cycle()
            except Exception as e:
                logger.error("Error during scheduled scraper cycle: %s", e, exc_info=True)

            logger.info("Sleeping for %d hours until next scraping cycle...", poll_interval_hours)
            await asyncio.sleep(poll_interval_hours * 3600)
    except asyncio.CancelledError:
        logger.info("Daemon cancelled, shutting down...")
    finally:
        await telegram_bot.stop()
        await scraper_manager.close()
        await playwright_worker.close()
        if dashboard_runner:
            await dashboard_runner.cleanup()


def main() -> None:
    parser = argparse.ArgumentParser(description="Autonomous Job Hunting & HITL Agent")
    parser.add_argument("--scrape", action="store_true", help="Run one-time scraping and matching cycle")
    parser.add_argument("--serve", action="store_true", help="Start continuous Telegram HITL daemon")
    parser.add_argument("--apply", type=str, metavar="JOB_ID", help="Execute Playwright auto-fill for job ID")
    parser.add_argument("--cv", type=str, default="EN", choices=["EN", "ID"], help="CV language to use (EN/ID)")
    parser.add_argument("--stats", action="store_true", help="Display SQLite database pipeline metrics")
    parser.add_argument("--headless", action="store_true", help="Run Playwright in headless mode")
    parser.add_argument("--live", action="store_true", help="Disable dry-run mode and submit live applications")

    args = parser.parse_args()

    if args.headless:
        config.headless = True
    if args.live:
        config.dry_run = False

    if args.stats:
        asyncio.run(display_stats())
    elif args.apply:
        asyncio.run(execute_application(args.apply, cv_language=args.cv))
    elif args.scrape:
        asyncio.run(run_scraper_cycle())
    elif args.serve:
        asyncio.run(run_daemon())
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
