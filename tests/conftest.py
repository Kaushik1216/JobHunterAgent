import pytest
from pathlib import Path
from job_agent.config import Settings
from job_agent.storage.database import DatabaseManager
from job_agent.storage.repository import JobRepository
from job_agent.models.schemas import EvaluatedJob, SearchTarget

@pytest.fixture
def tmp_db_path(tmp_path: Path) -> Path:
    return tmp_path / "test.db"

@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(
        db_path=tmp_path / "test.db",
        output_path=tmp_path / "jobs.md",
        criteria_path=tmp_path / "criteria.yaml",
        search_jitter_min=0.0,
        search_jitter_max=0.0,
        search_circuit_breaker_threshold=3,
        search_circuit_breaker_cooldown=60
    )

@pytest.fixture
def db_manager(tmp_db_path: Path):
    manager = DatabaseManager(tmp_db_path)
    with manager:
        manager.run_migrations()
        yield manager

@pytest.fixture
def repository(db_manager: DatabaseManager):
    return JobRepository(db_manager)

@pytest.fixture
def sample_evaluated_job() -> EvaluatedJob:
    return EvaluatedJob(
        title="Software Engineer",
        company="Test Corp",
        location="Remote",
        extracted_min_yoe=2,
        extracted_max_yoe=5,
        yoe_match=True,
        matched_skills=["Python", "Docker"],
        missing_skills=["FastAPI"],
        fit_score=0.85,
        summary_reason="Good match",
        apply_url="https://linkedin.com/jobs/view/123",
        source_query="test query",
        source_portal="linkedin",
        raw_snippet="We are looking for..."
    )

@pytest.fixture
def sample_search_target() -> SearchTarget:
    return SearchTarget(
        company="Test Corp",
        title="Engineer",
        location="Remote",
        target_yoe=3,
        core_skills=["Python"]
    )

@pytest.fixture
def sample_criteria_yaml(tmp_path: Path) -> Path:
    yaml_content = """
global:
  target_yoe: 3
  preferred_locations: ["Remote"]
  core_skills: ["Python", "FastAPI"]
targets:
  - company: "Stripe"
    title: "Software Engineer"
    location: "Remote"
"""
    yaml_path = tmp_path / "criteria.yaml"
    yaml_path.write_text(yaml_content)
    return yaml_path
