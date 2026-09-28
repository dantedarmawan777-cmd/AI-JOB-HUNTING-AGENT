"""
Database storage module for the Job Hunting Automation system.
Provides robust, thread-safe, and asynchronous SQLite storage for job tracking,
HITL lifecycle state machines, and audit logging.
"""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import aiosqlite

from config import config
from src.core.logger import get_logger
from src.core.models import (
    ApplicationStatus,
    Job,
    MatchResult,
    PlatformEnum,
    ScreeningQuestion,
)

logger = get_logger(__name__)


SCHEMA_SQL = """
PRAGMA journal_mode = WAL;
PRAGMA busy_timeout = 5000;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,
    platform TEXT NOT NULL,
    title TEXT NOT NULL,
    company TEXT NOT NULL,
    location TEXT NOT NULL,
    salary TEXT,
    salary_min REAL,
    salary_max REAL,
    salary_currency TEXT DEFAULT 'IDR',
    url TEXT UNIQUE NOT NULL,
    description TEXT,
    posted_date TEXT,
    work_type TEXT,
    status TEXT NOT NULL DEFAULT 'discovered',
    match_score INTEGER,
    match_reasoning TEXT,
    match_data TEXT,
    screening_questions TEXT,
    cv_language TEXT DEFAULT 'EN',
    screenshot_path TEXT,
    raw_data TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS application_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    previous_status TEXT,
    new_status TEXT,
    notes TEXT,
    metadata_json TEXT,
    timestamp TEXT NOT NULL,
    FOREIGN KEY(job_id) REFERENCES jobs(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_platform ON jobs(platform);
CREATE INDEX IF NOT EXISTS idx_jobs_url ON jobs(url);
CREATE INDEX IF NOT EXISTS idx_jobs_match_score ON jobs(match_score);
CREATE INDEX IF NOT EXISTS idx_history_job_id ON application_history(job_id);
"""


class Database:
    """Async and Thread-Safe SQLite Database Manager."""

    def __init__(self, db_path: Optional[Path | str] = None) -> None:
        self.db_path = Path(db_path) if db_path else config.db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_sync()

    def _init_sync(self) -> None:
        """Run initial schema migration synchronously."""
        with sqlite3.connect(str(self.db_path)) as conn:
            conn.executescript(SCHEMA_SQL)
            conn.commit()
        logger.debug("Database initialized at %s", self.db_path)

    async def init_async(self) -> None:
        """Ensure async connection operates with correct schema and PRAGMAs."""
        async with aiosqlite.connect(str(self.db_path)) as db:
            await db.executescript(SCHEMA_SQL)
            await db.commit()

    async def ensure_initial_seeds(self) -> None:
        """Seed initial target jobs immediately if database is empty on boot."""
        try:
            stats = await self.get_statistics()
            if stats.get("total", 0) < 4:
                from src.matcher.seed_jobs import get_curated_seed_jobs
                seed_jobs = get_curated_seed_jobs()
                for s_job in seed_jobs:
                    if not await self.job_exists(s_job.url):
                        await self.save_job(s_job)
                logger.info("Auto-seeded %d target opportunities on boot.", len(seed_jobs))
        except Exception as e:
            logger.warning("Auto-seed error: %s", e)


    # --------------------------------------------------------------------------
    # Job CRUD Operations
    # --------------------------------------------------------------------------

    async def save_job(self, job: Job) -> Job:
        """
        Insert or update a job record.
        Preserves existing status if job is already known unless explicitly changed.
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        job.updated_at = datetime.now(timezone.utc)

        match_data_str = job.match_result.model_dump_json() if job.match_result else None
        match_score = job.match_result.score if job.match_result else None
        match_reasoning = job.match_result.reasoning if job.match_result else None

        sq_str = json.dumps([sq.model_dump() for sq in job.screening_questions])
        raw_str = json.dumps(job.raw_data)

        async with aiosqlite.connect(str(self.db_path)) as db:
            db.row_factory = aiosqlite.Row
            # Check existing job
            async with db.execute("SELECT id, status FROM jobs WHERE url = ?", (job.url,)) as cursor:
                existing = await cursor.fetchone()

            if existing:
                existing_status = existing["status"]
                # Keep existing progress status unless passed job has explicit higher priority
                status_to_keep = job.status.value if job.status != ApplicationStatus.DISCOVERED else existing_status

                query = """
                UPDATE jobs SET
                    title = ?,
                    company = ?,
                    location = ?,
                    salary = ?,
                    salary_min = ?,
                    salary_max = ?,
                    salary_currency = ?,
                    description = ?,
                    posted_date = ?,
                    work_type = ?,
                    status = ?,
                    match_score = COALESCE(?, match_score),
                    match_reasoning = COALESCE(?, match_reasoning),
                    match_data = COALESCE(?, match_data),
                    screening_questions = ?,
                    cv_language = ?,
                    screenshot_path = COALESCE(?, screenshot_path),
                    raw_data = ?,
                    updated_at = ?
                WHERE id = ?
                """
                await db.execute(
                    query,
                    (
                        job.title,
                        job.company,
                        job.location,
                        job.salary,
                        job.salary_min,
                        job.salary_max,
                        job.salary_currency,
                        job.description,
                        job.posted_date,
                        job.work_type,
                        status_to_keep,
                        match_score,
                        match_reasoning,
                        match_data_str,
                        sq_str,
                        job.cv_language,
                        job.screenshot_path,
                        raw_str,
                        now_iso,
                        existing["id"],
                    ),
                )
                job.id = existing["id"]
                job.status = ApplicationStatus(status_to_keep)
            else:
                insert_query = """
                INSERT INTO jobs (
                    id, platform, title, company, location, salary,
                    salary_min, salary_max, salary_currency, url, description,
                    posted_date, work_type, status, match_score, match_reasoning,
                    match_data, screening_questions, cv_language, screenshot_path,
                    raw_data, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                await db.execute(
                    insert_query,
                    (
                        job.id,
                        job.platform.value if isinstance(job.platform, PlatformEnum) else job.platform,
                        job.title,
                        job.company,
                        job.location,
                        job.salary,
                        job.salary_min,
                        job.salary_max,
                        job.salary_currency,
                        job.url,
                        job.description,
                        job.posted_date,
                        job.work_type,
                        job.status.value,
                        match_score,
                        match_reasoning,
                        match_data_str,
                        sq_str,
                        job.cv_language,
                        job.screenshot_path,
                        raw_str,
                        now_iso,
                        now_iso,
                    ),
                )
                # Audit log
                await self._record_history_internal(
                    db,
                    job_id=job.id,
                    event_type="JOB_DISCOVERED",
                    prev_status=None,
                    new_status=job.status.value,
                    notes=f"Discovered on {job.platform}",
                )

            await db.commit()
            return job

    async def get_job_by_id(self, job_id: str) -> Optional[Job]:
        """Fetch job by ID."""
        async with aiosqlite.connect(str(self.db_path)) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)) as cursor:
                row = await cursor.fetchone()
                return self._row_to_job(row) if row else None

    async def get_job_by_url(self, url: str) -> Optional[Job]:
        """Fetch job by URL."""
        async with aiosqlite.connect(str(self.db_path)) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM jobs WHERE url = ?", (url,)) as cursor:
                row = await cursor.fetchone()
                return self._row_to_job(row) if row else None

    async def job_exists(self, url: str) -> bool:
        """Check if a job with URL already exists."""
        async with aiosqlite.connect(str(self.db_path)) as db:
            async with db.execute("SELECT 1 FROM jobs WHERE url = ?", (url,)) as cursor:
                return (await cursor.fetchone()) is not None

    async def update_job_status(
        self,
        job_id: str,
        status: ApplicationStatus,
        notes: str = "",
        screenshot_path: Optional[str] = None,
        extra_metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Update job application status with audit trail."""
        now_iso = datetime.now(timezone.utc).isoformat()
        async with aiosqlite.connect(str(self.db_path)) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT status, screenshot_path FROM jobs WHERE id = ?", (job_id,)) as cursor:
                row = await cursor.fetchone()
                if not row:
                    logger.warning("Job %s not found for status update", job_id)
                    return False
                prev_status = row["status"]
                curr_shot = screenshot_path or row["screenshot_path"]

            await db.execute(
                """
                UPDATE jobs
                SET status = ?, screenshot_path = ?, updated_at = ?
                WHERE id = ?
                """,
                (status.value, curr_shot, now_iso, job_id),
            )

            await self._record_history_internal(
                db,
                job_id=job_id,
                event_type="STATUS_CHANGED",
                prev_status=prev_status,
                new_status=status.value,
                notes=notes,
                metadata=extra_metadata,
            )
            await db.commit()
            logger.info("Job %s status updated: %s -> %s", job_id, prev_status, status.value)
            return True

    async def update_job_cv_language(self, job_id: str, cv_language: str) -> bool:
        """Update selected CV language for a job application."""
        now_iso = datetime.now(timezone.utc).isoformat()
        async with aiosqlite.connect(str(self.db_path)) as db:
            await db.execute(
                "UPDATE jobs SET cv_language = ?, updated_at = ? WHERE id = ?",
                (cv_language.upper(), now_iso, job_id),
            )
            await self._record_history_internal(
                db,
                job_id=job_id,
                event_type="CV_LANGUAGE_CHANGED",
                notes=f"Selected CV: {cv_language.upper()}",
            )
            await db.commit()
            return True

    async def get_jobs_by_status(
        self,
        status: ApplicationStatus,
        platform: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Job]:
        """Fetch list of jobs matching given status."""
        query = "SELECT * FROM jobs WHERE status = ?"
        params: List[Any] = [status.value]

        if platform:
            query += " AND platform = ?"
            params.append(platform)

        query += " ORDER BY match_score DESC, updated_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        async with aiosqlite.connect(str(self.db_path)) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                return [self._row_to_job(r) for r in rows]

    async def get_recent_jobs(self, limit: int = 50, offset: int = 0) -> List[Job]:
        """Fetch most recent jobs across all statuses."""
        query = "SELECT * FROM jobs ORDER BY updated_at DESC, match_score DESC LIMIT ? OFFSET ?"
        async with aiosqlite.connect(str(self.db_path)) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(query, (limit, offset)) as cursor:
                rows = await cursor.fetchall()
                return [self._row_to_job(r) for r in rows]

    async def get_pending_approvals(self, limit: int = 20) -> List[Job]:
        """Fetch shortlisted jobs awaiting user HITL approval."""
        return await self.get_jobs_by_status(ApplicationStatus.SHORTLISTED, limit=limit)

    async def get_approved_jobs(self, limit: int = 20) -> List[Job]:
        """Fetch jobs approved by user ready for Playwright auto-apply."""
        return await self.get_jobs_by_status(ApplicationStatus.APPROVED, limit=limit)

    async def get_statistics(self) -> Dict[str, Any]:
        """Aggregate stats on job counts per status and platform."""
        stats: Dict[str, Any] = {
            "total": 0,
            "by_status": {},
            "by_platform": {},
            "avg_match_score": 0.0,
        }
        async with aiosqlite.connect(str(self.db_path)) as db:
            db.row_factory = aiosqlite.Row
            # Status counts
            async with db.execute("SELECT status, count(*) as cnt FROM jobs GROUP BY status") as cursor:
                async for row in cursor:
                    stats["by_status"][row["status"]] = row["cnt"]
                    stats["total"] += row["cnt"]

            # Platform counts
            async with db.execute("SELECT platform, count(*) as cnt FROM jobs GROUP BY platform") as cursor:
                async for row in cursor:
                    stats["by_platform"][row["platform"]] = row["cnt"]

            # Avg score of shortlisted / approved
            async with db.execute("SELECT AVG(match_score) as avg_score FROM jobs WHERE match_score IS NOT NULL") as cursor:
                row = await cursor.fetchone()
                if row and row["avg_score"] is not None:
                    stats["avg_match_score"] = round(float(row["avg_score"]), 1)

        return stats

    # --------------------------------------------------------------------------
    # Audit History & Helpers
    # --------------------------------------------------------------------------

    async def _record_history_internal(
        self,
        db: aiosqlite.Connection,
        job_id: str,
        event_type: str,
        prev_status: Optional[str] = None,
        new_status: Optional[str] = None,
        notes: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Internal helper to insert into application_history table."""
        now_iso = datetime.now(timezone.utc).isoformat()
        meta_str = json.dumps(metadata) if metadata else None
        await db.execute(
            """
            INSERT INTO application_history (
                job_id, event_type, previous_status, new_status, notes, metadata_json, timestamp
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (job_id, event_type, prev_status, new_status, notes, meta_str, now_iso),
        )

    async def record_event(
        self,
        job_id: str,
        event_type: str,
        prev_status: Optional[str] = None,
        new_status: Optional[str] = None,
        notes: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Public API to append an audit log entry for a job."""
        async with aiosqlite.connect(str(self.db_path)) as db:
            await self._record_history_internal(
                db, job_id, event_type, prev_status, new_status, notes, metadata
            )
            await db.commit()

    def _row_to_job(self, row: aiosqlite.Row) -> Job:
        """Convert an SQLite row to a typed Job model."""
        match_result = None
        if row["match_data"]:
            try:
                match_dict = json.loads(row["match_data"])
                match_result = MatchResult(**match_dict)
            except Exception as e:
                logger.error("Failed to parse match_data for job %s: %s", row["id"], e)

        screening_questions: List[ScreeningQuestion] = []
        if row["screening_questions"]:
            try:
                sq_list = json.loads(row["screening_questions"])
                screening_questions = [ScreeningQuestion(**sq) for sq in sq_list]
            except Exception as e:
                logger.error("Failed to parse screening_questions for job %s: %s", row["id"], e)

        raw_data: Dict[str, Any] = {}
        if row["raw_data"]:
            try:
                raw_data = json.loads(row["raw_data"])
            except Exception:
                pass

        created_dt = datetime.fromisoformat(row["created_at"]) if row["created_at"] else datetime.now(timezone.utc)
        updated_dt = datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else datetime.now(timezone.utc)

        return Job(
            id=row["id"],
            platform=PlatformEnum(row["platform"]) if row["platform"] in PlatformEnum._value2member_map_ else PlatformEnum.OTHER,
            title=row["title"],
            company=row["company"],
            location=row["location"],
            salary=row["salary"],
            salary_min=row["salary_min"],
            salary_max=row["salary_max"],
            salary_currency=row["salary_currency"] or "IDR",
            url=row["url"],
            description=row["description"] or "",
            posted_date=row["posted_date"],
            work_type=row["work_type"],
            status=ApplicationStatus(row["status"]),
            match_result=match_result,
            screening_questions=screening_questions,
            cv_language=row["cv_language"] or "EN",
            screenshot_path=row["screenshot_path"],
            raw_data=raw_data,
            created_at=created_dt,
            updated_at=updated_dt,
        )


# Global Database Instance
db = Database()
