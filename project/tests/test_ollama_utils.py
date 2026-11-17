import pytest
from unittest.mock import MagicMock

from machining_formulas.llm.ollama_utils import (
    auth_headers,
    normalize_chat_url,
    candidate_chat_urls,
    candidate_model_list_urls,
    _DEFAULT_CHAT_URL,
)
from machining_formulas.llm.ollama_utils_v2 import (
    _extract_model_names,
    get_available_models,
    single_chat_request,
    test_connection as probe_connection,
)
from machining_formulas.gui.v3_gui import V3Calculator


def test_normalize_chat_url():
    """Verify normalize_chat_url handles Ollama and OpenAI-compatible inputs."""
    # None or empty
    assert normalize_chat_url(None) == _DEFAULT_CHAT_URL
    assert normalize_chat_url("") == _DEFAULT_CHAT_URL

    # Bare host -> OpenAI-compatible endpoint (Ollama serves it too)
    assert normalize_chat_url("http://localhost:11434") == "http://localhost:11434/v1/chat/completions"
    assert normalize_chat_url("http://localhost:11434/") == "http://localhost:11434/v1/chat/completions"

    # Explicit endpoints are preserved
    assert normalize_chat_url("http://localhost:11434/v1/chat") == "http://localhost:11434/v1/chat"
    assert normalize_chat_url("http://localhost:11434/api/chat") == "http://localhost:11434/api/chat"
    assert (
        normalize_chat_url("http://192.168.1.105:8080/v1/chat/completions")
        == "http://192.168.1.105:8080/v1/chat/completions"
    )

    # Base with /v1 or /api only
    assert normalize_chat_url("http://localhost:11434/v1") == "http://localhost:11434/v1/chat/completions"
    assert normalize_chat_url("http://localhost:11434/api") == "http://localhost:11434/api/chat"
    assert normalize_chat_url("http://192.168.1.105:8080/v1") == "http://192.168.1.105:8080/v1/chat/completions"


def test_candidate_chat_urls():
    """Verify candidate_chat_urls keeps the typed endpoint first and adds fallbacks."""
    assert candidate_chat_urls("http://localhost:11434/v1/chat") == [
        "http://localhost:11434/v1/chat",
        "http://localhost:11434/v1/chat/completions",
        "http://localhost:11434/api/chat",
    ]

    assert candidate_chat_urls("http://localhost:11434/api/chat") == [
        "http://localhost:11434/api/chat",
        "http://localhost:11434/v1/chat/completions",
        "http://localhost:11434/v1/chat",
    ]

    # OpenAI-compatible gateway: no Ollama-only /v1/chat call is needed there
    assert candidate_chat_urls("http://192.168.1.105:8080/v1") == [
        "http://192.168.1.105:8080/v1/chat/completions",
        "http://192.168.1.105:8080/v1/chat",
        "http://192.168.1.105:8080/api/chat",
    ]


def test_candidate_model_list_urls():
    """Verify model-list candidates cover OpenAI /v1/models and Ollama tags."""
    assert candidate_model_list_urls("http://192.168.1.105:8080/v1") == [
        "http://192.168.1.105:8080/v1/models",
        "http://192.168.1.105:8080/api/tags",
        "http://192.168.1.105:8080/v1/tags",
    ]
    assert candidate_model_list_urls("http://localhost:11434/api/tags")[0] == (
        "http://localhost:11434/api/tags"
    )


def test_extract_model_names_handles_both_schemas():
    """OpenAI returns data[].id, Ollama returns models[].name."""
    assert _extract_model_names({"data": [{"id": "qwen3.8-flash-next-q2_0"}]}) == [
        "qwen3.8-flash-next-q2_0"
    ]
    assert _extract_model_names({"models": [{"name": "llama3:latest"}]}) == ["llama3:latest"]
    assert _extract_model_names({"data": "nope", "models": None}) == []


def test_get_available_models_reads_openai_gateway(monkeypatch):
    """An OpenAI-compatible gateway lists models via /v1/models."""
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {"object": "list", "data": [{"id": "qwen3.8-flash-next-q2_0"}]}
    get = MagicMock(return_value=response)
    monkeypatch.setattr("machining_formulas.llm.ollama_utils_v2.requests.get", get)

    assert get_available_models("http://192.168.1.105:8080/v1") == ["qwen3.8-flash-next-q2_0"]
    assert get.call_args[0][0] == "http://192.168.1.105:8080/v1/models"


class DummyV3Calculator(V3Calculator):
    """Headless V3Calculator subclass for safe logic unit testing."""
    def __init__(self):
        # Skip tk initialization to prevent Tk/Tcl system dependency in tests
        self.root = MagicMock()
        self.tooltips = {}
        self.current_model_url = "http://localhost:11434"
        self.current_model_name = ""
        self.current_api_key = ""
        self.ollama_models = []
        
        # Mock widgets/variables
        self.model_url_entry = MagicMock()
        self.model_url_entry.get.return_value = "http://localhost:11434"
        self.model_selection_combo = MagicMock()
        self.status_var = MagicMock()

    def _run_background(self, work, on_success, on_error):
        """Run the job inline so these tests stay deterministic."""
        try:
            on_success(work())
        except Exception as exc:  # noqa: BLE001 - mirrors the real helper
            on_error(exc)


def test_refresh_model_list_success(monkeypatch, tmp_path):
    """Test refresh_model_list sets retrieved models in combo values when successful."""
    monkeypatch.setenv("MACHINING_FORMULAS_CONFIG_DIR", str(tmp_path))
    calc = DummyV3Calculator()
    
    # Mock get_available_models to return models
    mock_get_models = MagicMock(return_value=["llama3:latest", "gemma2"])
    monkeypatch.setattr("machining_formulas.gui.v3_gui.get_available_models", mock_get_models)
    
    calc.refresh_model_list()
    
    # Assert get_available_models called with correct URL
    mock_get_models.assert_called_once_with("http://localhost:11434", "")
    
    # Assert combobox values updated
    calc.model_selection_combo.__setitem__.assert_called_with("values", ["llama3:latest", "gemma2"])
    calc.model_selection_combo.set.assert_called_with("llama3:latest")
    assert calc.current_model_name == "llama3:latest"


def test_refresh_model_list_failure(monkeypatch):
    """Test refresh_model_list clears the selector instead of inventing models."""
    calc = DummyV3Calculator()

    # Mock get_available_models to fail (return empty list)
    mock_get_models = MagicMock(return_value=[])
    monkeypatch.setattr("machining_formulas.gui.v3_gui.get_available_models", mock_get_models)

    calc.refresh_model_list()

    # No fake fallback models: selector must be emptied and disabled
    calc.model_selection_combo.__setitem__.assert_called_with("values", [])
    calc.model_selection_combo.set.assert_called_with("")
    calc.model_selection_combo.configure.assert_called_with(state="disabled")
    assert calc.current_model_name == ""
    assert calc.ollama_models == []


def test_auth_headers_only_when_key_present(monkeypatch):
    """No Authorization header without a key; bearer token when one is set."""
    monkeypatch.delenv("MACHINING_FORMULAS_API_KEY", raising=False)
    monkeypatch.delenv("STRATA_API_KEY", raising=False)

    assert auth_headers() == {"Content-Type": "application/json"}
    assert auth_headers("  ") == {"Content-Type": "application/json"}
    assert auth_headers("sk-local")["Authorization"] == "Bearer sk-local"


def test_auth_headers_reads_env_fallbacks(monkeypatch):
    """MACHINING_FORMULAS_API_KEY wins over STRATA_API_KEY; explicit wins over both."""
    monkeypatch.setenv("STRATA_API_KEY", "strata-key")
    assert auth_headers()["Authorization"] == "Bearer strata-key"

    monkeypatch.setenv("MACHINING_FORMULAS_API_KEY", "app-key")
    assert auth_headers()["Authorization"] == "Bearer app-key"

    assert auth_headers("explicit-key")["Authorization"] == "Bearer explicit-key"


def test_get_available_models_sends_bearer_token(monkeypatch):
    """The model-list request carries the bearer token from the caller."""
    monkeypatch.delenv("MACHINING_FORMULAS_API_KEY", raising=False)
    monkeypatch.delenv("STRATA_API_KEY", raising=False)

    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {"data": [{"id": "qwen3.8-flash-next-q2_0"}]}
    get = MagicMock(return_value=response)
    monkeypatch.setattr("machining_formulas.llm.ollama_utils_v2.requests.get", get)

    get_available_models("http://192.168.1.105:8080/v1", "secret-key")

    assert get.call_args.kwargs["headers"]["Authorization"] == "Bearer secret-key"


def test_test_connection_sends_bearer_token(monkeypatch):
    """The connection probe also authenticates."""
    response = MagicMock()
    response.status_code = 200
    get = MagicMock(return_value=response)
    monkeypatch.setattr("machining_formulas.llm.ollama_utils_v2.requests.get", get)

    assert probe_connection("http://192.168.1.105:8080/v1", "secret-key") is True
    assert get.call_args.kwargs["headers"]["Authorization"] == "Bearer secret-key"


def test_single_chat_request_sends_bearer_token(monkeypatch):
    """Chat requests authenticate against the key-protected gateway."""
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {"choices": [{"message": {"content": "ok"}}]}
    post = MagicMock(return_value=response)
    monkeypatch.setattr("machining_formulas.llm.ollama_utils_v2.requests.post", post)

    assert single_chat_request(
        "http://192.168.1.105:8080/v1", "qwen3.8-flash-next-q2_0", "merhaba", api_key="secret-key"
    ) == "ok"
    assert post.call_args.kwargs["headers"]["Authorization"] == "Bearer secret-key"


def test_get_available_models_requires_key_when_server_demands_it(monkeypatch):
    """A gateway returning 401 without a token yields no models; the token fixes it."""
    monkeypatch.setattr("machining_formulas.llm.ollama_utils_v2.logger", MagicMock())

    def fake_get(url, headers=None, timeout=None):
        response = MagicMock()
        if (headers or {}).get("Authorization") == "Bearer secret-key":
            response.status_code = 200
            response.json.return_value = {"data": [{"id": "qwen3.8-flash-next-q2_0"}]}
        else:
            response.status_code = 401
        return response

    monkeypatch.setattr("machining_formulas.llm.ollama_utils_v2.requests.get", fake_get)

    assert get_available_models("http://192.168.1.105:8080/v1") == []
    assert get_available_models("http://192.168.1.105:8080/v1", "secret-key") == [
        "qwen3.8-flash-next-q2_0"
    ]
