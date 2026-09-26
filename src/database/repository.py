from __future__ import annotations

import json
from typing import Any
import sqlite3

import structlog

from exceptions import StorageError
from models.enums import JobStatus
from models.schemas import EvaluatedJob, ParsedResumeProfile, ResumeRecord
from database.database import DatabaseManager

logger = structlog.get_logger(__name__)

_ALLOWED_SORT = {
    "fit_score": "fit_score DESC",
    "company": "company COLLATE NOCASE ASC",
    "title": "title COLLATE NOCASE ASC",
    "status": "status ASC",
    "created_at": "created_at DESC",
    "portal": "source_portal ASC",
    "days_ago": "posted_days_ago ASC, created_at DESC",
    "experience": "extracted_min_yoe ASC",
}


class JobRepository:
    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager

    def _row_to_job(self, row: sqlite3.Row) -> EvaluatedJob:
        keys = row.keys()
        matched_skills = json.loads(row["matched_skills"])
        missing_skills = json.loads(row["missing_skills"])
        core_skills_raw = row["core_skills"] if "core_skills" in keys else "[]"
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
            source_portal=row["source_portal"] if "source_portal" in keys else "unknown",
            raw_snippet=row["raw_snippet"],
            status=JobStatus(row["status"]),
            evaluated=bool(row["evaluated"]) if "evaluated" in keys else True,
            search_title=row["search_title"] if "search_title" in keys else "",
            target_yoe=row["target_yoe"] if "target_yoe" in keys else None,
            core_skills=json.loads(core_skills_raw) if core_skills_raw else [],
            posted_days_ago=row["posted_days_ago"] if "posted_days_ago" in keys else None,
            db_id=str(row["id"]) if "id" in keys else None,
        )

    def _job_params(self, job: EvaluatedJob) -> tuple[Any, ...]:
        return (
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
            int(job.evaluated),
            job.search_title,
            job.target_yoe,
            json.dumps(job.core_skills),
            job.posted_days_ago,
        )

    def job_exists(self, url_hash: str) -> bool:
        sql = "SELECT 1 FROM jobs WHERE id = ? OR apply_url = ?"
        try:
            cursor = self.db.execute(sql, (url_hash, url_hash))
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
                summary_reason, status, source_query, source_portal, raw_snippet,
                evaluated, search_title, target_yoe, core_skills, posted_days_ago
            ) VALUES (
                ?, ?, ?, ?, ?,
                ?, ?, ?,
                ?, ?, ?,
                ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?
            )
        """
        try:
            with self.db.get_connection():
                self.db.execute(sql, self._job_params(job))
            logger.debug("job_saved", url_hash=job.url_hash())
        except StorageError as e:
            logger.error("save_job_failed", error=str(e), url_hash=job.url_hash())
            raise

    def update_job(self, job: EvaluatedJob) -> None:
        sql = """
            UPDATE jobs SET
                company = ?, title = ?, location = ?, apply_url = ?,
                extracted_min_yoe = ?, extracted_max_yoe = ?, yoe_match = ?,
                fit_score = ?, matched_skills = ?, missing_skills = ?,
                summary_reason = ?, status = ?, source_query = ?, source_portal = ?,
                raw_snippet = ?, evaluated = ?, search_title = ?, target_yoe = ?,
                core_skills = ?, posted_days_ago = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        """
        params = self._job_params(job)[1:] + (job.url_hash(),)
        try:
            with self.db.get_connection():
                self.db.execute(sql, params)
            logger.debug("job_updated", url_hash=job.url_hash())
        except StorageError as e:
            logger.error("update_job_failed", error=str(e), url_hash=job.url_hash())
            raise

    def get_job(self, url_hash: str) -> EvaluatedJob | None:
        sql = "SELECT * FROM jobs WHERE id = ? OR apply_url = ?"
        try:
            cursor = self.db.execute(sql, (url_hash, url_hash))
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

    def get_unevaluated_jobs(self) -> list[EvaluatedJob]:
        sql = "SELECT * FROM jobs WHERE evaluated = 0 ORDER BY created_at ASC"
        try:
            cursor = self.db.execute(sql)
            return [self._row_to_job(row) for row in cursor.fetchall()]
        except StorageError as e:
            logger.error("get_unevaluated_jobs_failed", error=str(e))
            raise

    def get_all_qualified(self, min_score: float = 0.0) -> list[EvaluatedJob]:
        sql = "SELECT * FROM jobs WHERE evaluated = 1 AND fit_score >= ? ORDER BY fit_score DESC"
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
            unevaluated = self.db.execute(
                "SELECT COUNT(*) as count FROM jobs WHERE evaluated = 0"
            ).fetchone()
            stats["unevaluated"] = int(unevaluated["count"]) if unevaluated else 0
            evaluated = self.db.execute(
                "SELECT COUNT(*) as count FROM jobs WHERE evaluated = 1"
            ).fetchone()
            stats["evaluated"] = int(evaluated["count"]) if evaluated else 0
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

    def list_jobs(
        self,
        *,
        companies: list[str] | None = None,
        portals: list[str] | None = None,
        statuses: list[str] | None = None,
        max_days: int | None = None,
        locations: list[str] | None = None,
        min_fit: float | None = None,
        evaluated: bool | None = None,
        yoe_match: bool | None = None,
        query: str | None = None,
        sort: str = "fit_score",
    ) -> list[EvaluatedJob]:
        clauses: list[str] = []
        params: list[Any] = []

        def add_in(column: str, values: list[str] | None) -> None:
            if not values:
                return
            placeholders = ",".join("?" for _ in values)
            clauses.append(f"{column} IN ({placeholders})")
            params.extend(values)

        add_in("company", companies)
        add_in("source_portal", portals)
        add_in("status", statuses)
        add_in("location", locations)
        
        if max_days is not None:
            clauses.append("posted_days_ago <= ?")
            params.append(max_days)

        if evaluated is not None:
            clauses.append("evaluated = ?")
            params.append(int(evaluated))

        if yoe_match is not None:
            clauses.append("yoe_match = ?")
            params.append(int(yoe_match))

        if min_fit is not None:
            # Unevaluated rows have a placeholder score of 0; keep them visible.
            clauses.append("(evaluated = 0 OR fit_score >= ?)")
            params.append(min_fit)

        if query:
            clauses.append(
                "(title LIKE ? OR company LIKE ? OR location LIKE ? OR matched_skills LIKE ? OR raw_snippet LIKE ?)"
            )
            like = f"%{query}%"
            params.extend([like, like, like, like, like])

        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        order = _ALLOWED_SORT.get(sort, _ALLOWED_SORT["fit_score"])
        sql = f"SELECT * FROM jobs {where} ORDER BY {order}"
        try:
            cursor = self.db.execute(sql, tuple(params))
            return [self._row_to_job(row) for row in cursor.fetchall()]
        except StorageError as e:
            logger.error("list_jobs_failed", error=str(e))
            raise

    def get_filter_options(self) -> dict[str, list[str]]:
        def distinct(column: str) -> list[str]:
            cursor = self.db.execute(
                f"SELECT DISTINCT {column} AS value FROM jobs WHERE {column} IS NOT NULL AND {column} != '' ORDER BY value COLLATE NOCASE"
            )
            return [str(row["value"]) for row in cursor.fetchall()]

        try:
            return {
                "companies": distinct("company"),
                "portals": distinct("source_portal"),
                "locations": distinct("location"),
                "statuses": [status.value for status in JobStatus],
            }
        except StorageError as e:
            logger.error("get_filter_options_failed", error=str(e))
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

    def purge_jobs(self, days: int) -> int:
        sql = "DELETE FROM jobs WHERE created_at < datetime('now', ?)"
        modifier = f"-{days} days"
        try:
            with self.db.get_connection():
                cursor = self.db.execute(sql, (modifier,))
                deleted = cursor.rowcount
            logger.info("purged_old_jobs", days=days, deleted_count=deleted)
            return deleted
        except StorageError as e:
            logger.error("purge_jobs_failed", error=str(e), days=days)
            raise

    def get_target_companies(self) -> list[dict[str, Any]]:
        """Return all target companies with enabled status and job count from DB."""
        sql = """
            SELECT 
                tc.name, 
                tc.enabled,
                COUNT(j.id) as job_count
            FROM target_companies tc
            LEFT JOIN jobs j ON LOWER(j.company) = LOWER(tc.name)
            GROUP BY tc.name
            ORDER BY tc.enabled DESC, tc.name COLLATE NOCASE ASC
        """
        try:
            cursor = self.db.execute(sql)
            return [
                {
                    "name": row["name"],
                    "enabled": bool(row["enabled"]),
                    "job_count": row["job_count"],
                }
                for row in cursor.fetchall()
            ]
        except Exception as e:
            logger.error("get_target_companies_failed", error=str(e))
            return []

    def set_enabled_companies(self, companies: list[str]) -> None:
        """Update enabled companies in target_companies table."""
        try:
            with self.db.get_connection():
                self.db.execute("UPDATE target_companies SET enabled = 0")
                for comp in companies:
                    c = comp.strip()
                    if not c:
                        continue
                    self.db.execute(
                        """
                        INSERT INTO target_companies (name, enabled)
                        VALUES (?, 1)
                        ON CONFLICT(name) DO UPDATE SET enabled = 1
                        """,
                        (c,),
                    )
        except Exception as e:
            logger.error("set_enabled_companies_failed", error=str(e))
            raise StorageError(f"Failed to update target companies: {e}") from e

    def _row_to_resume(self, row: sqlite3.Row) -> ResumeRecord:
        parsed_profile_obj = None
        if row["parsed_profile"]:
            try:
                profile_dict = json.loads(row["parsed_profile"])
                parsed_profile_obj = ParsedResumeProfile.model_validate(profile_dict)
            except Exception as e:
                logger.warning("failed_to_deserialize_resume_profile", error=str(e), id=row["id"])

        keys = row.keys()
        return ResumeRecord(
            id=row["id"],
            filename=row["filename"],
            file_path=row["file_path"],
            file_type=row["file_type"],
            raw_text=row["raw_text"],
            parsed_profile=parsed_profile_obj,
            candidate_name=row["candidate_name"],
            headline=row["headline"],
            email=row["email"],
            total_yoe=row["total_yoe"],
            is_active=bool(row["is_active"]),
            created_at=str(row["created_at"]) if "created_at" in keys else None,
            updated_at=str(row["updated_at"]) if "updated_at" in keys else None,
        )

    def save_resume(self, resume: ResumeRecord) -> ResumeRecord:
        """Persist or update resume record in database."""
        profile_json = resume.parsed_profile.model_dump_json() if resume.parsed_profile else None
        try:
            with self.db.get_connection():
                if resume.is_active:
                    self.db.execute("UPDATE resumes SET is_active = 0 WHERE id != ?", (resume.id,))
                
                self.db.execute(
                    """
                    INSERT INTO resumes (
                        id, filename, file_path, file_type, raw_text, parsed_profile,
                        candidate_name, headline, email, total_yoe, is_active, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    ON CONFLICT(id) DO UPDATE SET
                        filename = excluded.filename,
                        file_path = excluded.file_path,
                        file_type = excluded.file_type,
                        raw_text = excluded.raw_text,
                        parsed_profile = excluded.parsed_profile,
                        candidate_name = excluded.candidate_name,
                        headline = excluded.headline,
                        email = excluded.email,
                        total_yoe = excluded.total_yoe,
                        is_active = excluded.is_active,
                        updated_at = CURRENT_TIMESTAMP
                    """,
                    (
                        resume.id,
                        resume.filename,
                        resume.file_path,
                        resume.file_type,
                        resume.raw_text,
                        profile_json,
                        resume.candidate_name,
                        resume.headline,
                        resume.email,
                        resume.total_yoe,
                        1 if resume.is_active else 0,
                    ),
                )
            return resume
        except Exception as e:
            logger.error("save_resume_failed", error=str(e), id=resume.id)
            raise StorageError(f"Failed to save resume: {e}") from e

    def get_resume(self, resume_id: str) -> ResumeRecord | None:
        try:
            cursor = self.db.execute("SELECT * FROM resumes WHERE id = ?", (resume_id,))
            row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_resume(row)
        except Exception as e:
            logger.error("get_resume_failed", error=str(e), id=resume_id)
            return None

    def get_active_resume(self) -> ResumeRecord | None:
        try:
            cursor = self.db.execute("SELECT * FROM resumes WHERE is_active = 1 ORDER BY updated_at DESC LIMIT 1")
            row = cursor.fetchone()
            if not row:
                cursor = self.db.execute("SELECT * FROM resumes ORDER BY created_at DESC LIMIT 1")
                row = cursor.fetchone()
            if not row:
                return None
            return self._row_to_resume(row)
        except Exception as e:
            logger.error("get_active_resume_failed", error=str(e))
            return None

    def list_resumes(self) -> list[ResumeRecord]:
        try:
            cursor = self.db.execute("SELECT * FROM resumes ORDER BY is_active DESC, updated_at DESC")
            return [self._row_to_resume(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error("list_resumes_failed", error=str(e))
            return []

    def set_active_resume(self, resume_id: str) -> bool:
        try:
            with self.db.get_connection():
                self.db.execute("UPDATE resumes SET is_active = 0")
                cursor = self.db.execute("UPDATE resumes SET is_active = 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (resume_id,))
                return cursor.rowcount > 0
        except Exception as e:
            logger.error("set_active_resume_failed", error=str(e), id=resume_id)
            return False

    def delete_resume(self, resume_id: str) -> str | None:
        """Delete resume record and return file path so file can be removed."""
        try:
            resume = self.get_resume(resume_id)
            if not resume:
                return None
            with self.db.get_connection():
                self.db.execute("DELETE FROM resumes WHERE id = ?", (resume_id,))
                if resume.is_active:
                    self.db.execute("""
                        UPDATE resumes SET is_active = 1 
                        WHERE id = (SELECT id FROM resumes ORDER BY updated_at DESC LIMIT 1)
                    """)
            return resume.file_path
        except Exception as e:
            logger.error("delete_resume_failed", error=str(e), id=resume_id)
            return None


