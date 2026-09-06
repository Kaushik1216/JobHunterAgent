from __future__ import annotations

import time
import random
import structlog
from typing import Any
from ddgs import DDGS

from job_agent.config import Settings
from job_agent.constants import LINKEDIN_DORK_TEMPLATE
from job_agent.models.schemas import RawJobResult
from job_agent.exceptions import SearchError, RateLimitError, CircuitBreakerOpenError

logger = structlog.get_logger(__name__)

class LinkedInSearcher:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._consecutive_failures = 0
        self._circuit_open_until: float | None = None

    def _build_dork_query(self, company: str, title: str, location: str) -> str:
        """Build a search query. When company is provided, use LinkedIn dork.
        When company is empty (broad JD-based search), search the open web for jobs."""
        parts = []

        if company and company.strip():
            # Company-specific: use LinkedIn dork
            parts.append("site:linkedin.com/jobs")
            parts.append(f'"{company.strip()}"')
        else:
            # Broad search: search the open web for job postings
            parts.append("jobs hiring")

        if title and title.strip():
            parts.append(f'"{title.strip()}"')
        if location and location.strip():
            parts.append(f'"{location.strip()}"')

        return " ".join(parts)

    def _apply_jitter(self) -> None:
        delay = random.uniform(self.settings.search_jitter_min, self.settings.search_jitter_max)
        logger.debug("applying jitter delay", delay=delay)
        time.sleep(delay)

    def _check_circuit_breaker(self) -> None:
        if self._circuit_open_until and time.time() < self._circuit_open_until:
            raise CircuitBreakerOpenError(f"Circuit open until {self._circuit_open_until}")
        elif self._circuit_open_until:
            self._circuit_open_until = None
            self._consecutive_failures = 0
            logger.info("circuit breaker reset")

    def _record_failure(self) -> None:
        self._consecutive_failures += 1
        logger.warning("recording search failure", failures=self._consecutive_failures)
        if self._consecutive_failures >= self.settings.search_circuit_breaker_threshold:
            self._circuit_open_until = time.time() + self.settings.search_circuit_breaker_cooldown
            logger.error("circuit breaker opened", cooldown=self.settings.search_circuit_breaker_cooldown)

    def _record_success(self) -> None:
        if self._consecutive_failures > 0:
            logger.info("search success, resetting failure count")
            self._consecutive_failures = 0

    def search(self, company: str, title: str, location: str, max_results: int = 5) -> list[RawJobResult]:
        self._check_circuit_breaker()
        self._apply_jitter()

        query = self._build_dork_query(company, title, location)
        logger.info("searching jobs", query=query, max_results=max_results)

        try:
            results = []
            seen_urls = set()
            ddgs = DDGS()
            ddgs_results = ddgs.text(query, max_results=max_results)
            for res in ddgs_results:
                url = res.get("href", "")
                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)
                
                results.append(
                    RawJobResult(
                        title=res.get("title", ""),
                        url=url,
                        snippet=res.get("body", ""),
                        source_query=query
                    )
                )
            
            logger.info("search completed", results_count=len(results))
            self._record_success()
            return results
        except Exception as e:
            err_msg = str(e).lower()
            if "rate limit" in err_msg or "429" in err_msg or "timeout" in err_msg:
                self._record_failure()
                backoff = min(64.0, 2 ** self._consecutive_failures)
                logger.warning("rate limit hit, applying backoff", backoff=backoff)
                time.sleep(backoff)
                raise RateLimitError(f"Rate limited: {e}") from e
            else:
                self._record_failure()
                raise SearchError(f"Search failed: {e}") from e
