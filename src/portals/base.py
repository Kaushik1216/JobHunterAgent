from __future__ import annotations

import random
import time
from abc import ABC, abstractmethod
from typing import ClassVar, Literal, Protocol
from urllib.parse import urlparse

import structlog
from ddgs import DDGS

from config import Settings
from exceptions import CircuitBreakerOpenError, RateLimitError, SearchError
from models.schemas import RawJobResult

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

            ddgs_results = ddgs.text(query, max_results=max_results * 2, timelimit=timelimit) or []
            for res in ddgs_results:
                raw_url = res.get("href", "")
                url = normalize_job_url(raw_url)
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


def normalize_job_url(url: str) -> str:
    """Normalize and canonicalize job application URLs across portals."""
    if not url:
        return ""
    clean = url.strip()

    # 1. Decode DuckDuckGo redirect if present
    if "duckduckgo.com/l/?" in clean and "uddg=" in clean:
        import urllib.parse
        parsed = urllib.parse.urlparse(clean)
        qs = urllib.parse.parse_qs(parsed.query)
        if "uddg" in qs and qs["uddg"]:
            clean = urllib.parse.unquote(qs["uddg"][0])

    # 2. LinkedIn: Convert localized subdomains and slugs to canonical global view URL
    # e.g., https://in.linkedin.com/jobs/view/software-engineer-12345?trk=... -> https://www.linkedin.com/jobs/view/12345/
    import re
    li_match = re.search(r"linkedin\.com/jobs/view/(?:[\w-]+-)?(\d+)", clean, re.IGNORECASE)
    if li_match:
        return f"https://www.linkedin.com/jobs/view/{li_match.group(1)}"

    # 3. Indeed: Canonicalize jk parameter to direct viewjob link
    indeed_match = re.search(r"[?&]jk=([a-zA-Z0-9]+)", clean)
    if "indeed.com" in clean.lower() and indeed_match:
        return f"https://www.indeed.com/viewjob?jk={indeed_match.group(1)}"

    # 4. Greenhouse: Canonicalize boards.greenhouse.io/<company>/jobs/<id>
    gh_match = re.search(r"(https?://boards\.greenhouse\.io/[^/]+/jobs/\d+)", clean, re.IGNORECASE)
    if gh_match:
        return gh_match.group(1)

    # 5. Lever: Canonicalize jobs.lever.co/<company>/<uuid>
    lever_match = re.search(r"(https?://jobs\.lever\.co/[^/]+/[0-9a-fA-F-]+)", clean, re.IGNORECASE)
    if lever_match:
        return lever_match.group(1)

    # 6. Ashby: Canonicalize jobs.ashbyhq.com/<company>/<uuid>
    ashby_match = re.search(r"(https?://jobs\.ashbyhq\.com/[^/]+/[0-9a-fA-F-]+)", clean, re.IGNORECASE)
    if ashby_match:
        return ashby_match.group(1)

    # 7. Strip trailing tracking queries for generic URLs if safe
    clean = re.sub(r"([?&](?:utm_[^&=]+|trk|refId|trackingId|tracking|fbclid|gclid)=[^&=]*)", "", clean)
    clean = clean.rstrip("?&")
    return clean


def quoted_terms(*values: str) -> list[str]:
    return [f'"{value.strip()}"' for value in values if value and value.strip()]


class BoardJobPortal(WebSearchJobPortal):
    """Public job board (LinkedIn, Indeed, Naukri, ...)."""

    kind: ClassVar[PortalKind] = "board"
    site_filter: ClassVar[str] = ""

    def build_query(self, company: str, title: str, location: str) -> str:
        """Build a natural-language query that avoids advanced operator bot-blocking."""
        parts = []
        if self.site_filter:
            parts.append(self.site_filter)
        if company and company.strip():
            parts.append(f'"{company.strip()}"')
        if title and title.strip():
            parts.append(f'"{title.strip()}"')
        if location and location.strip():
            loc = location.strip()
            if loc.lower() in ("bengaluru", "bangalore"):
                parts.append("Bengaluru OR Bangalore")
            else:
                parts.append(f'"{loc}"')
        parts.append("job opening")
        return " ".join(parts)

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

        # Default to month timelimit to avoid retrieving 4-year-old archived links
        timelimit = "m"
        if getattr(self.settings, "search_max_days", None):
            days = self.settings.search_max_days
            if days <= 1:
                timelimit = "d"
            elif days <= 7:
                timelimit = "w"
            elif days <= 30:
                timelimit = "m"
            elif days <= 365:
                timelimit = "y"

        results = self._run_search(query, max_results, timelimit, company=company)

        # Progressive fallback ladder (d -> w -> m -> y) without unconstrained search
        if not results and timelimit in ("d", "w"):
            logger.info("no results with tight timelimit, widening to month", portal=self.portal_id)
            time.sleep(random.uniform(1.0, 2.0))
            results = self._run_search(query, max_results, timelimit="m", company=company)

        if not results and timelimit in ("d", "w", "m"):
            logger.info("no results with month timelimit, widening to year", portal=self.portal_id)
            time.sleep(random.uniform(1.0, 2.0))
            results = self._run_search(query, max_results, timelimit="y", company=company)

        logger.info("search completed", results_count=len(results), portal=self.portal_id)
        return results

    def _run_search(self, query: str, max_results: int, timelimit: str | None, company: str = "") -> list[RawJobResult]:
        try:
            results: list[RawJobResult] = []
            seen_urls: set[str] = set()
            ddgs = DDGS()
            ddgs_results = ddgs.text(query, max_results=max_results * 3, timelimit=timelimit) or []
            
            # Normalize company name for matching (handle "Amazon Web Services" -> "amazon")
            company_slug = company.strip().lower() if company else ""
            # Also check first word of company name (e.g. "Amazon Web Services" -> "amazon")
            company_first_word = company_slug.split()[0] if company_slug else ""

            blocked_patterns = [
                "/search?", "wikipedia.org", "reddit.com", "quora.com",
                "/salaries/", "ambitionbox.com", "levels.fyi", "glassdoor.com/salaries",
                "glassdoor.co.in/salaries", "/q-", "trk=expired",
            ]
            
            for res in ddgs_results:
                raw_url = res.get("href", "")
                url = normalize_job_url(raw_url)
                title_r = res.get("title", "")
                body = res.get("body", "")
                if not url or url in seen_urls:
                    continue
                if not self.accepts_url(url):
                    continue
                # Filter out aggregator and non-job pages
                url_lower = url.lower()
                if any(x in url_lower for x in blocked_patterns):
                    continue
                # Company relevance filter: if a specific company is requested,
                # only keep results where company name appears in URL or title
                if company_first_word:
                    title_lower = title_r.lower()
                    body_lower = body.lower()
                    if (company_first_word not in url_lower and
                        company_slug not in title_lower and
                        company_first_word not in title_lower and
                        company_slug not in body_lower[:200]):
                        logger.debug("filtered irrelevant company result", url=url[:80], company=company)
                        continue
                seen_urls.add(url)
                results.append(
                    RawJobResult(
                        title=title_r,
                        url=url,
                        snippet=body,
                        source_query=query,
                        source_portal=self.portal_id,
                    )
                )
                if len(results) >= max_results:
                    break
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


class AtsJobPortal(WebSearchJobPortal):
    """Company career site / applicant tracking system (Greenhouse, Lever, ...)."""

    kind: ClassVar[PortalKind] = "ats"
    site_filter: ClassVar[str] = ""

    def build_query(self, company: str, title: str, location: str) -> str:
        parts = []
        if self.site_filter:
            parts.append(self.site_filter)
        if company and company.strip():
            parts.append(f'"{company.strip()}"')
        if title and title.strip():
            parts.append(f'"{title.strip()}"')
        if location and location.strip():
            parts.append(f'"{location.strip()}"')
        parts.append("careers apply")
        return " ".join(parts)
