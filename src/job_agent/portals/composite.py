from __future__ import annotations

import structlog

from job_agent.config import Settings
from job_agent.exceptions import CircuitBreakerOpenError, SearchError
from job_agent.models.schemas import RawJobResult
from job_agent.portals.base import JobPortal
from job_agent.portals.registry import create_portals

logger = structlog.get_logger(__name__)


class MultiPortalSearcher:
    """Fan-out search across every enabled :class:`JobPortal`."""

    def __init__(self, portals: list[JobPortal]) -> None:
        self.portals = portals

    @classmethod
    def from_settings(cls, settings: Settings) -> MultiPortalSearcher:
        return cls(create_portals(settings))

    def search(
        self,
        company: str,
        title: str,
        location: str,
        max_results: int = 5,
    ) -> list[RawJobResult]:
        results: list[RawJobResult] = []
        seen_urls: set[str] = set()

        for portal in self.portals:
            try:
                found = portal.search(
                    company=company,
                    title=title,
                    location=location,
                    max_results=max_results,
                )
            except CircuitBreakerOpenError:
                logger.warning("portal_circuit_open", portal=portal.portal_id)
                continue
            except SearchError as exc:
                logger.error("portal_search_failed", portal=portal.portal_id, error=str(exc))
                continue

            for job in found:
                url = str(job.url)
                if url in seen_urls:
                    continue
                seen_urls.add(url)
                results.append(job)

        logger.info(
            "multi_portal_search_completed",
            portals=[portal.portal_id for portal in self.portals],
            results_count=len(results),
        )
        return results
