"""
Structured logging module for the Job Hunting Automation system.
Provides clean, consistent, and context-rich log outputs across all services.
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import Optional


class CustomFormatter(logging.Formatter):
    """Clean, high-visibility formatter with ANSI color support for terminal output."""

    # ANSI Colors
    GREY = "\x1b[38;20m"
    CYAN = "\x1b[36;20m"
    GREEN = "\x1b[32;20m"
    YELLOW = "\x1b[33;20m"
    RED = "\x1b[31;20m"
    BOLD_RED = "\x1b[31;1m"
    RESET = "\x1b[0m"

    FORMAT_TEMPLATE = "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d - %(message)s"
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

    FORMATS = {
        logging.DEBUG: CYAN + FORMAT_TEMPLATE + RESET,
        logging.INFO: GREEN + FORMAT_TEMPLATE + RESET,
        logging.WARNING: YELLOW + FORMAT_TEMPLATE + RESET,
        logging.ERROR: RED + FORMAT_TEMPLATE + RESET,
        logging.CRITICAL: BOLD_RED + FORMAT_TEMPLATE + RESET,
    }

    def format(self, record: logging.LogRecord) -> str:
        log_fmt = self.FORMATS.get(record.levelno, self.FORMAT_TEMPLATE)
        formatter = logging.Formatter(log_fmt, datefmt=self.DATE_FORMAT)
        return formatter.format(record)


_LOGGERS: dict[str, logging.Logger] = {}
_INITIALIZED = False


def setup_root_logging(
    log_level: int = logging.INFO,
    log_file: Optional[Path | str] = None,
) -> None:
    """Initialize root logging configuration once."""
    global _INITIALIZED
    if _INITIALIZED:
        return

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Console Handler with Color Formatter
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(CustomFormatter())
    root_logger.addHandler(console_handler)

    # File Handler (Plain text, no ANSI codes)
    if log_file:
        file_path = Path(log_file)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(file_path, encoding="utf-8")
        file_handler.setLevel(log_level)
        plain_formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        file_handler.setFormatter(plain_formatter)
        root_logger.addHandler(file_handler)

    # Mute overly chatty 3rd party libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("telegram").setLevel(logging.INFO)

    _INITIALIZED = True


def get_logger(name: str = "job_agent") -> logging.Logger:
    """
    Get a structured logger instance for a given module.

    Args:
        name: Name of the module or component.

    Returns:
        Configured Logger instance.
    """
    if not _INITIALIZED:
        env_level = os.getenv("LOG_LEVEL", "INFO").upper()
        level = getattr(logging, env_level, logging.INFO)
        log_file = os.getenv("LOG_FILE", "data/logs/app.log")
        setup_root_logging(log_level=level, log_file=log_file)

    if name not in _LOGGERS:
        logger = logging.getLogger(name)
        _LOGGERS[name] = logger

    return _LOGGERS[name]
