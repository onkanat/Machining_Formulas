"""Context builder for V2 model interactions.

This module provides utilities to build context strings
for model analysis of workspace data.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Any

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

        context = (
            base_context
            + "Çalışma Alanı İçeriği (Toplam {} hesaplama):\n\n".format(
                len(workspace.calculations)
            )
        )

        for i, calc in enumerate(workspace.calculations, 1):
            context += f"HESAPLAMA #{i}:\n"
            context += f"Tür: {calc.calc_type}\n"
            context += f"İşlem: {calc.calculation_name}\n"
            context += f"Parametreler: {calc.parameters}\n"
            context += f"Sonuç: {calc.result} {calc.unit}\n"

            if calc.user_notes:
                context += f"Kullanıcı Notları:\n"
                for note in calc.user_notes:
                    context += f"  • {note}\n"

            if calc.model_comments:
                context += f"Model Yorumları:\n"
                for comment in calc.model_comments:
                    context += f"  • {comment}\n"

            context += "\n" + "-" * 50 + "\n\n"

        analysis_prompt = (
            "Yukarıdaki çalışma alanını analiz et:\n"
            "1. Hesaplamaların teknik doğruluğu\n"
            "2. Parametrelerin pratik uygunluğu\n"
            "3. Sonuçların tutarlılığı\n"
            "4. Kullanıcı notlarına göre öneriler\n"
            "5. Potansiyel iyileştirmeler veya uyarılar\n\n"
            "Analiz sonuçlarını yapılandırılmış şekilde sun."
        )

        return base_context + context + analysis_prompt

    def build_calculation_review_context(self, calculation: CalculationEntry) -> str:
        """Build context for single calculation review."""
        base_context = self.system_prompt + "\n\n"

        context = base_context + f"İncelenecek Hesaplama:\n"
        context += f"Tür: {calculation.calc_type}\n"
        context += f"İşlem: {calculation.calculation_name}\n"
        context += f"Parametreler: {calculation.parameters}\n"
        context += f"Sonuç: {calculation.result} {calculation.unit}\n"

        if calculation.user_notes:
            context += f"Kullanıcı Notları:\n"
            for note in calculation.user_notes:
                context += f"  • {note}\n"

        if calculation.model_comments:
            context += f"Model Yorumları:\n"
            for comment in calculation.model_comments:
                context += f"  • {comment}\n"

        review_prompt = (
            "\nBu hesaplamayı detaylıca incele:\n"
            "1. Matematiksel doğruluk\n"
            "2. Parametrelerin mantığı\n"
            "3. Sonucun beklenen aralıkta olup olmadığı\n"
            "4. Pratik uygulamadaki geçerliliği\n"
            "5. Kullanıcı notlarına yanıt\n\n"
            "Değerlendirmeni net ve yapılandırılmış şekilde sun."
        )

        return base_context + context + review_prompt

    def build_general_review_context(self, workspace: Workspace) -> str:
        """Build general review context."""
        base_context = self.system_prompt + "\n\n"

        stats = self._get_workspace_stats(workspace)
        context = base_context + f"Çalışma Alanı Özeti:\n"
        context += f"Toplam Hesaplama: {stats['total']}\n"
        context += f"Hesaplama Türleri: {stats['types']}\n"
        context += f"Son Güncelleme: {stats['last_updated']}\n\n"

        context += workspace.get_full_context()

        general_prompt = (
            "Bu çalışma alanının genel durumunu değerlendir:\n"
            "1. Hesaplamalar arasındaki tutarlılığı\n"
            "2. Genel yaklaşımın doğruluğu\n"
            "3. Potansiyel eksiklikler veya iyileştirmeler\n"
            "4. Önerilen sonraki adımlar\n\n"
            "Genel değerlendirmeni sun."
        )

        return base_context + context + general_prompt

    def build_comparison_context(self, calculations: List[CalculationEntry]) -> str:
        """Build comparison context for multiple calculations."""
        base_context = self.system_prompt + "\n\n"

        if len(calculations) < 2:
            return base_context + "Karşılaştırma için en az 2 hesaplama gerekli."

        context = base_context + "Karşılaştırılacak Hesaplamalar:\n\n"

        for i, calc in enumerate(calculations, 1):
            context += f"HESAPLAMA #{i}:\n"
            context += f"Tür: {calc.calc_type}\n"
            context += f"İşlem: {calc.calculation_name}\n"
            context += f"Parametreler: {calc.parameters}\n"
            context += f"Sonuç: {calc.result} {calc.unit}\n"
            context += "\n"

        comparison_prompt = (
            "Bu hesaplamaları karşılaştır:\n"
            "1. Sonuçların tutarlılığı\n"
            "2. Parametre farklılıklarının etkileri\n"
            "3. Hangi yaklaşımın daha uygun olduğu\n"
            "4. Optimizasyon önerileri\n\n"
            "Karşılaştırma sonuçlarını sun."
        )

        return base_context + context + comparison_prompt

    def build_validation_context(
        self,
        calculation: CalculationEntry,
        expected_range: Optional[Dict[str, tuple]] = None,
    ) -> str:
        """Build context for calculation validation."""
        base_context = self.system_prompt + "\n\n"

        context = base_context + f"Doğrulanacak Hesaplama:\n"
        context += f"Tür: {calculation.calc_type}\n"
        context += f"İşlem: {calculation.calculation_name}\n"
        context += f"Parametreler: {calculation.parameters}\n"
        context += f"Sonuç: {calculation.result} {calculation.unit}\n"

        if expected_range:
            context += "\nBeklenen Değer Aralıkları:\n"
            for param, (min_val, max_val) in expected_range.items():
                context += f"  {param}: {min_val} - {max_val}\n"

        validation_prompt = (
            "\nBu hesaplamayı doğrula:\n"
            "1. Formülün doğru uygulanıp uygulanmadığı\n"
            "2. Birimlerin tutarlılığı\n"
            "3. Sonucun mantıklı olup olmadığı\n"
            "4. Beklenen aralıklarda olup olmadığı\n"
            "5. Potansiyel hata kaynakları\n\n"
            "Doğrulama sonucunu belirt."
        )

        return base_context + context + validation_prompt

    def build_edit_context_for_changes(
        self, workspace, calc_id: str, changes: Dict[str, Any]
    ) -> str:
        """Build context for calculation editing with specific changes."""
        base_context = self.system_prompt + "\n\n"

        calculation = workspace.get_calculation(calc_id)
        if not calculation:
            return base_context + "Hesaplama bulunamadı."

        edit_context = (
            f"Kullanıcı şu hesaplamayı düzenledi:\n"
            f"HESAPLAMA ID: {calc_id}\n"
            f"Tür: {calculation.calc_type}\n"
            f"İşlem: {calculation.calculation_name}\n"
            f"Önceki Parametreler: {calculation.parameters}\n"
            f"Önceki Sonuç: {calculation.result} {calculation.unit}\n"
            f"Yapılan Değişiklikler:\n"
        )

        for param, new_value in changes.items():
            old_value = calculation.parameters.get(param)
            if old_value is not None:
                edit_context += f"  {param}: {old_value} → {new_value}\n"
            else:
                edit_context += f"  {param}: → {new_value} (yeni)\n"

        edit_prompt = (
            "\nLütfen bu düzenlemeyi analiz et:\n"
            "1. Değişikliklerin mantıklı olup olmadığını kontrol et\n"
            "2. Mühendislik formüllerine uygunluğunu değerlendir\n"
            "3. Sonuçların tutarlılığını kontrol et\n"
            "4. Gerekli düzeltmeleri öner\n"
            "5. Analiz sonucunu net şekilde sun."
        )

        return base_context + edit_context + edit_prompt

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
