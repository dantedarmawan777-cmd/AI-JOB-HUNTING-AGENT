"""
Scrapers package for JobStreet, Glints, and Kalibrr.
"""

from src.scrapers.base import BaseScraper
from src.scrapers.jobstreet import JobStreetScraper
from src.scrapers.glints import GlintsScraper
from src.scrapers.kalibrr import KalibrrScraper
from src.scrapers.manager import ScraperManager, scraper_manager

__all__ = [
    "BaseScraper",
    "JobStreetScraper",
    "GlintsScraper",
    "KalibrrScraper",
    "ScraperManager",
    "scraper_manager",
]
