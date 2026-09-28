"""
Pydantic data models for the Job Hunting Automation system.
Defines schemas for Jobs, Application Status, Screening Questions, Match Results, and Candidate Profile.
"""

from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class ApplicationStatus(str, Enum):
    """Lifecycle statuses for a job listing/application."""
    DISCOVERED = "discovered"              # Scraped and stored
    SHORTLISTED = "shortlisted"            # Passed match score threshold, awaiting HITL review
    APPROVED = "approved"                  # Approved by user in Telegram HITL
    REJECTED = "rejected"                  # Rejected by user or filtered out
    SUBMITTING = "submitting"              # Currently being processed by Playwright
    SUBMITTED = "submitted"                # Successfully applied
    FAILED = "failed"                      # Execution failed (login issue, captcha, etc.)
    INTERVIEW_INVITED = "interview_invited"  # Tracking downstream interview invitation


class PlatformEnum(str, Enum):
    """Supported job platforms."""
    JOBSTREET = "jobstreet"
    GLINTS = "glints"
    KALIBRR = "kalibrr"
    LINKEDIN = "linkedin"
    OTHER = "other"


class ScreeningQuestionType(str, Enum):
    """Form field input types for application screening."""
    TEXT = "text"
    NUMBER = "number"
    SELECT = "select"
    RADIO = "radio"
    CHECKBOX = "checkbox"
    DATE = "date"
    FILE = "file"


class ScreeningQuestion(BaseModel):
    """Represents a pre-application screening or custom question."""
    id: str = Field(default_factory=lambda: "")
    question: str
    question_type: ScreeningQuestionType = ScreeningQuestionType.TEXT
    options: List[str] = Field(default_factory=list)
    answer: Optional[str] = None
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    required: bool = True

    def model_post_init(self, __context: Any) -> None:
        if not self.id:
            # Generate deterministic hash for the question text
            clean_q = re.sub(r"\s+", " ", self.question.strip().lower())
            self.id = hashlib.md5(clean_q.encode("utf-8")).hexdigest()[:10]


class MatchResult(BaseModel):
    """Evaluated match analysis between a Job description and Candidate Profile."""
    score: int = Field(ge=0, le=100, description="Match score from 0 to 100")
    reasoning: str = Field(default="", description="High level summary of the fit")
    matching_points: List[str] = Field(default_factory=list, description="Strengths & matching skills")
    missing_points: List[str] = Field(default_factory=list, description="Gaps or missing requirements")
    recommended_action: str = Field(default="APPLY", description="Recommended action: APPLY, REVIEW, SKIP")
    salary_fit: Optional[str] = None
    location_fit: Optional[str] = None
    evaluated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Job(BaseModel):
    """Unified job listing model across all scraping sources."""
    id: str = Field(default="")
    platform: PlatformEnum = PlatformEnum.OTHER
    title: str
    company: str
    location: str
    salary: Optional[str] = None
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: Optional[str] = "IDR"
    url: str
    description: str = ""
    posted_date: Optional[str] = None
    work_type: Optional[str] = None  # e.g., "Full-time", "Hybrid", "Remote"
    status: ApplicationStatus = ApplicationStatus.DISCOVERED
    match_result: Optional[MatchResult] = None
    screening_questions: List[ScreeningQuestion] = Field(default_factory=list)
    cv_language: str = Field(default="EN", description="CV Language to submit: 'EN' or 'ID'")
    screenshot_path: Optional[str] = None
    raw_data: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def model_post_init(self, __context: Any) -> None:
        if not self.id:
            self.id = self.generate_id(self.platform, self.company, self.title, self.url)

    @staticmethod
    def generate_id(platform: PlatformEnum | str, company: str, title: str, url: str) -> str:
        """Create a deterministic unique ID based on platform, company, title and URL."""
        plat_str = platform.value if isinstance(platform, PlatformEnum) else str(platform)
        # Normalize strings
        norm_key = f"{plat_str.lower()}|{company.strip().lower()}|{title.strip().lower()}|{url.strip().lower()}"
        return f"{plat_str[:3]}_{hashlib.sha256(norm_key.encode('utf-8')).hexdigest()[:12]}"

    @property
    def is_shortlist_candidate(self) -> bool:
        """Checks if the job qualifies for Telegram HITL shortlisting."""
        if self.match_result and self.match_result.score >= 70:
            return True
        return False

    def get_display_salary(self) -> str:
        """Get formatted salary or default placeholder."""
        if self.salary and self.salary.strip():
            return self.salary.strip()
        if self.salary_min or self.salary_max:
            curr = self.salary_currency or "IDR"
            if self.salary_min and self.salary_max:
                return f"{curr} {self.salary_min:,.0f} - {self.salary_max:,.0f}"
            if self.salary_min:
                return f">= {curr} {self.salary_min:,.0f}"
            if self.salary_max:
                return f"<= {curr} {self.salary_max:,.0f}"
        return "Not disclosed"


# Candidate Profile Models
class CandidateExperience(BaseModel):
    company: str
    position: str
    period: str
    duration_years: float = 0.0
    location: str = ""
    highlights: List[str] = Field(default_factory=list)


class CandidateEducation(BaseModel):
    degree: str
    institution: str
    period: str
    gpa: Optional[str] = None


class SalaryExpectation(BaseModel):
    currency: str = "IDR"
    expected_min: float = 25_000_000
    expected_target: float = 35_000_000
    negotiable: bool = True


class CandidateProfile(BaseModel):
    """Structured candidate profile representation."""
    full_name: str
    title: str
    email: str
    phone: str
    linkedin: str
    locations: List[str] = Field(default_factory=list)
    work_flexibility: List[str] = Field(default_factory=list)
    total_years_experience: float = 0.0
    summary: str
    core_competencies: List[str] = Field(default_factory=list)
    experience: List[CandidateExperience] = Field(default_factory=list)
    education: List[CandidateEducation] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    cv_files: Dict[str, str] = Field(default_factory=dict)
    salary_expectation: SalaryExpectation = Field(default_factory=SalaryExpectation)
    notice_period: str = "Immediately available / 1 month"


class AutoApplyResult(BaseModel):
    """Result payload from the Playwright execution worker."""
    job_id: str
    success: bool
    status: ApplicationStatus
    submitted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    screenshot_path: Optional[str] = None
    error_message: Optional[str] = None
    dry_run: bool = False
    answers_submitted: Dict[str, str] = Field(default_factory=dict)
