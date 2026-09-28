"""
LinkedIn public guest job search scraper.
Scrapes live job postings in Indonesia without authentication or Cloudflare blocks.
"""

from __future__ import annotations

import asyncio
import re
from typing import Any, Dict, List, Optional
from urllib.parse import quote, urljoin
from bs4 import BeautifulSoup

from src.core.logger import get_logger
from src.core.models import ApplicationStatus, Job, PlatformEnum
from src.scrapers.base import BaseScraper

logger = get_logger(__name__)


class LinkedInScraper(BaseScraper):
    """Scraper implementation for LinkedIn Public Jobs (Guest API)."""

    SEARCH_API_URL = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
    JOB_DETAIL_URL = "https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}"
    BASE_WEB_URL = "https://www.linkedin.com"

    def __init__(self) -> None:
        super().__init__(
            name="LinkedIn",
            platform=PlatformEnum.LINKEDIN,
            base_url=self.BASE_WEB_URL,
        )

    def get_default_headers(self) -> Dict[str, str]:
        headers = super().get_default_headers()
        headers.update({
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,id;q=0.8",
        })
        return headers

    async def search(
        self,
        keywords: List[str],
        locations: List[str],
        limit_per_keyword: int = 10,
    ) -> List[Job]:
        """Search LinkedIn across specified keywords and locations."""
        all_jobs: List[Job] = []
        seen_urls: set[str] = set()

        target_loc = "Indonesia"

        for kw in keywords[:3]:
            logger.info("[%s] Searching for '%s' in '%s'", self.name, kw, target_loc)
            jobs = await self._search_combo(kw, target_loc, limit_per_keyword)
            for j in jobs:
                if j.url not in seen_urls:
                    seen_urls.add(j.url)
                    all_jobs.append(j)
            await asyncio.sleep(1.0)

        logger.info("[%s] Found %d total unique jobs", self.name, len(all_jobs))
        return all_jobs


    async def _search_combo(self, keyword: str, location: str, limit: int) -> List[Job]:
        """Fetch and parse LinkedIn guest search HTML."""
        params = {
            "keywords": keyword,
            "location": location,
            "start": 0,
        }

        html = await self.fetch_url(self.SEARCH_API_URL, params=params, is_json=False)
        if not html:
            return []

        results: List[Job] = []
        soup = BeautifulSoup(html, "html.parser")
        cards = soup.find_all("li")

        for card in cards[:limit]:
            try:
                title_elem = card.find("h3", class_=re.compile(r"base-search-card__title|job-search-card__title"))
                if not title_elem:
                    continue
                title = title_elem.get_text(strip=True)

                comp_elem = card.find("h4", class_=re.compile(r"base-search-card__subtitle|job-search-card__subtitle"))
                company = comp_elem.get_text(strip=True) if comp_elem else "Confidential Company"

                loc_elem = card.find("span", class_=re.compile(r"job-search-card__location"))
                location_text = loc_elem.get_text(strip=True) if loc_elem else location

                link_elem = card.find("a", class_=re.compile(r"base-card__full-link"))
                if not link_elem:
                    link_elem = card.find("a")
                if not link_elem:
                    continue

                raw_url = link_elem.get("href", "")
                clean_url = raw_url.split("?")[0] if raw_url else ""
                if not clean_url:
                    continue

                time_elem = card.find("time")
                posted_date = time_elem.get("datetime") or time_elem.get_text(strip=True) if time_elem else None

                job = Job(
                    platform=PlatformEnum.LINKEDIN,
                    title=title,
                    company=company,
                    location=location_text,
                    url=clean_url,
                    posted_date=posted_date,
                    status=ApplicationStatus.DISCOVERED,
                )
                results.append(job)
            except Exception as e:
                logger.debug("[%s] Error parsing LinkedIn card: %s", self.name, e)
                continue

        return results

    async def fetch_job_details(self, job: Job) -> Job:
        """Fetch full job description from LinkedIn guest job posting endpoint."""
        # Extract job ID from URL
        match = re.search(r"-(\d+)$", job.url)
        if not match:
            match = re.search(r"/view/(\d+)", job.url)

        if match:
            job_id = match.group(1)
            detail_url = self.JOB_DETAIL_URL.format(job_id=job_id)
            html = await self.fetch_url(detail_url, is_json=False)
            if html:
                soup = BeautifulSoup(html, "html.parser")
                desc_elem = soup.find("div", class_=re.compile(r"show-more-less-html__markup|description__text"))
                if desc_elem:
                    job.description = desc_elem.get_text(separator="\n", strip=True)
                    return job

        return job
