from unittest.mock import MagicMock, patch

from models.schemas import RawJobResult
from portals.jd_fetcher import (
    clean_html_to_text,
    enrich_jobs_concurrently,
    fetch_job_description,
)


def test_clean_html_to_text():
    html_sample = """
    <div>
        <h2>Job Title</h2>
        <p>We are looking for a <strong>Software Engineer</strong>.</p>
        <ul>
            <li>Python &amp; FastAPI</li>
            <li>Docker &amp; AWS</li>
        </ul>
    </div>
    """
    cleaned = clean_html_to_text(html_sample)
    assert "Job Title" in cleaned
    assert "Software Engineer" in cleaned
    assert "• Python & FastAPI" in cleaned
    assert "• Docker & AWS" in cleaned
    assert "<strong>" not in cleaned


@patch("portals.jd_fetcher.httpx.Client")
def test_fetch_job_description_active_linkedin(mock_client_class):
    mock_client = MagicMock()
    mock_client_class.return_value.__enter__.return_value = mock_client

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.url = "https://www.linkedin.com/jobs/view/12345"
    mock_resp.text = """
    <html>
        <body>
            <div class="show-more-less-html__markup">
                About the role: We are hiring a Senior SDE to lead cloud infrastructure.
                Required: 5+ years of Python, Kubernetes, and AWS architecture.
            </div>
        </body>
    </html>
    """
    mock_client.get.return_value = mock_resp

    desc, is_expired = fetch_job_description("https://www.linkedin.com/jobs/view/12345", "fallback")
    assert not is_expired
    assert "Senior SDE" in desc
    assert "Kubernetes" in desc


@patch("portals.jd_fetcher.httpx.Client")
def test_fetch_job_description_expired_redirect(mock_client_class):
    mock_client = MagicMock()
    mock_client_class.return_value.__enter__.return_value = mock_client

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.url = "https://www.linkedin.com/jobs/software-engineer-jobs?trk=expired_jd_redirect"
    mock_resp.text = "<html>Expired listing redirect</html>"
    mock_client.get.return_value = mock_resp

    desc, is_expired = fetch_job_description("https://www.linkedin.com/jobs/view/old_job", "fallback")
    assert is_expired
    assert desc == "fallback"


@patch("portals.jd_fetcher.fetch_job_description")
def test_enrich_jobs_concurrently(mock_fetch):
    mock_fetch.side_effect = [
        ("Long rich description with skills and responsibilities " * 10, False),
        ("fallback", True),  # expired
    ]

    job1 = RawJobResult(
        title="Active Job",
        url="https://example.com/job1",
        snippet="Short",
        source_query="test",
        source_portal="linkedin",
    )
    job2 = RawJobResult(
        title="Expired Job",
        url="https://example.com/job2",
        snippet="Short",
        source_query="test",
        source_portal="linkedin",
    )

    enriched = enrich_jobs_concurrently([job1, job2])
    assert len(enriched) == 1
    assert enriched[0].title == "Active Job"
    assert "Long rich description" in enriched[0].snippet
