---
tags: [entity]
date: 2026-06-05
sources: [project/src/machining_formulas/core/engineering_calculator.py]
external_refs: []
status: active
---

# EngineeringCalculator

`EngineeringCalculator` sınıfı, projenin tüm matematiksel ve fiziksel hesaplama formüllerini içeren çekirdek modüldür. GUI ve LLM (AdvancedCalculator) katmanlarından tamamen bağımsızdır ve saf Python mantığıyla çalışır.

## Temel Özellikler

### 1. Şekil ve Hacim Formülleri (`self.shape_definitions`)
Geometrik şekillerin hacimlerini mm³ cinsinden hesaplayan lambda fonksiyonları sözlüğüdür:
- **Desteklenen Şekiller:** `triangle`, `circle`, `semi-circle`, `square`, `rectangle`, `parallelogram`, `rhombus`, `trapezoid`, `trapezium`, `kite`, `pentagon`, `hexagon`, `octagon`, `nonagon`, `decagon`, `tube`, `sphere`.
- **Girdi/Çıktı Birimi:** Boyutlar mm cinsindendir, hesaplanan hacim mm³ (milimetreküp) döner.

### 2. Malzeme Yoğunlukları (`self.material_density`)
Farklı metallerin ve plastiklerin g/cm³ cinsinden yoğunluk değerlerini tutar:
- **Çelik:** 7.85
- **Alüminyum:** 2.70
- **Bakır:** 8.96
- **Pirinç:** 8.50
- **Titanyum:** 4.51
- vb.

### 3. Talaşlı İmalat Tanımları
- **Tornalama (`turning_definitions`):** Kesme hızı (Cutting speed), İş mili devri (Spindle speed), Talaş kaldırma oranı (Metal removal rate), Net güç (Net power), İşleme süresi (Machining time).
- **Frezeleme (`milling_definitions`):** Tabla ilerlemesi (Table feed), Kesme hızı, İş mili devri, Diş başına ilerleme (Feed per tooth), Devir başına ilerleme (Feed per revolution), Talaş kaldırma oranı, Net güç, Tork (Torque).
- **Delme (`drilling_definitions`):** Kesme hızı, İş mili devri, İlerleme hızı (Feed rate), Talaş kaldırma oranı, İşleme süresi.

---

## Önemli Metotlar

### `calculate_material_mass(shape, density, *args)`
Verilen geometrik şekil ve malzeme yoğunluğuna göre kütleyi gram (g) cinsinden hesaplar.
- **Dönüşüm:** Hacim mm³ cinsinden hesaplandıktan sonra 1000'e bölünerek cm³'e çevrilir, ardından yoğunluk ile çarpılır ($Mass = Volume_{cm^3} \times Density_{g/cm^3}$).

### `calculate_turning / calculate_milling / calculate_drilling(definition, *args)`
İlgili talaşlı imalat kategorisindeki formülleri çalıştırır ve değeri ile birimini bir sözlük olarak döner:
```python
{
    "value": float,
    "units": str
}
```

### `get_calculation_params(calc_category_key, calc_method_key)`
Metot ve kategori anahtarlarına göre, arayüz veya LLM araç tanımları için parametre meta verilerini (parametre adı, birimi ve Türkçe ekran adı) döner.
- **Örnek Çıktı:** `[{"name": "Dm", "unit": "mm", "display_text_turkish": "İşlenen Çap"}]`
