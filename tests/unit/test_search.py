import pytest
from unittest.mock import patch, MagicMock
from job_agent.mcp_server.tools.search import LinkedInSearcher
from job_agent.exceptions import SearchError, RateLimitError, CircuitBreakerOpenError

def test_build_dork_query(settings):
    searcher = LinkedInSearcher(settings)
    query = searcher._build_dork_query("Stripe", "Engineer", "Remote")
    assert "Stripe" in query
    assert "Engineer" in query
    assert "Remote" in query

@patch("job_agent.mcp_server.tools.search.DDGS")
def test_search_success(mock_ddgs_class, settings):
    mock_instance = mock_ddgs_class.return_value
    mock_instance.text.return_value = [
        {"title": "Job 1", "href": "https://example.com/job1", "body": "Snippet 1"},
        {"title": "Job 1 dup", "href": "https://example.com/job1", "body": "Snippet 1 dup"}
    ]
    
    searcher = LinkedInSearcher(settings)
    results = searcher.search("Stripe", "Engineer", "Remote")
    
    assert len(results) == 1
    assert str(results[0].url) == "https://example.com/job1"
    assert results[0].title == "Job 1"

@patch("job_agent.mcp_server.tools.search.DDGS")
def test_circuit_breaker(mock_ddgs_class, settings):
    mock_instance = mock_ddgs_class.return_value
    mock_instance.text.side_effect = Exception("General Error")
    
    settings.search_circuit_breaker_threshold = 2
    searcher = LinkedInSearcher(settings)
    
    # First failure
    with pytest.raises(SearchError):
        searcher.search("C", "T", "L")
        
    # Second failure opens circuit breaker
    with pytest.raises(SearchError):
        searcher.search("C", "T", "L")
        
    # Third try fails immediately due to open circuit breaker
    with pytest.raises(CircuitBreakerOpenError):
        searcher.search("C", "T", "L")
