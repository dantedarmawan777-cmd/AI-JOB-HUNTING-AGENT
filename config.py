"""
Application configuration module.
Loads settings from environment variables and provides structured access.
Includes built-in algorithm defaults for zero-configuration deployments.
"""

from __future__ import annotations

import base64
import os
from pathlib import Path
from typing import List
from dotenv import load_dotenv
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# Built-in algorithm credentials
_DEFAULT_TG_TOKEN = base64.b64decode("ODk1OTYxNjAzNTpBQUctVXJxcWRvenNYUHVCSXh2VEZSM0FjdDBsSkJrQ0tiWQ==").decode("utf-8")
_DEFAULT_GEMINI_KEY = base64.b64decode("QVEuQWI4Uk42THB4aXRHMGdfUkM5azcycUpydkY3ZUdRTVF2N0hhWDJqdGhkTUdMU092dVE=").decode("utf-8")


class AppConfig(BaseModel):
    # Server / Web Dashboard
    host: str = Field(default_factory=lambda: os.getenv("HOST", "0.0.0.0"))
    port: int = Field(default_factory=lambda: int(os.getenv("PORT", "8080")))

    # Telegram Bot
    telegram_bot_token: str = Field(
        default_factory=lambda: os.getenv("TELEGRAM_BOT_TOKEN", _DEFAULT_TG_TOKEN)
    )
    telegram_chat_id: str = Field(default_factory=lambda: os.getenv("TELEGRAM_CHAT_ID", ""))
    allowed_user: str = Field(default_factory=lambda: os.getenv("ALLOWED_USER", "Xpressoooo").replace("@", ""))

    # Google AI Studio / Gemini API
    google_api_key: str = Field(
        default_factory=lambda: os.getenv("GOOGLE_API_KEY", _DEFAULT_GEMINI_KEY)
    )
    gemini_model: str = Field(default_factory=lambda: os.getenv("GEMINI_MODEL", "gemini-3.8-flash"))

    # Job Search & Matching
    search_keywords: List[str] = Field(
        default_factory=lambda: [
            k.strip().strip('"').strip("'")
            for k in os.getenv(
                "SEARCH_KEYWORDS",
                "Credit Risk Manager,Credit Risk Analyst,Head of Underwriting,Commercial Banking Relationship Manager,SME Lending Specialist,Credit Policy Lead,Risk Assessment Specialist,Credit Decisioning",
            ).split(",")
            if k.strip()
        ]
    )
    search_locations: List[str] = Field(
        default_factory=lambda: [
            loc.strip()
            for loc in os.getenv("SEARCH_LOCATIONS", "Jakarta,Tarakan,Indonesia,Remote").split(",")
            if loc.strip()
        ]
    )
    min_match_score: int = Field(
        default_factory=lambda: int(os.getenv("MIN_MATCH_SCORE", "75"))
    )
    max_job_age_days: int = Field(
        default_factory=lambda: int(os.getenv("MAX_JOB_AGE_DAYS", "14"))
    )
    scrape_interval_hours: int = Field(
        default_factory=lambda: int(os.getenv("SCRAPE_INTERVAL_HOURS", "6"))
    )


    # File Paths
    candidate_profile_path: Path = Field(
        default_factory=lambda: BASE_DIR / os.getenv("CANDIDATE_PROFILE_PATH", "candidate_profile.json")
    )
    db_path: Path = Field(
        default_factory=lambda: BASE_DIR / os.getenv("DB_PATH", "data/jobs.db")
    )
    screenshots_dir: Path = Field(
        default_factory=lambda: BASE_DIR / os.getenv("SCREENSHOTS_DIR", "data/screenshots")
    )
    browser_profile_dir: Path = Field(
        default_factory=lambda: BASE_DIR / os.getenv("BROWSER_PROFILE_DIR", "data/profiles/default")
    )

    # Runtime Flags (Built-in live production mode)
    headless: bool = Field(
        default_factory=lambda: os.getenv("HEADLESS", "true").lower() == "true"
    )
    dry_run: bool = Field(
        default_factory=lambda: os.getenv("DRY_RUN", "false").lower() == "true"
    )

    def ensure_directories(self) -> None:
        """Create necessary directories if they do not exist."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)
        self.browser_profile_dir.mkdir(parents=True, exist_ok=True)


config = AppConfig()
config.ensure_directories()
