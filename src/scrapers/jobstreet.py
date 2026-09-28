"""
JobStreet Indonesia scraper.
Supports SEEK/JobStreet API v4 and Next.js / HTML DOM fallback parsing.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional
from urllib.parse import quote, urljoin
from bs4 import BeautifulSoup

from src.core.logger import get_logger
from src.core.models import ApplicationStatus, Job, PlatformEnum
from src.scrapers.base import BaseScraper

logger = get_logger(__name__)


class JobStreetScraper(BaseScraper):
    """Scraper implementation for JobStreet Indonesia (SEEK Network)."""

    API_SEARCH_URL = "https://id.jobstreet.com/api/chalice-search/v4/search"
    API_JOB_URL = "https://id.jobstreet.com/api/chalice-search/v4/job/{job_id}"
    BASE_WEB_URL = "https://id.jobstreet.com"

    def __init__(self) -> None:
        super().__init__(
            name="JobStreet",
            platform=PlatformEnum.JOBSTREET,
            base_url=self.BASE_WEB_URL,
        )

    def get_default_headers(self) -> Dict[str, str]:
        headers = super().get_default_headers()
        headers.update({
            "Accept": "application/json, text/plain, */*",
            "x-seek-site": "id-jobstreet",
            "x-seek-client-version": "1.0.0",
        })
        return headers

    async def search(
        self,
        keywords: List[str],
        locations: List[str],
        limit_per_keyword: int = 15,
    ) -> List[Job]:
        """Search JobStreet across specified keywords and locations."""
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
        """Search single keyword and location combination."""
        # 1. Try REST Search API first
        api_params = {
            "siteKey": "ID-Main",
            "keywords": keyword,
            "where": location,
            "page": 1,
            "pageSize": min(limit, 30),
            "sortMode": "ListedDate",
            "sourcesystem": "houston",
        }

        data = await self.fetch_url(
            self.API_SEARCH_URL,
            params=api_params,
            is_json=True,
        )

        if data and isinstance(data, dict) and "data" in data and isinstance(data["data"], list):
            jobs = self._parse_api_jobs(data["data"])
            if jobs:
                return jobs[:limit]

        # 2. Fallback to HTML Search
        return await self._search_html(keyword, location, limit)

    def _parse_api_jobs(self, items: List[Dict[str, Any]]) -> List[Job]:
        """Parse structured API JSON items from SEEK/JobStreet API."""
        results: List[Job] = []
        for item in items:
            try:
                job_id = str(item.get("id", ""))
                title = item.get("title", "").strip()
                if not title:
                    continue

                advertiser = item.get("advertiser", {})
                company = advertiser.get("description", "").strip() if isinstance(advertiser, dict) else "Confidential Company"
                if not company:
                    company = "Confidential Company"

                loc_info = item.get("locationHierarchy", {})
                location = loc_info.get("city") or loc_info.get("state") or loc_info.get("area") or item.get("location", "Indonesia")
                if isinstance(location, dict):
                    location = location.get("label", "Indonesia")

                salary_raw = item.get("salary")
                display_sal, sal_min, sal_max, currency = self.parse_salary(salary_raw)

                # URL
                web_url = f"{self.BASE_WEB_URL}/id/job/{job_id}" if job_id else ""
                if not web_url:
                    continue

                posted_date = item.get("listingDate") or item.get("listingDateDisplay")
                work_type = item.get("workType") or item.get("workArrangements", {}).get("text")
                teaser = item.get("teaser", "")
                bullets = item.get("bulletPoints", [])
                bullet_str = "\n".join(f"• {b}" for b in bullets if b)
                description = f"{teaser}\n\n{bullet_str}".strip()

                job = Job(
                    platform=PlatformEnum.JOBSTREET,
                    title=title,
                    company=company,
                    location=str(location),
                    salary=display_sal,
                    salary_min=sal_min,
                    salary_max=sal_max,
                    salary_currency=currency,
                    url=web_url,
                    description=description,
                    posted_date=posted_date,
                    work_type=work_type,
                    status=ApplicationStatus.DISCOVERED,
                    raw_data=item,
                )
                results.append(job)
            except Exception as e:
                logger.warning("[%s] Error parsing API item: %s", self.name, e)
                continue

        return results

    async def _search_html(self, keyword: str, location: str, limit: int) -> List[Job]:
        """Parse HTML search result page."""
        kw_slug = quote(keyword.lower().replace(" ", "-"))
        loc_slug = quote(location.lower().replace(" ", "-"))
        url = f"{self.BASE_WEB_URL}/id/job-search/{kw_slug}-jobs/in-{loc_slug}/?sortmode=listeddate"

        html = await self.fetch_url(url, is_json=False)
        if not html:
            return []

        results: List[Job] = []
        soup = BeautifulSoup(html, "html.parser")

        # Check for __NEXT_DATA__
        next_data_script = soup.find("script", id="__NEXT_DATA__")
        if next_data_script and next_data_script.string:
            try:
                next_json = json.loads(next_data_script.string)
                redux_state = (
                    next_json.get("props", {})
                    .get("pageProps", {})
                    .get("reduxState", {})
                )
                search_results = redux_state.get("searchResult", {}).get("results", {})
                raw_jobs = search_results.get("data", []) or search_results.get("jobs", [])
                if raw_jobs:
                    parsed = self._parse_api_jobs(raw_jobs)
                    if parsed:
                        return parsed[:limit]
            except Exception as e:
                logger.debug("[%s] Could not extract __NEXT_DATA__: %s", self.name, e)

        # Fallback to DOM elements
        card_elements = soup.select('article[data-automation="jobListing"], article[data-automation="jobCard"], div[data-automation="job-card"]')
        for card in card_elements[:limit]:
            try:
                title_elem = card.select_one('a[data-automation="job-card-title"], a[data-automation="jobTitle"]')
                if not title_elem:
                    continue
                title = title_elem.get_text(strip=True)
                href = title_elem.get("href", "")
                full_url = urljoin(self.BASE_WEB_URL, href)

                comp_elem = card.select_one('a[data-automation="jobCompany"], a[data-automation="jobCardCompany"]')
                company = comp_elem.get_text(strip=True) if comp_elem else "Confidential Company"

                loc_elem = card.select_one('a[data-automation="jobLocation"], span[data-automation="jobCardLocation"]')
                location_text = loc_elem.get_text(strip=True) if loc_elem else location

                sal_elem = card.select_one('span[data-automation="jobSalary"], span[data-automation="jobCardSalary"]')
                salary_raw = sal_elem.get_text(strip=True) if sal_elem else None
                display_sal, sal_min, sal_max, currency = self.parse_salary(salary_raw)

                teaser_elem = card.select_one('span[data-automation="jobTeaser"]')
                teaser = teaser_elem.get_text(strip=True) if teaser_elem else ""

                job = Job(
                    platform=PlatformEnum.JOBSTREET,
                    title=title,
                    company=company,
                    location=location_text,
                    salary=display_sal,
                    salary_min=sal_min,
                    salary_max=sal_max,
                    salary_currency=currency,
                    url=full_url,
                    description=teaser,
                    status=ApplicationStatus.DISCOVERED,
                )
                results.append(job)
            except Exception as e:
                logger.debug("[%s] Error parsing DOM card: %s", self.name, e)
                continue

        return results

    async def fetch_job_details(self, job: Job) -> Job:
        """Fetch full job advertisement description and screening questions if available."""
        # Extract JobStreet Job ID from URL (e.g., /id/job/123456)
        match = re.search(r"/job/(\d+)", job.url)
        if match:
            job_id = match.group(1)
            api_url = self.API_JOB_URL.format(job_id=job_id)
            params = {"siteKey": "ID-Main"}
            detail_data = await self.fetch_url(api_url, params=params, is_json=True)
            if detail_data and isinstance(detail_data, dict):
                job_ad = detail_data.get("jobAd", {}) or detail_data
                desc_html = job_ad.get("jobAdDetails") or job_ad.get("content", "")
                if desc_html:
                    soup = BeautifulSoup(desc_html, "html.parser")
                    job.description = soup.get_text(separator="\n", strip=True)
                    return job

        # Fallback to HTML details page
        html = await self.fetch_url(job.url, is_json=False)
        if html:
            soup = BeautifulSoup(html, "html.parser")
            desc_elem = soup.select_one('div[data-automation="jobAdDetails"]')
            if desc_elem:
                job.description = desc_elem.get_text(separator="\n", strip=True)

        return job
