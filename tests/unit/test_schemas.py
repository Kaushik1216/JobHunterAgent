import pytest
from datetime import datetime
from pydantic import ValidationError
from job_agent.models.schemas import (
    GlobalFilters, SearchTarget, CriteriaConfig,
    RawJobResult, EvaluatedJob, ExecutionSummary
)
from job_agent.models.enums import JobStatus

def test_global_filters_valid():
    gf = GlobalFilters(target_yoe=5, preferred_locations=["NY"], core_skills=["Python"])
    assert gf.target_yoe == 5

def test_search_target_merge(sample_search_target):
    gf = GlobalFilters(target_yoe=5, preferred_locations=["NY"], core_skills=["Python", "Go"])
    merged = sample_search_target.merge_with_globals(gf)
    assert merged.target_yoe == 3
    assert merged.core_skills == ["Python"]

    target2 = SearchTarget(company="A", title="B", location="C")
    merged2 = target2.merge_with_globals(gf)
    assert merged2.target_yoe == 5
    assert merged2.core_skills == ["Python", "Go"]

def test_criteria_config_resolve():
    gf = GlobalFilters(target_yoe=2, preferred_locations=[], core_skills=["A"])
    target = SearchTarget(company="C", title="T", location="L")
    config = CriteriaConfig(global_filters=gf, targets=[target])
    resolved = config.resolve_targets()
    assert resolved[0].target_yoe == 2

def test_evaluated_job_hashing(sample_evaluated_job):
    import hashlib
    expected_hash = hashlib.sha256("https://linkedin.com/jobs/view/123".encode("utf-8")).hexdigest()
    assert sample_evaluated_job.url_hash() == expected_hash

def test_evaluated_job_validation():
    with pytest.raises(ValidationError):
        EvaluatedJob(
            title="A", company="B", location="C",
            extracted_min_yoe=0, extracted_max_yoe=0, yoe_match=True,
            matched_skills=[], missing_skills=[],
            fit_score=1.5, # Invalid
            summary_reason="", apply_url="http://a.com"
        )
    with pytest.raises(ValidationError):
        EvaluatedJob(
            title="A", company="B", location="C",
            extracted_min_yoe=0, extracted_max_yoe=0, yoe_match=True,
            matched_skills=[], missing_skills=[],
            fit_score=-0.1, # Invalid
            summary_reason="", apply_url="http://a.com"
        )

def test_execution_summary_properties():
    start = datetime(2023, 1, 1, 12, 0, 0)
    end = datetime(2023, 1, 1, 12, 0, 10)
    summary = ExecutionSummary(run_id="test", started_at=start, completed_at=end, jobs_found=10, jobs_qualified=5)
    assert summary.duration_seconds == 10.0
    assert summary.qualification_rate == 0.5

    empty_summary = ExecutionSummary(run_id="test2", started_at=start, jobs_found=0)
    assert empty_summary.duration_seconds == 0.0
    assert empty_summary.qualification_rate == 0.0
