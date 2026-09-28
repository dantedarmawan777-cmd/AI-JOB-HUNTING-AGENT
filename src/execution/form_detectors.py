"""
Form field detection and answer heuristic engine.
Maps candidate profile details to standard and custom job application form inputs.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple
from playwright.async_api import ElementHandle, Page

from src.core.logger import get_logger
from src.core.models import CandidateProfile

logger = get_logger(__name__)


class FormDetector:
    """Detects and resolves values for job application form fields."""

    @staticmethod
    def resolve_field_value(
        label_text: str,
        profile: CandidateProfile,
        field_type: str = "text",
        options: Optional[List[str]] = None,
    ) -> Optional[str]:
        """
        Derive optimal candidate value given form field label/question text.
        """
        lbl = label_text.lower().strip()
        opts = [o.lower() for o in (options or [])]

        # 1. Full Name / First Name / Last Name
        if any(k in lbl for k in ["first name", "nama depan"]):
            return "Aditya"
        if any(k in lbl for k in ["last name", "nama belakang", "surname", "family name"]):
            return "Darmawan"
        if any(k in lbl for k in ["full name", "nama lengkap", "name", "nama"]):
            return profile.full_name

        # 2. Email
        if any(k in lbl for k in ["email", "e-mail", "surel"]):
            return profile.email

        # 3. Phone / Mobile / WhatsApp
        if any(k in lbl for k in ["phone", "mobile", "telepon", "handphone", "whatsapp", "wa", "hp", "no hp"]):
            if any(k in lbl for k in ["08", "local", "hp", "whatsapp", "wa"]):
                return "08115994948"
            return profile.phone

        # 4. LinkedIn URL
        if any(k in lbl for k in ["linkedin", "profil linkedin", "url linkedin"]):
            return profile.linkedin

        # 5. Location / City / Address
        if any(k in lbl for k in ["city", "kota", "domisili", "current location", "lokasi sekarang"]):
            if opts:
                for opt in options or []:
                    if any(c.lower() in opt.lower() for c in ["jakarta", "indonesia"]):
                        return opt
            return "Jakarta"
        if any(k in lbl for k in ["address", "alamat", "residence"]):
            return "Jakarta, Indonesia"

        # 6. Total Experience
        if any(k in lbl for k in ["years of", "total experience", "work experience", "tahun pengalaman", "pengalaman kerja", "lama pengalaman", "years experience"]) and not any(k in lbl for k in ["credit", "underwriting", "sme", "commercial", "fintech"]):
            if opts:
                for opt in options or []:
                    if any(y in opt for y in ["10+", "10 -", "> 10", "15", "8+", "5+"]):
                        return opt
            return str(int(profile.total_years_experience))

        # 7. Credit Risk / Underwriting / Banking Experience
        if any(k in lbl for k in ["credit risk", "underwriting", "analis kredit", "sme", "commercial", "banking"]):
            if opts:
                for opt in options or []:
                    if opt in ["yes", "ya", "expert", "5+ years", "10+ years"]:
                        return opt
            return "15 years of comprehensive experience in Credit Risk, SME Underwriting, Commercial Banking, and FinTech Lending."

        # 8. Salary Expectation / General Salary / Current Salary
        if any(k in lbl for k in ["salary", "gaji", "remuneration", "kompensasi", "penghasilan", "expected pay"]):
            if any(k in lbl for k in ["current", "saat ini", "sekarang", "terakhir"]):
                return str(int(profile.salary_expectation.expected_min))
            if "juta" in lbl:
                return "35"
            return str(int(profile.salary_expectation.expected_target))

        # 10. Notice Period / Availability
        if any(k in lbl for k in ["notice period", "kapan bisa mulai", "availability", "earliest start date", "waktu pemberitahuan"]):
            if opts:
                for opt in options or []:
                    if any(a in opt.lower() for a in ["immediate", "segera", "1 month", "1 bulan", "15 days"]):
                        return opt
            return profile.notice_period

        # 11. Work Authorization & Right to Work
        if any(k in lbl for k in ["authorized to work", "hak bekerja", "warga negara", "citizenship", "nationality", "kewarganegaraan"]):
            if opts:
                for opt in options or []:
                    if any(w in opt.lower() for w in ["yes", "ya", "indonesia", "indonesian"]):
                        return opt
            return "Indonesian"

        # 12. Education Level & Major
        if any(k in lbl for k in ["education", "pendidikan", "gelar", "degree"]):
            if opts:
                for opt in options or []:
                    if any(d in opt.lower() for d in ["bachelor", "s1", "sarjana", "undergraduate"]):
                        return opt
            return "Bachelor's Degree (S1)"
        if any(k in lbl for k in ["major", "jurusan", "field of study", "studi"]):
            return "Forestry / S.Hut"
        if any(k in lbl for k in ["university", "institusi", "kampus", "universitas"]):
            return "Universitas Mulawarman"
        if any(k in lbl for k in ["gpa", "ipk"]):
            return "3.48"

        # 13. General Yes/No screening questions
        if opts:
            # If options are Yes/No or Ya/Tidak
            for opt in options or []:
                if opt.lower() in ["yes", "ya", "setuju", "agree"]:
                    return opt

        return None
