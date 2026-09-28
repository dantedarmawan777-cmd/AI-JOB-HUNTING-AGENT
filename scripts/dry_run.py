"""
End-to-End Dry-Run Simulation Script for AI Job-Hunting Agent.
Demonstrates the full pipeline:
1. Candidate profile loading (Aditya Darmawan)
2. Job posting ingestion & blacklist filtering
3. Weighted scoring & 2-sentence rationale generation
4. Contextual screening Q&A copy generation
5. SQLite tracking database persistence
6. Telegram HITL notification card rendering
7. Form detection & auto-fill preview
"""

from __future__ import annotations

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

# Configure UTF-8 stdout for Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Add project root directory to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import config
from src.core.database import db
from src.core.logger import get_logger
from src.core.models import (
    ApplicationStatus,
    Job,
    MatchResult,
    PlatformEnum,
    ScreeningQuestion,
    ScreeningQuestionType,
)
from src.matcher.blacklist import default_blacklist
from src.matcher.matcher import default_matcher
from src.matcher.profile_loader import load_candidate_profile
from src.copywriter.form_answers import default_form_engine
from src.telegram_hitl.messages import format_job_alert

logger = get_logger("dry_run")

SAMPLE_JOBS = [
    {
        "platform": PlatformEnum.JOBSTREET,
        "title": "Senior Credit Risk & Underwriting Lead (SME Loan)",
        "company": "PT Bank Digital Nusantara, Tbk",
        "location": "Jakarta Selatan (Hybrid)",
        "url": "https://www.jobstreet.co.id/job/76543210",
        "salary_min": 25000000,
        "salary_max": 35000000,
        "salary_currency": "IDR",
        "work_type": "Hybrid",
        "description": (
            "We are looking for a Senior Credit Risk & Underwriting Lead with 7+ years of experience in SME lending, "
            "commercial credit appraisal, debt service coverage ratio (DSCR) modeling, and digital risk scorecard calibration. "
            "The candidate will lead underwriting decisions, refine credit policies, mitigate NPLs, and collaborate with product teams."
        ),
        "posted_date": "2026-09-27",
        "screening_questions": [
            ScreeningQuestion(
                question="How many years of experience do you have in SME credit risk underwriting?",
                question_type=ScreeningQuestionType.NUMBER,
                required=True,
            ),
            ScreeningQuestion(
                question="What is your expected monthly salary in IDR?",
                question_type=ScreeningQuestionType.TEXT,
                required=True,
            ),
            ScreeningQuestion(
                question="Describe your experience with credit policy and scorecard calibration.",
                question_type=ScreeningQuestionType.TEXT,
                required=True,
            ),
            ScreeningQuestion(
                question="What is your current notice period?",
                question_type=ScreeningQuestionType.SELECT,
                options=["Immediately Available", "1 Month Notice", "2 Months Notice", "3+ Months Notice"],
                required=True,
            ),
        ],
    },
    {
        "platform": PlatformEnum.GLINTS,
        "title": "Credit Risk Manager (FinTech Lending)",
        "company": "FinTech Asia Capital",
        "location": "Jakarta (Remote)",
        "url": "https://glints.com/id/opportunities/jobs/credit-risk-mgr",
        "salary_min": 28000000,
        "salary_max": 40000000,
        "salary_currency": "IDR",
        "work_type": "Remote",
        "description": (
            "Seeking an experienced Credit Risk Manager to oversee alternative data underwriting, e-commerce loan portfolio risk, "
            "and SME working capital facilities. Minimum 5+ years in banking/fintech credit risk, strong command of DSCR, financial spreading, "
            "and automated decisioning engines."
        ),
        "posted_date": "2026-09-26",
        "screening_questions": [
            ScreeningQuestion(
                question="Do you have experience in both conventional banking and FinTech credit underwriting?",
                question_type=ScreeningQuestionType.TEXT,
                required=True,
            )
        ],
    },
    {
        "platform": PlatformEnum.KALIBRR,
        "title": "Fresh Graduate Admin Kredit & Telemarketing",
        "company": "PT Pinjaman Kilat Cepat",
        "location": "Jakarta Barat",
        "url": "https://www.kalibrr.com/c/sample/jobs/admin-kredit",
        "salary_min": 4500000,
        "salary_max": 5000000,
        "salary_currency": "IDR",
        "work_type": "On-site",
        "description": "Dibutuhkan staff admin kredit pemula dan telemarketing penawaran dana kilat harian tanpa jaminan. Fresh graduate dipersilahkan.",
        "posted_date": "2026-09-28",
        "screening_questions": [],
    },
]


async def run_dry_run_simulation() -> None:
    print("=" * 75)
    print(" 🚀 AI JOB-HUNTING & AUTO-APPLY BOT: DRY-RUN SIMULATION PIPELINE")
    print("=" * 75)

    # 1. Load Candidate Profile
    profile = load_candidate_profile()
    print(f"\n[1] Candidate Profile Loaded: {profile.full_name}")
    print(f"    • Title: {profile.title}")
    print(f"    • Experience: {profile.total_years_experience}+ Years across Banking & FinTech")
    print(f"    • Target Salary: IDR {profile.salary_expectation.expected_min:,.0f} - {profile.salary_expectation.expected_target:,.0f} / month")
    print(f"    • Target Locations: {', '.join(profile.locations)}")
    print(f"    • CV Files: EN={Path(profile.cv_files.get('EN', '')).name} | ID={Path(profile.cv_files.get('ID', '')).name}")

    # 2. Process Job Postings
    print("\n[2] Ingesting Job Postings & Running Filter / Matcher Pipeline...\n")
    processed_jobs = []

    for raw in SAMPLE_JOBS:
        job = Job(**raw)
        print(f"--- Processing: [{job.platform.value.upper()}] {job.title} @ {job.company} ---")

        # Step 2a: Blacklist Filter
        exclusion = default_blacklist.evaluate(job)

        if exclusion.is_excluded:
            job.status = ApplicationStatus.REJECTED
            print(f"  ❌ BLACKLISTED: [{exclusion.category}] {exclusion.reason}")
            await db.save_job(job)
            continue

        # Step 2b: Scoring & Matching
        match_res = default_matcher.calculate_match(job)
        job.match_result = match_res

        print(f"  🎯 Match Score: {match_res.score}% (Threshold: {config.min_match_score}%)")
        print(f"  📝 Rationale: {match_res.reasoning}")
        if match_res.matching_points:
            print(f"  💡 Matching Points: {', '.join(match_res.matching_points[:3])}")

        if match_res.score >= config.min_match_score:
            job.status = ApplicationStatus.SHORTLISTED
            # Step 2c: Generate Contextual Q&A Answers
            job = default_form_engine.populate_job_answers(job)
            print(f"  ✅ SHORTLISTED! Generated {len(job.screening_questions)} tailored screening responses.")
        else:
            job.status = ApplicationStatus.DISCOVERED
            print(f"  ⚠️ Score below threshold, saved as discovered.")

        await db.save_job(job)
        processed_jobs.append(job)
        print()

    # 3. Simulate Telegram HITL Notification Card
    print("=" * 75)
    print(" 📱 TELEGRAM HUMAN-IN-THE-LOOP (HITL) NOTIFICATION CARDS")
    print("=" * 75)

    for job in processed_jobs:
        if job.status != ApplicationStatus.SHORTLISTED:
            continue

        card_md = format_job_alert(job)
        print(f"\n[Telegram Message Payload -> User Chat]")
        print("-" * 60)
        print(card_md)
        print("-" * 60)
        print("Inline Interactive Buttons:")
        print(" [✅ Approve & Auto-Apply]  [❌ Skip]  [📄 CV: EN (Switch to ID)]  [🔗 Open Listing]")
        print("-" * 60)

        # Show Generated Screening Answers
        print("\n📋 Form Auto-Fill Preview (Zero-Slop Tailored Responses):")
        for idx, sq in enumerate(job.screening_questions, 1):
            print(f"  {idx}. Q: {sq.question}")
            print(f"     A: {sq.answer}")
            print(f"     Type: {sq.question_type.value} | Confidence: {int(sq.confidence * 100)}%")
        print()

    # 4. Display Database Statistics
    print("=" * 75)
    print(" 📊 LOCAL DATABASE & TRACKER DASHBOARD (data/jobs.db)")
    print("=" * 75)
    stats = await db.get_statistics()
    print(f"Total Jobs in DB:     {stats.get('total', 0)}")
    print(f"Average Match Score:  {stats.get('avg_match_score', 0)}%")
    print("\nStatus Breakdown:")
    for st, cnt in stats.get("by_status", {}).items():
        print(f"  • {st.upper():<16}: {cnt}")
    print("\nPlatform Breakdown:")
    for pl, cnt in stats.get("by_platform", {}).items():
        print(f"  • {pl.capitalize():<16}: {cnt}")

    print("\n" + "=" * 75)
    print(" ✅ DRY-RUN SIMULATION FINISHED SUCCESSFULLY! (Zero live submissions)")
    print("=" * 75 + "\n")


if __name__ == "__main__":
    asyncio.run(run_dry_run_simulation())
