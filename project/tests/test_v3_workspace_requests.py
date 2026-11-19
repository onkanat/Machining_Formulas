"""Tests for routing workspace model requests into review suggestions."""

from __future__ import annotations

import pytest

from machining_formulas.gui import v3_gui
from machining_formulas.gui.v3_gui import V3Calculator
from machining_formulas.workspace.workspace_buffer import WorkspaceBuffer
from machining_formulas.workspace.workspace_editor import (
    MODE_APPEND,
    MODE_INSERT,
    MODE_REPLACE,
    ModelRequest,
)


class FakeEditor:
    """Minimal editor double; the real widget is not needed for routing."""

    def __init__(self, buffer: WorkspaceBuffer):
        self.buffer = buffer
        self.messages = []
        self.opened = []
        self.dirty = False

    def is_dirty(self) -> bool:
        return self.dirty

    def get_current_content(self) -> str:
        return self.buffer.get_content()

    def open_review(self, edit_id=None) -> None:
        self.opened.append(edit_id)

    def finish_request(self, message: str = "") -> None:
        self.messages.append(message)


def _app(content: str) -> V3Calculator:
    app = V3Calculator.__new__(V3Calculator)
    app.workspace_buffer = WorkspaceBuffer()
    app.workspace_buffer.set_content(content)
    app.workspace_editor = FakeEditor(app.workspace_buffer)
    return app


def _pending(app: V3Calculator):
    return app.workspace_buffer.get_pending_suggestions()


def test_handle_model_request_preserves_raw_selection_for_editing():
    app = _app("    Vc = 170 m/min")
    app.current_model_name = "m"
    app.current_model_url = "http://localhost:11434"
    received = {}

    def fake_edit(source_text, request):
        received["text"] = source_text

    app._edit_workspace_text = fake_edit  # type: ignore[method-assign]

    app._handle_model_request(
        ModelRequest(source_text="    Vc = 170 m/min", mode=MODE_REPLACE, offset=0)
    )

    assert received["text"] == "    Vc = 170 m/min"


def test_handle_model_request_strips_selection_only_for_question_context():
    app = _app("belge")
    app.current_model_name = "m"
    app.current_model_url = "http://localhost:11434"
    received = {}

    def fake_answer(question, source_text, request):
        received["source"] = source_text

    app._answer_workspace_question = fake_answer  # type: ignore[method-assign]

    app._handle_model_request(
        ModelRequest(question=" kaç? ", source_text="  100 mm  ", mode=MODE_APPEND)
    )

    assert received["source"] == "100 mm"


def test_replace_suggestion_rejects_stale_offsets():
    raw = "    Vc = 170 m/min"
    app = _app(raw + "\nikinci satır")
    request = ModelRequest(source_text=raw.strip(), mode=MODE_REPLACE, offset=0)

    app._add_workspace_suggestion("yeni metin", request, replacement=raw.strip())

    assert _pending(app) == []
    assert "Metin değişti" in app.workspace_editor.messages[-1]


def test_replace_suggestion_keeps_indentation_when_text_matches():
    raw = "    Vc = 170 m/min"
    app = _app(raw + "\nikinci satır")
    request = ModelRequest(source_text=raw, mode=MODE_REPLACE, offset=0)

    app._add_workspace_suggestion("    Vc = 172 m/min", request, replacement=raw)
    suggestion = _pending(app)[0]

    assert suggestion.old_text == raw
    assert app.workspace_buffer.accept_suggestion(suggestion.id) is True
    assert app.workspace_buffer.get_content() == "    Vc = 172 m/min\nikinci satır"


def test_append_suggestion_adds_block_at_end():
    app = _app("mevcut metin")
    request = ModelRequest(question="soru", mode=MODE_APPEND, offset=0)

    app._add_workspace_suggestion("Soru: soru\n\nYanıt:\ncevap", request)

    suggestion = _pending(app)[0]
    assert suggestion.at_end is True
    assert app.workspace_buffer.accept_suggestion(suggestion.id) is True
    assert app.workspace_buffer.get_content() == "mevcut metin\n\nSoru: soru\n\nYanıt:\ncevap"


def test_insert_suggestion_clamps_offset_to_document_length():
    app = _app("abc")
    request = ModelRequest(question="soru", mode=MODE_INSERT, offset=99)

    app._add_workspace_suggestion("XYZ", request)

    suggestion = _pending(app)[0]
    assert suggestion.position == 3
    assert app.workspace_buffer.accept_suggestion(suggestion.id) is True
    assert app.workspace_buffer.get_content() == "abcXYZ"


def test_confirm_discard_changes_skips_dialog_for_clean_document(monkeypatch):
    app = _app("metin")
    app.workspace_editor.dirty = False
    monkeypatch.setattr(
        v3_gui.messagebox, "askyesnocancel", lambda *a, **k: pytest.fail("dialog açılmamalı")
    )

    assert app._confirm_discard_changes("Çıkış") is True


def test_confirm_discard_changes_cancel_keeps_working(monkeypatch):
    app = _app("metin")
    app.workspace_editor.dirty = True
    monkeypatch.setattr(v3_gui.messagebox, "askyesnocancel", lambda *a, **k: None)

    assert app._confirm_discard_changes("Çıkış") is False


def test_confirm_discard_changes_discards_without_saving(monkeypatch):
    app = _app("metin")
    app.workspace_editor.dirty = True
    monkeypatch.setattr(v3_gui.messagebox, "askyesnocancel", lambda *a, **k: False)
    app._save_workspace = lambda: pytest.fail("kaydet çağrılmamalı")  # type: ignore[method-assign]

    assert app._confirm_discard_changes("Çıkış") is True


def test_confirm_discard_changes_saves_and_follows_save_result(monkeypatch):
    app = _app("metin")
    app.workspace_editor.dirty = True
    monkeypatch.setattr(v3_gui.messagebox, "askyesnocancel", lambda *a, **k: True)
    app._save_workspace = lambda: True  # type: ignore[method-assign]

    assert app._confirm_discard_changes("Çıkış") is True

    app._save_workspace = lambda: False  # type: ignore[method-assign]
    assert app._confirm_discard_changes("Çıkış") is False
