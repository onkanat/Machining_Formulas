"""Workspace management for V2 single-page interaction system.

This module provides the core data structures and management logic
for the V2 workspace-based calculation system.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class CalculationEntry:
    """Represents a single calculation in the workspace."""

    id: str
    timestamp: datetime
    calc_type: str  # "Tornalama Hesaplamaları"
    calculation_name: str  # "Kesme Hızı"
    parameters: Dict[str, Any]  # {"Dm": 50, "n": 1000}
    result: float  # 157.1
    unit: str  # "m/min"
    user_notes: List[str] = field(default_factory=list)  # ["Bu değer yüksek görünüyor"]
    model_comments: List[str] = field(
        default_factory=list
    )  # ["Değerler doğru, kesme hızı uygun"]

    def add_user_note(self, note: str) -> None:
        """Add a user note to this calculation."""
        self.user_notes.append(note)

    def add_model_comment(self, comment: str) -> None:
        """Add a model comment to this calculation."""
        self.model_comments.append(comment)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "calc_type": self.calc_type,
            "calculation_name": self.calculation_name,
            "parameters": self.parameters,
            "result": self.result,
            "unit": self.unit,
            "user_notes": self.user_notes,
            "model_comments": self.model_comments,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CalculationEntry":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            calc_type=data["calc_type"],
            calculation_name=data["calculation_name"],
            parameters=data["parameters"],
            result=data["result"],
            unit=data["unit"],
            user_notes=data.get("user_notes", []),
            model_comments=data.get("model_comments", []),
        )


@dataclass
class Workspace:
    """Main workspace container for V2 system."""

    calculations: List[CalculationEntry] = field(default_factory=list)
    session_metadata: Dict[str, Any] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=datetime.now)
    version: str = "2.0"

    def add_calculation(
        self,
        calc_type: str,
        calc_name: str,
        params: Dict[str, Any],
        result: float,
        unit: str,
    ) -> str:
        """Add a new calculation and return its ID."""
        calc_id = str(uuid.uuid4())
        entry = CalculationEntry(
            id=calc_id,
            timestamp=datetime.now(),
            calc_type=calc_type,
            calculation_name=calc_name,
            parameters=params,
            result=result,
            unit=unit,
        )
        self.calculations.append(entry)
        self.last_updated = datetime.now()
        return calc_id

    def get_calculation(self, calc_id: str) -> Optional[CalculationEntry]:
        """Get calculation by ID."""
        for calc in self.calculations:
            if calc.id == calc_id:
                return calc
        return None

    def add_user_note(self, calc_id: str, note: str) -> bool:
        """Add user note to calculation. Returns True if successful."""
        calc = self.get_calculation(calc_id)
        if calc:
            calc.add_user_note(note)
            self.last_updated = datetime.now()
            return True
        return False

    def add_model_comment(self, calc_id: str, comment: str) -> bool:
        """Add model comment to calculation. Returns True if successful."""
        calc = self.get_calculation(calc_id)
        if calc:
            calc.add_model_comment(comment)
            self.last_updated = datetime.now()
            return True
        return False

    def edit_calculation(self, calc_id: str, new_params: Dict[str, Any]) -> bool:
        """Edit calculation parameters. Returns True if successful."""
        for calc in self.calculations:
            if calc.id == calc_id:
                calc.parameters = new_params
                self.last_updated = datetime.now()
                return True
        return False

    def remove_calculation(self, calc_id: str) -> bool:
        """Remove calculation by ID. Returns True if successful."""
        for i, calc in enumerate(self.calculations):
            if calc.id == calc_id:
                del self.calculations[i]
                self.last_updated = datetime.now()
                return True
        return False

    def clear_all(self) -> None:
        """Clear all calculations."""
        self.calculations.clear()
        self.last_updated = datetime.now()

    def get_full_context(self) -> str:
        """Get full workspace context as text for model analysis."""
        if not self.calculations:
            return "Bu çalışma alanında henüz hesaplama bulunmuyor."

        context = (
            f"Çalışma Alanı İçeriği (Toplam {len(self.calculations)} hesaplama):\n\n"
        )

        for i, calc in enumerate(self.calculations, 1):
            context += f"HESAPLAMA #{i}:\n"
            context += f"Tür: {calc.calc_type}\n"
            context += f"İşlem: {calc.calculation_name}\n"
            context += f"Parametreler: {calc.parameters}\n"
            context += f"Sonuç: {calc.result} {calc.unit}\n"

            if calc.user_notes:
                context += f"Kullanıcı Notları:\n"
                for note in calc.user_notes:
                    context += f"  - {note}\n"

            if calc.model_comments:
                context += f"Model Yorumları:\n"
                for comment in calc.model_comments:
                    context += f"  - {comment}\n"

            context += "\n" + "-" * 50 + "\n\n"

        return context

    def to_dict(self) -> Dict[str, Any]:
        """Convert workspace to dictionary for export."""
        return {
            "calculations": [calc.to_dict() for calc in self.calculations],
            "session_metadata": self.session_metadata,
            "last_updated": self.last_updated.isoformat(),
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Workspace":
        """Create workspace from dictionary."""
        workspace = cls(
            session_metadata=data.get("session_metadata", {}),
            version=data.get("version", "2.0"),
        )

        if "last_updated" in data:
            workspace.last_updated = datetime.fromisoformat(data["last_updated"])

        if "calculations" in data:
            workspace.calculations = [
                CalculationEntry.from_dict(calc_data)
                for calc_data in data["calculations"]
            ]

        return workspace


class WorkspaceManager:
    """Manager class for workspace operations in V2 system."""

    def __init__(self):
        self.workspace = Workspace()

    def add_calculation(
        self,
        calc_type: str,
        calc_name: str,
        params: Dict[str, Any],
        result: float,
        unit: str,
    ) -> str:
        """Add new calculation to workspace."""
        return self.workspace.add_calculation(
            calc_type, calc_name, params, result, unit
        )

    def get_calculation(self, calc_id: str) -> Optional[CalculationEntry]:
        """Get calculation by ID."""
        return self.workspace.get_calculation(calc_id)

    def add_user_note(self, calc_id: str, note: str) -> bool:
        """Add user note to calculation."""
        return self.workspace.add_user_note(calc_id, note)

    def add_model_comment(self, calc_id: str, comment: str) -> bool:
        """Add model comment to calculation."""
        return self.workspace.add_model_comment(calc_id, comment)

    def edit_calculation(self, calc_id: str, new_params: Dict[str, Any]) -> bool:
        """Edit calculation parameters."""
        return self.workspace.edit_calculation(calc_id, new_params)

    def remove_calculation(self, calc_id: str) -> bool:
        """Remove calculation."""
        return self.workspace.remove_calculation(calc_id)

    def clear_workspace(self) -> None:
        """Clear all calculations."""
        self.workspace.clear_all()

    def get_all_calculations(self) -> List[CalculationEntry]:
        """Get all calculations."""
        return self.workspace.calculations.copy()

    def get_full_context(self) -> str:
        """Get full context for model analysis."""
        return self.workspace.get_full_context()

    def export_session(self) -> Dict[str, Any]:
        """Export session data."""
        return self.workspace.to_dict()

    def import_session(self, data: Dict[str, Any]) -> None:
        """Import session data."""
        self.workspace = Workspace.from_dict(data)

    def get_session_stats(self) -> Dict[str, Any]:
        """Get session statistics."""
        calc_types = {}
        for calc in self.workspace.calculations:
            calc_type = calc.calc_type
            calc_types[calc_type] = calc_types.get(calc_type, 0) + 1

        return {
            "total_calculations": len(self.workspace.calculations),
            "calculation_types": calc_types,
            "last_updated": self.workspace.last_updated,
            "version": self.workspace.version,
        }
