import pytest
import json
from unittest.mock import MagicMock
from job_agent.inference.output_guard import OutputGuard
from job_agent.exceptions import OutputValidationError
from job_agent.models.schemas import EvaluatedJob

@pytest.fixture
def mock_client():
    return MagicMock()

def test_valid_json_output(mock_client):
    guard = OutputGuard(mock_client)
    valid_json = json.dumps({
        "title": "T", "company": "C", "location": "L",
        "extracted_min_yoe": 2, "extracted_max_yoe": 5, "yoe_match": True,
        "matched_skills": [], "missing_skills": [],
        "fit_score": 0.8, "summary_reason": "Good"
    })
    job = guard.validate_and_parse(valid_json, "url1", "q1", "s1")
    assert job.title == "T"
    assert job.apply_url == "url1"

def test_json_in_markdown(mock_client):
    guard = OutputGuard(mock_client)
    markdown_output = f"```json\n{json.dumps({'title': 'T', 'company': 'C', 'location': 'L', 'extracted_min_yoe': 2, 'extracted_max_yoe': 5, 'yoe_match': True, 'matched_skills': [], 'missing_skills': [], 'fit_score': 0.8, 'summary_reason': 'Good'})}\n```"
    job = guard.validate_and_parse(markdown_output, "url1")
    assert job.title == "T"

def test_invalid_json_triggers_retry(mock_client):
    mock_client.generate.return_value = json.dumps({
        "title": "T", "company": "C", "location": "L",
        "extracted_min_yoe": 2, "extracted_max_yoe": 5, "yoe_match": True,
        "matched_skills": [], "missing_skills": [],
        "fit_score": 0.8, "summary_reason": "Good"
    })
    
    guard = OutputGuard(mock_client)
    job = guard.validate_and_parse("invalid json text", "url1")
    
    assert mock_client.generate.call_count == 1
    assert job.title == "T"

def test_persistent_failure(mock_client):
    mock_client.generate.return_value = "still invalid"
    guard = OutputGuard(mock_client, max_retries=1)
    
    with pytest.raises(OutputValidationError):
        guard.validate_and_parse("invalid", "url1")

def test_schema_adherence_rate(mock_client):
    guard = OutputGuard(mock_client)
    valid_json = json.dumps({
        "title": "T", "company": "C", "location": "L",
        "extracted_min_yoe": 2, "extracted_max_yoe": 5, "yoe_match": True,
        "matched_skills": [], "missing_skills": [],
        "fit_score": 0.8, "summary_reason": "Good"
    })
    guard.validate_and_parse(valid_json, "url1")
    assert guard.schema_adherence_rate == 1.0
