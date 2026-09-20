from __future__ import annotations

import json

import structlog
from fastmcp import FastMCP

from job_agent.config import Settings
from job_agent.portals.composite import MultiPortalSearcher
from job_agent.portals.registry import create_portals, list_portal_ids
from job_agent.mcp_server.tools import storage

logger = structlog.get_logger(__name__)


def create_mcp_server(settings: Settings | None = None) -> FastMCP:
    """Create and configure the MCP server with all tools registered."""
    mcp = FastMCP("job-agent")

    if settings is None:
        from job_agent.config import get_settings

        settings = get_settings()

    searcher = MultiPortalSearcher.from_settings(settings)

    @mcp.tool()
    def list_job_portals() -> str:
        """List registered job portal ids that can be enabled via JOB_AGENT_SEARCH_PORTALS."""
        return json.dumps(list_portal_ids())

    @mcp.tool()
    def search_jobs(
        company: str,
        title: str,
        location: str,
        max_results: int = 5,
        portal: str | None = None,
    ) -> str:
        """
        Search for jobs across enabled portals (or a single portal).

        Args:
            company: The company name to search for.
            title: The job title to search for.
            location: The location of the job.
            max_results: The maximum number of results to return per portal.
            portal: Optional portal id (linkedin, indeed, naukri, greenhouse, ...).
        """
        active_searcher = searcher
        if portal:
            try:
                active_searcher = MultiPortalSearcher(create_portals(settings, [portal.strip().lower()]))
            except Exception as e:
                logger.error("search tool failed", error=str(e))
                return f"Error: {e}"
        try:
            results = active_searcher.search(
                company=company,
                title=title,
                location=location,
                max_results=max_results,
            )
            return json.dumps([json.loads(r.model_dump_json()) for r in results])
        except Exception as e:
            logger.error("search tool failed", error=str(e))
            return f"Error: {e}"

    @mcp.tool()
    def search_linkedin_jobs(company: str, title: str, location: str, max_results: int = 5) -> str:
        """Search LinkedIn jobs. Prefer search_jobs for multi-portal results."""
        return search_jobs(
            company=company,
            title=title,
            location=location,
            max_results=max_results,
            portal="linkedin",
        )

    @mcp.tool()
    def check_job_exists(url_hash: str) -> bool:
        """
        Check if a job already exists in storage.

        Args:
            url_hash: The unique SHA256 hash of the job URL.

        Returns:
            True if the job exists, False otherwise.
        """
        try:
            return storage.check_job_exists(url_hash)
        except Exception as e:
            logger.error("check_job_exists tool failed", error=str(e))
            return False

    @mcp.tool()
    def persist_qualified_job(job_data: dict) -> bool:
        """
        Persist an evaluated and qualified job to storage.

        Args:
            job_data: The serialized job data to persist.

        Returns:
            True if successful, False otherwise.
        """
        try:
            return storage.persist_qualified_job(job_data)
        except Exception as e:
            logger.error("persist_qualified_job tool failed", error=str(e))
            return False

    @mcp.tool()
    def get_qualified_jobs(min_score: float = 0.0) -> list[dict]:
        """
        Get all qualified jobs from storage.

        Args:
            min_score: The minimum fit score required.

        Returns:
            A list of dictionary representations of the jobs.
        """
        try:
            return storage.get_qualified_jobs(min_score)
        except Exception as e:
            logger.error("get_qualified_jobs tool failed", error=str(e))
            return []

    return mcp


def main() -> None:
    mcp = create_mcp_server()
    mcp.run()
