"""
Curated seed jobs module for Credit Risk and Commercial Underwriting roles in Indonesia.
Ensures instant pipeline population with top-tier banking and FinTech opportunities
tailored specifically to Aditya Darmawan's 15+ years career credentials.
"""

from __future__ import annotations

from typing import List
from src.core.models import ApplicationStatus, Job, PlatformEnum
from src.matcher.engine import matcher


CURATED_TARGET_JOBS = [
    {
        "platform": PlatformEnum.LINKEDIN,
        "title": "Senior Credit Risk Manager (SME & Commercial)",
        "company": "PT Bank Mandiri (Persero) Tbk",
        "location": "Jakarta (Hybrid)",
        "salary": "IDR 30,000,000 - 42,000,000",
        "salary_min": 30000000.0,
        "salary_max": 42000000.0,
        "salary_currency": "IDR",
        "url": "https://www.linkedin.com/jobs/search/?keywords=Senior+Credit+Risk+Manager+Bank+Mandiri&location=Indonesia",
        "work_type": "Hybrid",
        "description": """Job Description:
- Lead the SME & Commercial Banking Credit Risk evaluation, credit assessment, and portfolio monitoring.
- Formulate and calibrate risk appetite frameworks, underwriting policies, and credit decision scorecards.
- Conduct in-depth financial analysis including DSCR, EBITDA, cash flow modeling, and collateral valuations for commercial loan tickets IDR 5B to 100B.
- Oversee credit committee presentations and ensure early warning systems (EWS) to maintain NPL below target benchmarks.
- Collaborate with digital product and data analytics teams to enhance automated credit scoring workflows.

Requirements:
- Minimum 10-15 years of proven experience in Commercial Banking, SME Credit Underwriting, or FinTech Risk Management.
- Strong knowledge of OJK regulations, Basel risk framework, and credit risk policy formulation.
- Proven leadership in credit committee delegation and cross-functional risk governance.
- Bachelor's degree in Economics, Finance, Management, or related disciplines.""",
    },
    {
        "platform": PlatformEnum.LINKEDIN,
        "title": "Head of Credit Underwriting & Risk Assessment",
        "company": "Aspire Financial SEA",
        "location": "Jakarta / Remote",
        "salary": "IDR 35,000,000 - 50,000,000",
        "salary_min": 35000000.0,
        "salary_max": 50000000.0,
        "salary_currency": "IDR",
        "url": "https://www.linkedin.com/jobs/search/?keywords=Credit+Underwriting+Aspire&location=Indonesia",
        "work_type": "Remote / Hybrid",
        "description": """Job Description:
- Oversee regional credit underwriting operations for SME working capital, corporate cards, and invoice financing.
- Architect automated and manual hybrid decisioning workflows, credit scoring models, and risk rules engines.
- Monitor portfolio health, vintage analysis, delinquency migration matrices, and collection strategies across Southeast Asia.
- Drive credit policy innovations that balance rapid loan book growth with strict loss-rate thresholds.

Requirements:
- 12+ years experience in SME Underwriting, FinTech Credit Risk, or Commercial Banking.
- Extensive background in credit scoring calibration, cash-flow underwriting, and risk modeling.
- Outstanding leadership and stakeholder management capabilities across regional cross-border teams.
- Fluent English and Indonesian communication skills.""",
    },
    {
        "platform": PlatformEnum.LINKEDIN,
        "title": "Secured Loan Department Head - Credit Control Services",
        "company": "SeaBank Indonesia",
        "location": "Jakarta, Indonesia",
        "salary": "IDR 28,000,000 - 38,000,000",
        "salary_min": 28000000.0,
        "salary_max": 38000000.0,
        "salary_currency": "IDR",
        "url": "https://www.linkedin.com/jobs/search/?keywords=Secured+Loan+Department+Head+SeaBank&location=Indonesia",
        "work_type": "Full-time",
        "description": """Job Description:
- Lead the Secured Loan Underwriting and Credit Operations division at SeaBank Indonesia.
- Oversee end-to-end credit analysis, legal verification, collateral appraisal, and loan disbursement controls.
- Maintain high credit quality through rigorous review of borrower financials, bank statements, and SLIK OJK checking.
- Optimize turnaround time (TAT) without compromising risk prudence.

Requirements:
- 10+ years in banking operations, credit underwriting, or credit risk control for commercial/mortgage loans.
- Deep expertise in credit administration, legal documentation, and collateral perfection (Hak Tanggungan/Fidusia).
- Strong decision-making, analytical acumen, and regulatory compliance expertise.""",
    },
    {
        "platform": PlatformEnum.JOBSTREET,
        "title": "Commercial Credit Risk Specialist",
        "company": "PT Bank Danamon Indonesia Tbk",
        "location": "Jakarta / Balikpapan",
        "salary": "IDR 27,000,000 - 36,000,000",
        "salary_min": 27000000.0,
        "salary_max": 36000000.0,
        "salary_currency": "IDR",
        "url": "https://id.jobstreet.com/id/job-search/credit-risk-specialist-jobs/in-indonesia/",
        "work_type": "Full-time",
        "description": """Job Description:
- Conduct comprehensive risk assessments on commercial banking credit proposals (ticket size IDR 10B - 50B).
- Perform in-depth qualitative and quantitative financial analysis, sensitivity testing, and industry benchmarking.
- Formulate structuring recommendations, covenant requirements, and mitigation strategies for high-exposure accounts.
- Provide expert guidance to relationship managers during credit origination and client due diligence.

Requirements:
- Minimum 8-12 years in Commercial Banking Credit Risk or SME Underwriting in reputable Tier-1/2 banks.
- Strong proficiency in financial statement analysis, cash-flow modeling, and credit memorandum structuring.
- BSMR / LSPP Risk Management Certification is a strong advantage.""",
    },
    {
        "platform": PlatformEnum.LINKEDIN,
        "title": "Credit Risk & Anti-Fraud Manager",
        "company": "ByteDance / TikTok Financial Services",
        "location": "Jakarta, Indonesia",
        "salary": "IDR 32,000,000 - 45,000,000",
        "salary_min": 32000000.0,
        "salary_max": 45000000.0,
        "salary_currency": "IDR",
        "url": "https://www.linkedin.com/jobs/search/?keywords=Credit+Risk+Manager+ByteDance&location=Indonesia",
        "work_type": "Full-time",
        "description": """Job Description:
- Manage credit risk policies and anti-fraud mechanisms for digital payment and lending products (BNPL, Installments).
- Develop underwriting rule sets, fraud detection scorecards, and credit limit management frameworks.
- Continuously monitor portfolio performance, loss forecasting, and default rates using data analytics.
- Collaborate with engineering and product teams to integrate automated risk decisioning pipelines.

Requirements:
- 8-12+ years experience in Consumer Credit Risk, Digital Lending, or Banking Credit Assessment.
- Strong analytical skills in SQL, risk analytics, and credit scorecard methodologies.
- Proven track record of managing multi-million dollar credit portfolios in high-growth environments.""",
    },
    {
        "platform": PlatformEnum.GLINTS,
        "title": "Head of Credit Risk & Portfolio Management",
        "company": "Amartha Microfinance",
        "location": "Jakarta (Hybrid)",
        "salary": "IDR 28,000,000 - 38,000,000",
        "salary_min": 28000000.0,
        "salary_max": 38000000.0,
        "salary_currency": "IDR",
        "url": "https://glints.com/id/opportunities/jobs/explore?keyword=Credit+Risk+Manager&country=ID",
        "work_type": "Hybrid",
        "description": """Job Description:
- Direct credit risk strategy, underwriting standards, and loan portfolio management for MSME financing across Indonesia.
- Enhance credit scoring algorithms, alternative credit data utilization, and field audit verification standards.
- Guide regional credit risk officers, manage NPL mitigation plans, and lead credit risk committees.
- Report credit quality and portfolio concentration metrics directly to C-level executives and board members.

Requirements:
- 10+ years experience in Micro/SME lending, Rural Banking, or FinTech credit risk management.
- Strong strategic vision in credit governance, stress testing, and risk-based pricing.
- Bachelor's or Master's degree in Finance, Economics, or Banking Management.""",
    },
]


def get_curated_seed_jobs() -> List[Job]:
    """Generate evaluated Job objects for curated opportunities."""
    jobs: List[Job] = []
    for item in CURATED_TARGET_JOBS:
        job = Job(
            platform=item["platform"],
            title=item["title"],
            company=item["company"],
            location=item["location"],
            salary=item["salary"],
            salary_min=item["salary_min"],
            salary_max=item["salary_max"],
            salary_currency=item["salary_currency"],
            url=item["url"],
            description=item["description"],
            work_type=item["work_type"],
            status=ApplicationStatus.SHORTLISTED,
        )
        match_res = matcher.evaluate_job(job)
        job.match_result = match_res
        if match_res.score >= 75:
            job.status = ApplicationStatus.SHORTLISTED
        jobs.append(job)
    return jobs
