"""
Contextual Screening Form Answers Generator.

Generates concise, factual, and strictly zero-slop responses for job application
screening questions based on Aditya Darmawan's 15+ years career track record.
"""

from __future__ import annotations

import json
import re
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from config import BASE_DIR, config
from src.core.logger import get_logger
from src.core.models import (
    CandidateProfile,
    Job,
    ScreeningQuestion,
    ScreeningQuestionType,
)

logger = get_logger("copywriter.form_answers")


class QuestionCategory(str, Enum):
    """Identified categories of screening questions."""
    YEARS_EXPERIENCE_TOTAL = "years_experience_total"
    YEARS_EXPERIENCE_CREDIT_RISK = "years_experience_credit_risk"
    YEARS_EXPERIENCE_SME = "years_experience_sme"
    YEARS_EXPERIENCE_FINTECH = "years_experience_fintech"
    YEARS_EXPERIENCE_LEADERSHIP = "years_experience_leadership"
    SALARY_EXPECTATION = "salary_expectation"
    CURRENT_SALARY = "current_salary"
    NOTICE_PERIOD = "notice_period"
    WHY_HIRE_ME = "why_hire_me"
    WHY_APPLY = "why_apply"
    KEY_ACHIEVEMENTS = "key_achievements"
    CREDIT_UNDERWRITING_METHOD = "credit_underwriting_method"
    SCORECARD_CALIBRATION = "scorecard_calibration"
    NPL_DELINQUENCY_MANAGEMENT = "npl_delinquency_management"
    FINANCIAL_SPREADING_DSCR = "financial_spreading_dscr"
    COLLATERAL_DUE_DILIGENCE = "collateral_due_diligence"
    EDUCATION = "education"
    CERTIFICATIONS = "certifications"
    WORK_AUTHORIZATION = "work_authorization"
    LOCATION_RELOCATION = "location_relocation"
    WORK_FLEXIBILITY = "work_flexibility"
    LANGUAGE_PROFICIENCY = "language_proficiency"
    GENERIC_YES_NO = "generic_yes_no"
    UNKNOWN = "unknown"


class FormAnswersEngine:
    """
    Contextual Q&A generator for screening forms grounded in Aditya Darmawan's profile.
    """

    def __init__(
        self,
        candidate_profile: Optional[CandidateProfile] = None,
        profile_path: Optional[Union[Path, str]] = None,
    ) -> None:
        self.profile = candidate_profile or self._load_profile(profile_path)
        self._build_knowledge_base()

    def _load_profile(self, profile_path: Optional[Union[Path, str]]) -> CandidateProfile:
        """Load candidate profile from disk."""
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

    def _build_knowledge_base(self) -> None:
        """Construct structured factual answers for quick lookup."""
        self.kb = {
            # Numerical factual values
            "total_years_exp": 15,
            "credit_risk_years": 12,
            "sme_years": 12,
            "fintech_years": 6,
            "leadership_years": 5,
            "salary_min": int(self.profile.salary_expectation.expected_min),       # 25,000,000
            "salary_target": int(self.profile.salary_expectation.expected_target), # 35,000,000
            "notice_period_days": 30,
            "notice_period_text": "Immediately available / 1 month standard",
            
            # Formatted String Answers (Zero-slop, factual)
            QuestionCategory.YEARS_EXPERIENCE_TOTAL: "15+ years of cumulative professional experience.",
            QuestionCategory.YEARS_EXPERIENCE_CREDIT_RISK: "12+ years in credit risk underwriting and portfolio management across commercial banking and FinTech.",
            QuestionCategory.YEARS_EXPERIENCE_SME: "12+ years evaluating SME and commercial loan proposals, cash-flow underwriting, and borrower due diligence.",
            QuestionCategory.YEARS_EXPERIENCE_FINTECH: "6 years at Aspire SEA specializing in digital SME lending, corporate cards, and automated scorecard calibration.",
            QuestionCategory.YEARS_EXPERIENCE_LEADERSHIP: "5+ years in operational leadership, regional team supervision, and credit committee presentations.",
            
            QuestionCategory.SALARY_EXPECTATION: "IDR 25,000,000 – IDR 35,000,000 / month (negotiable depending on package and responsibilities).",
            QuestionCategory.CURRENT_SALARY: "IDR 25,000,000 – IDR 30,000,000 / month.",
            QuestionCategory.NOTICE_PERIOD: "Immediately available / 1 month notice standard.",
            
            QuestionCategory.WHY_HIRE_ME: (
                "With 15+ years across commercial banking (Maybank, CIMB Niaga) and regional FinTech lending (Aspire SEA), "
                "I bring verified expertise in SME credit underwriting, financial statement DSCR modeling, and digital scorecard calibration. "
                "During my 6-year tenure at Aspire SEA, I underwrote high-growth SME facilities and calibrated automated risk engines to sustain low default rates. "
                "Previously at Maybank, I was awarded Best Sales Person RO SME UpCountry (2014) for exemplary portfolio credit quality, rigorous due diligence, and covenant compliance. "
                "I deliver immediate operational value in structuring complex credit facilities, optimizing decisioning throughput, and safeguarding portfolio health."
            ),
            
            QuestionCategory.WHY_APPLY: (
                "I am applying to leverage my 15+ years of credit underwriting, financial spreading, and digital risk scorecard experience "
                "to strengthen your credit assessment capabilities, optimize underwriting turnaround times, and maintain robust portfolio risk discipline."
            ),
            
            QuestionCategory.KEY_ACHIEVEMENTS: (
                "1. Aspire SEA (6 Yrs): Calibrated digital risk scorecards and underwrote SME credit lines/cards across Southeast Asia while maintaining low default thresholds.\n"
                "2. Maybank Indonesia (4.5 Yrs): Awarded Best Sales Person RO SME UpCountry (2014) for outstanding credit quality, portfolio growth, and compliance performance.\n"
                "3. CIMB Niaga & Bank Mega: Structured complex credit memorandums, cash flow DSCR debt modeling, and legal perfection of collateral for commercial borrowers."
            ),
            
            QuestionCategory.CREDIT_UNDERWRITING_METHOD: (
                "My underwriting methodology integrates rigorous quantitative analysis (historical financial spreading, DSCR debt capacity, cash-flow verification) "
                "with structured qualitative due diligence (business model viability, trade reference checks, collateral perfection). "
                "In digital environments, I incorporate alternative data streams and bank statement parsing into decision engines to accelerate throughput while strictly enforcing loss parameters."
            ),
            
            QuestionCategory.SCORECARD_CALIBRATION: (
                "I have 6 years of direct experience at Aspire SEA formulating and calibrating internal underwriting scorecards. "
                "I balanced approval throughput with low default thresholds during volatile market conditions and collaborated with product/engineering teams to automate decisioning rules."
            ),
            
            QuestionCategory.NPL_DELINQUENCY_MANAGEMENT: (
                "I maintain portfolio quality through proactive early warning indicators, recurring covenant compliance checks, and interim financial reviews. "
                "When distress signals emerge, I execute structured remediation and credit limit adjustments to prevent non-performing loan (NPL) escalation."
            ),
            
            QuestionCategory.FINANCIAL_SPREADING_DSCR: (
                "I have 15+ years of experience spreading audited and in-house financial statements, calculating liquidity/solvency ratios, modeling DSCR debt service coverage, "
                "and stress-testing borrower cash flows under varied revenue scenarios."
            ),
            
            QuestionCategory.COLLATERAL_DUE_DILIGENCE: (
                "Extensive background in on-site borrower due diligence, physical collateral appraisal, title verification, and legal perfection (Hak Tanggungan and Fiduciary guarantees) "
                "in full adherence to Indonesian banking regulations."
            ),
            
            QuestionCategory.EDUCATION: "Bachelor of Forestry (S.Hut), Universitas Mulawarman (GPA 3.48 / 4.00, 2005 – 2009).",
            QuestionCategory.CERTIFICATIONS: "Work Excellence Program (Daya Dimensi Indonesia - DDI, 2013); Effective Communication Program (Business First, 2013).",
            QuestionCategory.WORK_AUTHORIZATION: "Yes, Indonesian citizen with full legal authorization to work in Indonesia.",
            QuestionCategory.LOCATION_RELOCATION: "Based in Indonesia (Jakarta / Balikpapan / Tarakan). Available for Remote, Hybrid, or On-site roles; open to relocation.",
            QuestionCategory.WORK_FLEXIBILITY: "Open to On-site, Hybrid, or Remote working arrangements.",
            QuestionCategory.LANGUAGE_PROFICIENCY: "English: Professional Working Proficiency. Indonesian: Native / Bilingual.",
        }

    def classify_question(self, question_text: str) -> QuestionCategory:
        """
        Classifies screening question text into standard question category using regex.
        """
        q = question_text.strip().lower()

        # 1. Salary / Compensation
        if re.search(r"\b(salary|salaries|gaji|compensation|remuneration|penghasilan|expected\s*pay|pay\s*expectation|rate)\b", q):
            if re.search(r"\b(current|terakhir|saat\s*ini|present|last\s*drawn)\b", q):
                return QuestionCategory.CURRENT_SALARY
            return QuestionCategory.SALARY_EXPECTATION

        # 2. Notice Period / Availability
        if re.search(r"\b(notice(\s*period)?|availability|ketersediaan|kapan\s*bisa\s*mulai|start\s*date|join\s*date|how\s*soon|earliest\s*date)\b", q):
            return QuestionCategory.NOTICE_PERIOD

        # 3. Technical & Specific Domain Questions
        if re.search(r"\b(scorecards?|decision\s*engines?|decisioning|scoring\s*models?|aturan\s*scoring)\b", q):
            return QuestionCategory.SCORECARD_CALIBRATION

        if re.search(r"\b(dscr|debt\s*service|spreadings?|laporan\s*keuangan|neraca|rugi\s*laba)\b", q):
            return QuestionCategory.FINANCIAL_SPREADING_DSCR

        if re.search(r"\b(financial\s*statements?)\b", q) and not re.search(r"\b(years?|berapa\s*tahun)\b", q):
            return QuestionCategory.FINANCIAL_SPREADING_DSCR

        if re.search(r"\b(npls?|delinquenc(y|ies)|early\s*warnings?|kolektibilitas|kredit\s*macet|bad\s*debts?)\b", q):
            return QuestionCategory.NPL_DELINQUENCY_MANAGEMENT

        if re.search(r"\b(collaterals?|agunan|jaminan|hak\s*tanggungan|fidusia|appraisals?)\b", q):
            return QuestionCategory.COLLATERAL_DUE_DILIGENCE

        if re.search(r"\b(underwriting\s*methods?|credit\s*assessment\s*approach|how\s*do\s*you\s*evaluate|metode\s*analisis)\b", q):
            return QuestionCategory.CREDIT_UNDERWRITING_METHOD

        # 4. Achievements / Why Hire / Why Apply
        if re.search(r"\b(achievements?|prestasi|pencapaian|accomplishments?|proudest)\b", q):
            return QuestionCategory.KEY_ACHIEVEMENTS

        if re.search(r"\b(why\s*(should\s*we\s*)?hire|mengapa\s*kami\s*harus|alasan\s*memilih|suitable\s*for\s*this|why\s*are\s*you\s*the\s*best)\b", q):
            return QuestionCategory.WHY_HIRE_ME

        if re.search(r"\b(why\s*are\s*you\s*interested|why\s*apply|mengapa\s*melamar|alasan\s*melamar|why\s*do\s*you\s*want\s*to\s*join|motivations?|cover\s*letters?)\b", q):
            return QuestionCategory.WHY_APPLY

        # 5. Domain / FinTech / SME / Credit Risk / Leadership experience
        if re.search(r"\b(fintech|digital\s*lending|p2p)\b", q):
            return QuestionCategory.YEARS_EXPERIENCE_FINTECH

        if re.search(r"\b(sme|commercial|ukm|umkm|business\s*banking)\b", q):
            return QuestionCategory.YEARS_EXPERIENCE_SME

        if re.search(r"\b(credit|underwrit|analisis\s*kredit|risk|analyst)\b", q):
            return QuestionCategory.YEARS_EXPERIENCE_CREDIT_RISK

        if re.search(r"\b(lead|leader|leadership|manager|supervis|manajerial|kepemimpinan)\b", q):
            return QuestionCategory.YEARS_EXPERIENCE_LEADERSHIP

        # 6. Overall Experience
        if re.search(r"\b(years?(\s*of\s*(total\s*)?experience)?|pengalaman(\s*kerja)?|lama\s*bekerja|total\s*experience)\b", q):
            return QuestionCategory.YEARS_EXPERIENCE_TOTAL

        # 7. Education / Certifications
        if re.search(r"\b(educations?|degrees?|pendidikan|universitas|ipk|gpa|jurusan|majors?|lulusan)\b", q):
            return QuestionCategory.EDUCATION

        if re.search(r"\b(certificat(ions?|es?)|sertifikasi|pelatihan|courses?|trainings?)\b", q):
            return QuestionCategory.CERTIFICATIONS

        # 8. Location / Relocation / Work Authorization
        if re.search(r"\b(authorized|work\s*permits?|izin\s*kerja|legal\s*to\s*work|warga\s*negara|citizens?)\b", q):
            return QuestionCategory.WORK_AUTHORIZATION

        if re.search(r"\b(relocate|relocation|relokasi|pindah|willing\s*to\s*travel|ditempatkan)\b", q):
            return QuestionCategory.LOCATION_RELOCATION

        if re.search(r"\b(remote|hybrid|on-site|wfh|work\s*from\s*home|lokasi\s*kerja)\b", q):
            return QuestionCategory.WORK_FLEXIBILITY

        if re.search(r"\b(english|bahasa\s*inggris|languages?|bahasa)\b", q):
            return QuestionCategory.LANGUAGE_PROFICIENCY

        # 9. Generic Yes/No questions regarding skills/experience
        if re.search(r"\b(do\s*you\s*have|apakah\s*anda\s*memiliki|are\s*you\s*experienced|have\s*you\s*ever|apakah\s*bersedia)\b", q):
            return QuestionCategory.GENERIC_YES_NO

        return QuestionCategory.UNKNOWN

    def answer_question(
        self,
        question: Union[ScreeningQuestion, str],
        job_context: Optional[Union[Job, Dict[str, Any]]] = None,
    ) -> str:
        """
        Generate a contextual, zero-slop answer for a single screening question.

        Args:
            question: ScreeningQuestion object or question string.
            job_context: Optional target Job for contextual tailoring.

        Returns:
            Factual answer string.
        """
        if isinstance(question, ScreeningQuestion):
            q_text = question.question
            q_type = question.question_type
            options = question.options
        else:
            q_text = str(question)
            q_type = ScreeningQuestionType.TEXT
            options = []

        category = self.classify_question(q_text)

        # Handle numeric field requirements
        if q_type == ScreeningQuestionType.NUMBER:
            return self._format_number_answer(category)

        # Handle option choices (SELECT, RADIO, CHECKBOX)
        if options and q_type in [
            ScreeningQuestionType.SELECT,
            ScreeningQuestionType.RADIO,
            ScreeningQuestionType.CHECKBOX,
        ]:
            return self._match_best_option(category, options, q_text)

        # Handle contextual free-text answers
        if category == QuestionCategory.WHY_HIRE_ME or category == QuestionCategory.WHY_APPLY:
            return self._generate_contextual_pitch(category, job_context)

        # Look up from factual KB
        if category in self.kb:
            return str(self.kb[category])

        # Fallback for generic Yes/No
        if category == QuestionCategory.GENERIC_YES_NO:
            return "Yes, with over 15 years of proven experience in credit risk, underwriting, and commercial lending."

        # Fallback for unknown questions
        return self._generate_fallback_answer(q_text, job_context)

    def _format_number_answer(self, category: QuestionCategory) -> str:
        """Formats purely numeric answers for number input fields."""
        if category == QuestionCategory.YEARS_EXPERIENCE_TOTAL:
            return "15"
        if category in [QuestionCategory.YEARS_EXPERIENCE_CREDIT_RISK, QuestionCategory.YEARS_EXPERIENCE_SME]:
            return "12"
        if category == QuestionCategory.YEARS_EXPERIENCE_FINTECH:
            return "6"
        if category == QuestionCategory.YEARS_EXPERIENCE_LEADERSHIP:
            return "5"
        if category == QuestionCategory.SALARY_EXPECTATION:
            return str(self.kb["salary_min"])  # 25000000
        if category == QuestionCategory.CURRENT_SALARY:
            return str(self.kb["salary_min"])  # 25000000
        if category == QuestionCategory.NOTICE_PERIOD:
            return "30"
        return "15"

    def _match_best_option(
        self,
        category: QuestionCategory,
        options: List[str],
        question_text: str,
    ) -> str:
        """
        Fuzzy matches the candidate's factual profile to the most appropriate dropdown/radio option.
        """
        if not options:
            return self.kb.get(category, "Yes")

        clean_options = [opt.strip() for opt in options if opt.strip()]
        if not clean_options:
            return "Yes"

        # 1. Yes / No options
        norm_opts = [o.lower() for o in clean_options]
        if "yes" in norm_opts or "ya" in norm_opts:
            for opt in clean_options:
                if opt.lower() in ["yes", "ya", "true", "benar", "bersedia", "ya, saya bersedia", "yes, i am"]:
                    return opt

        # 2. Years of experience range matching (15 years total / 12 years credit / 6 years fintech)
        if category in [
            QuestionCategory.YEARS_EXPERIENCE_TOTAL,
            QuestionCategory.YEARS_EXPERIENCE_CREDIT_RISK,
            QuestionCategory.YEARS_EXPERIENCE_SME,
            QuestionCategory.YEARS_EXPERIENCE_FINTECH,
            QuestionCategory.YEARS_EXPERIENCE_LEADERSHIP,
            QuestionCategory.UNKNOWN,
        ]:
            target_years = self._get_target_years(category)

            # Step 2a: If candidate has >= 10 years, look for the highest tier first (>10, 10+, 10-15, >10 years, etc.)
            if target_years >= 10:
                for opt in clean_options:
                    opt_lower = opt.lower()
                    if any(p in opt_lower for p in ["> 10", "10+", ">10", "10-15", "10 - 15", "lebih dari 10", "more than 10", "above 10", "15+"]):
                        return opt

            # Step 2b: If candidate has >= 5 years, look for 5-10 bracket
            if target_years >= 5:
                for opt in clean_options:
                    opt_lower = opt.lower()
                    if any(p in opt_lower for p in ["5-10", "5 - 10", "5-7", "5 - 7", "5+ years", "5-8", "6"]):
                        return opt

            # Step 2c: Number extraction fallback
            for opt in clean_options:
                digits = re.findall(r"\d+", opt)
                if digits and any(int(d) in range(target_years - 2, target_years + 5) for d in digits):
                    return opt

        # 3. Salary options
        if category in [QuestionCategory.SALARY_EXPECTATION, QuestionCategory.CURRENT_SALARY]:
            for opt in clean_options:
                opt_lower = opt.lower()
                # Check for 25M - 35M range
                if any(k in opt_lower for k in ["25", "30", "35", "20 - 30", "20-30", "20 - 35", "25 - 35", "25-35", "> 20", "> 25"]):
                    return opt

        # 4. Notice Period options
        if category == QuestionCategory.NOTICE_PERIOD:
            for opt in clean_options:
                opt_lower = opt.lower()
                if any(k in opt_lower for k in ["immediate", "segera", "1 month", "1 bulan", "30 days", "30 hari", "less than 1 month", "< 1 month"]):
                    return opt

        # 5. Education options
        if category == QuestionCategory.EDUCATION:
            for opt in clean_options:
                opt_lower = opt.lower()
                if any(k in opt_lower for k in ["bachelor", "s1", "undergraduate", "sarjana", "degree"]):
                    return opt

        # 6. Work Flexibility / Mode
        if category in [QuestionCategory.WORK_FLEXIBILITY, QuestionCategory.LOCATION_RELOCATION]:
            for opt in clean_options:
                opt_lower = opt.lower()
                if any(k in opt_lower for k in ["any", "all", "hybrid", "remote", "flexible", "jakarta", "on-site / hybrid / remote", "ya", "yes"]):
                    return opt

        # 7. English Proficiency
        if category == QuestionCategory.LANGUAGE_PROFICIENCY:
            for opt in clean_options:
                opt_lower = opt.lower()
                if any(k in opt_lower for k in ["professional", "fluent", "advanced", "proficient", "tingkat lanjut", "fasih"]):
                    return opt

        # Default fallback to first non-empty option
        return clean_options[0]

    def _get_target_years(self, category: QuestionCategory) -> int:
        """Get integer target years for category."""
        if category == QuestionCategory.YEARS_EXPERIENCE_FINTECH:
            return 6
        if category == QuestionCategory.YEARS_EXPERIENCE_LEADERSHIP:
            return 5
        if category in [QuestionCategory.YEARS_EXPERIENCE_CREDIT_RISK, QuestionCategory.YEARS_EXPERIENCE_SME]:
            return 12
        return 15

    def _generate_contextual_pitch(
        self,
        category: QuestionCategory,
        job_context: Optional[Union[Job, Dict[str, Any]]],
    ) -> str:
        """
        Generate tailored value proposition referencing target company/title.
        """
        base_pitch = self.kb[category]
        if not job_context:
            return base_pitch

        title = job_context.title if isinstance(job_context, Job) else job_context.get("title", "")
        company = job_context.company if isinstance(job_context, Job) else job_context.get("company", "")

        if not title and not company:
            return base_pitch

        tailored_sentence = (
            f"Specifically for the {title or 'Credit Risk'} role at {company or 'your organization'}, "
            "I will apply my 15+ years of institutional commercial banking and regional FinTech underwriting "
            "to streamline credit turnaround times while rigorously safeguarding portfolio risk metrics."
        )

        return f"{base_pitch}\n\n{tailored_sentence}"

    def _generate_fallback_answer(
        self,
        question_text: str,
        job_context: Optional[Union[Job, Dict[str, Any]]],
    ) -> str:
        """
        Factual fallback answer grounded in candidate profile.
        """
        return (
            "I have 15+ years of experience across commercial banking (Maybank, CIMB Niaga) and regional FinTech lending (Aspire SEA), "
            "specializing in SME credit underwriting, financial statement analysis (DSCR), and digital risk scorecard calibration. "
            "I am fully prepared to apply this background to deliver immediate operational results."
        )

    def answer_screening_questions(
        self,
        questions: List[ScreeningQuestion],
        job_context: Optional[Job] = None,
    ) -> List[ScreeningQuestion]:
        """
        Processes and populates answers for a list of ScreeningQuestions on a Job.
        """
        for q in questions:
            ans = self.answer_question(q, job_context)
            q.answer = ans
            q.confidence = 0.95
            logger.info("Answered screening question [%s]: '%s' -> '%s'", q.id, q.question[:40], ans[:60])
        return questions

    def populate_job_answers(self, job: Job) -> Job:
        """
        Answer all screening questions attached to a Job instance.
        """
        if job.screening_questions:
            self.answer_screening_questions(job.screening_questions, job_context=job)
        return job


# Default singleton instance
default_form_engine = FormAnswersEngine()
