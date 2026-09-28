"""
Web Dashboard & REST API Server for Job Hunting Agent.
Provides web-accessible dashboard for Railway Public Networking.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any, Dict, Optional
from aiohttp import web

from config import config
from src.core.database import db
from src.core.gemini_assistant import gemini_assistant
from src.core.logger import get_logger
from src.core.models import ApplicationStatus
from src.dashboard.template import DASHBOARD_HTML
from src.matcher.profile_loader import get_cv_path_for_language, load_candidate_profile
from src.scrapers.manager import scraper_manager
from src.telegram_hitl.bot import telegram_bot

logger = get_logger("dashboard.server")


async def handle_index(request: web.Request) -> web.Response:
    """Serve single-page responsive dashboard HTML."""
    return web.Response(text=DASHBOARD_HTML, content_type="text/html")


async def handle_get_stats(request: web.Request) -> web.Response:
    """Return pipeline statistics as JSON."""
    stats = await db.get_statistics()
    return web.json_response(stats)


async def handle_get_jobs(request: web.Request) -> web.Response:
    """Return list of jobs with optional status filter."""
    status_filter = request.query.get("status")
    limit = int(request.query.get("limit", 100))

    if status_filter and status_filter != "all":
        try:
            status_enum = ApplicationStatus(status_filter.lower())
            jobs = await db.get_jobs_by_status(status_enum, limit=limit)
        except ValueError:
            jobs = await db.get_recent_jobs(limit=limit)
    else:
        jobs = await db.get_recent_jobs(limit=limit)

    return web.json_response([j.model_dump(mode="json") for j in jobs])


async def handle_get_job_detail(request: web.Request) -> web.Response:
    """Return single job details by ID."""
    job_id = request.match_info.get("job_id")
    if not job_id:
        return web.json_response({"error": "Missing job_id"}, status=400)

    job = await db.get_job_by_id(job_id)
    if not job:
        return web.json_response({"error": "Job not found"}, status=404)

    return web.json_response(job.model_dump(mode="json"))


async def handle_approve_job(request: web.Request) -> web.Response:
    """Approve a shortlisted job for Playwright auto-apply execution."""
    job_id = request.match_info.get("job_id")
    if not job_id:
        return web.json_response({"error": "Missing job_id"}, status=400)

    job = await db.get_job_by_id(job_id)
    if not job:
        return web.json_response({"error": "Job not found"}, status=404)

    await db.update_job_status(job.id, ApplicationStatus.APPROVED, notes="Approved via Web Dashboard")

    # Trigger background Playwright auto-fill worker
    async def _execute():
        from src.execution.auto_fill import auto_fill_engine
        await auto_fill_engine.execute_job_application(job)

    asyncio.create_task(_execute())

    return web.json_response({"success": True, "message": f"Job {job.title} approved", "job_id": job.id})


async def handle_reject_job(request: web.Request) -> web.Response:
    """Reject/skip a job listing."""
    job_id = request.match_info.get("job_id")
    if not job_id:
        return web.json_response({"error": "Missing job_id"}, status=400)

    job = await db.get_job_by_id(job_id)
    if not job:
        return web.json_response({"error": "Job not found"}, status=404)

    await db.update_job_status(job.id, ApplicationStatus.REJECTED, notes="Rejected via Web Dashboard")
    return web.json_response({"success": True, "message": f"Job {job.title} marked as rejected", "job_id": job.id})


async def handle_toggle_cv(request: web.Request) -> web.Response:
    """Toggle target CV language between EN and ID."""
    job_id = request.match_info.get("job_id")
    if not job_id:
        return web.json_response({"error": "Missing job_id"}, status=400)

    try:
        data = await request.json()
    except Exception:
        data = {}

    new_lang = (data.get("cv_language") or "EN").upper()
    job = await db.get_job_by_id(job_id)
    if not job:
        return web.json_response({"error": "Job not found"}, status=404)

    await db.update_job_cv_language(job.id, new_lang)
    return web.json_response({"success": True, "cv_language": new_lang, "job_id": job.id})


async def handle_trigger_scrape(request: web.Request) -> web.Response:
    """Trigger background job scraping cycle."""
    async def _scrape():
        shortlisted = await scraper_manager.run_all()
        for j in shortlisted:
            await telegram_bot.send_job_alert(j)
            await asyncio.sleep(1.0)

    asyncio.create_task(_scrape())
    return web.json_response({"success": True, "message": "Scraping cycle initiated in background."})


async def handle_chat_message(request: web.Request) -> web.Response:
    """Chat with Gemini Assistant about jobs, candidates, or cover letters."""
    try:
        data = await request.json()
        user_text = data.get("message", "").strip()
    except Exception:
        user_text = ""

    if not user_text:
        return web.json_response({"error": "Empty message"}, status=400)

    reply = await gemini_assistant.chat(user_text)
    return web.json_response({"reply": reply})


async def handle_get_profile(request: web.Request) -> web.Response:
    """Return structured candidate profile."""
    profile = load_candidate_profile()
    return web.json_response(profile.model_dump(mode="json"))


async def handle_get_resume_pdf(request: web.Request) -> web.Response:
    """Serve PDF resume file for EN or ID version."""
    lang = request.match_info.get("lang", "EN").upper()
    cv_path = get_cv_path_for_language(lang)
    if not cv_path or not cv_path.exists():
        return web.Response(text=f"CV file for {lang} not found", status=404)

    return web.FileResponse(cv_path, headers={"Content-Disposition": f'inline; filename="{cv_path.name}"'})


async def handle_get_screenshot(request: web.Request) -> web.Response:
    """Serve application proof screenshot."""
    filename = request.match_info.get("filename", "")
    screenshot_path = config.screenshots_dir / filename
    if not screenshot_path.exists():
        return web.Response(text="Screenshot not found", status=404)

    return web.FileResponse(screenshot_path)


async def handle_get_config(request: web.Request) -> web.Response:
    """Return runtime configuration."""
    return web.json_response({
        "scrape_interval_hours": config.scrape_interval_hours,
        "min_match_score": config.min_match_score,
        "dry_run": config.dry_run,
        "headless": config.headless,
        "allowed_user": config.allowed_user,
    })


async def handle_update_interval(request: web.Request) -> web.Response:
    """Update auto-scrape interval in hours."""
    try:
        data = await request.json()
        hours = int(data.get("interval_hours", 6))
        if 1 <= hours <= 72:
            config.scrape_interval_hours = hours
            logger.info("Updated auto-scrape interval to %d hours via Web Dashboard", hours)
            return web.json_response({"success": True, "scrape_interval_hours": hours})
        return web.json_response({"error": "Interval must be between 1 and 72 hours"}, status=400)
    except Exception as e:
        return web.json_response({"error": str(e)}, status=400)


def create_dashboard_app() -> web.Application:
    """Build aiohttp web application with all dashboard routes."""
    app = web.Application()

    # Routes
    app.router.add_get("/", handle_index)
    app.router.add_get("/api/stats", handle_get_stats)
    app.router.add_get("/api/config", handle_get_config)
    app.router.add_post("/api/config/interval", handle_update_interval)
    app.router.add_get("/api/jobs", handle_get_jobs)
    app.router.add_get("/api/jobs/{job_id}", handle_get_job_detail)
    app.router.add_post("/api/jobs/{job_id}/approve", handle_approve_job)
    app.router.add_post("/api/jobs/{job_id}/reject", handle_reject_job)
    app.router.add_post("/api/jobs/{job_id}/toggle-cv", handle_toggle_cv)
    app.router.add_post("/api/scrape", handle_trigger_scrape)
    app.router.add_post("/api/chat", handle_chat_message)
    app.router.add_get("/api/profile", handle_get_profile)
    app.router.add_get("/api/resumes/{lang}", handle_get_resume_pdf)
    app.router.add_get("/api/screenshots/{filename}", handle_get_screenshot)

    return app



async def run_dashboard_server(host: Optional[str] = None, port: Optional[int] = None) -> web.AppRunner:
    """Run web dashboard HTTP server as an async task."""
    bind_host = host or config.host
    bind_port = port or config.port

    app = create_dashboard_app()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, bind_host, bind_port)
    await site.start()
    logger.info("Web Dashboard server active on http://%s:%s", bind_host, bind_port)
    return runner
