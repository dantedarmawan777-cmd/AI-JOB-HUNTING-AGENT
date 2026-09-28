"""
Core modules for Job Hunting Automation Agent.
"""

from src.core.logger import get_logger, setup_root_logging
from src.core.models import (
    ApplicationStatus,
    AutoApplyResult,
    CandidateEducation,
    CandidateExperience,
    CandidateProfile,
    Job,
    MatchResult,
    PlatformEnum,
    SalaryExpectation,
    ScreeningQuestion,
    ScreeningQuestionType,
)
from src.core.database import Database, db

__all__ = [
    "get_logger",
    "setup_root_logging",
    "ApplicationStatus",
    "AutoApplyResult",
    "CandidateEducation",
    "CandidateExperience",
    "CandidateProfile",
    "Job",
    "MatchResult",
    "PlatformEnum",
    "SalaryExpectation",
    "ScreeningQuestion",
    "ScreeningQuestionType",
    "Database",
    "db",
]
