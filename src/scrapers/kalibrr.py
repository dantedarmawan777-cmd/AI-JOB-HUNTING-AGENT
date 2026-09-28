"""
Kalibrr scraper for Indonesian and regional opportunities.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional
from urllib.parse import quote, urljoin
from bs4 import BeautifulSoup

from src.core.logger import get_logger
from src.core.models import ApplicationStatus, Job, PlatformEnum
from src.scrapers.base import BaseScraper

logger = get_logger(__name__)


class KalibrrScraper(BaseScraper):
    """Scraper implementation for Kalibrr."""

    BASE_WEB_URL = "https://www.kalibrr.com"
    API_SEARCH_URL = "https://www.kalibrr.com/api/job_board/search"

    def __init__(self) -> None:
        super().__init__(
            name="Kalibrr",
            platform=PlatformEnum.KALIBRR,
            base_url=self.BASE_WEB_URL,
        )

    async def search(
        self,
        keywords: List[str],
        locations: List[str],
        limit_per_keyword: int = 15,
    ) -> List[Job]:
        """Search Kalibrr across specified keywords and locations."""
        all_jobs: List[Job] = []
        seen_urls: set[str] = set()

        for kw in keywords:
            for loc in locations:
                logger.info("[%s] Searching for '%s' in '%s'", self.name, kw, loc)
                jobs = await self._search_combo(kw, loc, limit_per_keyword)
                for j in jobs:
                    if j.url not in seen_urls:
                        seen_urls.add(j.url)
                        all_jobs.append(j)

        logger.info("[%s] Found %d total unique jobs", self.name, len(all_jobs))
        return all_jobs

    async def _search_combo(self, keyword: str, location: str, limit: int) -> List[Job]:
        """Search single keyword / location combo."""
        # 1. Kalibrr API
        params = {
            "keywords": keyword,
            "countries": "Indonesia",
            "limit": limit,
            "offset": 0,
        }
        data = await self.fetch_url(self.API_SEARCH_URL, params=params, is_json=True)
        if data and isinstance(data, dict):
            raw_jobs = data.get("jobs", [])
            if raw_jobs and isinstance(raw_jobs, list):
                return self._parse_kalibrr_jobs(raw_jobs)

        # 2. Fallback to HTML
        return await self._search_html(keyword, location, limit)

    def _parse_kalibrr_jobs(self, items: List[Dict[str, Any]]) -> List[Job]:
        """Parse structured Kalibrr API records."""
        results: List[Job] = []
        for item in items:
            try:
                title = item.get("name", "").strip()
                if not title:
                    continue

                company = item.get("company_info", {}).get("name") or item.get("company_name", "Confidential")
                loc_info = item.get("google_location", {}) or {}
                location_str = loc_info.get("address_components", {}).get("city") or item.get("location", "Indonesia")
                if isinstance(location_str, dict):
                    location_str = str(location_str.get("name", "Indonesia"))

                sal_min = item.get("salary_min")
                sal_max = item.get("salary_max")
                currency = item.get("salary_currency", "IDR") or "IDR"
                display_sal = None
                if sal_min or sal_max:
                    display_sal = f"{currency} {sal_min:,.0f} - {sal_max:,.0f}" if sal_min and sal_max else f"{currency} {sal_min or sal_max:,.0f}"

                slug = item.get("slug", "")
                company_slug = item.get("company_info", {}).get("slug", "") or item.get("company_slug", "")
                job_id = item.get("id", "")
                
                if company_slug and slug:
                    url = f"{self.BASE_WEB_URL}/c/{company_slug}/jobs/{job_id}/{slug}"
                elif job_id:
                    url = f"{self.BASE_WEB_URL}/job-board/te/{slug or job_id}"
                else:
                    continue

                description = item.get("job_description") or ""
                qualifications = item.get("qualifications") or ""
                full_desc = f"{description}\n\nQualifications:\n{qualifications}".strip()
                if "<p>" in full_desc or "<br" in full_desc:
                    soup = BeautifulSoup(full_desc, "html.parser")
                    full_desc = soup.get_text(separator="\n", strip=True)

                job = Job(
                    platform=PlatformEnum.KALIBRR,
                    title=title,
                    company=company,
                    location=str(location_str),
                    salary=display_sal,
                    salary_min=float(sal_min) if sal_min else None,
                    salary_max=float(sal_max) if sal_max else None,
                    salary_currency=currency,
                    url=url,
                    description=full_desc,
                    posted_date=item.get("created_at") or item.get("published_at"),
                    status=ApplicationStatus.DISCOVERED,
                    raw_data=item,
                )
                results.append(job)
            except Exception as e:
                logger.debug("[%s] Error parsing Kalibrr job: %s", self.name, e)
                continue

        return results

    async def _search_html(self, keyword: str, location: str, limit: int) -> List[Job]:
        """Scrape Kalibrr HTML search page."""
        kw_enc = quote(keyword.lower().replace(" ", "-"))
        url = f"{self.BASE_WEB_URL}/job-board/te/{kw_enc}/co/Indonesia"

        html = await self.fetch_url(url, is_json=False)
        if not html:
            return []

        results: List[Job] = []
        soup = BeautifulSoup(html, "html.parser")
        cards = soup.select('div[itemtype*="JobPosting"], div[class*="k-border-subtle"], div[class*="JobCard"]')

        for card in cards[:limit]:
            try:
                title_elem = card.select_one('h2 a, a[itemprop="title"], a[class*="k-font-bold"]')
                if not title_elem:
                    continue
                title = title_elem.get_text(strip=True)
                href = title_elem.get("href", "")
                full_url = urljoin(self.BASE_WEB_URL, href)

                comp_elem = card.select_one('a[class*="k-text-subdued"], span[itemprop="hiringOrganization"]')
                company = comp_elem.get_text(strip=True) if comp_elem else "Confidential"

                loc_elem = card.select_one('span[itemprop="jobLocation"], a[class*="k-text-subdued"]')
                location_text = loc_elem.get_text(strip=True) if loc_elem else location

                sal_elem = card.select_one('span[class*="salary"]')
                salary_raw = sal_elem.get_text(strip=True) if sal_elem else None
                display_sal, sal_min, sal_max, currency = self.parse_salary(salary_raw)

                job = Job(
                    platform=PlatformEnum.KALIBRR,
                    title=title,
                    company=company,
                    location=location_text,
                    salary=display_sal,
                    salary_min=sal_min,
                    salary_max=sal_max,
                    salary_currency=currency,
                    url=full_url,
                    description="",
                    status=ApplicationStatus.DISCOVERED,
                )
                results.append(job)
            except Exception as e:
                logger.debug("[%s] Error parsing HTML card: %s", self.name, e)
                continue

        return results

    async def fetch_job_details(self, job: Job) -> Job:
        """Fetch full job details from Kalibrr job listing page."""
        html = await self.fetch_url(job.url, is_json=False)
        if not html:
            return job

        soup = BeautifulSoup(html, "html.parser")
        desc_elem = soup.select_one('div[itemprop="description"], div[class*="description"]')
        if desc_elem:
            job.description = desc_elem.get_text(separator="\n", strip=True)

        return job
