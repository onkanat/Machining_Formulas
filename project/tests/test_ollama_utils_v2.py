import pytest
from machining_formulas.llm.ollama_utils_v2 import (
    single_chat_request,
    get_available_models,
    test_connection as ollama_test_connection,
)

class DummyResponse:
    def __init__(self, json_data, status_code=200, text=""):
        self._json_data = json_data
        self.status_code = status_code
        self.text = text

    def json(self):
        return self._json_data


def test_single_chat_request_openai_format(monkeypatch):
    """Test single_chat_request parses OpenAI/v1 compatible format correctly."""
    def mock_post(*args, **kwargs):
        return DummyResponse({
            "choices": [
                {
                    "message": {
                        "content": "Test OpenAI Response"
                    }
                }
            ]
        })
    monkeypatch.setattr("requests.post", mock_post)

    result = single_chat_request("http://localhost:11434", "llama3", "Hello")
    assert result == "Test OpenAI Response"


def test_single_chat_request_ollama_format(monkeypatch):
    """Test single_chat_request parses native Ollama format correctly."""
    def mock_post(*args, **kwargs):
        return DummyResponse({
            "message": {
                "content": "Test Ollama Response"
            }
        })
    monkeypatch.setattr("requests.post", mock_post)

    result = single_chat_request("http://localhost:11434", "llama3", "Hello")
    assert result == "Test Ollama Response"


def test_get_available_models_success(monkeypatch):
    """Test get_available_models returns list of model names."""
    def mock_get(*args, **kwargs):
        return DummyResponse({
            "models": [
                {"name": "llama3:latest"},
                {"name": "gemma2"}
            ]
        })
    monkeypatch.setattr("requests.get", mock_get)

    models = get_available_models("http://localhost:11434")
    assert models == ["llama3:latest", "gemma2"]


def test_test_connection_success(monkeypatch):
    """Test test_connection returns True when server responds 200."""
    def mock_get(*args, **kwargs):
        return DummyResponse({}, status_code=200)
    monkeypatch.setattr("requests.get", mock_get)

    assert ollama_test_connection("http://localhost:11434") is True


def test_test_connection_failure(monkeypatch):
    """Test test_connection returns False when server fails."""
    def mock_get(*args, **kwargs):
        raise Exception("Connection Refused")
    monkeypatch.setattr("requests.get", mock_get)

    assert ollama_test_connection("http://localhost:11434") is False
