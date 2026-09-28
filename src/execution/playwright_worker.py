"""
Playwright browser worker module.
Manages persistent browser profiles, anti-detection stealth configuration,
and browser lifecycle for web automation.
"""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Optional
from playwright.async_api import (
    BrowserContext,
    Page,
    Playwright,
    async_playwright,
)

from config import config
from src.core.logger import get_logger

logger = get_logger(__name__)


# Stealth script to mask automated browser fingerprints
STEALTH_INJECTION_SCRIPT = """
Object.defineProperty(navigator, 'webdriver', {
    get: () => undefined
});

Object.defineProperty(navigator, 'plugins', {
    get: () => [1, 2, 3, 4, 5]
});

Object.defineProperty(navigator, 'languages', {
    get: () => ['id-ID', 'id', 'en-US', 'en']
});

window.chrome = {
    runtime: {}
};
"""


class PlaywrightWorker:
    """Manages persistent browser lifecycle and page automation."""

    def __init__(
        self,
        user_data_dir: Optional[Path | str] = None,
        headless: Optional[bool] = None,
    ) -> None:
        self.user_data_dir = Path(user_data_dir) if user_data_dir else config.browser_profile_dir
        self.headless = headless if headless is not None else config.headless
        self.user_data_dir.mkdir(parents=True, exist_ok=True)

        self._playwright: Optional[Playwright] = None
        self._context: Optional[BrowserContext] = None
        self._lock = asyncio.Lock()

    async def get_context(self) -> BrowserContext:
        """
        Acquire or initialize persistent browser context.
        Ensures persistent login cookies & session data are maintained across runs.
        """
        async with self._lock:
            if self._context is None:
                if self._playwright is None:
                    self._playwright = await async_playwright().start()

                logger.info(
                    "Launching Playwright Persistent Context (Headless: %s, Profile: %s)",
                    self.headless, self.user_data_dir
                )

                launch_args = [
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-infobars",
                    "--disable-dev-shm-usage",
                    "--disable-extensions",
                    "--no-first-run",
                    "--window-size=1280,800",
                ]

                self._context = await self._playwright.chromium.launch_persistent_context(
                    user_data_dir=str(self.user_data_dir),
                    headless=self.headless,
                    args=launch_args,
                    viewport={"width": 1280, "height": 800},
                    user_agent=(
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
                    ),
                    locale="id-ID",
                    timezone_id="Asia/Jakarta",
                    accept_downloads=True,
                )

                # Add init stealth scripts
                await self._context.add_init_script(STEALTH_INJECTION_SCRIPT)

            return self._context

    async def new_page(self) -> Page:
        """Open a new tab with standard timeouts."""
        context = await self.get_context()
        page = await context.new_page()
        page.set_default_timeout(20000)  # 20s
        page.set_default_navigation_timeout(30000)  # 30s
        return page

    async def capture_screenshot(self, page: Page, name_prefix: str) -> Path:
        """
        Capture high-resolution screenshot and save to screenshots directory.
        """
        config.screenshots_dir.mkdir(parents=True, exist_ok=True)
        screenshot_path = config.screenshots_dir / f"{name_prefix}.png"
        try:
            await page.screenshot(path=str(screenshot_path), full_page=True)
            logger.info("Screenshot captured at: %s", screenshot_path)
        except Exception as e:
            logger.warning("Full-page screenshot failed, trying viewport screenshot: %s", e)
            try:
                await page.screenshot(path=str(screenshot_path), full_page=False)
            except Exception as e2:
                logger.error("Failed to capture screenshot: %s", e2)
        return screenshot_path

    async def close(self) -> None:
        """Close browser context and stop Playwright."""
        async with self._lock:
            if self._context:
                try:
                    await self._context.close()
                except Exception as e:
                    logger.debug("Error closing context: %s", e)
                self._context = None

            if self._playwright:
                try:
                    await self._playwright.stop()
                except Exception as e:
                    logger.debug("Error stopping playwright: %s", e)
                self._playwright = None
            logger.info("Playwright worker shutdown completed.")


# Global Playwright Worker
playwright_worker = PlaywrightWorker()
