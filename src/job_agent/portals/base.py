from __future__ import annotations

import random
import time
from abc import ABC, abstractmethod
from typing import ClassVar, Literal, Protocol
from urllib.parse import urlparse

import structlog
from ddgs import DDGS

from job_agent.config import Settings
from job_agent.exceptions import CircuitBreakerOpenError, RateLimitError, SearchError
from job_agent.models.schemas import RawJobResult

logger = structlog.get_logger(__name__)

PortalKind = Literal["board", "ats"]


class JobSearcher(Protocol):
    """Search contract used by the pipeline and MCP tools."""

    def search(
        self,
        company: str,
        title: str,
        location: str,
        max_results: int = 5,
    ) -> list[RawJobResult]:
        ...


class JobPortal(ABC):
    """Common interface for every job board and company ATS.

    Subclass :class:`BoardJobPortal` or :class:`AtsJobPortal` for DuckDuckGo-backed
    search, or implement :meth:`search` yourself for an official API.
    """

    portal_id: ClassVar[str]
    display_name: ClassVar[str]
    kind: ClassVar[PortalKind] = "board"
    url_host_suffixes: ClassVar[tuple[str, ...]] = ()

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    @abstractmethod
    def build_query(self, company: str, title: str, location: str) -> str:
        """Return the portal-specific search query."""

    @abstractmethod
    def search(
        self,
        company: str,
        title: str,
        location: str,
        max_results: int = 5,
    ) -> list[RawJobResult]:
        """Fetch raw job listings from this portal."""

    def accepts_url(self, url: str) -> bool:
        """Return True when a result URL belongs to this portal."""
        if not self.url_host_suffixes:
            return True
        host = (urlparse(url).netloc or "").lower()
        if host.startswith("www."):
            host = host[4:]
        return any(host == suffix or host.endswith(f".{suffix}") for suffix in self.url_host_suffixes)


class WebSearchJobPortal(JobPortal):
    """DuckDuckGo-backed portal with jitter and a circuit breaker."""

    def __init__(self, settings: Settings) -> None:
        super().__init__(settings)
        self._consecutive_failures = 0
        self._circuit_open_until: float | None = None

    def _apply_jitter(self) -> None:
        delay = random.uniform(self.settings.search_jitter_min, self.settings.search_jitter_max)
        logger.debug("applying jitter delay", delay=delay, portal=self.portal_id)
        time.sleep(delay)

    def _check_circuit_breaker(self) -> None:
        if self._circuit_open_until and time.time() < self._circuit_open_until:
            raise CircuitBreakerOpenError(f"Circuit open until {self._circuit_open_until}")
        if self._circuit_open_until:
            self._circuit_open_until = None
            self._consecutive_failures = 0
            logger.info("circuit breaker reset", portal=self.portal_id)

    def _record_failure(self) -> None:
        self._consecutive_failures += 1
        logger.warning(
            "recording search failure",
            failures=self._consecutive_failures,
            portal=self.portal_id,
        )
        if self._consecutive_failures >= self.settings.search_circuit_breaker_threshold:
            self._circuit_open_until = time.time() + self.settings.search_circuit_breaker_cooldown
            logger.error(
                "circuit breaker opened",
                cooldown=self.settings.search_circuit_breaker_cooldown,
                portal=self.portal_id,
            )

    def _record_success(self) -> None:
        if self._consecutive_failures > 0:
            logger.info("search success, resetting failure count", portal=self.portal_id)
            self._consecutive_failures = 0

    def search(
        self,
        company: str,
        title: str,
        location: str,
        max_results: int = 5,
    ) -> list[RawJobResult]:
        self._check_circuit_breaker()
        self._apply_jitter()

        query = self.build_query(company, title, location)
        logger.info("searching jobs", query=query, max_results=max_results, portal=self.portal_id)

        try:
            results: list[RawJobResult] = []
            seen_urls: set[str] = set()
            ddgs = DDGS()
            
            timelimit = None
            if getattr(self.settings, 'search_max_days', None):
                days = self.settings.search_max_days
                if days <= 1:
                    timelimit = "d"
                elif days <= 7:
                    timelimit = "w"
                elif days <= 30:
                    timelimit = "m"
                elif days <= 365:
                    timelimit = "y"
            
            ddgs_results = ddgs.text(query, max_results=max_results, timelimit=timelimit)
            for res in ddgs_results:
                url = res.get("href", "")
                if not url or url in seen_urls or not self.accepts_url(url):
                    continue
                seen_urls.add(url)
                results.append(
                    RawJobResult(
                        title=res.get("title", ""),
                        url=url,
                        snippet=res.get("body", ""),
                        source_query=query,
                        source_portal=self.portal_id,
                    )
                )

            logger.info("search completed", results_count=len(results), portal=self.portal_id)
            self._record_success()
            return results
        except Exception as e:
            err_msg = str(e).lower()
            self._record_failure()
            if "rate limit" in err_msg or "429" in err_msg or "timeout" in err_msg:
                backoff = min(64.0, 2 ** self._consecutive_failures)
                logger.warning("rate limit hit, applying backoff", backoff=backoff, portal=self.portal_id)
                time.sleep(backoff)
                raise RateLimitError(f"Rate limited: {e}") from e
            raise SearchError(f"Search failed: {e}") from e


def quoted_terms(*values: str) -> list[str]:
    return [f'"{value.strip()}"' for value in values if value and value.strip()]


class BoardJobPortal(WebSearchJobPortal):
    """Public job board (LinkedIn, Indeed, Naukri, ...)."""

    kind: ClassVar[PortalKind] = "board"
    site_filter: ClassVar[str] = ""

    def build_query(self, company: str, title: str, location: str) -> str:
        parts = [self.site_filter] if self.site_filter else []
        if company and company.strip():
            parts.append(f'intitle:"{company.strip()}"')
        else:
            parts.append("jobs hiring")
        parts.extend(quoted_terms(title, location))
        return " ".join(parts)


class AtsJobPortal(WebSearchJobPortal):
    """Company career site / applicant tracking system (Greenhouse, Lever, ...)."""

    kind: ClassVar[PortalKind] = "ats"
    site_filter: ClassVar[str] = ""

    def build_query(self, company: str, title: str, location: str) -> str:
        parts = [self.site_filter] if self.site_filter else []
        if company and company.strip():
            parts.append(f'intitle:"{company.strip()}"')
        parts.extend(quoted_terms(title, location))
        if "jobs" not in " ".join(parts).lower():
            parts.append("jobs")
        return " ".join(parts)
