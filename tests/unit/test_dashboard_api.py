import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from dashboard.api import create_app
from models.schemas import EvaluatedJob


def test_api_list_jobs_and_filters(settings, sample_evaluated_job):
    app = create_app(settings)
    client = TestClient(app)

    # Insert sample job into repo
    repo = app.state.dashboard.repository
    repo.save_job(sample_evaluated_job)

    # GET /api/jobs
    res = client.get("/api/jobs")
    assert res.status_code == 200
    jobs = res.json()
    assert len(jobs) == 1
    assert jobs[0]["title"] == sample_evaluated_job.title

    # Filter with status
    res = client.get("/api/jobs?status=NEW")
    assert res.status_code == 200
    assert len(res.json()) == 1

    res = client.get("/api/jobs?status=APPLIED")
    assert res.status_code == 200
    assert len(res.json()) == 0

    # Filter with sort
    res = client.get("/api/jobs?sort=days_ago")
    assert res.status_code == 200
    assert len(res.json()) == 1


def test_api_evaluate_single_job(settings, sample_evaluated_job):
    app = create_app(settings)
    client = TestClient(app)

    # Insert sample job as unevaluated
    job_id = sample_evaluated_job.url_hash()
    sample_evaluated_job.evaluated = False
    sample_evaluated_job.fit_score = 0.0
    app.state.dashboard.repository.save_job(sample_evaluated_job)

    # Mock Pipeline._match_one
    mock_evaluated = sample_evaluated_job.model_copy(update={
        "evaluated": True,
        "fit_score": 0.92,
        "matched_skills": ["Python", "FastAPI"],
        "missing_skills": [],
        "summary_reason": "Excellent candidate fit",
    })

    with patch("dashboard.api.Pipeline._match_one", return_value=mock_evaluated):
        res = client.post(f"/api/jobs/{job_id}/evaluate")
        assert res.status_code == 200
        data = res.json()
        assert data["id"] == job_id
        assert data["evaluated"] is True
        assert data["fit_score"] == 0.92
        assert "FastAPI" in data["matched_skills"]


def test_api_evaluate_job_not_found(settings):
    app = create_app(settings)
    client = TestClient(app)

    res = client.post("/api/jobs/nonexistent-job-id/evaluate")
    assert res.status_code == 404
