"""
Tests for Web Dashboard HTTP endpoints and REST API.
"""

import pytest
from aiohttp.test_utils import TestClient, TestServer
from src.dashboard.server import create_dashboard_app


@pytest.mark.asyncio
async def test_dashboard_index_route():
    app = create_dashboard_app()
    client = TestClient(TestServer(app))
    await client.start_server()

    try:
        res = await client.get("/")
        assert res.status == 200
        text = await res.text()
        assert "AI Job-Hunting" in text
        assert "Aditya Darmawan" in text
    finally:
        await client.close()


@pytest.mark.asyncio
async def test_dashboard_stats_and_jobs_api():
    app = create_dashboard_app()
    client = TestClient(TestServer(app))
    await client.start_server()

    try:
        # Test stats
        res_stats = await client.get("/api/stats")
        assert res_stats.status == 200
        stats = await res_stats.json()
        assert "total" in stats

        # Test jobs
        res_jobs = await client.get("/api/jobs")
        assert res_jobs.status == 200
        jobs = await res_jobs.json()
        assert isinstance(jobs, list)

        # Test profile
        res_prof = await client.get("/api/profile")
        assert res_prof.status == 200
        prof = await res_prof.json()
        assert prof["full_name"] == "Aditya Darmawan"
    finally:
        await client.close()
