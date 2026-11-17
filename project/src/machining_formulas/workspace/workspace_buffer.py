"""Workspace Buffer - Collaborative text editor for user and model interaction."""

from __future__ import annotations

import difflib
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


def line_diff(old_text: str, new_text: str, context: int = 2) -> List[Tuple[str, str]]:
    """Return a line-based diff as ``(tag, text)`` pairs.

    Tags are ``" "`` (context), ``"-"`` (removed), ``"+"`` (added) and ``"@"``
    (hunk header). Identical inputs produce an empty list.
    """
    old_lines = old_text.splitlines()
    new_lines = new_text.splitlines()
    if old_lines == new_lines:
        return []

    chunks = list(difflib.unified_diff(old_lines, new_lines, lineterm="", n=context))
    # İlk iki satır ---/+++ başlıklarıdır; içerik satırı gibi görünseler de atılır.
    result: List[Tuple[str, str]] = []
    for chunk in chunks[2:]:
        tag = chunk[:1]
        if tag in (" ", "-", "+"):
            result.append((tag, chunk[1:]))
        else:
            result.append(("@", chunk))
    return result


class EditType(Enum):
    """Type of edit operation."""

    USER_INSERT = "user_insert"
    USER_DELETE = "user_delete"
    USER_REPLACE = "user_replace"
    MODEL_INSERT = "model_insert"
    MODEL_DELETE = "model_delete"
    MODEL_REPLACE = "model_replace"


@dataclass
class WorkspaceEdit:
    """Represents a single edit operation in workspace."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    edit_type: EditType = EditType.USER_INSERT
    position: int = 0
    old_text: str = ""
    new_text: str = ""
    author: str = "user"
    accepted: bool = True
    rejected: bool = False
    stale: bool = False
    # "Sona ekle" önerileri kullanıcı belgeyi düzenlese bile sona uygulanır.
    at_end: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "edit_type": self.edit_type.value,
            "position": self.position,
            "old_text": self.old_text,
            "new_text": self.new_text,
            "author": self.author,
            "accepted": self.accepted,
            "rejected": self.rejected,
            "stale": self.stale,
            "at_end": self.at_end,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkspaceEdit":
        edit = cls()
        edit.id = data["id"]
        edit.timestamp = datetime.fromisoformat(data["timestamp"])
        edit.edit_type = EditType(data["edit_type"])
        edit.position = data["position"]
        edit.old_text = data["old_text"]
        edit.new_text = data["new_text"]
        edit.author = data["author"]
        edit.accepted = data["accepted"]
        edit.rejected = data.get("rejected", False)
        edit.stale = data.get("stale", False)
        edit.at_end = data.get("at_end", False)
        return edit


@dataclass
class WorkspaceVersion:
    """Represents a version of the workspace content."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    content: str = ""
    edit_ids: List[str] = field(default_factory=list)
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "content": self.content,
            "edit_ids": self.edit_ids,
            "description": self.description,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WorkspaceVersion":
        version = cls()
        version.id = data["id"]
        version.timestamp = datetime.fromisoformat(data["timestamp"])
        version.content = data["content"]
        version.edit_ids = data["edit_ids"]
        version.description = data["description"]
        return version


class WorkspaceBuffer:
    """Core workspace buffer for collaborative editing."""

    def __init__(self):
        self.content: str = ""
        self.edits: List[WorkspaceEdit] = []
        self.versions: List[WorkspaceVersion] = []
        self.current_version_id: Optional[str] = None

        self._create_version("Initial workspace")

    def get_content(self) -> str:
        return self.content

    def set_content(
        self, content: str, author: str = "user", description: str = "Content updated"
    ):
        old_content = self.content
        self.content = content

        edit = WorkspaceEdit(
            edit_type=EditType.USER_REPLACE if author == "user" else EditType.MODEL_REPLACE,
            position=0,
            old_text=old_content,
            new_text=content,
            author=author,
        )
        self.edits.append(edit)
        self._create_version(description, [edit.id])
        return edit

    def insert_text(self, position: int, text: str, author: str = "user") -> WorkspaceEdit:
        if position < 0 or position > len(self.content):
            position = len(self.content)

        self.content = self.content[:position] + text + self.content[position:]

        edit = WorkspaceEdit(
            edit_type=EditType.USER_INSERT if author == "user" else EditType.MODEL_INSERT,
            position=position,
            new_text=text,
            author=author,
        )
        self.edits.append(edit)
        self._create_version(f"Inserted text at position {position}", [edit.id])
        return edit

    def delete_text(self, start: int, end: int, author: str = "user") -> Optional[WorkspaceEdit]:
        if start < 0:
            start = 0
        if end > len(self.content):
            end = len(self.content)
        if start >= end:
            return None

        deleted_text = self.content[start:end]
        self.content = self.content[:start] + self.content[end:]

        edit = WorkspaceEdit(
            edit_type=EditType.USER_DELETE if author == "user" else EditType.MODEL_DELETE,
            position=start,
            old_text=deleted_text,
            author=author,
        )
        self.edits.append(edit)
        self._create_version(f"Deleted text from {start} to {end}", [edit.id])
        return edit

    def replace_text(self, start: int, end: int, text: str, author: str = "user") -> WorkspaceEdit:
        if start < 0:
            start = 0
        if end > len(self.content):
            end = len(self.content)
        if start > end:
            start, end = end, start

        old_text = self.content[start:end]
        self.content = self.content[:start] + text + self.content[end:]

        edit = WorkspaceEdit(
            edit_type=EditType.USER_REPLACE if author == "user" else EditType.MODEL_REPLACE,
            position=start,
            old_text=old_text,
            new_text=text,
            author=author,
        )
        self.edits.append(edit)
        self._create_version(f"Replaced text from {start} to {end} with '{text}'", [edit.id])
        return edit

    def suggest_edit(
        self,
        start: int,
        end: int,
        text: str,
        description: str = "",
        *,
        at_end: bool = False,
    ) -> WorkspaceEdit:
        if start < 0:
            start = 0
        if end > len(self.content):
            end = len(self.content)
        if start > end:
            start, end = end, start

        old_text = self.content[start:end]

        # Aynı öneri tekrar üretildiğinde (ör. model aynı yanıtı döndürdüğünde)
        # listeye ikinci bir kopya eklemek yerine mevcut öneri döndürülür.
        for existing in self.get_pending_suggestions():
            if existing.old_text == old_text and existing.new_text == text:
                return existing

        edit = WorkspaceEdit(
            edit_type=EditType.MODEL_INSERT if not old_text else EditType.MODEL_REPLACE,
            position=start,
            old_text=old_text,
            new_text=text,
            author="model",
            accepted=False,
            at_end=at_end,
        )
        self.edits.append(edit)
        return edit

    def _suggestion_is_current(self, edit: WorkspaceEdit) -> bool:
        """Return False when the workspace changed after the suggestion was made."""
        end = edit.position + len(edit.old_text)
        if edit.position < 0 or end > len(self.content):
            edit.stale = True
            return False
        if self.content[edit.position:end] != edit.old_text:
            edit.stale = True
            return False
        return True

    def accept_suggestion(self, edit_id: str) -> bool:
        for edit in self.edits:
            if edit.id == edit_id and not edit.accepted:
                if edit.edit_type != EditType.MODEL_INSERT and not self._suggestion_is_current(edit):
                    return False

                if edit.edit_type == EditType.MODEL_INSERT:
                    position = (
                        len(self.content)
                        if edit.at_end
                        else max(0, min(edit.position, len(self.content)))
                    )
                    edit.position = position
                    self.content = (
                        self.content[:position]
                        + edit.new_text
                        + self.content[position:]
                    )
                elif edit.edit_type == EditType.MODEL_DELETE:
                    self.content = (
                        self.content[:edit.position]
                        + self.content[edit.position + len(edit.old_text):]
                    )
                elif edit.edit_type == EditType.MODEL_REPLACE:
                    self.content = (
                        self.content[:edit.position]
                        + edit.new_text
                        + self.content[edit.position + len(edit.old_text):]
                    )

                edit.accepted = True
                self._create_version(
                    f"Accepted model suggestion: {edit.new_text[:50]}...",
                    [edit.id],
                )
                return True
        return False

    def reject_suggestion(self, edit_id: str) -> bool:
        for edit in self.edits:
            if edit.id == edit_id and not edit.accepted and not edit.rejected:
                edit.rejected = True
                self._create_version(
                    f"Rejected model suggestion: {edit.new_text[:50]}...",
                    [edit.id],
                )
                return True
        return False

    def get_pending_suggestions(self) -> List[WorkspaceEdit]:
        return [
            edit
            for edit in self.edits
            if edit.author == "model"
            and edit.accepted is False
            and not edit.rejected
            and not edit.stale
        ]

    def get_edit_history(self, limit: int = 50) -> List[WorkspaceEdit]:
        return self.edits[-limit:] if limit > 0 else self.edits

    def get_version_history(self) -> List[WorkspaceVersion]:
        return self.versions

    def restore_version(self, version_id: str) -> bool:
        for version in self.versions:
            if version.id == version_id:
                self.content = version.content
                self.current_version_id = version_id
                self._create_version(f"Restored to version: {version.description}")
                return True
        return False

    def _create_version(self, description: str, edit_ids: Optional[List[str]] = None):
        version = WorkspaceVersion(
            content=self.content,
            edit_ids=edit_ids or [],
            description=description,
        )
        self.versions.append(version)
        self.current_version_id = version.id

        if len(self.versions) > 100:
            self.versions = self.versions[-100:]

    def get_stats(self) -> Dict[str, Any]:
        user_edits = len([e for e in self.edits if e.author == "user"])
        model_edits = len([e for e in self.edits if e.author == "model"])
        pending_suggestions = len(self.get_pending_suggestions())

        return {
            "content_length": len(self.content),
            "total_edits": len(self.edits),
            "user_edits": user_edits,
            "model_edits": model_edits,
            "pending_suggestions": pending_suggestions,
            "versions": len(self.versions),
            "last_modified": self.edits[-1].timestamp if self.edits else None,
        }

    def export_session(self) -> Dict[str, Any]:
        return {
            "content": self.content,
            "edits": [edit.to_dict() for edit in self.edits],
            "versions": [version.to_dict() for version in self.versions],
            "stats": self.get_stats(),
        }

    def import_session(self, data: Dict[str, Any]) -> bool:
        try:
            self.content = data.get("content", "")
            self.edits = [
                WorkspaceEdit.from_dict(edit_data)
                for edit_data in data.get("edits", [])
            ]
            self.versions = [
                WorkspaceVersion.from_dict(version_data)
                for version_data in data.get("versions", [])
            ]

            if self.versions:
                self.current_version_id = self.versions[-1].id
            else:
                self._create_version("Imported workspace")

            return True
        except Exception:
            return False

    def clear_all(self):
        self.set_content("", "user", "Workspace cleared")
