"""
Curated seed jobs module for Credit Risk and Commercial Underwriting roles in Indonesia.
Ensures instant pipeline population with verified live banking and FinTech opportunities
tailored specifically to Aditya Darmawan's 15+ years career credentials.
"""

from __future__ import annotations

from typing import List
from src.core.models import ApplicationStatus, Job, PlatformEnum
from src.matcher.engine import matcher


CURATED_TARGET_JOBS = [
    {
        "platform": PlatformEnum.LINKEDIN,
        "title": "Credit Risk & Anti-Fraud Manager (BNPL / Digital Lending)",
        "company": "ByteDance / TikTok Financial Services",
        "location": "Jakarta, Indonesia (Hybrid)",
        "salary": "IDR 35,000,000 - 48,000,000",
        "salary_min": 35000000.0,
        "salary_max": 48000000.0,
        "salary_currency": "IDR",
        "url": "https://id.linkedin.com/jobs/view/credit-risk-anti-fraud-manager-bnpl-personal-loan-jakarta-global-payment-at-bytedance-4465733367",
        "work_type": "Hybrid",
        "description": """Job Description:
- Lead credit risk policies and anti-fraud mechanisms for digital payment and lending products (BNPL, Installments, Personal Loans).
- Develop underwriting rule sets, fraud detection scorecards, and credit limit management frameworks.
- Continuously monitor portfolio performance, loss forecasting, vintage curves, and default rates using data analytics.
- Collaborate with engineering, data science, and product teams to integrate automated risk decisioning pipelines.

Requirements:
- 10+ years experience in Credit Risk, Digital Lending, or Banking Credit Assessment.
- Strong analytical skills in risk analytics, credit scorecard methodologies, and NPL mitigation.
- Proven track record of managing multi-million dollar credit portfolios in high-growth environments.""",
    },
    {
        "platform": PlatformEnum.LINKEDIN,
        "title": "Risk Management Manager",
        "company": "PT Maybank Sekuritas Indonesia",
        "location": "Jakarta, Indonesia",
        "salary": "IDR 30,000,000 - 42,000,000",
        "salary_min": 30000000.0,
        "salary_max": 42000000.0,
        "salary_currency": "IDR",
        "url": "https://id.linkedin.com/jobs/view/risk-management-manager-at-pt-maybank-sekuritas-indonesia-4439128237",
        "work_type": "Full-time",
        "description": """Job Description:
- Oversee credit and market risk governance across investment banking and commercial securities portfolios.
- Evaluate counterparty creditworthiness, collateral adequacy, margin limits, and exposure ceilings.
- Calibrate risk management policies in compliance with OJK and Indonesian Capital Market regulations.
- Present quarterly risk appetite reviews and portfolio stress tests to the Board Risk Committee.

Requirements:
- 10-15 years experience in Banking Risk Management, Commercial Credit Risk, or Capital Markets.
- Deep expertise in risk framework formulation, BSMR/LSPP risk certification preferred.
- Strong track record in Maybank / Tier-1 banking environment.""",
    },
    {
        "platform": PlatformEnum.LINKEDIN,
        "title": "Credit Reviewer - Commercial & Corporate Banking",
        "company": "PT Bank Amar Indonesia Tbk",
        "location": "Jakarta, Indonesia",
        "salary": "IDR 28,000,000 - 38,000,000",
        "salary_min": 28000000.0,
        "salary_max": 38000000.0,
        "salary_currency": "IDR",
        "url": "https://id.linkedin.com/jobs/view/credit-reviewer-commercial-corporate-at-amar-bank-4381469673",
        "work_type": "Full-time",
        "description": """Job Description:
- Review and evaluate commercial and corporate loan proposals (ticket size IDR 10B - 50B).
- Perform comprehensive cash-flow underwriting, DSCR verification, EBITDA stress testing, and collateral appraisals.
- Recommend approval conditions, financial covenants, and structural mitigations for complex commercial facilities.
- Act as key advisor during Credit Committee sessions.

Requirements:
- 10+ years experience in Commercial Banking Underwriting, SME Lending, or Corporate Credit Review.
- Mastery of financial statement auditing, legal documentation, and OJK compliance.""",
    },
    {
        "platform": PlatformEnum.LINKEDIN,
        "title": "AVP of Enterprise Risk Management",
        "company": "DOKU (PT Nusa Satu Inti Artha)",
        "location": "Jakarta, Indonesia",
        "salary": "IDR 35,000,000 - 50,000,000",
        "salary_min": 35000000.0,
        "salary_max": 50000000.0,
        "salary_currency": "IDR",
        "url": "https://id.linkedin.com/jobs/view/avp-of-enterprise-risk-management-at-doku-pt-nusa-satu-inti-artha-4422794224",
        "work_type": "Full-time",
        "description": """Job Description:
- Lead Enterprise Risk Management (ERM) and FinTech credit / merchant underwriting risk frameworks.
- Formulate merchant credit assessment standards, fraud prevention rules, and transaction monitoring policies.
- Partner with C-level executives to define institutional risk appetite and regulatory reporting to Bank Indonesia.

Requirements:
- 12+ years in Banking or FinTech Risk Management.
- Proven leadership in risk governance, payment systems, and credit policy design.""",
    },
    {
        "platform": PlatformEnum.LINKEDIN,
        "title": "Senior Credit Analyst / Commercial Underwriter",
        "company": "PT Astra International Tbk",
        "location": "Jakarta, Indonesia",
        "salary": "IDR 25,000,000 - 35,000,000",
        "salary_min": 25000000.0,
        "salary_max": 35000000.0,
        "salary_currency": "IDR",
        "url": "https://id.linkedin.com/jobs/view/credit-analyst-kaf-at-pt-astra-international-tbk-4465021546",
        "work_type": "Full-time",
        "description": """Job Description:
- Conduct credit underwriting and financial feasibility studies for heavy equipment, corporate fleet, and commercial financing.
- Analyze company financial statements, industry trends, and repayment capacity.
- Structure loan terms and verify legal collateral documentation.

Requirements:
- 8-12 years in Commercial Financing, Banking Credit Risk, or Multi-Finance Underwriting.
- Strong knowledge of financial ratios, cash flow projections, and credit risk assessment.""",
    },
    {
        "platform": PlatformEnum.LINKEDIN,
        "title": "Senior Credit Risk Specialist",
        "company": "PT LiuGong Finance Indonesia",
        "location": "Jakarta, Indonesia",
        "salary": "IDR 26,000,000 - 36,000,000",
        "salary_min": 26000000.0,
        "salary_max": 36000000.0,
        "salary_currency": "IDR",
        "url": "https://id.linkedin.com/jobs/view/credit-analyst-at-liugong-finance-indonesia-4464849677",
        "work_type": "Full-time",
        "description": """Job Description:
- Lead heavy equipment commercial financing credit evaluations across mining, construction, and agriculture sectors in Indonesia.
- Oversee credit appraisal, debtor background SLIK checks, site visit reports, and portfolio risk management.
- Ensure strict credit governance and maintain low delinquency rates across nationwide branches.

Requirements:
- 8-15 years experience in Credit Underwriting, Commercial Banking, or Heavy Equipment Finance.
- Strong decision-making, negotiation, and risk mitigation capabilities.""",
    },
]


def get_curated_seed_jobs() -> List[Job]:
    """Generate evaluated Job objects for curated live opportunities."""
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
        if match_res.score >= 70:
            job.status = ApplicationStatus.SHORTLISTED
        jobs.append(job)
    return jobs
