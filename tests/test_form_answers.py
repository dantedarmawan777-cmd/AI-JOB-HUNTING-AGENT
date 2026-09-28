"""
Unit tests for FormAnswersEngine module.
"""

import pytest
from src.copywriter.form_answers import FormAnswersEngine, QuestionCategory
from src.core.models import Job, PlatformEnum, ScreeningQuestion, ScreeningQuestionType


@pytest.fixture
def form_engine():
    return FormAnswersEngine()


def test_question_classification(form_engine):
    assert form_engine.classify_question("How many years of total experience do you have?") == QuestionCategory.YEARS_EXPERIENCE_TOTAL
    assert form_engine.classify_question("Berapa tahun pengalaman Anda di credit risk?") == QuestionCategory.YEARS_EXPERIENCE_CREDIT_RISK
    assert form_engine.classify_question("Years of experience in SME lending?") == QuestionCategory.YEARS_EXPERIENCE_SME
    assert form_engine.classify_question("Experience in FinTech / Digital lending?") == QuestionCategory.YEARS_EXPERIENCE_FINTECH
    assert form_engine.classify_question("What is your expected monthly salary?") == QuestionCategory.SALARY_EXPECTATION
    assert form_engine.classify_question("Berapa lama notice period Anda?") == QuestionCategory.NOTICE_PERIOD
    assert form_engine.classify_question("Why should we hire you for this role?") == QuestionCategory.WHY_HIRE_ME
    assert form_engine.classify_question("What are your key career achievements?") == QuestionCategory.KEY_ACHIEVEMENTS
    assert form_engine.classify_question("Describe your experience with financial statements and DSCR.") == QuestionCategory.FINANCIAL_SPREADING_DSCR
    assert form_engine.classify_question("Have you calibrated underwriting scorecards?") == QuestionCategory.SCORECARD_CALIBRATION


def test_factual_answers_content(form_engine):
    # Why hire me
    ans_why = form_engine.answer_question("Why should we hire you?")
    assert "15+ years" in ans_why
    assert "Maybank" in ans_why
    assert "Aspire SEA" in ans_why
    assert "Best Sales Person RO SME UpCountry (2014)" in ans_why

    # Key achievements
    ans_achieve = form_engine.answer_question("Key career achievements")
    assert "Best Sales Person RO SME UpCountry (2014)" in ans_achieve
    assert "Aspire SEA" in ans_achieve

    # Salary expectation
    ans_salary = form_engine.answer_question("Expected salary")
    assert "25,000,000" in ans_salary
    assert "35,000,000" in ans_salary

    # Notice period
    ans_notice = form_engine.answer_question("Notice period / Availability")
    assert "Immediately" in ans_notice or "1 month" in ans_notice


def test_numeric_question_type(form_engine):
    q_tot = ScreeningQuestion(
        question="Total years of experience?",
        question_type=ScreeningQuestionType.NUMBER,
    )
    ans_tot = form_engine.answer_question(q_tot)
    assert ans_tot == "15"

    q_cr = ScreeningQuestion(
        question="Years of credit underwriting experience?",
        question_type=ScreeningQuestionType.NUMBER,
    )
    ans_cr = form_engine.answer_question(q_cr)
    assert ans_cr == "12"

    q_fin = ScreeningQuestion(
        question="Years in FinTech?",
        question_type=ScreeningQuestionType.NUMBER,
    )
    ans_fin = form_engine.answer_question(q_fin)
    assert ans_fin == "6"

    q_sal = ScreeningQuestion(
        question="Expected monthly salary (numbers only)?",
        question_type=ScreeningQuestionType.NUMBER,
    )
    ans_sal = form_engine.answer_question(q_sal)
    assert ans_sal == "25000000"


def test_option_selection_matching(form_engine):
    # Experience range dropdown
    q_exp = ScreeningQuestion(
        question="How many years of relevant experience do you possess?",
        question_type=ScreeningQuestionType.SELECT,
        options=["< 1 year", "1-3 years", "3-5 years", "5-10 years", "> 10 years"],
    )
    ans_exp = form_engine.answer_question(q_exp)
    assert ans_exp == "> 10 years"

    # Notice period radio
    q_np = ScreeningQuestion(
        question="When are you available to start?",
        question_type=ScreeningQuestionType.RADIO,
        options=["Immediately", "2 weeks", "1 month", "2 months or more"],
    )
    ans_np = form_engine.answer_question(q_np)
    assert ans_np in ["Immediately", "1 month"]

    # Education select
    q_edu = ScreeningQuestion(
        question="Highest degree completed?",
        question_type=ScreeningQuestionType.SELECT,
        options=["High School", "Diploma / D3", "Bachelor's Degree (S1)", "Master's Degree (S2)", "Doctorate"],
    )
    ans_edu = form_engine.answer_question(q_edu)
    assert ans_edu == "Bachelor's Degree (S1)"

    # Yes/No Question
    q_auth = ScreeningQuestion(
        question="Are you authorized to work in Indonesia?",
        question_type=ScreeningQuestionType.RADIO,
        options=["Yes", "No"],
    )
    ans_auth = form_engine.answer_question(q_auth)
    assert ans_auth == "Yes"


def test_populate_job_answers(form_engine):
    job = Job(
        platform=PlatformEnum.JOBSTREET,
        title="Credit Underwriting Specialist",
        company="PT Finansial Unggul",
        location="Jakarta",
        url="https://jobstreet.co.id/job/test-555",
        screening_questions=[
            ScreeningQuestion(question="Expected monthly salary?", question_type=ScreeningQuestionType.TEXT),
            ScreeningQuestion(question="Notice period?", question_type=ScreeningQuestionType.TEXT),
            ScreeningQuestion(question="Why should we hire you?", question_type=ScreeningQuestionType.TEXT),
            ScreeningQuestion(question="Years of experience in credit risk?", question_type=ScreeningQuestionType.NUMBER),
        ],
    )

    populated_job = form_engine.populate_job_answers(job)
    for q in populated_job.screening_questions:
        assert q.answer is not None
        assert len(q.answer) > 0
        assert q.confidence >= 0.90
