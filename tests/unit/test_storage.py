import pytest
import sqlite3
from database.database import DatabaseManager
from database.repository import JobRepository
from models.enums import JobStatus

def test_database_manager_connects(tmp_db_path):
    manager = DatabaseManager(tmp_db_path)
    conn = manager.connect()
    assert isinstance(conn, sqlite3.Connection)
    assert tmp_db_path.exists()
    manager.close()

def test_migrations_idempotent(db_manager):
    # migrations already run in fixture
    cursor = db_manager.execute("SELECT version FROM schema_migrations")
    initial_count = len(cursor.fetchall())
    
    # run again
    db_manager.run_migrations()
    cursor = db_manager.execute("SELECT version FROM schema_migrations")
    assert len(cursor.fetchall()) == initial_count

def test_save_and_get_job(repository, sample_evaluated_job):
    repository.save_job(sample_evaluated_job)
    assert repository.job_exists(sample_evaluated_job.url_hash())
    
    job = repository.get_job(sample_evaluated_job.url_hash())
    assert job is not None
    assert job.title == sample_evaluated_job.title
    assert job.company == sample_evaluated_job.company
    assert job.source_portal == "linkedin"

def test_save_duplicate_job(repository, sample_evaluated_job):
    repository.save_job(sample_evaluated_job)
    repository.save_job(sample_evaluated_job)  # Should not raise error
    
    jobs = repository.get_all_jobs()
    assert len(jobs) == 1

def test_get_jobs_by_status(repository, sample_evaluated_job):
    sample_evaluated_job.status = JobStatus.NEW
    repository.save_job(sample_evaluated_job)
    
    jobs = repository.get_jobs_by_status(JobStatus.NEW)
    assert len(jobs) == 1
    
    jobs_empty = repository.get_jobs_by_status(JobStatus.APPLIED)
    assert len(jobs_empty) == 0

def test_get_all_qualified(repository, sample_evaluated_job):
    sample_evaluated_job.fit_score = 0.8
    repository.save_job(sample_evaluated_job)
    
    jobs = repository.get_all_qualified(min_score=0.7)
    assert len(jobs) == 1
    
    jobs_empty = repository.get_all_qualified(min_score=0.9)
    assert len(jobs_empty) == 0

def test_update_status(repository, sample_evaluated_job):
    repository.save_job(sample_evaluated_job)
    repository.update_status(sample_evaluated_job.url_hash(), JobStatus.APPLIED)
    
    job = repository.get_job(sample_evaluated_job.url_hash())
    assert job.status == JobStatus.APPLIED

def test_get_run_stats(repository, sample_evaluated_job):
    repository.save_job(sample_evaluated_job)
    stats = repository.get_run_stats()
    assert stats[JobStatus.NEW.value] == 1
    assert stats["total"] == 1


def test_list_jobs_statuses_filter(repository, sample_evaluated_job):
    sample_evaluated_job.status = JobStatus.NEW
    repository.save_job(sample_evaluated_job)

    results_new = repository.list_jobs(statuses=["NEW"])
    assert len(results_new) == 1

    results_applied = repository.list_jobs(statuses=["APPLIED"])
    assert len(results_applied) == 0

    results_multi = repository.list_jobs(statuses=["NEW", "APPLIED"])
    assert len(results_multi) == 1


def test_list_jobs_snippet_query(repository, sample_evaluated_job):
    sample_evaluated_job.raw_snippet = "Expertise in Kubernetes and distributed systems required"
    repository.save_job(sample_evaluated_job)

    assert len(repository.list_jobs(query="Kubernetes")) == 1
    assert len(repository.list_jobs(query="distributed systems")) == 1
    assert len(repository.list_jobs(query="nonexistent_skill")) == 0


def test_list_jobs_sort_days_ago_and_experience(repository, sample_evaluated_job):
    sample_evaluated_job.posted_days_ago = 2
    sample_evaluated_job.extracted_min_yoe = 3
    repository.save_job(sample_evaluated_job)

    sorted_days = repository.list_jobs(sort="days_ago")
    assert len(sorted_days) == 1

    sorted_exp = repository.list_jobs(sort="experience")
    assert len(sorted_exp) == 1

