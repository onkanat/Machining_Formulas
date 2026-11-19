"""
Tests for V3 workspace buffer functionality.

This module tests the collaborative workspace buffer where
users and models can edit content together.
"""

import pytest
from datetime import datetime
from machining_formulas.workspace.workspace_buffer import (
    EditType,
    WorkspaceBuffer,
    WorkspaceEdit,
    line_diff,
)


class TestWorkspaceBuffer:
    """Test core workspace buffer functionality."""

    def test_workspace_creation(self):
        """Test workspace buffer creation."""
        buffer = WorkspaceBuffer()
        assert buffer.get_content() == ""
        assert len(buffer.edits) == 0
        assert len(buffer.versions) == 1  # Initial version

    def test_set_content(self):
        """Test setting workspace content."""
        buffer = WorkspaceBuffer()
        buffer.set_content("Hello World", "user", "Initial content")

        assert buffer.get_content() == "Hello World"
        assert len(buffer.edits) == 1
        assert buffer.edits[0].author == "user"
        assert buffer.edits[0].new_text == "Hello World"

    def test_insert_text(self):
        """Test text insertion."""
        buffer = WorkspaceBuffer()
        buffer.set_content("Hello World", "user")

        edit = buffer.insert_text(5, " Beautiful", "user")
        assert buffer.get_content() == "Hello Beautiful World"
        assert edit.position == 5
        assert edit.new_text == " Beautiful"
        assert edit.author == "user"

    def test_delete_text(self):
        """Test text deletion."""
        buffer = WorkspaceBuffer()
        buffer.set_content("Hello Beautiful World", "user")

        edit = buffer.delete_text(6, 16, "user")  # Delete " Beautiful "
        assert buffer.get_content() == "Hello World"
        assert edit.old_text == "Beautiful "
        assert edit.author == "user"

    def test_replace_text(self):
        """Test text replacement."""
        buffer = WorkspaceBuffer()
        buffer.set_content("Hello World", "user")

        edit = buffer.replace_text(6, 11, "Universe", "user")
        assert buffer.get_content() == "Hello Universe"
        assert edit.old_text == "World"
        assert edit.new_text == "Universe"

    def test_model_suggestion(self):
        """Test model suggestion functionality."""
        buffer = WorkspaceBuffer()
        buffer.set_content("Hello World", "user")

        suggestion = buffer.suggest_edit(6, 11, "Universe", "Model suggestion")
        assert buffer.get_content() == "Hello World"  # Should not change
        assert suggestion.author == "model"
        assert not suggestion.accepted

        # Check pending suggestions
        pending = buffer.get_pending_suggestions()
        assert len(pending) == 1
        assert pending[0].id == suggestion.id

    def test_accept_suggestion(self):
        """Test accepting model suggestion."""
        buffer = WorkspaceBuffer()
        buffer.set_content("Hello World", "user")

        suggestion = buffer.suggest_edit(6, 11, "Universe", "Model suggestion")
        success = buffer.accept_suggestion(suggestion.id)

        assert success
        assert buffer.get_content() == "Hello Universe"
        assert suggestion.accepted

        # No pending suggestions
        pending = buffer.get_pending_suggestions()
        assert len(pending) == 0

    def test_reject_suggestion(self):
        """Test rejecting model suggestion."""
        buffer = WorkspaceBuffer()
        buffer.set_content("Hello World", "user")

        suggestion = buffer.suggest_edit(6, 11, "Universe", "Model suggestion")
        success = buffer.reject_suggestion(suggestion.id)

        assert success
        assert buffer.get_content() == "Hello World"  # Should not change

        # No pending suggestions
        pending = buffer.get_pending_suggestions()
        assert len(pending) == 0

    def test_version_history(self):
        """Test version history tracking."""
        buffer = WorkspaceBuffer()

        # Initial version
        assert len(buffer.versions) == 1

        # Make some edits
        buffer.set_content("Hello", "user")
        buffer.insert_text(5, " World", "user")
        buffer.replace_text(6, 11, "Universe", "user")

        # Should have versions for each edit
        assert len(buffer.versions) >= 3

        # Test version restore
        content_after_edits = buffer.get_content()
        first_version_id = buffer.versions[1].id  # Skip initial version

        success = buffer.restore_version(first_version_id)
        assert success
        assert buffer.get_content() == "Hello"

        # After restore, a new version is created, so we need to find the original latest
        # The content after all edits should be in one of the versions
        original_content_found = any(
            version.content == content_after_edits for version in buffer.versions
        )
        assert original_content_found, (
            "Content after edits should be preserved in version history"
        )

    def test_workspace_stats(self):
        """Test workspace statistics."""
        buffer = WorkspaceBuffer()

        # Make various edits
        buffer.set_content("Hello", "user")
        buffer.insert_text(5, " World", "user")
        buffer.suggest_edit(6, 11, "Universe", "Model suggestion")

        stats = buffer.get_stats()
        assert stats["content_length"] == 11  # "Hello World"
        assert stats["user_edits"] == 2
        assert stats["model_edits"] == 1
        assert stats["pending_suggestions"] == 1
        assert stats["total_edits"] == 3
        assert stats["versions"] >= 2

    def test_export_import_session(self):
        """Test session export and import."""
        buffer1 = WorkspaceBuffer()
        buffer1.set_content("Hello World", "user")
        buffer1.insert_text(5, " Beautiful", "user")

        # Export session
        session_data = buffer1.export_session()
        assert "content" in session_data
        assert "edits" in session_data
        assert "versions" in session_data
        assert session_data["content"] == "Hello Beautiful World"

        # Import to new buffer
        buffer2 = WorkspaceBuffer()
        success = buffer2.import_session(session_data)

        assert success
        assert buffer2.get_content() == "Hello Beautiful World"
        assert len(buffer2.edits) == len(buffer1.edits)

    def test_invalid_import_keeps_existing_document(self):
        """Bozuk bir dosya mevcut belgeyi yarım yüklemeyle bozmamalı."""
        buffer = WorkspaceBuffer()
        buffer.set_content("Korunacak metin", "user")
        before = buffer.get_content()

        assert buffer.import_session({"content": 123}) is False
        assert buffer.import_session(["content"]) is False
        assert buffer.import_session({"content": "yeni", "edits": ["bozuk"]}) is False

        assert buffer.get_content() == before

    def test_clear_all(self):
        """Test clearing workspace."""
        buffer = WorkspaceBuffer()
        buffer.set_content("Hello World", "user")
        buffer.insert_text(5, " Beautiful", "user")

        buffer.clear_all()
        assert buffer.get_content() == ""
        assert len(buffer.versions) >= 1  # Should have clear version


class TestWorkspaceEdit:
    """Test workspace edit functionality."""

    def test_edit_creation(self):
        """Test edit creation."""
        edit = WorkspaceEdit(
            edit_type=EditType.USER_INSERT, position=5, new_text="Hello", author="user"
        )

        assert edit.edit_type == EditType.USER_INSERT
        assert edit.position == 5
        assert edit.new_text == "Hello"
        assert edit.author == "user"
        assert edit.accepted == True

    def test_edit_serialization(self):
        """Test edit serialization."""
        edit = WorkspaceEdit(
            edit_type=EditType.MODEL_REPLACE,
            position=10,
            old_text="World",
            new_text="Universe",
            author="model",
            accepted=False,
        )

        # Convert to dict
        edit_dict = edit.to_dict()
        assert edit_dict["edit_type"] == "model_replace"
        assert edit_dict["position"] == 10
        assert edit_dict["old_text"] == "World"
        assert edit_dict["new_text"] == "Universe"
        assert edit_dict["author"] == "model"
        assert edit_dict["accepted"] == False

        # Convert back from dict
        restored_edit = WorkspaceEdit.from_dict(edit_dict)
        assert restored_edit.edit_type == EditType.MODEL_REPLACE
        assert restored_edit.position == 10
        assert restored_edit.old_text == "World"
        assert restored_edit.new_text == "Universe"
        assert restored_edit.author == "model"
        assert restored_edit.accepted == False


class TestCollaborativeEditing:
    """Test collaborative editing scenarios."""

    def test_user_model_collaboration(self):
        """Test user and model editing together."""
        buffer = WorkspaceBuffer()

        # User writes initial content
        buffer.set_content("Project calculation:", "user")

        # Model suggests improvement
        suggestion = buffer.suggest_edit(
            len("Project calculation:"),
            len("Project calculation:"),
            "\n- Cutting speed: Vc = π × D × n / 1000\n- Spindle speed: n = Vc × 1000 / (π × D)",
            "Model suggestion",
        )

        # User accepts suggestion
        buffer.accept_suggestion(suggestion.id)

        expected = """Project calculation:
- Cutting speed: Vc = π × D × n / 1000
- Spindle speed: n = Vc × 1000 / (π × D)"""

        assert buffer.get_content() == expected

        # User adds calculation
        buffer.insert_text(
            len(expected), "\n\nFor D=50mm, n=1000 rpm:\nVc = 157.1 m/min", "user"
        )

        # Check final state
        final_content = buffer.get_content()
        assert "157.1 m/min" in final_content
        assert "π × D × n" in final_content

    def test_multiple_suggestions(self):
        """Test handling multiple model suggestions."""
        buffer = WorkspaceBuffer()
        buffer.set_content("Cutting speed formula: Vc = π × D × n", "user")

        # First suggestion
        suggestion1 = buffer.suggest_edit(28, 28, " / 1000", "Model suggestion 1")

        # Second suggestion
        suggestion2 = buffer.suggest_edit(
            0, 15, "Metric cutting speed", "Model suggestion 2"
        )

        # Should have 2 pending suggestions
        pending = buffer.get_pending_suggestions()
        assert len(pending) == 2

        # Accept first suggestion only
        buffer.accept_suggestion(suggestion1.id)

        # Content should have first suggestion applied
        content = buffer.get_content()
        # Note: Overlapping suggestions create conflicts, this is expected behavior
        assert "/ 1000" in content
        assert "Metric cutting speed formula" not in content

        # Reject second suggestion
        buffer.reject_suggestion(suggestion2.id)
        pending = buffer.get_pending_suggestions()
        assert len(pending) == 0

    def test_edit_conflict_resolution(self):
        """Test edit conflict scenarios."""
        buffer = WorkspaceBuffer()
        buffer.set_content("Hello World", "user")

        # Model suggests replacing "World" with "Universe"
        suggestion = buffer.suggest_edit(6, 11, "Universe", "Model suggestion")

        # User edits the same area before accepting suggestion
        buffer.replace_text(6, 11, "Earth", "user")

        # Accept model suggestion: it is stale, so it must be refused
        success = buffer.accept_suggestion(suggestion.id)

        assert success is False
        assert suggestion.stale is True
        assert buffer.get_content() == "Hello Earth"


class TestLineDiff:
    """Test the line-based diff used by the review panel."""

    def test_identical_text_has_no_diff(self):
        assert line_diff("a\nb", "a\nb") == []

    def test_added_lines_are_marked(self):
        diff = line_diff("a\nb", "a\nb\nc")
        added = [text for tag, text in diff if tag == "+"]
        assert added == ["c"]
        assert all(tag != "-" for tag, _ in diff)

    def test_removed_lines_are_marked(self):
        diff = line_diff("a\nb\nc", "a\nc")
        removed = [text for tag, text in diff if tag == "-"]
        assert removed == ["b"]

    def test_replaced_line_shows_both_sides(self):
        diff = line_diff("Hello World", "Hello Universe")
        assert ("-", "Hello World") in diff
        assert ("+", "Hello Universe") in diff

    def test_context_lines_are_kept(self):
        old = "1\n2\n3\n4\n5\n6\n7"
        new = "1\n2\n3\n4\n5\n6\nseven"
        diff = line_diff(old, new)
        context = [text for tag, text in diff if tag == " "]
        assert "5" in context
        assert ("-", "7") in diff
        assert ("+", "seven") in diff

    def test_empty_old_text_is_all_additions(self):
        diff = line_diff("", "Soru: x\n\nYanıt:\ny")
        content_lines = [(tag, text) for tag, text in diff if tag != "@"]
        assert all(tag == "+" for tag, _ in content_lines)
        assert [text for _, text in content_lines] == ["Soru: x", "", "Yanıt:", "y"]


class TestSuggestionReviewFlow:
    """Test the suggestion types and dedupe used by the review panel."""

    def test_empty_old_text_creates_insert_suggestion(self):
        buffer = WorkspaceBuffer()
        buffer.set_content("Hello", "user")

        suggestion = buffer.suggest_edit(5, 5, " World")

        assert suggestion.edit_type == EditType.MODEL_INSERT
        assert suggestion.old_text == ""

    def test_duplicate_suggestion_is_not_stacked(self):
        buffer = WorkspaceBuffer()
        buffer.set_content("Hello", "user")

        first = buffer.suggest_edit(5, 5, " World")
        second = buffer.suggest_edit(5, 5, " World")

        assert first.id == second.id
        assert len(buffer.get_pending_suggestions()) == 1

    def test_same_replacement_text_at_different_positions_is_not_deduped(self):
        buffer = WorkspaceBuffer()
        buffer.set_content("XaXb", "user")

        first = buffer.suggest_edit(0, 1, "Y")
        second = buffer.suggest_edit(2, 3, "Y")

        assert first.id != second.id
        assert len(buffer.get_pending_suggestions()) == 2

    def test_accepting_at_end_suggestion_appends_after_later_edits(self):
        buffer = WorkspaceBuffer()
        buffer.set_content("Hello", "user")
        suggestion = buffer.suggest_edit(5, 5, "\nWorld", at_end=True)

        buffer.insert_text(len(buffer.get_content()), "!", "user")
        assert buffer.accept_suggestion(suggestion.id) is True

        assert buffer.get_content() == "Hello!\nWorld"

    def test_accepting_insert_suggestion_clamps_position(self):
        buffer = WorkspaceBuffer()
        buffer.set_content("Hello", "user")
        suggestion = buffer.suggest_edit(100, 100, "!")

        assert buffer.accept_suggestion(suggestion.id) is True
        assert buffer.get_content() == "Hello!"

    def test_at_end_flag_survives_round_trip(self):
        edit = WorkspaceEdit(edit_type=EditType.MODEL_INSERT, at_end=True)

        restored = WorkspaceEdit.from_dict(edit.to_dict())

        assert restored.at_end is True


class TestAnswerBlock:
    """Test how model answers are formatted before insertion."""

    def test_question_is_kept_when_short(self):
        from machining_formulas.workspace.workspace_editor import format_answer_block

        block = format_answer_block("Çap 100 mm, 550 rpm?", "Vc = 172.79 m/min")

        assert block.startswith("Soru: Çap 100 mm, 550 rpm?")
        assert "Vc = 172.79 m/min" in block

    def test_answer_only_when_question_missing(self):
        from machining_formulas.workspace.workspace_editor import format_answer_block

        assert format_answer_block("", "  Vc = 172.79 m/min  ") == "Vc = 172.79 m/min"

    def test_long_question_is_not_embedded(self):
        from machining_formulas.workspace.workspace_editor import format_answer_block

        block = format_answer_block("x" * 600, "yanıt")

        assert block == "yanıt"


class TestEditorBufferSync:
    """Editörde yazılan metin buffer'a eksiksiz yansımalı."""

    @staticmethod
    def _replay(old: str, new: str) -> str:
        from machining_formulas.workspace.workspace_editor import WorkspaceEditor

        buffer = WorkspaceBuffer()
        buffer.set_content(old)

        class Recorder:
            workspace_buffer = buffer

        WorkspaceEditor._record_text_change(Recorder(), old, new)
        return buffer.get_content()

    @pytest.mark.parametrize(
        ("old", "new"),
        [
            ("a", "aa"),  # tek karakterin tekrarı
            ("abc", "abcabc"),  # metnin kopyalanması
            ("abab", "ababab"),
            ("abc", "abcd"),
            ("hello world", "hello"),
            ("abc", ""),
            ("", "abc"),
            ("Vc = 170", "Vc = 172"),
        ],
    )
    def test_buffer_matches_edited_text(self, old, new):
        assert self._replay(old, new) == new

    def test_identical_text_records_no_edit(self):
        from machining_formulas.workspace.workspace_editor import WorkspaceEditor

        buffer = WorkspaceBuffer()
        buffer.set_content("abc")
        before = len(buffer.edits)

        class Recorder:
            workspace_buffer = buffer

        WorkspaceEditor._record_text_change(Recorder(), "abc", "abc")

        assert len(buffer.edits) == before


class TestEditorSavedState:
    """Belge yalnızca gerçekten kaydedilince "temiz" sayılmalı."""

    class _FakeText:
        def __init__(self):
            self.content = ""

        def delete(self, *_args):
            self.content = ""

        def insert(self, index, text):
            self.content = text if index == "1.0" else self.content + text

        def edit_modified(self, _flag):
            pass

        def get(self, *_args):
            return self.content

    @classmethod
    def _editor(cls, content: str):
        from machining_formulas.workspace.workspace_editor import WorkspaceEditor

        buffer = WorkspaceBuffer()

        class Dummy:
            workspace_buffer = buffer
            text_editor = cls._FakeText()
            _user_editing = True
            _last_known_content = ""
            _saved_content = ""

            def _update_line_numbers(self):
                pass

            def _update_status(self):
                pass

            def get_current_content(self):
                return self.text_editor.get().rstrip("\n")

        dummy = Dummy()
        buffer.set_content(content)
        return dummy, WorkspaceEditor

    def test_loading_content_does_not_mark_document_saved(self):
        dummy, editor = self._editor("öneri kabul edildi")

        editor._load_content(dummy)

        assert editor.is_dirty(dummy) is True

        editor.mark_saved(dummy)
        assert editor.is_dirty(dummy) is False

    def test_empty_answer_returns_empty_block(self):
        from machining_formulas.workspace.workspace_editor import format_answer_block

        assert format_answer_block("soru", "   ") == ""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
