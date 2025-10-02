# Copilot Instructions (Machining_Formulas)

Amaç
- Bu depo, imalat (tornalama/frezeleme) hesaplamaları ile malzeme kütlesi hesabını yapar ve Ollama tabanlı LLM ile konuşma/araç-çağırma (tool-calling) entegre çalışır.
- Çekirdek hesaplama mantığı [`EngineeringCalculator`](engineering_calculator.py) sınıfındadır.
- GUI ve LLM entegrasyonu [`AdvancedCalculator`](horz_gui.py) ile yönetilir; Ollama ve yardımcı araç akışı artık ayrı yardımcı modüllerle modülerleştirilmiştir.

Ana Modüller ve Semboller
- Çekirdek hesaplayıcı: [`EngineeringCalculator`](engineering_calculator.py)
  - Tornalama: [`EngineeringCalculator.calculate_turning`](engineering_calculator.py), tanımlar: `turning_definitions`
  - Frezeleme: [`EngineeringCalculator.calculate_milling`](engineering_calculator.py), tanımlar: `milling_definitions`
  - Malzeme kütlesi: [`EngineeringCalculator.calculate_material_mass`](engineering_calculator.py)
  - Parametre meta bilgisi: [`EngineeringCalculator.get_calculation_params`](engineering_calculator.py)
  - Şekil parametreleri: [`EngineeringCalculator.get_shape_parameters`](engineering_calculator.py)
  - Şekil adları: [`EngineeringCalculator.get_available_shapes`](engineering_calculator.py)
- GUI + LLM katmanı:
  - Başlatıcı/arayüz: [`AdvancedCalculator`](horz_gui.py)
  - Execute modu mixin: [`ExecuteModeMixin`](execute_mode.py)
  - Ollama URL yardımcıları ve tool şeması: [`ollama_utils`](ollama_utils.py)
  - Tool çağrısı argüman normalizasyonu: [`material_utils`](material_utils.py)
  - Tool şeması üretimi: [`AdvancedCalculator._get_calculator_tools_definition`](horz_gui.py) → `ollama_utils.build_calculator_tools_definition`
  - Ollama çağrısı: [`AdvancedCalculator.call_ollama_api`](horz_gui.py)
  - Tool çağrısı işleme: [`AdvancedCalculator.handle_tool_calls`](horz_gui.py) (yardımcı metotlar: `_parse_tool_call`, `_execute_tool_call`, `_attempt_mass_fallback`)

Genel Kurallar
- Dilde süreklilik: Kullanıcı arayüzü ve mesajlar Türkçe. Kodda fonksiyon/parametre isimleri mevcut İngilizce anahtarlarla uyumlu tutulur.
- Mevcut fonksiyonları kullan: Yeni hesaplamalar eklerken önce [`EngineeringCalculator`](engineering_calculator.py) içinde tanımla, GUI ve LLM şemasını bu kaynaktan üret.
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
- Parametre alanlarını her hesaplama için [`EngineeringCalculator.get_calculation_params`](engineering_calculator.py) üzerinden üret.
- Malzeme kütlesi özel akışı:
  - Şekil seçimi (TR ad → iç anahtar için [`EngineeringCalculator.get_available_shapes`](engineering_calculator.py))
  - Şekil boyutları: [`EngineeringCalculator.get_shape_parameters`](engineering_calculator.py) ile sıralı alınır.
- Çeviri/etiketler için `tooltips.json` kullanılır.

LLM / Ollama Entegrasyonu
- Mesaj akışı ve tool tanımları [`AdvancedCalculator.call_ollama_api`](horz_gui.py) ve [`AdvancedCalculator._get_calculator_tools_definition`](horz_gui.py) içinde.
- Tool isimleri:
  - Tornalama: `calculate_turning_{method_key}`
  - Frezeleme: `calculate_milling_{method_key}`
  - Kütle: `calculate_material_mass`
- Argüman sıralaması ve isimleri, her zaman [`EngineeringCalculator.get_calculation_params`](engineering_calculator.py) ve [`EngineeringCalculator.get_shape_parameters`](engineering_calculator.py) çıktısına göre derlenir.
- Model URL ve etiketler:
  - Varsayılan chat uç noktası `http://localhost:11434/v1/chat`; `ollama_utils.normalize_chat_url` ve `candidate_chat_urls` hem `/v1/chat` hem `/api/chat` için yedekler üretir.
  - Model listesi `refresh_model_list` içinde `candidate_tags_urls` ile `/v1/tags`/`/api/tags` üzerinden dinamik çekilir; başarısızlıkta küçük statik listeye düşülür.
- İsteklerde `requests` kullanırken timeout ver (ör. 20s) ve HTTP hatalarını yakala.
- Konuşma geçmişi ve araç yanıtları `self.history` yapısal listesinde tutulur; her tool sonucu `role="tool"` objesi olarak eklenmelidir.
- Malzeme kütlesi argümanları `material_utils.prepare_material_mass_arguments` ile normalize edilir; yeni şekil parametreleri eklenirken bu yardımcıyı güncelleyin ve fallback senaryolarını (`_attempt_mass_fallback`) gözden geçirin.

Güvenlik ve Gizlilik
- `ExecuteModeMixin` (`execute_mode.py`) eval tabanlı işlevi kapsüller; karışık sınıfa müdahale ederken mixin’i genişletin ve `_get_exec_mode_calculator` sağlandığından emin olun.
  - `eval` erişimi sadece seçili metne izin verir; güvenlik değişikliklerinde açık uyarı metinlerini güncelleyin ve pytest ile senaryoları doğrulayın.
- API anahtarları veya gizli bilgiler kayda yazılmaz.

Test ve Doğrulama
- Pytest ile `tests/` altında birim testleri:
  - Şekil hacimleri (ör: üçgen/dikdörtgen/dairenin bilinen sonuçları)
  - Tornalama/frezeleme örnek değerleri (README örnekleri)
  - Parametre meta bilgisi (beklenen anahtarlar/sıra)
- `tests/test_handle_tool_calls.py` sahte `AdvancedCalculator` örneklerini oluştururken `debug_show_raw_model_responses` ve yeni yardımcı metodların gerektirdiği alanlar set edilmelidir.
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
// filepath: /Users/.../engineering_calculator.py
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
- Çekirdek sınıf: [`EngineeringCalculator`](engineering_calculator.py)
- Tool şeması: [`AdvancedCalculator._get_calculator_tools_definition`](horz_gui.py)
- Tool çağrısı işleme: [`AdvancedCalculator.handle_tool_calls`](horz_gui.py)
- Parametre meta: [`EngineeringCalculator.get_calculation_params`](engineering_calculator.py)
- Şekil parametreleri: [`EngineeringCalculator.get_shape_parameters`](engineering_calculator.py)
- GUI: [horz_gui.py](horz_gui.py), README: [README.md](README.md), İpuçları: [tooltips.json](tooltips.json)