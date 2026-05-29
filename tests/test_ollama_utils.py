import pytest
from unittest.mock import MagicMock

from machining_formulas.llm.ollama_utils import (
    normalize_chat_url,
    candidate_chat_urls,
    candidate_tags_urls,
)
from machining_formulas.gui.v3_gui import V3Calculator


def test_normalize_chat_url():
    """Verify normalize_chat_url handles various input patterns correctly."""
    # None or empty
    assert normalize_chat_url(None) == "http://localhost:11434/v1/chat"
    assert normalize_chat_url("") == "http://localhost:11434/v1/chat"
    
    # Standard URL with or without trailing slash
    assert normalize_chat_url("http://localhost:11434") == "http://localhost:11434/v1/chat"
    assert normalize_chat_url("http://localhost:11434/") == "http://localhost:11434/v1/chat"
    
    # Already containing /v1/chat or /api/chat
    assert normalize_chat_url("http://localhost:11434/v1/chat") == "http://localhost:11434/v1/chat"
    assert normalize_chat_url("http://localhost:11434/api/chat") == "http://localhost:11434/api/chat"
    
    # Base with /v1 or /api only
    assert normalize_chat_url("http://localhost:11434/v1") == "http://localhost:11434/v1/chat"
    assert normalize_chat_url("http://localhost:11434/api") == "http://localhost:11434/api/chat"


def test_candidate_chat_urls():
    """Verify candidate_chat_urls produces correct legacy and v1 candidates."""
    # Start with v1/chat
    candidates = candidate_chat_urls("http://localhost:11434/v1/chat")
    assert candidates == ["http://localhost:11434/v1/chat", "http://localhost:11434/api/chat"]

    # Start with api/chat
    candidates = candidate_chat_urls("http://localhost:11434/api/chat")
    assert candidates == ["http://localhost:11434/api/chat", "http://localhost:11434/v1/chat"]

    # Start with base URL
    candidates = candidate_chat_urls("http://localhost:11434")
    assert candidates == ["http://localhost:11434/v1/chat", "http://localhost:11434/api/chat"]


def test_candidate_tags_urls():
    """Verify candidate_tags_urls generates tags endpoints correctly."""
    candidates = candidate_tags_urls("http://localhost:11434")
    assert candidates == ["http://localhost:11434/v1/tags", "http://localhost:11434/api/tags"]


class DummyV3Calculator(V3Calculator):
    """Headless V3Calculator subclass for safe logic unit testing."""
    def __init__(self):
        # Skip tk initialization to prevent Tk/Tcl system dependency in tests
        self.root = MagicMock()
        self.tooltips = {}
        self.current_model_url = "http://localhost:11434"
        self.current_model_name = ""
        self.ollama_models = []
        
        # Mock widgets/variables
        self.model_url_entry = MagicMock()
        self.model_url_entry.get.return_value = "http://localhost:11434"
        self.model_selection_combo = MagicMock()
        self.status_var = MagicMock()


def test_refresh_model_list_success(monkeypatch):
    """Test refresh_model_list sets retrieved models in combo values when successful."""
    calc = DummyV3Calculator()
    
    # Mock get_available_models to return models
    mock_get_models = MagicMock(return_value=["llama3:latest", "gemma2"])
    monkeypatch.setattr("machining_formulas.gui.v3_gui.get_available_models", mock_get_models)
    
    calc.refresh_model_list()
    
    # Assert get_available_models called with correct URL
    mock_get_models.assert_called_once_with("http://localhost:11434")
    
    # Assert combobox values updated
    calc.model_selection_combo.__setitem__.assert_called_with("values", ["llama3:latest", "gemma2"])
    calc.model_selection_combo.set.assert_called_with("llama3:latest")
    assert calc.current_model_name == "llama3:latest"


def test_refresh_model_list_failure(monkeypatch):
    """Test refresh_model_list assigns fallback models when server/connection fails."""
    calc = DummyV3Calculator()
    
    # Mock get_available_models to fail (return empty list or raise exception)
    mock_get_models = MagicMock(return_value=[])
    monkeypatch.setattr("machining_formulas.gui.v3_gui.get_available_models", mock_get_models)
    
    calc.refresh_model_list()
    
    # Assert fallback models are assigned to values
    expected_fallbacks = ["llama3", "gemma2", "mistral"]
    calc.model_selection_combo.__setitem__.assert_called_with("values", expected_fallbacks)
    calc.model_selection_combo.set.assert_called_with("llama3")
    assert calc.current_model_name == "llama3"
