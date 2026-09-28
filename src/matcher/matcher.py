"""
Candidate-Job Matching Engine module.

Evaluates job listings against Aditya Darmawan's 15+ years professional profile.
Computes weighted multi-dimensional match scores (0-100%), enforces >=75% shortlist threshold,
and generates concise, zero-slop 2-sentence rationales.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from config import BASE_DIR, config
from src.core.logger import get_logger
from src.core.models import (
    ApplicationStatus,
    CandidateProfile,
    Job,
    MatchResult,
    SalaryExpectation,
)
from src.matcher.blacklist import BlacklistFilter, default_blacklist

logger = get_logger("matcher.engine")


class JobMatcher:
    """
    Evaluates Job listings against Aditya Darmawan's verified career profile.
    """

    # Scoring weights across 5 core competency pillars
    WEIGHTS = {
        "credit_risk_underwriting": 0.30,  # Credit risk, underwriting, DSCR, financial spreading, NPL
        "sme_commercial_banking": 0.25,    # SME lending, commercial banking, facility structuring, due diligence
        "fintech_digital_lending": 0.20,   # Digital lending, automated scorecards, alternative data, FinTech
        "leadership_stakeholder": 0.15,    # Relationship management, credit committee, team/ops leadership
        "seniority_fit": 0.10,             # Seniority level (Senior, Lead, Manager, Specialist, 5-15+ yrs)
    }

    # Minimum score threshold to qualify for HITL / shortlisting
    SHORTLIST_THRESHOLD = 75

    # Core Competency Keywords & Patterns
    KEYWORDS_CREDIT_RISK = [
        r"\bcredit\s*risk\b", r"\bunderwriting\b", r"\bcredit\s*analyst\b",
        r"\bcredit\s*assessment\b", r"\bcredit\s*approval\b", r"\bcredit\s*memo(randum)?\b",
        r"\bfinancial\s*statement\b", r"\bfinancial\s*spreading\b",
        r"\b(dscr|debt\s*service\s*coverage)\b", r"\bdebt\s*capacity\b",
        r"\bratio\s*analysis\b", r"\bcash\s*flow\b", r"\bworking\s*capital\b",
        r"\b(npl|non-performing\s*loans?)\b", r"\bdelinquency\b", r"\bearly\s*warning\b",
        r"\bcovenant\s*(compliance|monitoring)?\b", r"\bcredit\s*policy\b", r"\brisk\s*mitigation\b",
        r"\banalisis\s*kredit\b", r"\bmanajemen\s*risiko\b", r"\bkelayakan\s*kredit\b",
    ]

    KEYWORDS_SME_COMMERCIAL = [
        r"\b(sme|ukm|umkm)\b", r"\bcommercial\s*(bank(ing)?|lending|credit|loans?|products?)\b",
        r"\bcorporate\s*(bank(ing)?|lending|credit)\b", r"\bbusiness\s*banking\b", r"\bbusiness\s*loans?\b",
        r"\brelationship\s*manager\b", r"\baccount\s*officer\b", r"\bloan\s*structuring\b",
        r"\bfacility\s*sizing\b", r"\btrade\s*finance\b", r"\bletter\s*of\s*credit\b",
        r"\bdue\s*diligence\b", r"\bcollateral\s*appraisal\b", r"\blegal\s*perfection\b",
        r"\bhak\s*tanggungan\b", r"\bfidusia\b", r"\bagunan\b", r"\bkredit\s*modal\s*kerja\b",
    ]

    KEYWORDS_FINTECH_DIGITAL = [
        r"\bfintech\b", r"\bdigital\s*(sme\s*)?lending\b", r"\bdigital\s*credit\b",
        r"\bp2p(\s*lending)?\b", r"\bscorecards?\b", r"\brisk\s*scoring\b",
        r"\bautomated\s*(risk\s*)?decisioning\b", r"\bdecision\s*engine\b",
        r"\balternative\s*data\b", r"\b(bank\s*statement\s*parsing|digital\s*statement)\b",
        r"\bcorporate\s*cards?\b", r"\badvance\s*(cards?|lines?)\b", r"\bcredit\s*cards?\b",
        r"\bopen\s*banking\b", r"\be-commerce\s*cash\s*flow\b", r"\bdigital\s*bank(ing)?\b",
    ]

    KEYWORDS_LEADERSHIP = [
        r"\bleadership\b", r"\bteam\s*(lead(er)?|leadership|management)\b", r"\bmanager\b",
        r"\bsupervisor\b", r"\bcredit\s*committee\b", r"\bstakeholder\s*management\b",
        r"\bportfolio\s*management\b", r"\boperations\s*manager\b", r"\bbranch\s*management\b",
        r"\bcross-functional\b", r"\bmentor(ing)?\b",
    ]

    KEYWORDS_SENIORITY = [
        r"\bsenior\b", r"\bsr\.?\b", r"\blead\b", r"\bspecialist\b", r"\bhead\b",
        r"\bvp\b", r"\bavp\b", r"\bmanager\b", r"\bexpert\b", r"\bprincipal\b",
        r"\b(3|5|6|7|8|9|10|12|15)\+?\s*(years?|thn|tahun)\b",
    ]

    def __init__(
        self,
        candidate_profile: Optional[CandidateProfile] = None,
        profile_path: Optional[Union[Path, str]] = None,
        blacklist_filter: Optional[BlacklistFilter] = None,
        min_match_score: int = SHORTLIST_THRESHOLD,
    ) -> None:
        self.min_match_score = min_match_score
        self.blacklist_filter = blacklist_filter or default_blacklist
        self.profile = candidate_profile or self._load_profile(profile_path)
        self._compile_patterns()

    def _load_profile(self, profile_path: Optional[Union[Path, str]]) -> CandidateProfile:
        """Load candidate profile from json file."""
        target_path = Path(profile_path) if profile_path else config.candidate_profile_path
        if not target_path.exists():
            target_path = BASE_DIR / "candidate_profile.json"

        if not target_path.exists():
            logger.warning("candidate_profile.json not found at %s. Initializing default profile.", target_path)
            return CandidateProfile(
                full_name="Aditya Darmawan",
                title="Senior Credit Risk & Underwriting Specialist",
                email="dantedarmawan@yahoo.com",
                phone="+62 811-599-4948",
                linkedin="https://www.linkedin.com/in/aditya-darmawan-641218b1/",
                total_years_experience=15,
                summary="Senior Credit Risk and Underwriting Specialist with over 15 years experience...",
            )

        with open(target_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return CandidateProfile.model_validate(data)

    def _compile_patterns(self) -> None:
        """Pre-compile regex patterns for performance."""
        self._re_credit = [re.compile(p, re.IGNORECASE) for p in self.KEYWORDS_CREDIT_RISK]
        self._re_sme = [re.compile(p, re.IGNORECASE) for p in self.KEYWORDS_SME_COMMERCIAL]
        self._re_fintech = [re.compile(p, re.IGNORECASE) for p in self.KEYWORDS_FINTECH_DIGITAL]
        self._re_lead = [re.compile(p, re.IGNORECASE) for p in self.KEYWORDS_LEADERSHIP]
        self._re_senior = [re.compile(p, re.IGNORECASE) for p in self.KEYWORDS_SENIORITY]

    def _score_category(self, text: str, patterns: List[re.Pattern]) -> Tuple[float, List[str]]:
        """
        Calculates normalized score (0.0 - 1.0) and matches for a pattern group.
        """
        matched: List[str] = []
        for pat in patterns:
            m = pat.search(text)
            if m:
                matched.append(m.group(0))

        # Calibrated scaling
        count = len(matched)
        if count == 0:
            return 0.0, []
        if count == 1:
            return 0.60, matched
        if count == 2:
            return 0.80, matched
        if count == 3:
            return 0.92, matched
        return 1.0, matched

    def calculate_match(self, job: Union[Job, Dict[str, Any]]) -> MatchResult:
        """
        Compute multi-dimensional match score, points, and 2-sentence rationale.
        """
        if isinstance(job, Job):
            title = job.title
            company = job.company
            description = job.description
            location = job.location
            salary = job.salary
            salary_min = job.salary_min
            salary_max = job.salary_max
        else:
            title = job.get("title", "")
            company = job.get("company", "")
            description = job.get("description", "")
            location = job.get("location", "")
            salary = job.get("salary")
            salary_min = job.get("salary_min")
            salary_max = job.get("salary_max")

        full_text = f"{title}\n{company}\n{description}"

        # 1. Run Blacklist Check First
        exclusion = self.blacklist_filter.evaluate(job)
        if exclusion.is_excluded:
            return MatchResult(
                score=0,
                reasoning=f"Excluded by safety filter: {exclusion.reason}",
                matching_points=[],
                missing_points=[exclusion.reason or "Blacklisted listing"],
                recommended_action="SKIP",
                salary_fit="Mismatched",
                location_fit="N/A",
            )

        # 2. Evaluate Core Pillars
        score_cr, matches_cr = self._score_category(full_text, self._re_credit)
        score_sme, matches_sme = self._score_category(full_text, self._re_sme)
        score_fin, matches_fin = self._score_category(full_text, self._re_fintech)
        score_lead, matches_lead = self._score_category(full_text, self._re_lead)
        score_sen, matches_sen = self._score_category(full_text, self._re_senior)

        # Title alignment bonus
        title_boost = 0.0
        if re.search(r"\b(credit|underwrit|risk|sme|commercial|lending|policy)\b", title, re.IGNORECASE):
            title_boost = 0.12

        # Weighted calculation with domain flexibility (Commercial Banking OR FinTech)
        domain_primary = max(score_sme, score_fin)
        domain_secondary = min(score_sme, score_fin)

        raw_score = (
            score_cr * 0.35
            + domain_primary * 0.30
            + domain_secondary * 0.05
            + score_lead * 0.15
            + score_sen * 0.15
            + title_boost
        )

        final_score = int(min(100.0, max(0.0, raw_score * 100)))

        # Compile matching points
        matching_points: List[str] = []
        if matches_cr:
            matching_points.append(f"Credit Risk & Underwriting: Matched key terms ({', '.join(matches_cr[:3])})")
        if matches_sme:
            matching_points.append(f"SME & Commercial Banking: Matched domain keywords ({', '.join(matches_sme[:3])})")
        if matches_fin:
            matching_points.append(f"FinTech & Digital Lending: Matched digital risk capabilities ({', '.join(matches_fin[:3])})")
        if matches_lead:
            matching_points.append(f"Leadership & Operations: Matched stakeholder/management requirements ({', '.join(matches_lead[:2])})")
        if matches_sen:
            matching_points.append(f"Seniority Fit: Aligns with 15+ years career tier ({', '.join(matches_sen[:2])})")

        # Compile missing points / gaps
        missing_points: List[str] = []
        if score_cr < 0.3:
            missing_points.append("Limited explicit credit underwriting or risk assessment requirements in JD")
        if score_sme < 0.3 and score_fin < 0.3:
            missing_points.append("Role does not emphasize SME commercial banking or digital FinTech lending domain")
        if score_sen < 0.3:
            missing_points.append("Seniority tier or required years of experience not clearly stated")

        # Evaluate Salary Fit
        salary_fit = self._evaluate_salary(salary, salary_min, salary_max)

        # Evaluate Location Fit
        location_fit = self._evaluate_location(location)

        # Generate 2-sentence concise rationale
        reasoning = self._generate_rationale(
            title=title,
            company=company,
            score=final_score,
            matches_cr=matches_cr,
            matches_sme=matches_sme,
            matches_fin=matches_fin,
        )

        # Recommended Action
        if final_score >= self.min_match_score:
            recommended_action = "APPLY"
        elif final_score >= 60:
            recommended_action = "REVIEW"
        else:
            recommended_action = "SKIP"

        return MatchResult(
            score=final_score,
            reasoning=reasoning,
            matching_points=matching_points,
            missing_points=missing_points,
            recommended_action=recommended_action,
            salary_fit=salary_fit,
            location_fit=location_fit,
        )

    def _generate_rationale(
        self,
        title: str,
        company: str,
        score: int,
        matches_cr: List[str],
        matches_sme: List[str],
        matches_fin: List[str],
    ) -> str:
        """
        Generates a factual, zero-slop 2-sentence rationale tailored to Aditya Darmawan.
        """
        # Sentence 1: Foundation in 15+ yrs commercial banking & FinTech lending
        s1 = (
            "Aditya offers 15+ years of cumulative experience spanning institutional commercial banking "
            "(Maybank, CIMB Niaga) and regional FinTech lending (Aspire SEA), specializing in SME credit "
            "underwriting, financial statement DSCR modeling, and automated risk scorecards."
        )

        # Sentence 2: Targeted alignment with specific role needs
        if matches_fin and matches_cr:
            s2 = (
                f"His 6-year tenure at Aspire SEA calibrating digital underwriting scorecards and structuring SME credit facilities "
                f"directly fulfills the key risk and decisioning requirements for the {title} position at {company}."
            )
        elif matches_sme:
            s2 = (
                f"His proven track record in SME commercial loan underwriting, borrower due diligence, and portfolio covenant management "
                f"(including Maybank's Best RO SME UpCountry award) provides immediate operational impact for {company}."
            )
        elif score >= 75:
            s2 = (
                f"His extensive background in credit policy formulation, debt capacity modeling, and risk mitigation "
                f"strongly matches the core responsibilities outlined for this {title} role."
            )
        else:
            s2 = (
                f"While Aditya possesses senior credit risk qualifications, this role shows limited direct overlap "
                f"with his core SME commercial underwriting and digital scorecard calibration background."
            )

        return f"{s1} {s2}"

    def _evaluate_salary(
        self,
        salary_str: Optional[str],
        salary_min: Optional[float],
        salary_max: Optional[float],
    ) -> str:
        """Evaluates whether disclosed salary meets the IDR 25M - 35M range."""
        target_min = self.profile.salary_expectation.expected_min  # 25,000,000
        target_max = self.profile.salary_expectation.expected_target  # 35,000,000

        if salary_min is not None and salary_max is not None:
            if salary_max < 20_000_000:
                return f"Below target (Max IDR {salary_max:,.0f} < Target IDR 25M)"
            if salary_min >= target_min or salary_max >= target_min:
                return f"Competitive (IDR {salary_min:,.0f} - {salary_max:,.0f})"
            return f"Moderate (IDR {salary_min:,.0f} - {salary_max:,.0f})"

        if salary_str:
            norm = salary_str.lower()
            # Check for numbers in millions
            nums = [int(n) for n in re.findall(r"\b(\d+)\b", norm)]
            if any(n in range(25, 60) for n in nums):
                return f"Matches target range ({salary_str})"
            if any(n in range(1, 19) for n in nums) and ("juta" in norm or "jt" in norm or "million" in norm):
                return f"Below target ({salary_str})"
            return f"Disclosed ({salary_str})"

        return "Not disclosed (Expectation: IDR 25M - 35M negotiable)"

    def _evaluate_location(self, location_str: str) -> str:
        """Evaluates location compatibility against candidate preference."""
        norm_loc = location_str.strip().lower()
        if not norm_loc:
            return "Flexible / Remote"

        preferred_locations = [loc.lower() for loc in self.profile.locations]  # jakarta, balikpapan, tarakan
        if any(pref in norm_loc for pref in preferred_locations):
            return f"Direct match ({location_str})"

        if any(w in norm_loc for w in ["remote", "work from home", "wfh", "anywhere", "indonesia"]):
            return f"Remote / Nationwide match ({location_str})"

        if any(w in norm_loc for w in ["hybrid", "jabodetabek", "tangerang", "bekasi", "depok", "bogor"]):
            return f"Greater Jakarta region match ({location_str})"

        return f"Location requires discussion ({location_str})"

    def match_and_update_job(self, job: Job) -> Job:
        """
        Evaluate job, attach match_result, and update application status.
        """
        result = self.calculate_match(job)
        job.match_result = result

        if result.recommended_action == "APPLY":
            job.status = ApplicationStatus.SHORTLISTED
            logger.info("Job SHORTLISTED [Score: %d]: %s @ %s", result.score, job.title, job.company)
        elif result.recommended_action == "SKIP":
            job.status = ApplicationStatus.REJECTED
            logger.info("Job REJECTED/SKIPPED [Score: %d]: %s @ %s", result.score, job.title, job.company)
        else:
            # "REVIEW"
            job.status = ApplicationStatus.DISCOVERED
            logger.info("Job DISCOVERED/REVIEW [Score: %d]: %s @ %s", result.score, job.title, job.company)

        return job


# Default singleton instance
default_matcher = JobMatcher()
