"""
Job matching intelligence engine.
Evaluates scraped job listings against candidate profile (Aditya Darmawan)
and computes match score, strengths, gaps, and recommendation.
"""

from __future__ import annotations

import re
from typing import List, Tuple
from datetime import datetime, timezone

from src.core.logger import get_logger
from src.core.models import CandidateProfile, Job, MatchResult
from src.matcher.profile_loader import load_candidate_profile

logger = get_logger(__name__)


class MatcherEngine:
    """Evaluates job fit against candidate profile."""

    def __init__(self, profile: CandidateProfile | None = None) -> None:
        self.profile = profile or load_candidate_profile()

        # Core Banking & Risk Keyword Taxonomies
        self.primary_keywords = [
            "credit risk", "underwriting", "underwriter", "credit analyst", "credit approval",
            "sme lending", "commercial banking", "relationship manager", "credit policy",
            "risk assessment", "credit decisioning", "loan structuring", "dscr", "cash flow lending",
            "npl", "delinquency", "portfolio risk", "fintech lending", "credit scoring",
            "borrower due diligence", "collateral appraisal", "credit committee",
        ]

        self.secondary_keywords = [
            "banking", "financial analysis", "working capital", "trade finance", "letter of credit",
            "covenant compliance", "ratio analysis", "financial statement", "risk mitigation",
            "business loan", "commercial loan", "scorecard", "decision engine",
        ]

        self.negative_keywords = [
            "internship", "intern", "fresh graduate", "magang",
            "software engineer", "frontend", "backend", "devops", "qa engineer",
            "graphic designer", "ui/ux designer", "content creator",
            "customer service agent", "telemarketing", "teller",
        ]

    def evaluate_job(self, job: Job) -> MatchResult:
        """
        Compute holistic match score between job listing and candidate profile.
        Returns detailed MatchResult.
        """
        text_corpus = f"{job.title}\n{job.description}\n{job.work_type or ''}".lower()
        title_lower = job.title.lower()

        # 1. Negative Filter Check
        for neg in self.negative_keywords:
            if re.search(rf"\b{re.escape(neg)}\b", title_lower):
                return MatchResult(
                    score=15,
                    reasoning=f"Irrelevant role type: matched negative keyword '{neg}'.",
                    matching_points=[],
                    missing_points=[f"Role appears to be {neg} rather than Senior Credit Risk/Banking."],
                    recommended_action="SKIP",
                )

        # 2. Score Components
        title_score, title_matches = self._score_title(title_lower)
        desc_score, desc_matches = self._score_description(text_corpus)
        exp_score, exp_gap = self._score_experience(text_corpus)
        loc_score, loc_status = self._score_location(job.location, text_corpus)
        salary_score, sal_status = self._score_salary(job)

        # Weighted Total Score (0 - 100)
        # Weights: Title (35%), Description/Skills (35%), Experience (15%), Location (10%), Salary (5%)
        raw_score = (
            (title_score * 0.35) +
            (desc_score * 0.35) +
            (exp_score * 0.15) +
            (loc_score * 0.10) +
            (salary_score * 0.05)
        )
        final_score = int(min(100, max(0, round(raw_score))))

        # Strengths & Matching Points
        matching_points: List[str] = []
        if title_matches:
            matching_points.append(f"Title relevance: {', '.join(title_matches[:3])}")
        if desc_matches:
            matching_points.append(f"Key skill matches: {', '.join(desc_matches[:5])}")
        matching_points.append(f"Experience alignment: 15+ years banking & FinTech track record")
        if loc_status:
            matching_points.append(f"Location fit: {loc_status}")

        # Missing Points / Gaps
        missing_points: List[str] = []
        if exp_gap:
            missing_points.append(exp_gap)
        if loc_score < 70:
            missing_points.append(f"Location '{job.location}' may require relocation confirmation.")
        if salary_score < 60:
            missing_points.append(f"Salary fit: {sal_status}")

        # Action recommendation
        if final_score >= 80:
            rec_action = "APPLY"
            reasoning = f"High priority fit ({final_score}% match). Aligns strongly with Aditya's credit underwriting, SME banking, and FinTech risk experience."
        elif final_score >= 65:
            rec_action = "REVIEW"
            reasoning = f"Moderate fit ({final_score}% match). Good overlap with banking/risk profile, review specific company requirements."
        else:
            rec_action = "SKIP"
            reasoning = f"Low fit ({final_score}% match). Role deviates from core credit risk management competencies."

        return MatchResult(
            score=final_score,
            reasoning=reasoning,
            matching_points=matching_points,
            missing_points=missing_points,
            recommended_action=rec_action,
            salary_fit=sal_status,
            location_fit=loc_status,
            evaluated_at=datetime.now(timezone.utc),
        )

    def _score_title(self, title_lower: str) -> Tuple[float, List[str]]:
        """Score job title alignment."""
        matches: List[str] = []
        score = 20.0

        for kw in self.primary_keywords:
            if kw in title_lower:
                matches.append(kw)
                score += 35.0

        for kw in self.secondary_keywords:
            if kw in title_lower:
                matches.append(kw)
                score += 15.0

        # Seniority boost
        if any(s in title_lower for s in ["senior", "lead", "head", "manager", "specialist", "avp", "vp"]):
            score += 15.0
            matches.append("Seniority Alignment")

        return min(100.0, score), matches

    def _score_description(self, text_corpus: str) -> Tuple[float, List[str]]:
        """Score job description against candidate core competencies."""
        matches: List[str] = []
        points = 0.0

        for kw in self.primary_keywords:
            if re.search(rf"\b{re.escape(kw)}\b", text_corpus):
                matches.append(kw)
                points += 12.0

        for kw in self.secondary_keywords:
            if re.search(rf"\b{re.escape(kw)}\b", text_corpus):
                if kw not in matches:
                    matches.append(kw)
                points += 6.0

        # Check domain indicators
        for domain in ["fintech", "sme", "commercial", "multifinance", "p2p", "digital banking", "bank"]:
            if domain in text_corpus:
                points += 5.0

        return min(100.0, max(20.0, points)), matches

    def _score_experience(self, text_corpus: str) -> Tuple[float, str]:
        """Check required years of experience."""
        # Find experience patterns like "5+ years", "3-5 tahun", "minimum 7 years"
        match = re.search(r"(\d{1,2})\s*(?:\+|-\s*\d{1,2})?\s*(?:years?|thn|tahun)", text_corpus)
        if match:
            try:
                req_years = int(match.group(1))
                if req_years <= self.profile.total_years_experience:
                    return 100.0, ""
                else:
                    return 70.0, f"Role mentions {req_years}+ years experience requirement."
            except ValueError:
                pass
        return 90.0, ""

    def _score_location(self, job_location: str, text_corpus: str) -> Tuple[float, str]:
        """Check location compatibility."""
        loc_clean = job_location.lower()
        if "remote" in loc_clean or "remote" in text_corpus:
            return 100.0, "Remote work flexible"
        for pref in self.profile.locations:
            if pref.lower() in loc_clean:
                return 100.0, f"Direct location match ({pref})"
        if "indonesia" in loc_clean:
            return 85.0, "Indonesia nationwide"
        return 65.0, f"Location listed as {job_location}"

    def _score_salary(self, job: Job) -> Tuple[float, str]:
        """Check salary alignment if disclosed."""
        if not job.salary_min and not job.salary_max:
            return 80.0, "Salary negotiable / not disclosed"

        target_min = self.profile.salary_expectation.expected_min
        if job.salary_max and job.salary_max >= target_min:
            return 100.0, f"Salary meets target (up to {job.get_display_salary()})"
        elif job.salary_min and job.salary_min >= (target_min * 0.8):
            return 85.0, f"Salary acceptable ({job.get_display_salary()})"
        elif job.salary_max and job.salary_max < (target_min * 0.7):
            return 50.0, f"Salary is below target ({job.get_display_salary()})"

        return 75.0, "Salary within review range"


# Global Matcher Instance
matcher = MatcherEngine()
