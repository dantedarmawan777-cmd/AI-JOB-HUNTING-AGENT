"""
Blacklist and exclusion filter module for job hunting automation.

Filters out:
1. Junior / entry-level positions (e.g. Fresh Graduate, Magang, Admin Kredit, Telemarketing, CS).
2. Illegal / questionable pinjol / predatory lending entities and recruitment scams.
3. Closed postings or postings older than 14 days.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from src.core.logger import get_logger
from src.core.models import Job, ApplicationStatus

logger = get_logger("matcher.blacklist")


@dataclass
class ExclusionResult:
    """Detailed result of blacklist evaluation."""
    is_excluded: bool
    reason: Optional[str] = None
    category: Optional[str] = None  # "junior", "predatory_pinjol", "expired_or_closed"
    matched_pattern: Optional[str] = None


class BlacklistFilter:
    """
    Exclusion filter enforcing strict candidate seniority and domain safety standards.
    """

    # 1. Junior / Entry-Level / Frontline Titles and Keywords
    JUNIOR_TITLE_PATTERNS: List[str] = [
        r"\b(fresh\s*grad(uate)?s?)\b",
        r"\b(lulusan\s*baru)\b",
        r"\b(magang|intern(ship)?|apprentice(ship)?|trainee|ojt|pkl)\b",
        r"\b(entry\s*level)\b",
        r"\b(junior|jr\.?)\s+(staff|officer|analyst|associate|clerk|admin)\b",
        r"\b(admin(istrasi)?\s*kredit|credit\s*admin(istration)?)\b",
        r"\b(telemarketing|telesales|tele-marketing|tele-sales)\b",
        r"\b(customer\s*service|call\s*center|contact\s*center|layanan\s*pelanggan|cs\s+officer)\b",
        r"\b(desk\s*coll(ection)?|tele\s*coll(ection)?|field\s*coll(ector|ection)?|penagih(an)?\s*lapangan|kolektor)\b",
        r"\b(frontliner|front\s*office|receptionist|resepsionis)\b",
        r"\b(spg|spb|sales\s*promotion|pramuniaga|kasir|cashier)\b",
        r"\b(staf\s*administrasi|admin\s*staff|administrative\s*assistant|data\s*entry)\b",
        r"\b(kurir|courier|driver|pengemudi|office\s*boy|office\s*girl|ob|og)\b",
        r"\b(management\s*trainee|officer\s*development\s*program|odp|mdp)\b",  # Generic entry-level trainee tracks
    ]

    # Junior indicators in job description / requirements (context-sensitive)
    JUNIOR_DESC_PATTERNS: List[str] = [
        r"\b(fresh\s*graduates?\s*(are\s*)?(welcome|encouraged\s*to\s*apply|dipersilakan\s*melamar))\b",
        r"\b(lulusan\s*baru\s*dipersilakan)\b",
        r"\b(no\s*experience\s*required|pengalaman\s*tidak\s*(diutamakan|diperlukan)|tanpa\s*pengalaman)\b",
        r"\b(minimal\s*(lulusan\s*)?(sma|smk|sederajat)\b(?!\s*(or\s*bachelor|atau\s*s1|d3)))",
        r"\b(usia\s*maks(imal)?\s*(2[0-3]|1[89])\s*tahun)\b",
        r"\b(max(imum)?\s*age\s*(2[0-3]|1[89])\s*years?\s*old)\b",
    ]

    # Exceptions / White-listed contexts where junior words might appear in a senior JD
    SENIORITY_OVERRIDE_PATTERNS: List[str] = [
        r"\b(head|lead|leader|manager|vp|avp|director|chief|senior|sr\.?|principal|specialist|expert)\b",
        r"\b(mentor(ing)?|supervis(e|ing)|manag(e|ing))\s+junior",
        r"\bnot\s+for\s+fresh\s*graduates\b",
        r"\bbukan\s+untuk\s+fresh\s*graduate\b",
        r"\b(minimum|minimal|at\s*least)\s*([3-9]|1[0-9])\s*(years?|thn|tahun)\b",
    ]

    # 2. Illegal / Questionable Pinjol / Predatory Entities & Recruitment Scams
    ILLEGAL_PINJOL_ENTITIES: Set[str] = {
        "pinjol ilegal", "dana kilat", "rupiah super", "pinjam duit cepat",
        "kantong darurat", "saku kilat", "dompet mudah", "uang pintar",
        "kredit berlian", "pohon duit", "kredit kelinci", "pinjam yuk ilegal",
        "pinjaman kilat ksp", "ksp sumber dana penipuan", "fast rupiah",
        "pinjaman harian tanpa slik", "rentenir digital", "dana gaul",
        "kantong kta", "saku darurat", "kredit pintar clone", "rupiah cepat clone",
    }

    PREDATORY_PINJOL_PATTERNS: List[str] = [
        r"\b(pinjol\s*ilegal|pinjaman\s*online\s*ilegal)\b",
        r"\b(tanpa\s*izin\s*ojk|unregistered\s*p2p|unlicensed\s*lending)\b",
        r"\b(tanpa\s*bi\s*checking\s*dan\s*tanpa\s*slik\s*bunga\s*harian)\b",
        r"\b(bunga\s*harian\s*(1%|2%|3%|[5-9]%|[1-9][0-9]%))\b",
        r"\b(jasa\s*(hapus|bobol|joki)\s*(data\s*)?pinjol)\b",
        r"\b(buka\s*rekening\s*(bank\s*)?dapat\s*(komisi|upah|uang))\b",
        r"\b(money\s*mule|sewa\s*rekening|jual\s*beli\s*rekening)\b",
        r"\b(tugas\s*like\s*(dan|&)\s*(subscribe|follow)\s*komisi\s*harian)\b",
        r"\b(biaya\s*administrasi\s*pelatihan\s*sebelum\s*kerja|bayar\s*uang\s*seragam)\b",
    ]

    # 3. Closed Status Indicators
    CLOSED_STATUS_KEYWORDS: Set[str] = {
        "closed", "expired", "archived", "filled", "inactive", "withdrawn",
        "ditutup", "kadaluarsa", "selesai", "tidak aktif"
    }

    CLOSED_TEXT_PATTERNS: List[str] = [
        r"\b(job\s*(is\s*)?closed|application\s*closed|no\s*longer\s*accepting\s*applications?)\b",
        r"\b(lowongan\s*(sudah\s*)?ditutup|pendaftaran\s*telah\s*berakhir)\b",
        r"\b(this\s*job\s*has\s*expired)\b",
    ]

    def __init__(self, max_job_age_days: int = 14) -> None:
        self.max_job_age_days = max_job_age_days
        self._compile_regexes()

    def _compile_regexes(self) -> None:
        """Compile regex patterns for performance."""
        self._re_junior_title = [re.compile(p, re.IGNORECASE) for p in self.JUNIOR_TITLE_PATTERNS]
        self._re_junior_desc = [re.compile(p, re.IGNORECASE) for p in self.JUNIOR_DESC_PATTERNS]
        self._re_senior_override = [re.compile(p, re.IGNORECASE) for p in self.SENIORITY_OVERRIDE_PATTERNS]
        self._re_predatory = [re.compile(p, re.IGNORECASE) for p in self.PREDATORY_PINJOL_PATTERNS]
        self._re_closed_text = [re.compile(p, re.IGNORECASE) for p in self.CLOSED_TEXT_PATTERNS]

    def is_junior_position(self, title: str, description: str = "") -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Check if the position is junior, entry-level, admin, or frontline.

        Returns:
            Tuple of (is_junior, reason, matched_pattern)
        """
        clean_title = title.strip()
        clean_desc = description.strip()

        # Step 1: Check title for junior patterns
        for pattern in self._re_junior_title:
            match = pattern.search(clean_title)
            if match:
                # Check if it's a senior override in title (e.g. "Head of Credit Admin")
                is_senior = False
                for s_pat in self._re_senior_override:
                    if s_pat.search(clean_title):
                        # Special check: If title is strictly "Admin Kredit" or "Telemarketing", senior words might not exist
                        # But if "Senior Credit Admin" or "Head of Customer Service", decide based on role nature
                        if re.search(r"\b(head|lead|manager|vp|director|chief)\b", clean_title, re.IGNORECASE):
                            is_senior = True
                            break
                if not is_senior:
                    matched = match.group(0)
                    return True, f"Junior/Entry-level role title detected: '{matched}'", matched

        # Step 2: Check description for junior/no-experience requirements
        if clean_desc:
            # First verify if role has strong senior indicators that override description noise
            has_strong_senior_title = bool(
                re.search(r"\b(senior|manager|lead|head|specialist|vp|director|analyst)\b", clean_title, re.IGNORECASE)
            )
            
            for pattern in self._re_junior_desc:
                match = pattern.search(clean_desc)
                if match:
                    # If the title explicitly says Senior/Manager/Head, don't exclude unless explicit fresh grad welcome in title
                    if not has_strong_senior_title:
                        matched = match.group(0)
                        return True, f"Junior requirement pattern detected in description: '{matched}'", matched

        return False, None, None

    def is_predatory_pinjol(self, company: str, description: str = "") -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Check if the employer is an illegal pinjol, predatory lender, or recruitment scam.

        Returns:
            Tuple of (is_predatory, reason, matched_pattern)
        """
        norm_company = company.strip().lower()
        norm_desc = description.strip().lower()

        # Check known illegal pinjol entity names
        for illegal_name in self.ILLEGAL_PINJOL_ENTITIES:
            if illegal_name in norm_company:
                return True, f"Employer matched blacklisted predatory lending entity: '{company}'", illegal_name

        # Check predatory / scam patterns in description and company
        full_text = f"{company}\n{description}"
        for pattern in self._re_predatory:
            match = pattern.search(full_text)
            if match:
                matched = match.group(0)
                return True, f"Predatory lending / scam indicator detected: '{matched}'", matched

        return False, None, None

    def is_expired_or_closed(
        self,
        posted_date: Optional[Union[str, datetime]] = None,
        status: Optional[str] = None,
        description: str = "",
        max_days: Optional[int] = None,
        reference_date: Optional[datetime] = None,
    ) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Check if the job posting is closed, archived, or older than max_days (default 14).

        Returns:
            Tuple of (is_closed_or_expired, reason, matched_pattern)
        """
        limit_days = max_days if max_days is not None else self.max_job_age_days
        ref_dt = reference_date or datetime.now(timezone.utc)

        # 1. Check explicit status
        if status:
            norm_status = status.strip().lower()
            if norm_status in self.CLOSED_STATUS_KEYWORDS or norm_status == ApplicationStatus.REJECTED.value:
                return True, f"Job status is explicitly marked as '{status}'", status

        # 2. Check description for closed indicators
        if description:
            for pattern in self._re_closed_text:
                match = pattern.search(description)
                if match:
                    matched = match.group(0)
                    return True, f"Posting content indicates closure: '{matched}'", matched

        # 3. Check posting date age
        if posted_date:
            parsed_dt, age_days = self.parse_posted_date_to_age(posted_date, ref_dt)
            if age_days is not None and age_days > limit_days:
                return True, f"Posting age ({age_days:.1f} days) exceeds maximum allowable threshold ({limit_days} days)", f"{age_days:.1f} days"

        return False, None, None

    @staticmethod
    def parse_posted_date_to_age(
        posted_date: Union[str, datetime],
        reference_date: Optional[datetime] = None,
    ) -> Tuple[Optional[datetime], Optional[float]]:
        """
        Parse posted date string or datetime into (parsed_datetime, age_in_days).
        Handles relative strings ('3 days ago', '1 minggu lalu', 'yesterday') and ISO/calendar dates.
        """
        ref_dt = reference_date or datetime.now(timezone.utc)

        if isinstance(posted_date, datetime):
            dt = posted_date if posted_date.tzinfo else posted_date.replace(tzinfo=timezone.utc)
            delta = ref_dt - dt
            age_days = max(0.0, delta.total_seconds() / 86400.0)
            return dt, age_days

        date_str = str(posted_date).strip().lower()
        if not date_str:
            return None, None

        # Relative parsing - English & Indonesian
        if "just now" in date_str or "baru saja" in date_str or "today" in date_str or "hari ini" in date_str:
            return ref_dt, 0.0

        if "yesterday" in date_str or "kemarin" in date_str:
            dt = ref_dt - timedelta(days=1)
            return dt, 1.0

        # Regex for 'X hours ago' / 'X jam lalu'
        m_hour = re.search(r"(\d+)\s*(?:hours?|hrs?|jam)\s*(?:ago|yang\s*lalu|lalu)?", date_str)
        if m_hour:
            hours = int(m_hour.group(1))
            dt = ref_dt - timedelta(hours=hours)
            return dt, hours / 24.0

        # Regex for 'X days ago' / 'X hari lalu'
        m_day = re.search(r"(\d+)\s*(?:days?|d|hari)\s*(?:ago|yang\s*lalu|lalu)?", date_str)
        if m_day:
            days = int(m_day.group(1))
            dt = ref_dt - timedelta(days=days)
            return dt, float(days)

        # Regex for 'X weeks ago' / 'X minggu lalu'
        m_week = re.search(r"(\d+)\s*(?:weeks?|w|minggu)\s*(?:ago|yang\s*lalu|lalu)?", date_str)
        if m_week:
            weeks = int(m_week.group(1))
            dt = ref_dt - timedelta(days=weeks * 7)
            return dt, float(weeks * 7)

        # Regex for 'X months ago' / 'X bulan lalu'
        m_month = re.search(r"(\d+)\s*(?:months?|m|bulan)\s*(?:ago|yang\s*lalu|lalu)?", date_str)
        if m_month:
            months = int(m_month.group(1))
            dt = ref_dt - timedelta(days=months * 30)
            return dt, float(months * 30)

        # Explicit standard date formats
        # ISO format: 2026-09-14T08:00:00Z or 2026-09-14
        iso_clean = date_str.replace("z", "+00:00")
        try:
            dt = datetime.fromisoformat(iso_clean)
            if not dt.tzinfo:
                dt = dt.replace(tzinfo=timezone.utc)
            delta = ref_dt - dt
            return dt, max(0.0, delta.total_seconds() / 86400.0)
        except ValueError:
            pass

        # Formats like '14 Sep 2026', '2026/09/14', '14/09/2026'
        date_formats = [
            "%d %b %Y", "%d %B %Y", "%b %d, %Y", "%B %d, %Y",
            "%Y-%m-%d", "%Y/%m/%d", "%d/%m/%Y", "%d-%m-%Y"
        ]
        for fmt in date_formats:
            try:
                dt = datetime.strptime(date_str, fmt).replace(tzinfo=timezone.utc)
                delta = ref_dt - dt
                return dt, max(0.0, delta.total_seconds() / 86400.0)
            except ValueError:
                continue

        return None, None

    def evaluate(
        self,
        job: Union[Job, Dict[str, Any]],
        reference_date: Optional[datetime] = None,
    ) -> ExclusionResult:
        """
        Evaluate a Job against all exclusion filters.

        Args:
            job: Job model instance or dictionary.
            reference_date: Reference datetime for posting age (defaults to now).

        Returns:
            ExclusionResult with decision and details.
        """
        if isinstance(job, Job):
            title = job.title
            company = job.company
            description = job.description
            posted_date = job.posted_date
            status = job.status.value if hasattr(job.status, "value") else str(job.status)
        else:
            title = job.get("title", "")
            company = job.get("company", "")
            description = job.get("description", "")
            posted_date = job.get("posted_date")
            status = job.get("status")

        # 1. Predatory Lending / Scam Check (Highest severity)
        is_pred, reason_pred, pat_pred = self.is_predatory_pinjol(company, description)
        if is_pred:
            logger.info("Blacklisted job [%s @ %s]: %s", title, company, reason_pred)
            return ExclusionResult(
                is_excluded=True,
                reason=reason_pred,
                category="predatory_pinjol",
                matched_pattern=pat_pred,
            )

        # 2. Junior / Entry Level Check
        is_jr, reason_jr, pat_jr = self.is_junior_position(title, description)
        if is_jr:
            logger.info("Blacklisted job [%s @ %s]: %s", title, company, reason_jr)
            return ExclusionResult(
                is_excluded=True,
                reason=reason_jr,
                category="junior",
                matched_pattern=pat_jr,
            )

        # 3. Expired or Closed Check
        is_closed, reason_closed, pat_closed = self.is_expired_or_closed(
            posted_date=posted_date,
            status=status,
            description=description,
            reference_date=reference_date,
        )
        if is_closed:
            logger.info("Blacklisted job [%s @ %s]: %s", title, company, reason_closed)
            return ExclusionResult(
                is_excluded=True,
                reason=reason_closed,
                category="expired_or_closed",
                matched_pattern=pat_closed,
            )

        return ExclusionResult(is_excluded=False)


# Default singleton instance
default_blacklist = BlacklistFilter()
