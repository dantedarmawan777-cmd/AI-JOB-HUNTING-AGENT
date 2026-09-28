"""
Scraper orchestration and pipeline manager.
Runs multi-source scrapers concurrently, performs deduplication,
evaluates candidate fit, and persists shortlisted candidates to SQLite.
"""

from __future__ import annotations

import asyncio
from typing import Dict, List, Optional, Type

from config import config
from src.core.database import db
from src.core.logger import get_logger
from src.core.models import ApplicationStatus, Job, PlatformEnum
from src.matcher.engine import matcher
from src.scrapers.base import BaseScraper
from src.scrapers.glints import GlintsScraper
from src.scrapers.jobstreet import JobStreetScraper
from src.scrapers.kalibrr import KalibrrScraper

logger = get_logger(__name__)


class ScraperManager:
    """Manages multi-platform scrapers with concurrency and deduplication."""

    def __init__(self) -> None:
        self.scrapers: Dict[PlatformEnum, BaseScraper] = {
            PlatformEnum.JOBSTREET: JobStreetScraper(),
            PlatformEnum.GLINTS: GlintsScraper(),
            PlatformEnum.KALIBRR: KalibrrScraper(),
        }

    async def close(self) -> None:
        """Gracefully close all underlying scraper sessions."""
        for name, scraper in self.scrapers.items():
            try:
                await scraper.close()
            except Exception as e:
                logger.warning("Error closing scraper %s: %s", name, e)

    async def run_all(
        self,
        keywords: Optional[List[str]] = None,
        locations: Optional[List[str]] = None,
        min_score: Optional[int] = None,
        limit_per_keyword: int = 15,
    ) -> List[Job]:
        """
        Execute concurrent scraping across all job platforms.

        Args:
            keywords: Override list of search keywords (defaults to config)
            locations: Override list of locations (defaults to config)
            min_score: Minimum match score threshold for shortlisting (defaults to config)
            limit_per_keyword: Max jobs per keyword combination

        Returns:
            List of newly discovered & shortlisted Job objects ready for Telegram review.
        """
        search_kws = keywords or config.search_keywords
        search_locs = locations or config.search_locations
        threshold = min_score if min_score is not None else config.min_match_score

        logger.info(
            "Starting multi-platform scraper run. Keywords: %d, Locations: %d, Threshold: %d",
            len(search_kws), len(search_locs), threshold
        )

        tasks = [
            scraper.search(keywords=search_kws, locations=search_locs, limit_per_keyword=limit_per_keyword)
            for scraper in self.scrapers.values()
        ]

        # Concurrently search all boards
        scraper_results = await asyncio.gather(*tasks, return_exceptions=True)

        all_scraped_jobs: List[Job] = []
        for scraper_instance, res in zip(self.scrapers.values(), scraper_results):
            if isinstance(res, Exception):
                logger.error("Scraper [%s] encountered fatal error: %s", scraper_instance.name, res)
            elif isinstance(res, list):
                logger.info("Scraper [%s] returned %d job postings", scraper_instance.name, len(res))
                all_scraped_jobs.extend(res)

        # Process, Deduplicate, Enrich & Score
        shortlisted_jobs: List[Job] = []
        for job in all_scraped_jobs:
            try:
                # Check DB deduplication
                if await db.job_exists(job.url):
                    logger.debug("Skipping existing job URL: %s", job.url)
                    continue

                # Enrich details if description is minimal
                if len(job.description.strip()) < 100:
                    scraper = self.scrapers.get(job.platform)
                    if scraper:
                        try:
                            job = await scraper.fetch_job_details(job)
                        except Exception as e:
                            logger.debug("Failed detail enrichment for %s: %s", job.url, e)

                # Match against Candidate Profile
                match_res = matcher.evaluate_job(job)
                job.match_result = match_res

                if match_res.score >= threshold:
                    job.status = ApplicationStatus.SHORTLISTED
                    logger.info(
                        "🌟 Shortlisted job [%s] '%s' at '%s' (Score: %d)",
                        job.platform.value, job.title, job.company, match_res.score
                    )
                    shortlisted_jobs.append(job)
                else:
                    job.status = ApplicationStatus.DISCOVERED
                    logger.debug(
                        "Job '%s' at '%s' did not meet threshold (Score: %d < %d)",
                        job.title, job.company, match_res.score, threshold
                    )

                # Save to database
                await db.save_job(job)

            except Exception as e:
                logger.error("Error processing job '%s' from %s: %s", job.title, job.platform, e)

        logger.info(
            "Scraper cycle completed. Discovered: %d, Shortlisted: %d",
            len(all_scraped_jobs), len(shortlisted_jobs)
        )
        return shortlisted_jobs


# Global Scraper Manager
scraper_manager = ScraperManager()
