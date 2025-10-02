from horz_gui import AdvancedCalculator


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
