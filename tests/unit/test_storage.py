import pytest
import sqlite3
from job_agent.storage.database import DatabaseManager
from job_agent.storage.repository import JobRepository
from job_agent.models.enums import JobStatus

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
