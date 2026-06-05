from machining_formulas.gui.advanced_calculator import AdvancedCalculator


class DummyResponse:
    def __init__(self, payload):
        self._payload = payload

    def json(self):
        return self._payload


def _build_calculator_stub():
    calc = AdvancedCalculator.__new__(AdvancedCalculator)
    calc.history = []
    calc.add_to_workspace = lambda *args, **kwargs: None
    calc.update_status_bar = lambda *args, **kwargs: None
    calc._candidate_chat_urls = lambda url: [url]
    calc._debug_log_raw_response = lambda *args, **kwargs: None
    calc.debug_show_raw_model_responses = False
    calc.force_legacy_chat = False
    calc.current_chat_url = None
    calc._last_tool_run_details = None
    calc._tool_loop_limit = 4
    return calc


def test_handle_tool_calls_returns_follow_up_message():
    calculator = _build_calculator_stub()

    captured_payload = {}
    expected_response = {
        "message": {
            "role": "assistant",
            "content": "Kesme hızı: 157.08 m/min"
        }
    }

    def fake_post_chat(url_candidates, payload, headers, timeout=60):
        captured_payload["messages"] = payload["messages"]
        return DummyResponse(expected_response), url_candidates[0], False

    calculator._post_chat_with_legacy_support = (  # type: ignore[assignment]
        fake_post_chat
    )

    messages_history = [{"role": "system", "content": "Sistem"}]
    original_history_snapshot = list(messages_history)

    tool_calls = [{
        "id": "call-1",
        "function": {
            "name": "calculate_turning_cutting_speed",
            "arguments": {"Dm": 50, "n": 1000}
        }
    }]

    assistant_message, updated_history = calculator.handle_tool_calls(
        "http://localhost:11434/v1/chat",
        "llama3",
        messages_history,
        tool_calls,
        []
    )

    assert assistant_message == expected_response["message"]
    assert calculator.current_chat_url == "http://localhost:11434/v1/chat"

    assert messages_history == original_history_snapshot
    assert len(updated_history) == len(messages_history) + 3

    tool_entries = [
        msg for msg in updated_history
        if msg.get("role") == "tool"
    ]
    assert tool_entries, "Tool sonucu güncel mesaja eklenmedi"
    assert tool_entries[0]["content"].startswith("157.08")

    assert calculator.history, "Tool sonuçları global history'ye yazılmadı"
    assert calculator.history[0]["content"].startswith("157.08")

    sent_messages = captured_payload["messages"]
    assert sent_messages[1]["role"] == "assistant"
    assert sent_messages[1]["tool_calls"]
    assert sent_messages[2]["role"] == "tool"

    assert sent_messages[2]["content"].startswith("157.08")


def test_handle_tool_calls_builds_error_summary_when_model_is_silent():
    calculator = _build_calculator_stub()

    expected_response = {
        "message": {
            "role": "assistant",
            "content": ""
        }
    }

    def fake_post_chat(url_candidates, payload, headers, timeout=60):
        return DummyResponse(expected_response), url_candidates[0], False

    calculator._post_chat_with_legacy_support = (  # type: ignore[assignment]
        fake_post_chat
    )

    messages_history = [
        {"role": "system", "content": "Sistem"},
        {"role": "user", "content": "Çap 100 mm yuvarlak çelik parça"},
    ]

    tool_calls = [{
        "id": "call-err",
        "function": {
            "name": "calculate_material_mass",
            "arguments": {
                "shape_key": "circle",
                "density": 7.85,
                "radius": 50
            }
        }
    }]

    assistant_message, updated_history = calculator.handle_tool_calls(
        "http://localhost:11434/v1/chat",
        "llama3",
        messages_history,
        tool_calls,
        []
    )

    content = assistant_message.get("content", "").lower()
    assert content, "Hata özeti oluşturulmadı"
    assert "eksik parametreleri" in content
    assert "length" in content

    assert updated_history[-1]["content"] == assistant_message["content"]
    assert calculator._last_tool_run_details
    assert calculator._last_tool_run_details["errors"]


def test_handle_tool_calls_returns_success_summary_when_model_is_silent():
    calculator = _build_calculator_stub()

    expected_response = {
        "message": {
            "role": "assistant",
            "content": ""
        }
    }

    def fake_post_chat(url_candidates, payload, headers, timeout=60):
        return DummyResponse(expected_response), url_candidates[0], False

    calculator._post_chat_with_legacy_support = (  # type: ignore[assignment]
        fake_post_chat
    )

    messages_history = [
        {"role": "system", "content": "Sistem"},
        {
            "role": "user",
            "content": "yuvarlak çelik malzeme, yarıçap 50 mm, boy 100 mm"
        },
    ]

    tool_calls = [{
        "id": "call-success",
        "function": {
            "name": "calculate_material_mass",
            "arguments": {
                "shape_key": "circle",
                "density": 7.85,
                "radius": 50,
                "length": 100
            }
        }
    }]

    assistant_message, updated_history = calculator.handle_tool_calls(
        "http://localhost:11434/v1/chat",
        "llama3",
        messages_history,
        tool_calls,
        []
    )

    content = assistant_message.get("content", "")
    assert content, "Başarılı araç çağrısı sonrası mesaj boş olmamalı"
    assert "Araç sonuçları başarıyla alındı" in content
    assert "g (" in content
    assert "kg" in content

    # Güncellenen tarihçe mesajı da aynı içeriği taşımalı
    assert updated_history[-1]["content"] == content


def test_handle_tool_calls_multi_turn_success():
    """Test handle_tool_calls handles consecutive multiple tool calls in a single turn and appends them in order."""
    calculator = _build_calculator_stub()

    captured_payload = {}
    expected_response = {
        "message": {
            "role": "assistant",
            "content": "Çoklu araç sonuçları özeti: Kesme hızı ve tabla ilerlemesi başarıyla hesaplandı."
        }
    }

    def fake_post_chat(url_candidates, payload, headers, timeout=60):
        captured_payload["messages"] = payload["messages"]
        return DummyResponse(expected_response), url_candidates[0], False

    calculator._post_chat_with_legacy_support = (  # type: ignore[assignment]
        fake_post_chat
    )

    messages_history = [{"role": "system", "content": "Sistem"}]
    
    # Multiple tool calls sent consecutively
    tool_calls = [
        {
            "id": "call-1",
            "function": {
                "name": "calculate_turning_cutting_speed",
                "arguments": {"Dm": 50, "n": 1000}
            }
        },
        {
            "id": "call-2",
            "function": {
                "name": "calculate_milling_table_feed",
                "arguments": {"fz": 0.1, "n": 1000, "ZEFF": 4}
            }
        }
    ]

    assistant_message, updated_history = calculator.handle_tool_calls(
        "http://localhost:11434/v1/chat",
        "llama3",
        messages_history,
        tool_calls,
        []
    )

    assert assistant_message == expected_response["message"]
    
    # Check the history sequencing:
    # 1. System message
    # 2. Assistant message containing tool calls
    # 3. First tool execution result
    # 4. Second tool execution result
    # 5. Final assistant response summarizing both
    assert len(updated_history) == len(messages_history) + 4
    
    tool_messages = [msg for msg in updated_history if msg.get("role") == "tool"]
    assert len(tool_messages) == 2
    assert "157.08" in tool_messages[0]["content"]
    assert "400.0" in tool_messages[1]["content"]


def test_handle_tool_calls_history_role_tool_sequence():
    """Verify that role="tool" messages are appended to self.history in exact sequence."""
    calculator = _build_calculator_stub()

    expected_response = {
        "message": {
            "role": "assistant",
            "content": "Sonuçlar özeti"
        }
    }

    def fake_post_chat(url_candidates, payload, headers, timeout=60):
        return DummyResponse(expected_response), url_candidates[0], False

    calculator._post_chat_with_legacy_support = fake_post_chat

    messages_history = [{"role": "system", "content": "Sistem"}]
    
    tool_calls = [
        {
            "id": "call-1",
            "function": {
                "name": "calculate_turning_cutting_speed",
                "arguments": {"Dm": 50, "n": 1000}
            }
        }
    ]

    calculator.history = []
    
    calculator.handle_tool_calls(
        "http://localhost:11434/v1/chat",
        "llama3",
        messages_history,
        tool_calls,
        []
    )
    
    # Assert self.history contains the tool message in correct order
    assert len(calculator.history) == 1
    assert calculator.history[0]["role"] == "tool"
    assert calculator.history[0]["tool_call_id"] == "call-1"
    assert "157.08" in calculator.history[0]["content"]


def test_handle_tool_calls_drilling_success():
    """Verify that calculate_drilling_* tool calls are successfully executed and returned."""
    calculator = _build_calculator_stub()

    expected_response = {
        "message": {
            "role": "assistant",
            "content": "Matkap kesme hızı hesaplandı."
        }
    }

    def fake_post_chat(url_candidates, payload, headers, timeout=60):
        return DummyResponse(expected_response), url_candidates[0], False

    calculator._post_chat_with_legacy_support = fake_post_chat

    messages_history = [{"role": "system", "content": "Sistem"}]
    
    tool_calls = [
        {
            "id": "call-drilling-1",
            "function": {
                "name": "calculate_drilling_cutting_speed",
                "arguments": {"Dc": 10, "n": 1000}
            }
        }
    ]

    calculator.history = []
    
    assistant_message, updated_history = calculator.handle_tool_calls(
        "http://localhost:11434/v1/chat",
        "llama3",
        messages_history,
        tool_calls,
        []
    )
    
    assert assistant_message == expected_response["message"]
    
    # Assert self.history contains the tool message with correct value (approx 31.42)
    assert len(calculator.history) == 1
    assert calculator.history[0]["role"] == "tool"
    assert calculator.history[0]["tool_call_id"] == "call-drilling-1"
    assert "31.42" in calculator.history[0]["content"]


