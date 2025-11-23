"""Context builder for V2 model interactions.

This module provides utilities to build context strings
for model analysis of workspace data.
"""

from __future__ import annotations

from typing import Dict, List, Any, Optional
from workspace_manager import Workspace, CalculationEntry


class ContextBuilder:
    """Builds context strings for model analysis."""

    def __init__(self):
        self.system_prompt = (
            "Sen bir mühendislik hesaplama asistanısın. "
            "Verilen hesaplamaları analiz et, doğrula ve yapıcı yorumlar yap. "
            "Hesaplamaların doğruluğunu kontrol et, pratik değerler aralığında olup olmadığını değerlendir. "
            "Kullanıcı notlarına dikkat et ve onlara göre öneriler sun. "
            "Yanıtlarını kısa, net ve teknik olarak doğru tut."
        )

    def build_analysis_context(self, workspace: Workspace) -> str:
        """Build full workspace analysis context."""
        base_context = self.system_prompt + "\n\n"

        if not workspace.calculations:
            return base_context + "Bu çalışma alanında henüz hesaplama bulunmuyor."

        workspace_context = workspace.get_full_context()

        analysis_prompt = (
            "Yukarıdaki çalışma alanını analiz et:\n"
            "1. Hesaplamaların teknik doğruluğu\n"
            "2. Parametrelerin pratik uygunluğu\n"
            "3. Sonuçların tutarlılığı\n"
            "4. Kullanıcı notlarına göre öneriler\n"
            "5. Potansiyel iyileştirmeler veya uyarılar\n\n"
            "Analiz sonuçlarını yapılandırılmış şekilde sun."
        )

        return base_context + workspace_context + "\n\n" + analysis_prompt

    def build_calculation_review_context(self, calculation: CalculationEntry) -> str:
        """Build context for single calculation review."""
        base_context = self.system_prompt + "\n\n"

        calc_context = (
            f"İncelenecek Hesaplama:\n"
            f"Tür: {calculation.calc_type}\n"
            f"İşlem: {calculation.calculation_name}\n"
            f"Parametreler: {calculation.parameters}\n"
            f"Sonuç: {calculation.result} {calculation.unit}\n"
        )

        if calculation.user_notes:
            calc_context += "\nKullanıcı Notları:\n"
            for note in calculation.user_notes:
                calc_context += f"  - {note}\n"

        if calculation.model_comments:
            calc_context += "\nÖnceki Model Yorumları:\n"
            for comment in calculation.model_comments:
                calc_context += f"  - {comment}\n"

        review_prompt = (
            "\nBu hesaplamayı detaylıca incele:\n"
            "1. Matematiksel doğruluk\n"
            "2. Parametrelerin mantığı\n"
            "3. Sonucun beklenen aralıkta olup olmadığı\n"
            "4. Pratik uygulamadaki geçerliliği\n"
            "5. Kullanıcı notlarına yanıt\n\n"
            "Değerlendirmeni net ve yapıcı şekilde sun."
        )

        return base_context + calc_context + review_prompt

    def build_general_review_context(self, workspace: Workspace) -> str:
        """Build context for general workspace review."""
        base_context = self.system_prompt + "\n\n"

        stats = self._get_workspace_stats(workspace)
        stats_context = (
            f"Çalışma Alanı Özeti:\n"
            f"Toplam Hesaplama: {stats['total']}\n"
            f"Hesaplama Türleri: {stats['types']}\n"
            f"Son Güncelleme: {stats['last_updated']}\n\n"
        )

        full_context = stats_context + workspace.get_full_context()

        general_prompt = (
            "Bu çalışma alanının genel durumunu değerlendir:\n"
            "1. Hesaplamalar arasındaki tutarlılık\n"
            "2. Genel yaklaşımın doğruluğu\n"
            "3. Potansiyel eksiklikler veya iyileştirmeler\n"
            "4. Önerilen sonraki adımlar\n\n"
            "Genel değerlendirmeni sun."
        )

        return base_context + full_context + "\n\n" + general_prompt

    def build_comparison_context(self, calculations: List[CalculationEntry]) -> str:
        """Build context for comparing multiple calculations."""
        base_context = self.system_prompt + "\n\n"

        if len(calculations) < 2:
            return base_context + "Karşılaştırma için en az 2 hesaplama gerekli."

        comparison_context = "Karşılaştırılacak Hesaplamalar:\n\n"

        for i, calc in enumerate(calculations, 1):
            comparison_context += (
                f"HESAPLAMA {i}:\n"
                f"Tür: {calc.calc_type}\n"
                f"İşlem: {calc.calculation_name}\n"
                f"Parametreler: {calc.parameters}\n"
                f"Sonuç: {calc.result} {calc.unit}\n"
            )

            if calc.user_notes:
                comparison_context += "Notlar: " + "; ".join(calc.user_notes) + "\n"

            comparison_context += "\n"

        comparison_prompt = (
            "Bu hesaplamaları karşılaştır:\n"
            "1. Sonuçların tutarlılığı\n"
            "2. Parametre farklılıklarının etkileri\n"
            "3. Hangi yaklaşımın daha uygun olduğu\n"
            "4. Optimizasyon önerileri\n\n"
            "Karşılaştırma sonuçlarını sun."
        )

        return base_context + comparison_context + comparison_prompt

    def build_validation_context(
        self,
        calculation: CalculationEntry,
        expected_range: Optional[Dict[str, tuple]] = None,
    ) -> str:
        """Build context for calculation validation."""
        base_context = self.system_prompt + "\n\n"

        validation_context = (
            f"Doğrulanacak Hesaplama:\n"
            f"Tür: {calculation.calc_type}\n"
            f"İşlem: {calculation.calculation_name}\n"
            f"Parametreler: {calculation.parameters}\n"
            f"Sonuç: {calculation.result} {calculation.unit}\n"
        )

        if expected_range:
            validation_context += "\nBeklenen Değer Aralıkları:\n"
            for param, (min_val, max_val) in expected_range.items():
                validation_context += f"  {param}: {min_val} - {max_val}\n"

        validation_prompt = (
            "\nBu hesaplamayı doğrula:\n"
            "1. Formülün doğru uygulanıp uygulanmadığı\n"
            "2. Birimlerin tutarlılığı\n"
            "3. Sonucun mantıklı olup olmadığı\n"
            "4. Beklenen aralıklarda olup olmadığı\n"
            "5. Potansiyel hata kaynakları\n\n"
            "Doğrulama sonucunu belirt."
        )

        return base_context + validation_context + validation_prompt

    def _get_workspace_stats(self, workspace: Workspace) -> Dict[str, Any]:
        """Get workspace statistics for context building."""
        calc_types = {}
        for calc in workspace.calculations:
            calc_type = calc.calc_type
            calc_types[calc_type] = calc_types.get(calc_type, 0) + 1

        return {
            "total": len(workspace.calculations),
            "types": calc_types,
            "last_updated": workspace.last_updated.strftime("%Y-%m-%d %H:%M:%S"),
        }
