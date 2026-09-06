import pytest
from pathlib import Path
from job_agent.export.markdown_exporter import MarkdownExporter
from job_agent.models.schemas import ExecutionSummary

def test_export_jobs(tmp_path, sample_evaluated_job):
    out_file = tmp_path / "jobs.md"
    exporter = MarkdownExporter(out_file)
    exporter.export_jobs([sample_evaluated_job])
    
    assert out_file.exists()
    content = out_file.read_text()
    assert "Job Discovery Report" in content
    assert sample_evaluated_job.company in content
    assert sample_evaluated_job.title in content
    assert f"{sample_evaluated_job.fit_score:.2f}" in content

def test_export_empty_jobs(tmp_path):
    out_file = tmp_path / "jobs.md"
    exporter = MarkdownExporter(out_file)
    exporter.export_jobs([])
    
    content = out_file.read_text()
    assert "No qualified jobs found" in content

def test_jobs_sorted_by_score(tmp_path, sample_evaluated_job):
    job2 = sample_evaluated_job.model_copy()
    job2.title = "Better Job"
    job2.fit_score = 0.95
    
    out_file = tmp_path / "jobs.md"
    exporter = MarkdownExporter(out_file)
    exporter.export_jobs([sample_evaluated_job, job2])
    
    content = out_file.read_text()
    # job2 should appear before sample_evaluated_job
    idx1 = content.find("Better Job")
    idx2 = content.find("Software Engineer")
    assert idx1 < idx2
