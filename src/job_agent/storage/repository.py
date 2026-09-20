from __future__ import annotations

import json
from typing import Any
import sqlite3

import structlog

from job_agent.exceptions import StorageError
from job_agent.models.enums import JobStatus
from job_agent.models.schemas import EvaluatedJob
from job_agent.storage.database import DatabaseManager

logger = structlog.get_logger(__name__)


class JobRepository:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def _row_to_job(self, row: sqlite3.Row) -> EvaluatedJob:
        matched_skills = json.loads(row["matched_skills"])
        missing_skills = json.loads(row["missing_skills"])
        return EvaluatedJob(
            title=row["title"],
            company=row["company"],
            location=row["location"],
            extracted_min_yoe=row["extracted_min_yoe"],
            extracted_max_yoe=row["extracted_max_yoe"],
            yoe_match=bool(row["yoe_match"]),
            matched_skills=matched_skills,
            missing_skills=missing_skills,
            fit_score=row["fit_score"],
            summary_reason=row["summary_reason"],
            apply_url=row["apply_url"],
            source_query=row["source_query"],
            source_portal=row["source_portal"] if "source_portal" in row.keys() else "unknown",
            raw_snippet=row["raw_snippet"],
            status=JobStatus(row["status"]),
        )

    def job_exists(self, url_hash: str) -> bool:
        sql = "SELECT 1 FROM jobs WHERE id = ?"
        try:
            cursor = self.db.execute(sql, (url_hash,))
            return cursor.fetchone() is not None
        except StorageError as e:
            logger.error("job_exists_check_failed", error=str(e), url_hash=url_hash)
            raise

    def save_job(self, job: EvaluatedJob) -> None:
        sql = """
            INSERT OR IGNORE INTO jobs (
                id, company, title, location, apply_url,
                extracted_min_yoe, extracted_max_yoe, yoe_match,
                fit_score, matched_skills, missing_skills,
                summary_reason, status, source_query, source_portal, raw_snippet
            ) VALUES (
                ?, ?, ?, ?, ?,
                ?, ?, ?,
                ?, ?, ?,
                ?, ?, ?, ?, ?
            )
        """
        params = (
            job.url_hash(),
            job.company,
            job.title,
            job.location,
            job.apply_url,
            job.extracted_min_yoe,
            job.extracted_max_yoe,
            job.yoe_match,
            job.fit_score,
            json.dumps(job.matched_skills),
            json.dumps(job.missing_skills),
            job.summary_reason,
            job.status.value,
            job.source_query,
            job.source_portal,
            job.raw_snippet,
        )
        try:
            with self.db.get_connection():
                self.db.execute(sql, params)
            logger.debug("job_saved", url_hash=job.url_hash())
        except StorageError as e:
            logger.error("save_job_failed", error=str(e), url_hash=job.url_hash())
            raise

    def get_job(self, url_hash: str) -> EvaluatedJob | None:
        sql = "SELECT * FROM jobs WHERE id = ?"
        try:
            cursor = self.db.execute(sql, (url_hash,))
            row = cursor.fetchone()
            if row:
                return self._row_to_job(row)
            return None
        except StorageError as e:
            logger.error("get_job_failed", error=str(e), url_hash=url_hash)
            raise

    def get_jobs_by_status(self, status: JobStatus) -> list[EvaluatedJob]:
        sql = "SELECT * FROM jobs WHERE status = ?"
        try:
            cursor = self.db.execute(sql, (status.value,))
            return [self._row_to_job(row) for row in cursor.fetchall()]
        except StorageError as e:
            logger.error("get_jobs_by_status_failed", error=str(e), status=status)
            raise

    def get_all_qualified(self, min_score: float = 0.0) -> list[EvaluatedJob]:
        sql = "SELECT * FROM jobs WHERE fit_score >= ? ORDER BY fit_score DESC"
        try:
            cursor = self.db.execute(sql, (min_score,))
            return [self._row_to_job(row) for row in cursor.fetchall()]
        except StorageError as e:
            logger.error("get_all_qualified_failed", error=str(e), min_score=min_score)
            raise

    def update_status(self, url_hash: str, status: JobStatus) -> None:
        sql = "UPDATE jobs SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?"
        try:
            with self.db.get_connection():
                self.db.execute(sql, (status.value, url_hash))
            logger.debug("status_updated", url_hash=url_hash, status=status)
        except StorageError as e:
            logger.error("update_status_failed", error=str(e), url_hash=url_hash)
            raise

    def get_run_stats(self) -> dict[str, int]:
        sql = "SELECT status, COUNT(*) as count FROM jobs GROUP BY status"
        try:
            cursor = self.db.execute(sql)
            stats = {row["status"]: row["count"] for row in cursor.fetchall()}
            stats["total"] = sum(stats.values())
            return stats
        except StorageError as e:
            logger.error("get_run_stats_failed", error=str(e))
            raise

    def get_all_jobs(self) -> list[EvaluatedJob]:
        sql = "SELECT * FROM jobs"
        try:
            cursor = self.db.execute(sql)
            return [self._row_to_job(row) for row in cursor.fetchall()]
        except StorageError as e:
            logger.error("get_all_jobs_failed", error=str(e))
            raise

    def delete_job(self, url_hash: str) -> bool:
        sql = "DELETE FROM jobs WHERE id = ?"
        try:
            with self.db.get_connection():
                cursor = self.db.execute(sql, (url_hash,))
                return cursor.rowcount > 0
        except StorageError as e:
            logger.error("delete_job_failed", error=str(e), url_hash=url_hash)
            raise
