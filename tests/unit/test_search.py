from unittest.mock import MagicMock, patch

import pytest

from job_agent.exceptions import CircuitBreakerOpenError, ConfigurationError, SearchError
from job_agent.mcp_server.tools.search import LinkedInSearcher
from job_agent.models.schemas import RawJobResult
from job_agent.portals.ats import GreenhousePortal, LeverPortal
from job_agent.portals.boards import IndeedPortal, LinkedInPortal, NaukriPortal
from job_agent.portals.composite import MultiPortalSearcher
from job_agent.portals.registry import create_portals, list_portal_ids


def test_linkedin_build_query(settings):
    searcher = LinkedInSearcher(settings)
    query = searcher.build_query("Stripe", "Engineer", "Remote")
    assert "site:linkedin.com/jobs" in query
    assert "Stripe" in query
    assert "Engineer" in query
    assert "Remote" in query


def test_board_and_ats_queries(settings):
    indeed = IndeedPortal(settings).build_query("Stripe", "Engineer", "Bengaluru")
    assert "site:indeed.com" in indeed
    naukri = NaukriPortal(settings).build_query("Flipkart", "Software Engineer", "Bengaluru")
    assert "site:naukri.com" in naukri
    greenhouse = GreenhousePortal(settings).build_query("Stripe", "Engineer", "Remote")
    assert "site:greenhouse.io" in greenhouse
    lever = LeverPortal(settings).build_query("Stripe", "Engineer", "Remote")
    assert "site:jobs.lever.co" in lever


def test_accepts_url(settings):
    linkedin = LinkedInPortal(settings)
    assert linkedin.accepts_url("https://www.linkedin.com/jobs/view/123")
    assert not linkedin.accepts_url("https://indeed.com/viewjob?jk=1")
    indeed = IndeedPortal(settings)
    assert indeed.accepts_url("https://in.indeed.com/viewjob?jk=1")


@patch("job_agent.portals.base.DDGS")
def test_search_success(mock_ddgs_class, settings):
    mock_instance = mock_ddgs_class.return_value
    mock_instance.text.return_value = [
        {"title": "Job 1", "href": "https://www.linkedin.com/jobs/view/1", "body": "Snippet 1"},
        {"title": "Job 1 dup", "href": "https://www.linkedin.com/jobs/view/1", "body": "Snippet 1 dup"},
        {"title": "Off site", "href": "https://example.com/job1", "body": "Ignored"},
    ]

    searcher = LinkedInSearcher(settings)
    results = searcher.search("Stripe", "Engineer", "Remote")

    assert len(results) == 1
    assert str(results[0].url) == "https://www.linkedin.com/jobs/view/1"
    assert results[0].title == "Job 1"
    assert results[0].source_portal == "linkedin"


@patch("job_agent.portals.base.DDGS")
def test_circuit_breaker(mock_ddgs_class, settings):
    mock_instance = mock_ddgs_class.return_value
    mock_instance.text.side_effect = Exception("General Error")

    settings.search_circuit_breaker_threshold = 2
    searcher = LinkedInSearcher(settings)

    with pytest.raises(SearchError):
        searcher.search("C", "T", "L")

    with pytest.raises(SearchError):
        searcher.search("C", "T", "L")

    with pytest.raises(CircuitBreakerOpenError):
        searcher.search("C", "T", "L")


def test_registry_unknown_portal(settings):
    with pytest.raises(ConfigurationError, match="Unknown job portal"):
        create_portals(settings, ["not-a-portal"])


def test_registry_lists_builtin_portals():
    ids = list_portal_ids()
    for expected in ("linkedin", "indeed", "naukri", "greenhouse", "lever", "ashby"):
        assert expected in ids


def test_multi_portal_dedupes_and_isolates_failures(settings):
    good = MagicMock()
    good.portal_id = "linkedin"
    good.search.return_value = [
        RawJobResult(
            title="A",
            url="https://linkedin.com/jobs/view/1",
            snippet="s",
            source_portal="linkedin",
        ),
        RawJobResult(
            title="Dup",
            url="https://linkedin.com/jobs/view/1",
            snippet="s",
            source_portal="linkedin",
        ),
    ]
    bad = MagicMock()
    bad.portal_id = "indeed"
    bad.search.side_effect = SearchError("down")

    searcher = MultiPortalSearcher([good, bad])
    results = searcher.search("C", "T", "L")
    assert len(results) == 1
    assert results[0].source_portal == "linkedin"
