# Copilot Instructions (Machining_Formulas)

Amaç
- Bu depo, imalat (tornalama/frezeleme) hesaplamaları ile malzeme kütlesi hesabını yapar ve Ollama tabanlı LLM ile konuşma/araç-çağırma (tool-calling) entegre çalışır.
- Repo `src/` layout kullanır; kanonik paket yolu `src/machining_formulas/` altındadır.
- Çekirdek hesaplama mantığı [`EngineeringCalculator`](src/machining_formulas/core/engineering_calculator.py) sınıfındadır.
- Üretim GUI: Tkinter tabanlı V3 arayüzü [`V3Calculator`](src/machining_formulas/gui/v3_gui.py) ile sağlanır. Giriş noktası: `python -m machining_formulas`.
- Tool-calling odaklı minimal sınıf (özellikle testler için): [`AdvancedCalculator`](src/machining_formulas/gui/advanced_calculator.py).

Ana Modüller ve Semboller
- Çekirdek hesaplayıcı: [`EngineeringCalculator`](src/machining_formulas/core/engineering_calculator.py)
  - Tornalama: `EngineeringCalculator.calculate_turning`, tanımlar: `turning_definitions`
  - Frezeleme: `EngineeringCalculator.calculate_milling`, tanımlar: `milling_definitions`
  - Malzeme kütlesi: `EngineeringCalculator.calculate_material_mass`
  - Parametre meta bilgisi: `EngineeringCalculator.get_calculation_params`
  - Şekil parametreleri: `EngineeringCalculator.get_shape_parameters`
  - Şekil adları: `EngineeringCalculator.get_available_shapes`
- GUI katmanı:
  - V3 Tkinter arayüzü + dinamik parametre formları + sekme header canvas: [`V3Calculator`](src/machining_formulas/gui/v3_gui.py)
  - Execute modu mixin (eval güvenliği): [`ExecuteModeMixin`](src/machining_formulas/gui/execute_mode.py)
- LLM yardımcıları:
  - Ollama URL yardımcıları + tool şeması üretimi: [`ollama_utils`](src/machining_formulas/llm/ollama_utils.py)
    - `normalize_chat_url`, `candidate_chat_urls`, `candidate_tags_urls`
    - `build_calculator_tools_definition(calculator)`
  - V3 GUI’nin basit istek/bağlantı fonksiyonları: [`ollama_utils_v2`](src/machining_formulas/llm/ollama_utils_v2.py)
  - Tool çağrısı argüman normalizasyonu (kütle/şekil/malzeme): [`material_utils`](src/machining_formulas/llm/material_utils.py)
- Tool-calling sınıfı (test odaklı): [`AdvancedCalculator`](src/machining_formulas/gui/advanced_calculator.py)
  - Tool çağrısı işleme: `AdvancedCalculator.handle_tool_calls()` (yardımcılar: `_parse_tool_arguments`, `_execute_tool`, `_build_silent_model_summary`, ...)
- Assets:
  - Kanonik asset klasörü repo kökünde `assets/` altındadır.
  - Çeviri/etiketler: `assets/tooltips.json`
  - Görseller: `assets/images/*.png`
  - Path çözümü: `machining_formulas.assets.asset_path()` (`src/machining_formulas/assets.py`)

Genel Kurallar
- Dilde süreklilik: Kullanıcı arayüzü ve mesajlar Türkçe. Kodda fonksiyon/parametre isimleri mevcut İngilizce anahtarlarla uyumlu tutulur.
- Mevcut fonksiyonları kullan: Yeni hesaplamalar eklerken önce [`EngineeringCalculator`](src/machining_formulas/core/engineering_calculator.py) içinde tanımla; GUI (dinamik parametreler) ve LLM tool şemasını bu kaynaktan üret.
- Birim tutarlılığı: 
  - Uzunluk: mm
  - Hacim: mm³ (iç hesap), dışa dönük kütlede cm³’e dönüşüm var.
  - Hız: m/min, rpm
  - MRR (cm³/min) dönüşümleri dikkatle korunmalı.
- Formül değişiklikleri: Her değişiklik için birim testi zorunlu. Varsayılan formülleri testle doğrulamadan değiştirme.
- Hata mesajları: Kullanıcıya sade TR mesajlar, geliştirici loglarında yeterli bağlam.

Kod Stili
- Python 3.10+ tip ipuçları kullan.
- Docstring ve kısa örnekler ekle.
- Hataları ValueError ile sar ve açıklayıcı mesaj ver (mevcut desen korunur).
- Fonksiyon/parametre isimleri: `EngineeringCalculator`’daki anahtarlarla birebir.

GUI ve Dinamik Parametreler
- Parametre alanlarını her hesaplama için `EngineeringCalculator.get_calculation_params()` üzerinden üret.
- Malzeme kütlesi özel akışı:
  - Şekil seçimi (TR ad → iç anahtar için `EngineeringCalculator.get_available_shapes()`)
  - Şekil boyutları: `EngineeringCalculator.get_shape_parameters()` ile sıralı alınır.
- Çeviri/etiketler için `assets/tooltips.json` kullanılır (kodda `asset_path("tooltips.json")`).
- Sekme header görselleri `assets/images/` altında tutulur (örn: `turning.png`, `milling.png`, `material.png`, `drilling.png`).

LLM / Ollama Entegrasyonu
- Tool şeması üretimi `machining_formulas.llm.ollama_utils.build_calculator_tools_definition()` ile yapılır.
- Tool çağrısı yürütümü ve history güncellemesi test odaklı `machining_formulas.gui.advanced_calculator.AdvancedCalculator.handle_tool_calls()` içindedir.
- Tool isimleri:
  - Tornalama: `calculate_turning_{method_key}`
  - Frezeleme: `calculate_milling_{method_key}`
  - Kütle: `calculate_material_mass`
- Argüman sıralaması ve isimleri, her zaman [`EngineeringCalculator.get_calculation_params`](engineering_calculator.py) ve [`EngineeringCalculator.get_shape_parameters`](engineering_calculator.py) çıktısına göre derlenir.
- Model URL ve etiketler:
  - URL normalizasyonu: `ollama_utils.normalize_chat_url()`; aday uç noktalar: `candidate_chat_urls()` ve `candidate_tags_urls()`.
  - V3 GUI model listesi/bağlantı testi için `ollama_utils_v2.get_available_models()` ve `ollama_utils_v2.test_connection()` kullanır.
- İsteklerde `requests` kullanırken timeout ver (ör. 20s) ve HTTP hatalarını yakala.
- Konuşma geçmişi ve araç yanıtları `self.history` yapısal listesinde tutulur; her tool sonucu `role="tool"` objesi olarak eklenmelidir.
- Malzeme kütlesi argümanları `material_utils.prepare_material_mass_arguments()` ile normalize edilir; yeni şekil parametreleri eklenirken bu yardımcıyı güncelleyin ve fallback senaryolarını gözden geçirin.

Güvenlik ve Gizlilik
- `ExecuteModeMixin` (`src/machining_formulas/gui/execute_mode.py`) eval tabanlı işlevi kapsüller; karışık sınıfa müdahale ederken mixin’i genişletin ve `_get_exec_mode_calculator` sağlandığından emin olun.
  - `eval` erişimi sadece seçili metne izin verir; güvenlik değişikliklerinde açık uyarı metinlerini güncelleyin ve pytest ile senaryoları doğrulayın.
- API anahtarları veya gizli bilgiler kayda yazılmaz.

Test ve Doğrulama
- Pytest ile `tests/` altında birim testleri:
  - Şekil hacimleri (ör: üçgen/dikdörtgen/dairenin bilinen sonuçları)
  - Tornalama/frezeleme örnek değerleri (README örnekleri)
  - Parametre meta bilgisi (beklenen anahtarlar/sıra)
- `tests/test_handle_tool_calls.py` sahte `AdvancedCalculator` örneklerini oluştururken `debug_show_raw_model_responses` ve diğer gerekli alanlar set edilmelidir.
- Kenar durumları: Hatalı şekil, eksik parametre, tip hatası, 0/bölme vb.

Değişiklik Önerisi Nasıl Sunulur
- Kod değişikliği önerileri şu formatta verilmelidir:
  - Dört backtick ile başla/bitir
  - Dil adı (örn. `python`, `markdown`)
  - İlk satır yorumunda `// filepath: ...` ile tam yol
  - Var olan dosya değişirse `...existing code...` yer tutucularını kullan
- Örnek:
```
This is the code block that represents the suggested code change:
```instructions
// filepath: /Users/.../src/machining_formulas/core/engineering_calculator.py
# ...existing code...
def new_func():
    pass
# ...existing code...
```

Commit/PR
- Mesaj formatı: `area: kısa açıklama` (örn. `gui: ollama timeout eklendi`)
- Her PR:
- Test ekler/günceller
- README veya yeni özellik için kısa dokümantasyon güncellemesi yapar
- Manuel test adımlarını açıklar

Hızlı Referans Bağlantıları
- Çekirdek sınıf: [`EngineeringCalculator`](src/machining_formulas/core/engineering_calculator.py)
- V3 GUI: [`V3Calculator`](src/machining_formulas/gui/v3_gui.py) (giriş: `python -m machining_formulas`)
- Tool şeması: `ollama_utils.build_calculator_tools_definition` → [`ollama_utils`](src/machining_formulas/llm/ollama_utils.py)
- Tool çağrısı işleme: `AdvancedCalculator.handle_tool_calls` → [`AdvancedCalculator`](src/machining_formulas/gui/advanced_calculator.py)
- Parametre meta: `EngineeringCalculator.get_calculation_params`
- Şekil parametreleri: `EngineeringCalculator.get_shape_parameters`
- Assets: [`asset_path`](src/machining_formulas/assets.py), `assets/tooltips.json`, `assets/images/`
- README: [README.md](README.md)