"""
Base scraper abstraction for the Job Hunting Automation system.
Defines common networking, retry logic, headers spoofing, and parsing utilities.
"""

from __future__ import annotations

import asyncio
import random
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple
import aiohttp

from src.core.logger import get_logger
from src.core.models import Job, PlatformEnum

logger = get_logger(__name__)

DESKTOP_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Safari/605.1.15",
]


class BaseScraper(ABC):
    """Abstract base class for all job board scrapers."""

    def __init__(self, name: str, platform: PlatformEnum, base_url: str) -> None:
        self.name = name
        self.platform = platform
        self.base_url = base_url
        self._session: Optional[aiohttp.ClientSession] = None

    async def get_session(self) -> aiohttp.ClientSession:
        """Acquire or create an async HTTP client session bound to the active event loop."""
        try:
            current_loop = asyncio.get_running_loop()
        except RuntimeError:
            current_loop = None

        is_invalid = (
            self._session is None
            or self._session.closed
            or (current_loop and getattr(self._session, "_loop", None) != current_loop)
            or (self._session._loop and self._session._loop.is_closed())
        )

        if is_invalid:
            if self._session and not self._session.closed:
                try:
                    await self._session.close()
                except Exception:
                    pass
            timeout = aiohttp.ClientTimeout(total=25, connect=10)
            connector = aiohttp.TCPConnector(limit=10, ssl=False)
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                connector=connector,
                headers=self.get_default_headers(),
            )
        return self._session

    def get_default_headers(self) -> Dict[str, str]:
        """Generate realistic browser-like request headers."""
        return {
            "User-Agent": random.choice(DESKTOP_USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,application/json,*/*;q=0.8",
            "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-User": "?1",
        }

    async def close(self) -> None:
        """Close the underlying aiohttp session."""
        if self._session and not self._session.closed:
            try:
                await self._session.close()
            except Exception:
                pass
            self._session = None

    async def __aenter__(self) -> BaseScraper:
        await self.get_session()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.close()

    async def fetch_url(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        is_json: bool = False,
        retries: int = 3,
        backoff_seconds: float = 1.5,
    ) -> Optional[Any]:
        """
        Fetch URL with exponential backoff and rate limit handling.
        """
        req_headers = {**self.get_default_headers(), **(headers or {})}

        for attempt in range(1, retries + 1):
            try:
                session = await self.get_session()
                async with session.get(url, params=params, headers=req_headers) as response:
                    if response.status == 200:
                        if is_json:
                            return await response.json(content_type=None)
                        return await response.text()
                    elif response.status == 429:
                        wait = backoff_seconds * (2 ** (attempt - 1))
                        logger.warning(
                            "[%s] Rate limited (429) on %s. Backing off for %.1fs (attempt %d/%d)",
                            self.name, url, wait, attempt, retries
                        )
                        await asyncio.sleep(wait)
                    elif response.status in (500, 502, 503, 504):
                        wait = backoff_seconds * attempt
                        logger.warning(
                            "[%s] Server error (%d) on %s. Retrying in %.1fs (attempt %d/%d)",
                            self.name, response.status, url, wait, attempt, retries
                        )
                        await asyncio.sleep(wait)
                    else:
                        logger.warning(
                            "[%s] Request to %s returned HTTP %d",
                            self.name, url, response.status
                        )
                        return None
            except asyncio.CancelledError:
                raise
            except Exception as e:
                logger.warning(
                    "[%s] Network error requesting %s (attempt %d/%d): %s",
                    self.name, url, attempt, retries, str(e)
                )
                if attempt < retries:
                    await asyncio.sleep(backoff_seconds * attempt)

        logger.error("[%s] Exhausted all %d retries for %s", self.name, retries, url)
        return None

    @staticmethod
    def parse_salary(salary_raw: Optional[str]) -> Tuple[Optional[str], Optional[float], Optional[float], Optional[str]]:
        """
        Parse raw salary strings into (display_str, min_val, max_val, currency).
        """
        if not salary_raw or not salary_raw.strip():
            return None, None, None, "IDR"

        raw = salary_raw.strip()
        currency = "IDR"
        if "sgd" in raw.lower() or "s$" in raw.lower():
            currency = "SGD"
        elif "usd" in raw.lower() or "$" in raw.lower():
            currency = "USD"
        elif "myr" in raw.lower() or "rm" in raw.lower():
            currency = "MYR"

        cleaned = re.sub(r"[^\d\s\-\–kKmM\.,]", "", raw)
        numbers = re.findall(r"\b\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?\b|\b\d+\b", cleaned)

        parsed_nums: List[float] = []
        for num_str in numbers:
            num_clean = num_str.replace(".", "").replace(",", "")
            try:
                val = float(num_clean)
                if "jt" in raw.lower() or "juta" in raw.lower():
                    if val < 1000:
                        val *= 1_000_000
                elif val < 1000 and ("k" in raw.lower() or "rb" in raw.lower()):
                    val *= 1_000
                parsed_nums.append(val)
            except ValueError:
                continue

        min_val = parsed_nums[0] if len(parsed_nums) >= 1 else None
        max_val = parsed_nums[1] if len(parsed_nums) >= 2 else (min_val if min_val else None)

        return raw, min_val, max_val, currency

    @abstractmethod
    async def search(
        self,
        keywords: List[str],
        locations: List[str],
        limit_per_keyword: int = 15,
    ) -> List[Job]:
        """Execute search on job board for specified keywords and locations."""
        pass

    @abstractmethod
    async def fetch_job_details(self, job: Job) -> Job:
        """Enrich job model with full description, requirements, and screening questions."""
        pass
