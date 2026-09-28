"""
Tests for Gemini AI Assistant integration.
"""

import pytest
from src.core.gemini_assistant import gemini_assistant
from src.core.models import Job, PlatformEnum


@pytest.mark.asyncio
async def test_gemini_assistant_chat_offline_fallback():
    # Test fallback formatting
    res = gemini_assistant._generate_fallback_response(
        "status lowongan",
        {
            "pipeline_statistics": {"total": 5, "avg_match_score": 85.0},
            "shortlisted_pending_jobs": [
                {
                    "id": "job_123",
                    "title": "Credit Risk Manager",
                    "company": "Bank Digital XYZ",
                    "salary": "IDR 25M - 35M",
                    "score": 90,
                }
            ],
        },
    )
    assert "Bank Digital XYZ" in res
    assert "Credit Risk Manager" in res


@pytest.mark.asyncio
async def test_gemini_assistant_context_gathering():
    ctx = await gemini_assistant._gather_system_context("halo apa kabar")
    assert "candidate" in ctx
    assert ctx["candidate"]["name"] == "Aditya Darmawan"
    assert "pipeline_statistics" in ctx
