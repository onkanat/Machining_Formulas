"""Tests for V2 workspace manager functionality."""

import pytest
from datetime import datetime
from workspace_manager import WorkspaceManager, CalculationEntry, Workspace


class TestCalculationEntry:
    """Test CalculationEntry class."""

    def test_calculation_entry_creation(self):
        """Test creating a calculation entry."""
        calc = CalculationEntry(
            id="test-123",
            timestamp=datetime.now(),
            calc_type="Tornalama Hesaplamaları",
            calculation_name="Kesme Hızı",
            parameters={"Dm": 50, "n": 1000},
            result=157.1,
            unit="m/min",
        )

        assert calc.id == "test-123"
        assert calc.calc_type == "Tornalama Hesaplamaları"
        assert calc.calculation_name == "Kesme Hızı"
        assert calc.parameters == {"Dm": 50, "n": 1000}
        assert calc.result == 157.1
        assert calc.unit == "m/min"
        assert calc.user_notes == []
        assert calc.model_comments == []

    def test_add_user_note(self):
        """Test adding user notes."""
        calc = CalculationEntry(
            id="test-123",
            timestamp=datetime.now(),
            calc_type="Tornalama Hesaplamaları",
            calculation_name="Kesme Hızı",
            parameters={"Dm": 50, "n": 1000},
            result=157.1,
            unit="m/min",
        )

        calc.add_user_note("Bu değer yüksek görünüyor")
        assert len(calc.user_notes) == 1
        assert calc.user_notes[0] == "Bu değer yüksek görünüyor"

        calc.add_user_note("İkinci not")
        assert len(calc.user_notes) == 2
        assert calc.user_notes[1] == "İkinci not"

    def test_add_model_comment(self):
        """Test adding model comments."""
        calc = CalculationEntry(
            id="test-123",
            timestamp=datetime.now(),
            calc_type="Tornalama Hesaplamaları",
            calculation_name="Kesme Hızı",
            parameters={"Dm": 50, "n": 1000},
            result=157.1,
            unit="m/min",
        )

        calc.add_model_comment("Değerler doğru")
        assert len(calc.model_comments) == 1
        assert calc.model_comments[0] == "Değerler doğru"

    def test_to_dict(self):
        """Test serialization to dictionary."""
        calc = CalculationEntry(
            id="test-123",
            timestamp=datetime.now(),
            calc_type="Tornalama Hesaplamaları",
            calculation_name="Kesme Hızı",
            parameters={"Dm": 50, "n": 1000},
            result=157.1,
            unit="m/min",
            user_notes=["Test notu"],
            model_comments=["Model yorumu"],
        )

        data = calc.to_dict()

        assert data["id"] == "test-123"
        assert data["calc_type"] == "Tornalama Hesaplamaları"
        assert data["calculation_name"] == "Kesme Hızı"
        assert data["parameters"] == {"Dm": 50, "n": 1000}
        assert data["result"] == 157.1
        assert data["unit"] == "m/min"
        assert data["user_notes"] == ["Test notu"]
        assert data["model_comments"] == ["Model yorumu"]
        assert "timestamp" in data

    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            "id": "test-123",
            "timestamp": datetime.now().isoformat(),
            "calc_type": "Tornalama Hesaplamaları",
            "calculation_name": "Kesme Hızı",
            "parameters": {"Dm": 50, "n": 1000},
            "result": 157.1,
            "unit": "m/min",
            "user_notes": ["Test notu"],
            "model_comments": ["Model yorumu"],
        }

        calc = CalculationEntry.from_dict(data)

        assert calc.id == "test-123"
        assert calc.calc_type == "Tornalama Hesaplamaları"
        assert calc.calculation_name == "Kesme Hızı"
        assert calc.parameters == {"Dm": 50, "n": 1000}
        assert calc.result == 157.1
        assert calc.unit == "m/min"
        assert calc.user_notes == ["Test notu"]
        assert calc.model_comments == ["Model yorumu"]


class TestWorkspace:
    """Test Workspace class."""

    def test_workspace_creation(self):
        """Test creating an empty workspace."""
        workspace = Workspace()

        assert workspace.calculations == []
        assert workspace.session_metadata == {}
        assert workspace.version == "2.0"
        assert isinstance(workspace.last_updated, datetime)

    def test_add_calculation(self):
        """Test adding a calculation to workspace."""
        workspace = Workspace()

        calc_id = workspace.add_calculation(
            calc_type="Tornalama Hesaplamaları",
            calc_name="Kesme Hızı",
            params={"Dm": 50, "n": 1000},
            result=157.1,
            unit="m/min",
        )

        assert len(workspace.calculations) == 1
        assert calc_id is not None
        assert isinstance(calc_id, str)

        calc = workspace.calculations[0]
        assert calc.calc_type == "Tornalama Hesaplamaları"
        assert calc.calculation_name == "Kesme Hızı"
        assert calc.parameters == {"Dm": 50, "n": 1000}
        assert calc.result == 157.1
        assert calc.unit == "m/min"

    def test_get_calculation(self):
        """Test getting calculation by ID."""
        workspace = Workspace()

        calc_id = workspace.add_calculation(
            calc_type="Tornalama Hesaplamaları",
            calc_name="Kesme Hızı",
            params={"Dm": 50, "n": 1000},
            result=157.1,
            unit="m/min",
        )

        calc = workspace.get_calculation(calc_id)
        assert calc is not None
        assert calc.id == calc_id

        # Test non-existent ID
        non_existent = workspace.get_calculation("non-existent")
        assert non_existent is None

    def test_add_user_note(self):
        """Test adding user note to calculation."""
        workspace = Workspace()

        calc_id = workspace.add_calculation(
            calc_type="Tornalama Hesaplamaları",
            calc_name="Kesme Hızı",
            params={"Dm": 50, "n": 1000},
            result=157.1,
            unit="m/min",
        )

        success = workspace.add_user_note(calc_id, "Test notu")
        assert success is True

        calc = workspace.get_calculation(calc_id)
        assert len(calc.user_notes) == 1
        assert calc.user_notes[0] == "Test notu"

        # Test non-existent calculation
        success = workspace.add_user_note("non-existent", "Test notu")
        assert success is False

    def test_add_model_comment(self):
        """Test adding model comment to calculation."""
        workspace = Workspace()

        calc_id = workspace.add_calculation(
            calc_type="Tornalama Hesaplamaları",
            calc_name="Kesme Hızı",
            params={"Dm": 50, "n": 1000},
            result=157.1,
            unit="m/min",
        )

        success = workspace.add_model_comment(calc_id, "Model yorumu")
        assert success is True

        calc = workspace.get_calculation(calc_id)
        assert len(calc.model_comments) == 1
        assert calc.model_comments[0] == "Model yorumu"

    def test_remove_calculation(self):
        """Test removing calculation."""
        workspace = Workspace()

        calc_id = workspace.add_calculation(
            calc_type="Tornalama Hesaplamaları",
            calc_name="Kesme Hızı",
            params={"Dm": 50, "n": 1000},
            result=157.1,
            unit="m/min",
        )

        assert len(workspace.calculations) == 1

        success = workspace.remove_calculation(calc_id)
        assert success is True
        assert len(workspace.calculations) == 0

        # Test removing non-existent calculation
        success = workspace.remove_calculation("non-existent")
        assert success is False

    def test_clear_all(self):
        """Test clearing all calculations."""
        workspace = Workspace()

        # Add multiple calculations
        for i in range(3):
            workspace.add_calculation(
                calc_type="Tornalama Hesaplamaları",
                calc_name="Kesme Hızı",
                params={"Dm": 50 + i, "n": 1000 + i},
                result=157.1 + i,
                unit="m/min",
            )

        assert len(workspace.calculations) == 3

        workspace.clear_all()
        assert len(workspace.calculations) == 0

    def test_get_full_context(self):
        """Test getting full context as text."""
        workspace = Workspace()

        # Empty workspace
        context = workspace.get_full_context()
        assert "henüz hesaplama bulunmuyor" in context

        # Add calculation
        workspace.add_calculation(
            calc_type="Tornalama Hesaplamaları",
            calc_name="Kesme Hızı",
            params={"Dm": 50, "n": 1000},
            result=157.1,
            unit="m/min",
        )

        context = workspace.get_full_context()
        assert "Tornalama Hesaplamaları" in context
        assert "Kesme Hızı" in context
        assert "157.1" in context
        assert "m/min" in context

    def test_workspace_serialization(self):
        """Test workspace serialization and deserialization."""
        workspace = Workspace()

        # Add calculation with notes and comments
        calc_id = workspace.add_calculation(
            calc_type="Tornalama Hesaplamaları",
            calc_name="Kesme Hızı",
            params={"Dm": 50, "n": 1000},
            result=157.1,
            unit="m/min",
        )

        workspace.add_user_note(calc_id, "Test notu")
        workspace.add_model_comment(calc_id, "Model yorumu")

        # Serialize
        data = workspace.to_dict()
        assert data["version"] == "2.0"
        assert len(data["calculations"]) == 1
        assert "last_updated" in data

        # Deserialize
        new_workspace = Workspace.from_dict(data)
        assert len(new_workspace.calculations) == 1
        assert new_workspace.version == "2.0"

        calc = new_workspace.calculations[0]
        assert calc.calc_type == "Tornalama Hesaplamaları"
        assert calc.user_notes == ["Test notu"]
        assert calc.model_comments == ["Model yorumu"]


class TestWorkspaceManager:
    """Test WorkspaceManager class."""

    def test_workspace_manager_creation(self):
        """Test creating workspace manager."""
        manager = WorkspaceManager()

        assert isinstance(manager.workspace, Workspace)
        assert len(manager.get_all_calculations()) == 0

    def test_manager_add_calculation(self):
        """Test adding calculation through manager."""
        manager = WorkspaceManager()

        calc_id = manager.add_calculation(
            calc_type="Tornalama Hesaplamaları",
            calc_name="Kesme Hızı",
            params={"Dm": 50, "n": 1000},
            result=157.1,
            unit="m/min",
        )

        assert calc_id is not None
        assert len(manager.get_all_calculations()) == 1

        calc = manager.get_calculation(calc_id)
        assert calc is not None
        assert calc.result == 157.1

    def test_manager_session_stats(self):
        """Test getting session statistics."""
        manager = WorkspaceManager()

        # Empty stats
        stats = manager.get_session_stats()
        assert stats["total_calculations"] == 0
        assert stats["calculation_types"] == {}

        # Add calculations
        manager.add_calculation(
            calc_type="Tornalama Hesaplamaları",
            calc_name="Kesme Hızı",
            params={"Dm": 50, "n": 1000},
            result=157.1,
            unit="m/min",
        )

        manager.add_calculation(
            calc_type="Frezeleme Hesaplamaları",
            calc_name="Tabla İlerlemesi",
            params={"fz": 0.1, "n": 1000, "ZEFF": 4},
            result=400.0,
            unit="mm/min",
        )

        manager.add_calculation(
            calc_type="Tornalama Hesaplamaları",
            calc_name="İş Mili Hızı",
            params={"Vc": 200, "Dm": 50},
            result=1273.2,
            unit="rpm",
        )

        stats = manager.get_session_stats()
        assert stats["total_calculations"] == 3
        assert stats["calculation_types"]["Tornalama Hesaplamaları"] == 2
        assert stats["calculation_types"]["Frezeleme Hesaplamaları"] == 1
        assert "last_updated" in stats
        assert stats["version"] == "2.0"

    def test_manager_export_import(self):
        """Test exporting and importing sessions."""
        manager = WorkspaceManager()

        # Add calculation
        calc_id = manager.add_calculation(
            calc_type="Tornalama Hesaplamaları",
            calc_name="Kesme Hızı",
            params={"Dm": 50, "n": 1000},
            result=157.1,
            unit="m/min",
        )

        manager.add_user_note(calc_id, "Test notu")

        # Export
        exported_data = manager.export_session()
        assert exported_data["version"] == "2.0"
        assert len(exported_data["calculations"]) == 1

        # Clear and import
        manager.clear_workspace()
        assert len(manager.get_all_calculations()) == 0

        manager.import_session(exported_data)
        assert len(manager.get_all_calculations()) == 1

        calc = manager.get_all_calculations()[0]
        assert calc.user_notes == ["Test notu"]
        assert calc.result == 157.1
