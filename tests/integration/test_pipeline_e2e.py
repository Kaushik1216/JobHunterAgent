import pytest
from unittest.mock import MagicMock
from job_agent.core.pipeline import Pipeline
from job_agent.models.schemas import SearchTarget, RawJobResult, EvaluatedJob
from job_agent.models.enums import JobStatus
from job_agent.observability.metrics import MetricsCollector

def test_pipeline_e2e(db_manager, repository, settings, tmp_path, sample_evaluated_job):
    # Setup mocks
    mock_searcher = MagicMock()
    mock_ollama_client = MagicMock()
    mock_output_guard = MagicMock()
    
    # Configure exporter
    from job_agent.export.markdown_exporter import MarkdownExporter
    exporter = MarkdownExporter(tmp_path / "jobs.md")
    
    # Configure metrics
    metrics = MetricsCollector()
    
    # Create target
    target = SearchTarget(
        company="Test Corp",
        title="Engineer",
        location="Remote",
        target_yoe=3,
        core_skills=["Python"]
    )
    
    # Mock raw job results
    raw_job = RawJobResult(
        title="Test Engineer",
        url="https://linkedin.com/jobs/view/123",
        snippet="Test snippet",
        source_query="test query",
        source_portal="linkedin",
    )
    # The pipeline calls searcher.search()
    mock_searcher.search.return_value = [raw_job]
    
    # Mock ollama text generation
    mock_ollama_client.generate.return_value = '{"test": "json"}'
    
    # Mock output guard parsing
    mock_output_guard.validate_and_parse.return_value = sample_evaluated_job
    
    # Initialize pipeline
    pipeline = Pipeline(
        searcher=mock_searcher,
        repository=repository,
        ollama_client=mock_ollama_client,
        output_guard=mock_output_guard,
        exporter=exporter,
        metrics=metrics,
        settings=settings
    )
    
    # The pipeline filters by settings.fit_score_threshold
    settings.fit_score_threshold = 0.5
    
    # Run pipeline
    qualified_jobs = pipeline.process_target(target)
    
    # Verify results
    assert len(qualified_jobs) == 1
    assert qualified_jobs[0].title == sample_evaluated_job.title
    
    # Verify persistence
    assert repository.job_exists(sample_evaluated_job.url_hash())
    
    # Verify metrics
    assert metrics.jobs_found == 1
    assert metrics.jobs_qualified == 1
