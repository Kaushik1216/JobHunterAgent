import pytest
from unittest.mock import patch, MagicMock
from inference.client import LLMClient, check_llm_connection
from config import Settings


def test_llm_client_headers_with_api_key():
    settings = Settings(llm_provider="online", llm_api_key="secret-key", llm_base_url="https://api.openai.com/v1")
    client = LLMClient(settings)
    assert "Authorization" in client._client.headers
    assert client._client.headers["Authorization"] == "Bearer secret-key"


def test_llm_client_headers_without_api_key():
    settings = Settings(llm_provider="local", llm_api_key="", llm_base_url="http://localhost:1234/v1")
    client = LLMClient(settings)
    assert "Authorization" not in client._client.headers


def test_check_llm_connection_empty_url():
    res = check_llm_connection(base_url="", model="qwen")
    assert res["success"] is False
    assert "Base URL cannot be empty" in res["error"]


def test_check_llm_connection_empty_model():
    res = check_llm_connection(base_url="http://localhost:1234/v1", model="")
    assert res["success"] is False
    assert "Model name cannot be empty" in res["error"]


@patch("httpx.Client.post")
def test_check_llm_connection_success(mock_post):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [{"message": {"content": "Connected"}}]
    }
    mock_resp.raise_for_status.return_value = None
    mock_post.return_value = mock_resp

    res = check_llm_connection(
        base_url="http://localhost:1234/v1",
        model="qwen2.5-7b-instruct",
        api_key="test-key",
        provider="local",
    )
    assert res["success"] is True
    assert "Successfully connected" in res["message"]
    assert res["model"] == "qwen2.5-7b-instruct"
    assert "latency_ms" in res
