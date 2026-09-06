from __future__ import annotations
import structlog
from typing import Any

logger = structlog.get_logger(__name__)

# A global reference that can be set during server initialization
_repository: Any = None

def set_repository(repo: Any) -> None:
    global _repository
    _repository = repo

def check_job_exists(url_hash: str) -> bool:
    if _repository is None:
        logger.warning("repository not set")
        return False
    return _repository.check_job_exists(url_hash)

def persist_qualified_job(job_data: dict) -> bool:
    if _repository is None:
        logger.warning("repository not set")
        return False
    return _repository.persist_qualified_job(job_data)

def get_qualified_jobs(min_score: float = 0.0) -> list[dict]:
    if _repository is None:
        logger.warning("repository not set")
        return []
    return _repository.get_qualified_jobs(min_score)
