"""Tests for V2 model integration and context building."""

import pytest
from datetime import datetime
from workspace_manager import WorkspaceManager, CalculationEntry
from context_builder import ContextBuilder


class TestContextBuilder:
    """Test context builder functionality."""

    @pytest.fixture
    def context_builder(self):
        """Create context builder."""
        return ContextBuilder()

    @pytest.fixture
    def sample_workspace(self):
        """Create sample workspace with calculations."""
        workspace = WorkspaceManager()

        # Add turning calculation
        workspace.add_calculation(
            calc_type="Tornalama Hesaplamaları",
            calc_name="Kesme Hızı",
            params={"Dm": 50, "n": 1000},
            result=157.1,
            unit="m/min",
        )

        # Add material calculation
        workspace.add_calculation(
            calc_type="Malzeme Hesaplamaları",
            calc_name="Kütle Hesabı",
            params={
                "shape_key": "circle",
                "density": 7.85,
                "length": 100,
                "radius": 50,
            },
            result=6165.38,
            unit="g",
        )

        return workspace

    def test_system_prompt(self, context_builder):
        """Test system prompt generation."""
        assert context_builder.system_prompt is not None
        assert "mühendislik hesaplama asistanı" in context_builder.system_prompt
        assert len(context_builder.system_prompt) > 50

    def test_build_analysis_context_empty_workspace(self, context_builder):
        """Test building analysis context for empty workspace."""
        empty_workspace = WorkspaceManager()
        context = context_builder.build_analysis_context(empty_workspace.workspace)

        assert "henüz hesaplama bulunmuyor" in context
        assert context_builder.system_prompt in context

    def test_build_analysis_context_with_calculations(
        self, context_builder, sample_workspace
    ):
        """Test building analysis context with calculations."""
        context = context_builder.build_analysis_context(sample_workspace.workspace)

        assert context_builder.system_prompt in context
        assert "Tornalama Hesaplamaları" in context
        assert "Malzeme Hesaplamaları" in context
        assert "157.1" in context
        assert "6165.38" in context
        assert "m/min" in context
        assert "g" in context
        assert "analiz et" in context.lower()

    def test_build_calculation_review_context(self, context_builder):
        """Test building single calculation review context."""
        calc = CalculationEntry(
            id="test-123",
            timestamp=datetime.now(),
            calc_type="Tornalama Hesaplamaları",
            calculation_name="Kesme Hızı",
            parameters={"Dm": 50, "n": 1000},
            result=157.1,
            unit="m/min",
            user_notes=["Bu değer yüksek görünüyor"],
            model_comments=["Değerler doğru"],
        )

        context = context_builder.build_calculation_review_context(calc)

        assert "Tornalama Hesaplamaları" in context
        assert "Kesme Hızı" in context
        assert "157.1" in context
        assert "Bu değer yüksek görünüyor" in context
        assert "Değerler doğru" in context
        assert "incele" in context.lower()

    def test_build_general_review_context(self, context_builder, sample_workspace):
        """Test building general review context."""
        context = context_builder.build_general_review_context(
            sample_workspace.workspace
        )

        assert "Tornalama Hesaplamaları" in context
        assert "Malzeme Hesaplamaları" in context
        assert "Toplam Hesaplama: 2" in context
        assert "genel durumunu değerlendir" in context.lower()

    def test_build_comparison_context(self, context_builder, sample_workspace):
        """Test building comparison context."""
        calculations = sample_workspace.get_all_calculations()
        context = context_builder.build_comparison_context(calculations)

        assert "Karşılaştırılacak Hesaplamalar" in context
        assert "Tornalama Hesaplamaları" in context
        assert "Malzeme Hesaplamaları" in context
        assert "karşılaştır" in context.lower()

    def test_build_comparison_context_insufficient_calculations(self, context_builder):
        """Test comparison context with insufficient calculations."""
        workspace = WorkspaceManager()
        workspace.add_calculation(
            calc_type="Tornalama Hesaplamaları",
            calc_name="Kesme Hızı",
            params={"Dm": 50, "n": 1000},
            result=157.1,
            unit="m/min",
        )

        calculations = workspace.get_all_calculations()
        context = context_builder.build_comparison_context(calculations)

        assert "en az 2 hesaplama gerekli" in context

    def test_build_validation_context(self, context_builder):
        """Test building validation context."""
        calc = CalculationEntry(
            id="test-123",
            timestamp=datetime.now(),
            calc_type="Tornalama Hesaplamaları",
            calculation_name="Kesme Hızı",
            parameters={"Dm": 50, "n": 1000},
            result=157.1,
            unit="m/min",
        )

        expected_range = {"Dm": (10, 500), "n": (100, 10000)}
        context = context_builder.build_validation_context(calc, expected_range)

        assert "Doğrulanacak Hesaplama" in context
        assert "Tornalama Hesaplamaları" in context
        assert "157.1" in context
        assert "Beklenen Değer Aralıkları" in context
        assert "10 - 500" in context
        assert "100 - 10000" in context
        assert "doğrula" in context.lower()

    def test_get_workspace_stats(self, context_builder, sample_workspace):
        """Test getting workspace statistics."""
        stats = context_builder._get_workspace_stats(sample_workspace.workspace)

        assert stats["total"] == 2
        assert "Tornalama Hesaplamaları" in stats["types"]
        assert "Malzeme Hesaplamaları" in stats["types"]
        assert stats["types"]["Tornalama Hesaplamaları"] == 1
        assert stats["types"]["Malzeme Hesaplamaları"] == 1
        assert "last_updated" in stats


class TestModelIntegration:
    """Test model integration scenarios."""

    @pytest.fixture
    def sample_workspace(self):
        """Create sample workspace for model testing."""
        workspace = WorkspaceManager()

        # Add multiple calculations for comprehensive testing
        workspace.add_calculation(
            calc_type="Tornalama Hesaplamaları",
            calc_name="Kesme Hızı",
            params={"Dm": 50, "n": 1000},
            result=157.1,
            unit="m/min",
        )

        workspace.add_calculation(
            calc_type="Tornalama Hesaplamaları",
            calc_name="İş Mili Hızı",
            params={"Vc": 200, "Dm": 50},
            result=1273.2,
            unit="rpm",
        )

        workspace.add_calculation(
            calc_type="Malzeme Hesaplamaları",
            calc_name="Kütle Hesabı",
            params={
                "shape_key": "circle",
                "density": 7.85,
                "length": 100,
                "radius": 50,
            },
            result=6165.38,
            unit="g",
        )

        return workspace

    def test_full_workspace_analysis_context(self, sample_workspace):
        """Test full workspace analysis context generation."""
        context_builder = ContextBuilder()
        context = context_builder.build_analysis_context(sample_workspace.workspace)

        # Verify all calculations are included
        assert "Kesme Hızı" in context
        assert "İş Mili Hızı" in context
        assert "Kütle Hesabı" in context

        # Verify parameters are included
        assert "Dm: 50" in context
        assert "n: 1000" in context
        assert "Vc: 200" in context
        assert "density: 7.85" in context

        # Verify results are included
        assert "157.1" in context
        assert "1273.2" in context
        assert "6165.38" in context

        # Verify units are included
        assert "m/min" in context
        assert "rpm" in context
        assert "g" in context

        # Verify analysis instructions are included
        assert "analiz et" in context.lower()
        assert "teknik doğruluğu" in context.lower()
        assert "pratik uygunluğu" in context.lower()

    def test_calculation_specific_review_context(self, sample_workspace):
        """Test calculation-specific review context."""
        context_builder = ContextBuilder()
        calculations = sample_workspace.get_all_calculations()

        # Test turning calculation review
        turning_calc = calculations[0]  # First turning calculation
        context = context_builder.build_calculation_review_context(turning_calc)

        assert "Tornalama Hesaplamaları" in context
        assert "Kesme Hızı" in context
        assert "157.1" in context
        assert "incele" in context.lower()
        assert "matematiksel doğruluk" in context.lower()

    def test_comparison_context_generation(self, sample_workspace):
        """Test comparison context for multiple calculations."""
        context_builder = ContextBuilder()
        calculations = sample_workspace.get_all_calculations()

        # Get only turning calculations for comparison
        turning_calcs = [
            c for c in calculations if c.calc_type == "Tornalama Hesaplamaları"
        ]
        context = context_builder.build_comparison_context(turning_calcs)

        assert "Karşılaştırılacak Hesaplamalar" in context
        assert "Kesme Hızı" in context
        assert "İş Mili Hızı" in context
        assert "karşılaştır" in context.lower()
        assert "tutarlılığı" in context.lower()

    def test_validation_context_with_ranges(self, sample_workspace):
        """Test validation context with expected ranges."""
        context_builder = ContextBuilder()
        calculations = sample_workspace.get_all_calculations()

        calc = calculations[0]  # First calculation
        expected_ranges = {
            "Dm": (1, 1000),  # Diameter: 1-1000mm
            "n": (10, 10000),  # RPM: 10-10000
            "Vc": (1, 1000),  # Cutting speed: 1-1000 m/min
            "density": (1, 25),  # Density: 1-25 g/cm³
            "length": (1, 10000),  # Length: 1-10000mm
        }

        context = context_builder.build_validation_context(calc, expected_ranges)

        assert "Doğrulanacak Hesaplama" in context
        assert "Beklenen Değer Aralıkları" in context
        assert "1 - 1000" in context
        assert "10 - 10000" in context
        assert "doğrula" in context.lower()

    def test_context_length_and_complexity(self, sample_workspace):
        """Test that contexts have appropriate length and complexity."""
        context_builder = ContextBuilder()

        # Test full analysis context
        full_context = context_builder.build_analysis_context(
            sample_workspace.workspace
        )
        assert len(full_context) > 500  # Should be substantial
        assert len(full_context) < 5000  # But not too long

        # Test single calculation context
        calculations = sample_workspace.get_all_calculations()
        single_context = context_builder.build_calculation_review_context(
            calculations[0]
        )
        assert len(single_context) > 200  # Should be detailed
        assert len(single_context) < 2000  # But manageable

        # Test comparison context
        turning_calcs = [
            c for c in calculations if c.calc_type == "Tornalama Hesaplamaları"
        ]
        comparison_context = context_builder.build_comparison_context(turning_calcs)
        assert len(comparison_context) > 300  # Should include both calculations
        assert len(comparison_context) < 3000  # But reasonable

    def test_context_turkish_language(self, sample_workspace):
        """Test that contexts are properly formatted in Turkish."""
        context_builder = ContextBuilder()
        context = context_builder.build_analysis_context(sample_workspace.workspace)

        # Check for Turkish prompts and labels
        assert "Çalışma Alanı İçeriği" in context
        assert "HESAPLAMA" in context
        assert "Tür:" in context
        assert "İşlem:" in context
        assert "Parametreler:" in context
        assert "Sonuç:" in context
        assert "Kullanıcı Notları:" in context
        assert "Model Yorumları:" in context

        # Check for Turkish instructions
        turkish_keywords = [
            "analiz et",
            "doğruluğu",
            "uygunluğu",
            "tutarlılığı",
            "değerlendir",
            "öneriler",
            "uyarılar",
        ]

        for keyword in turkish_keywords:
            assert keyword in context.lower()

    def test_context_structuring(self, sample_workspace):
        """Test that contexts are properly structured."""
        context_builder = ContextBuilder()
        context = context_builder.build_analysis_context(sample_workspace.workspace)

        # Check for proper sectioning
        lines = context.split("\n")

        # Should have header
        assert any("Çalışma Alanı İçeriği" in line for line in lines)

        # Should have calculation sections
        calc_sections = [line for line in lines if "HESAPLAMA" in line]
        assert len(calc_sections) >= 2  # At least 2 calculations

        # Should have separators
        separators = [line for line in lines if "---" in line]
        assert len(separators) >= 1  # At least some separators

        # Should have analysis instructions
        analysis_lines = [line for line in lines if "analiz et" in line.lower()]
        assert len(analysis_lines) >= 1
