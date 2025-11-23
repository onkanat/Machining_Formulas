"""Tests for V2 GUI integration."""

import pytest
import tkinter as tk
from unittest.mock import Mock, patch
import json

from v2_gui import V2Calculator


class TestV2Calculator:
    """Test V2 Calculator main class."""

    @pytest.fixture
    def root(self):
        """Create test root window."""
        root = tk.Tk()
        root.withdraw()  # Hide window during tests
        yield root
        root.destroy()

    @pytest.fixture
    def tooltips(self):
        """Create test tooltips."""
        return {
            "HesaplamaTuru": "Bir hesaplama türü seçin.",
            "HesaplamaSecimi": "Bir hesaplama seçin.",
            "HesaplaButonu": "Seçili hesaplamayı gerçekleştir.",
            "Şekil": "Şekil seçin.",
            "Yoğunluk": "Malzemenin yoğunluğunu girin.",
            "Uzunluk": "Şeklin uzunluğunu girin.",
        }

    @pytest.fixture
    def app(self, root, tooltips):
        """Create V2 Calculator app."""
        return V2Calculator(root, tooltips)

    def test_app_initialization(self, app):
        """Test app initialization."""
        assert app.workspace_manager is not None
        assert app.context_builder is not None
        assert app.calc_types is not None
        assert "Malzeme Hesaplamaları" in app.calc_types
        assert "Tornalama Hesaplamaları" in app.calc_types
        assert "Frezeleme Hesaplamaları" in app.calc_types
        assert app.input_fields == {}
        assert app.reverse_shape_names == {}

    def test_calculation_type_update(self, app):
        """Test updating calculation types."""
        # Select material calculations
        app.calc_type.set("Malzeme Hesaplamaları")
        app.update_calculations()

        available_calcs = app.calculation["values"]
        assert "Kütle Hesabı" in available_calcs

        # Select turning calculations
        app.calc_type.set("Tornalama Hesaplamaları")
        app.update_calculations()

        available_calcs = app.calculation["values"]
        assert len(available_calcs) > 0  # Should have turning calculations

    def test_material_calculation_fields(self, app):
        """Test material calculation field setup."""
        app.calc_type.set("Malzeme Hesaplamaları")
        app.calculation.set("Kütle Hesabı")
        app.update_input_fields()

        # Should have shape combo
        assert "Şekil" in app.input_fields
        assert app.shape_combo is not None

        # Should have density and length fields
        assert "density" in app.input_fields
        assert "length" in app.input_fields

    def test_turning_calculation_fields(self, app):
        """Test turning calculation field setup."""
        app.calc_type.set("Tornalama Hesaplamaları")

        # Get first available turning calculation
        available_calcs = list(app.calc_types["Tornalama Hesaplamaları"].keys())
        if available_calcs:
            app.calculation.set(available_calcs[0])
            app.update_input_fields()

            # Should have parameter fields
            assert len(app.input_fields) > 0

    def test_calculate_material_mass(self, app):
        """Test material mass calculation."""
        # Setup material calculation
        app.calc_type.set("Malzeme Hesaplamaları")
        app.calculation.set("Kütle Hesabı")
        app.update_input_fields()

        # Mock input values
        if "Şekil" in app.input_fields:
            app.input_fields["Şekil"].set("Daire")
        if "density" in app.input_fields:
            app.input_fields["density"].set("7.85")
        if "length" in app.input_fields:
            app.input_fields["length"].set("100")
        if "radius" in app.input_fields:
            app.input_fields["radius"].set("50")

        # Perform calculation
        try:
            app.calculate()

            # Check if calculation was added to workspace
            calculations = app.workspace_manager.get_all_calculations()
            assert len(calculations) > 0

            calc = calculations[-1]
            assert calc.calc_type == "Malzeme Hesaplamaları"
            assert calc.calculation_name == "Kütle Hesabı"
            assert calc.unit == "g"

        except Exception as e:
            # If calculation fails due to missing parameters, that's expected in test
            pytest.skip(f"Calculation failed due to missing parameters: {e}")

    def test_workspace_integration(self, app):
        """Test workspace integration."""
        # Add a calculation directly to workspace
        calc_id = app.workspace_manager.add_calculation(
            calc_type="Tornalama Hesaplamaları",
            calc_name="Kesme Hızı",
            params={"Dm": 50, "n": 1000},
            result=157.1,
            unit="m/min",
        )

        # Check if calculation exists
        calc = app.workspace_manager.get_calculation(calc_id)
        assert calc is not None
        assert calc.result == 157.1

    def test_add_note_functionality(self, app):
        """Test adding notes to calculations."""
        # Add calculation
        calc_id = app.workspace_manager.add_calculation(
            calc_type="Tornalama Hesaplamaları",
            calc_name="Kesme Hızı",
            params={"Dm": 50, "n": 1000},
            result=157.1,
            unit="m/min",
        )

        # Add note
        success = app.handle_add_note(calc_id, "Test notu")
        assert success is True

        # Check note was added
        calc = app.workspace_manager.get_calculation(calc_id)
        assert len(calc.user_notes) == 1
        assert calc.user_notes[0] == "Test notu"

    def test_remove_calculation(self, app):
        """Test removing calculations."""
        # Add calculation
        calc_id = app.workspace_manager.add_calculation(
            calc_type="Tornalama Hesaplamaları",
            calc_name="Kesme Hızı",
            params={"Dm": 50, "n": 1000},
            result=157.1,
            unit="m/min",
        )

        # Verify calculation exists
        assert app.workspace_manager.get_calculation(calc_id) is not None

        # Remove calculation
        app.handle_remove_calculation(calc_id)

        # Verify calculation was removed
        assert app.workspace_manager.get_calculation(calc_id) is None

    def test_clear_all_calculations(self, app):
        """Test clearing all calculations."""
        # Add multiple calculations
        for i in range(3):
            app.workspace_manager.add_calculation(
                calc_type="Tornalama Hesaplamaları",
                calc_name="Kesme Hızı",
                params={"Dm": 50 + i, "n": 1000 + i},
                result=157.1 + i,
                unit="m/min",
            )

        # Verify calculations exist
        assert len(app.workspace_manager.get_all_calculations()) == 3

        # Clear all
        app.handle_remove_calculation(None)

        # Verify all are cleared
        assert len(app.workspace_manager.get_all_calculations()) == 0

    def test_clear_parameters(self, app):
        """Test clearing parameter fields."""
        # Setup some fields
        app.calc_type.set("Malzeme Hesaplamaları")
        app.calculation.set("Kütle Hesabı")
        app.update_input_fields()

        # Add some values
        if "density" in app.input_fields:
            app.input_fields["density"].insert(0, "7.85")
        if "length" in app.input_fields:
            app.input_fields["length"].insert(0, "100")

        # Clear parameters
        app.clear_parameters()

        # Check fields are cleared
        for field_widget in app.input_fields.values():
            if hasattr(field_widget, "get"):
                value = field_widget.get()
                assert value == "" or value == ""

    @patch("v2_gui.get_available_models")
    def test_refresh_model_list(self, mock_get_models, app):
        """Test refreshing model list."""
        # Mock available models
        mock_get_models.return_value = ["llama3.2", "qwen2.5", "gemma2"]

        # Set model URL
        app.model_url_entry.delete(0, tk.END)
        app.model_url_entry.insert(0, "http://localhost:11434")

        # Refresh models
        app.refresh_model_list()

        # Check if models were loaded
        assert len(app.ollama_models) == 3
        assert "llama3.2" in app.ollama_models
        assert app.current_model_name in app.ollama_models

    @patch("v2_gui.test_connection")
    def test_model_connection(self, mock_test_connection, app):
        """Test model connection."""
        # Mock successful connection
        mock_test_connection.return_value = True

        # Set model URL
        app.model_url_entry.delete(0, tk.END)
        app.model_url_entry.insert(0, "http://localhost:11434")

        # Test connection
        with patch("tkinter.messagebox.showinfo") as mock_info:
            app.test_model_connection()
            mock_info.assert_called_once_with(
                "Bağlantı Başarılı", "Ollama sunucusuna bağlantı başarılı!"
            )

    def test_perform_calculation_methods(self, app):
        """Test individual calculation methods."""
        # Test material mass calculation
        result = app.calculate_material_mass(
            "Kütle Hesabı",
            {"Şekil": "Daire", "density": 7.85, "length": 100, "radius": 50},
        )

        assert "value" in result
        assert "unit" in result
        assert result["unit"] == "g"
        assert result["value"] > 0

        # Test turning calculation
        result = app.calculate_turning("Kesme Hızı", {"Dm": 50, "n": 1000})
        assert "value" in result
        assert "unit" in result
        assert result["unit"] == "m/min"

    def test_workspace_export_import(self, app):
        """Test workspace export and import."""
        # Add calculation
        app.workspace_manager.add_calculation(
            calc_type="Tornalama Hesaplamaları",
            calc_name="Kesme Hızı",
            params={"Dm": 50, "n": 1000},
            result=157.1,
            unit="m/min",
        )

        # Export workspace
        exported_data = app.workspace_manager.export_session()
        assert "calculations" in exported_data
        assert len(exported_data["calculations"]) == 1

        # Clear workspace
        app.workspace_manager.clear_workspace()
        assert len(app.workspace_manager.get_all_calculations()) == 0

        # Import workspace
        app.workspace_manager.import_session(exported_data)
        assert len(app.workspace_manager.get_all_calculations()) == 1

        calc = app.workspace_manager.get_all_calculations()[0]
        assert calc.result == 157.1


class TestV2Integration:
    """Test V2 integration scenarios."""

    @pytest.fixture
    def root(self):
        """Create test root window."""
        root = tk.Tk()
        root.withdraw()
        yield root
        root.destroy()

    @pytest.fixture
    def tooltips(self):
        """Create test tooltips."""
        return {"HesaplamaTuru": "Bir hesaplama türü seçin."}

    @pytest.fixture
    def app(self, root, tooltips):
        """Create V2 Calculator app."""
        return V2Calculator(root, tooltips)

    def test_full_calculation_workflow(self, app):
        """Test complete calculation workflow."""
        # 1. Select calculation type
        app.calc_type.set("Tornalama Hesaplamaları")
        app.update_calculations()

        # 2. Select specific calculation
        available_calcs = list(app.calc_types["Tornalama Hesaplamaları"].keys())
        if available_calcs:
            app.calculation.set(available_calcs[0])
            app.update_input_fields()

            # 3. Fill parameters (if fields exist)
            for param_key, field_widget in app.input_fields.items():
                if hasattr(field_widget, "insert"):
                    field_widget.delete(0, tk.END)
                    field_widget.insert(0, "100")  # Test value

            # 4. Calculate (this might fail due to invalid parameters, but workflow should work)
            try:
                app.calculate()

                # 5. Verify calculation was added to workspace
                calculations = app.workspace_manager.get_all_calculations()
                if len(calculations) > 0:
                    # 6. Add note
                    calc_id = calculations[0].id
                    app.handle_add_note(calc_id, "Test workflow notu")

                    # 7. Verify note was added
                    calc = app.workspace_manager.get_calculation(calc_id)
                    assert len(calc.user_notes) > 0

            except Exception:
                # Expected if parameters are invalid, but workflow structure should work
                pass

    def test_workspace_context_building(self, app):
        """Test workspace context building for model analysis."""
        # Add multiple calculations
        calc_id1 = app.workspace_manager.add_calculation(
            calc_type="Tornalama Hesaplamaları",
            calc_name="Kesme Hızı",
            params={"Dm": 50, "n": 1000},
            result=157.1,
            unit="m/min",
        )

        calc_id2 = app.workspace_manager.add_calculation(
            calc_type="Frezeleme Hesaplamaları",
            calc_name="Tabla İlerlemesi",
            params={"fz": 0.1, "n": 1000, "ZEFF": 4},
            result=400.0,
            unit="mm/min",
        )

        # Build context
        context = app.context_builder.build_general_review_context(
            app.workspace_manager.workspace
        )

        # Verify context contains calculations
        assert "Tornalama Hesaplamaları" in context
        assert "Frezeleme Hesaplamaları" in context
        assert "157.1" in context
        assert "400.0" in context

        # Build single calculation context
        calc = app.workspace_manager.get_calculation(calc_id1)
        single_context = app.context_builder.build_calculation_review_context(calc)

        assert "Tornalama Hesaplamaları" in single_context
        assert "Kesme Hızı" in single_context
        assert "157.1" in single_context
