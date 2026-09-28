"""
Glints Indonesia job scraper.
Supports Glints API and Next.js / HTML DOM fallback parsing.
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


class GlintsScraper(BaseScraper):
    """Scraper implementation for Glints (Indonesia & Southeast Asia)."""

    BASE_WEB_URL = "https://glints.com"
    API_SEARCH_URL = "https://glints.com/api/job-posts"
    GRAPHQL_URL = "https://glints.com/api/graphql"

    def __init__(self) -> None:
        super().__init__(
            name="Glints",
            platform=PlatformEnum.GLINTS,
            base_url=self.BASE_WEB_URL,
        )

    def get_default_headers(self) -> Dict[str, str]:
        headers = super().get_default_headers()
        headers.update({
            "Accept": "application/json, text/plain, */*",
            "Origin": self.BASE_WEB_URL,
            "Referer": f"{self.BASE_WEB_URL}/id/opportunities/jobs/explore",
        })
        return headers

    async def search(
        self,
        keywords: List[str],
        locations: List[str],
        limit_per_keyword: int = 15,
    ) -> List[Job]:
        """Search Glints across specified keywords and locations."""
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
        # 1. Try Next.js Page & __NEXT_DATA__
        html_jobs = await self._search_html(keyword, location, limit)
        if html_jobs:
            return html_jobs

        # 2. Try REST API endpoint
        api_params = {
            "keyword": keyword,
            "country": "ID",
            "cityName": location if location.lower() != "indonesia" else "",
            "limit": limit,
            "page": 1,
        }
        data = await self.fetch_url(self.API_SEARCH_URL, params=api_params, is_json=True)
        if data and isinstance(data, dict):
            raw_jobs = data.get("data", []) or data.get("jobPosts", [])
            if raw_jobs and isinstance(raw_jobs, list):
                return self._parse_glints_jobs(raw_jobs)[:limit]

        return []

    def _parse_glints_jobs(self, items: List[Dict[str, Any]]) -> List[Job]:
        """Parse structured Glints job objects."""
        results: List[Job] = []
        for item in items:
            try:
                job_id = str(item.get("id", ""))
                title = item.get("title", "").strip()
                if not title:
                    continue

                company_obj = item.get("company", {})
                company_name = company_obj.get("name", "Confidential") if isinstance(company_obj, dict) else "Confidential"

                # Location & Remote
                cities = item.get("cities", [])
                city_str = ", ".join(c.get("name", "") for c in cities if isinstance(c, dict)) if cities else ""
                country = item.get("country", {}).get("name", "Indonesia") if isinstance(item.get("country"), dict) else "Indonesia"
                is_remote = item.get("isRemote", False)
                location = city_str or country
                if is_remote:
                    location = f"{location} (Remote)" if location else "Remote"

                # Salary
                sal_min = item.get("minSalary")
                sal_max = item.get("maxSalary")
                currency = item.get("currency", "IDR") or "IDR"
                display_sal = None
                if sal_min or sal_max:
                    display_sal = f"{currency} {sal_min:,.0f} - {sal_max:,.0f}" if sal_min and sal_max else f"{currency} {sal_min or sal_max:,.0f}"

                # URL
                slug = item.get("slug") or job_id
                url = f"{self.BASE_WEB_URL}/id/opportunities/jobs/{slug}"

                description = item.get("description") or item.get("jobDescription") or ""
                if description and ("<p>" in description or "<div>" in description):
                    soup = BeautifulSoup(description, "html.parser")
                    description = soup.get_text(separator="\n", strip=True)

                work_type = "Remote" if is_remote else item.get("type") or item.get("jobType")

                job = Job(
                    platform=PlatformEnum.GLINTS,
                    title=title,
                    company=company_name,
                    location=location,
                    salary=display_sal,
                    salary_min=float(sal_min) if sal_min else None,
                    salary_max=float(sal_max) if sal_max else None,
                    salary_currency=currency,
                    url=url,
                    description=description,
                    posted_date=item.get("createdAt") or item.get("updatedAt"),
                    work_type=work_type,
                    status=ApplicationStatus.DISCOVERED,
                    raw_data=item,
                )
                results.append(job)
            except Exception as e:
                logger.debug("[%s] Error parsing job item: %s", self.name, e)
                continue

        return results

    async def _search_html(self, keyword: str, location: str, limit: int) -> List[Job]:
        """Search Glints opportunities explore page and extract __NEXT_DATA__."""
        kw_enc = quote(keyword)
        url = f"{self.BASE_WEB_URL}/id/opportunities/jobs/explore?keyword={kw_enc}&country=ID"

        html = await self.fetch_url(url, is_json=False)
        if not html:
            return []

        soup = BeautifulSoup(html, "html.parser")
        next_script = soup.find("script", id="__NEXT_DATA__")
        if next_script and next_script.string:
            try:
                data = json.loads(next_script.string)
                page_props = data.get("props", {}).get("pageProps", {})
                
                # Check different JSON paths where Glints stores job listings
                job_posts = (
                    page_props.get("initialReduxState", {}).get("exploreJobs", {}).get("data", {}).get("jobPosts", [])
                    or page_props.get("exploreJobs", {}).get("data", {}).get("jobPosts", [])
                    or page_props.get("jobPosts", [])
                    or page_props.get("data", {}).get("jobs", [])
                )
                if job_posts and isinstance(job_posts, list):
                    parsed = self._parse_glints_jobs(job_posts)
                    if parsed:
                        return parsed[:limit]
            except Exception as e:
                logger.debug("[%s] Could not parse __NEXT_DATA__: %s", self.name, e)

        # Fallback to HTML card extraction
        results: List[Job] = []
        cards = soup.select('div[class*="JobCardsc__JobcardContainer"], div[class*="CompactOpportunityCardsc__Card"], div[class*="JobCard"]')
        for card in cards[:limit]:
            try:
                title_elem = card.select_one('h2[class*="JobTitle"], h3[class*="JobTitle"], a[class*="JobTitle"]')
                link_elem = card.select_one('a[href*="/opportunities/jobs/"]') or card.select_one('a')
                if not title_elem or not link_elem:
                    continue

                title = title_elem.get_text(strip=True)
                href = link_elem.get("href", "")
                full_url = urljoin(self.BASE_WEB_URL, href)

                comp_elem = card.select_one('a[class*="CompanyLink"], div[class*="CompanyName"]')
                company = comp_elem.get_text(strip=True) if comp_elem else "Confidential Company"

                loc_elem = card.select_one('div[class*="Location"], span[class*="Location"]')
                location_text = loc_elem.get_text(strip=True) if loc_elem else location

                sal_elem = card.select_one('span[class*="Salary"], div[class*="Salary"]')
                salary_raw = sal_elem.get_text(strip=True) if sal_elem else None
                display_sal, sal_min, sal_max, currency = self.parse_salary(salary_raw)

                job = Job(
                    platform=PlatformEnum.GLINTS,
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
        """Fetch full job details from Glints opportunity page."""
        html = await self.fetch_url(job.url, is_json=False)
        if not html:
            return job

        soup = BeautifulSoup(html, "html.parser")
        next_script = soup.find("script", id="__NEXT_DATA__")
        if next_script and next_script.string:
            try:
                data = json.loads(next_script.string)
                page_props = data.get("props", {}).get("pageProps", {})
                job_data = (
                    page_props.get("jobPost", {})
                    or page_props.get("opportunity", {})
                    or page_props.get("data", {})
                )
                if job_data:
                    desc = job_data.get("description") or job_data.get("jobDescription")
                    if desc:
                        soup_desc = BeautifulSoup(desc, "html.parser")
                        job.description = soup_desc.get_text(separator="\n", strip=True)
                        return job
            except Exception as e:
                logger.debug("[%s] Error extracting detail __NEXT_DATA__: %s", self.name, e)

        # Fallback to DOM elements
        desc_elem = soup.select_one('div[class*="DescriptionSection"], div[class*="JobDescription"], div[id="job-description"]')
        if desc_elem:
            job.description = desc_elem.get_text(separator="\n", strip=True)

        return job
