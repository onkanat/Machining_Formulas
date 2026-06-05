---
tags: [concept]
date: 2026-06-05
sources: [project/src/machining_formulas/llm/]
external_refs: []
status: active
---

# Ollama ve Tool-Calling Entegrasyonu

Bu döküman, projedeki büyük dil modeli (LLM - Ollama) entegrasyonunu, dinamik araç (tool) tanımlarının nasıl üretildiğini ve istek yönlendirme mantığını açıklar.

## Dinamik Araç Tanımı (Dynamic Tool Schema Generation)

Dil modeline (Ollama) sunulacak olan araç listesi, kod tabanında sabit (hardcoded) bir şema yerine, `EngineeringCalculator` içindeki tanımlardan çalışma zamanında dinamik olarak üretilir. Bu işlem `ollama_utils.py` altındaki `build_calculator_tools_definition(calculator)` fonksiyonu tarafından yapılır:

1. **Tornalama, Frezeleme ve Delme Araçları:**
   - Sınıftaki `turning_definitions`, `milling_definitions` ve `drilling_definitions` sözlüklerindeki her bir metod taranır.
   - `get_calculation_params` metodu çağrılarak her bir formül için gerekli parametre isimleri, birimleri ve Türkçe isimleri elde edilir.
   - Her bir formül için `calculate_turning_{method_name}` vb. isminde bir JSON şeması fonksiyonu üretilir.

2. **Kütle Hesaplama Aracı (`calculate_material_mass`):**
   - Geometrik şekil (`shape_key`), yoğunluk (`density`) ve uzunluk (`length`) zorunlu parametrelerdir.
   - Sınıftaki tüm geometrik şekil formülleri taranarak, şekillere özel ek boyut parametreleri (genişlik, yükseklik, dış yarıçap vb.) dinamik olarak şemaya eklenir.

---

## İstek Yönlendirme ve Fallback Mekanizması

Farklı ağ ortamlarında veya Ollama sürümlerinde (örneğin local çalışırken veya uzak bir sunucudayken) bağlantı problemlerini önlemek için yedekli rotalar (`candidate_chat_urls`) otomatik üretilir:

- Kullanıcı bir URL girdiğinde (`http://192.168.1.14:11434` gibi):
  - Uç nokta `/v1/chat` (OpenAI uyumlu yeni araç çağırma API'si) formatına normalize edilir.
  - Yedek olarak `/api/chat` (Ollama legacy chat API'si) rotası eklenir.
- İstek atılırken ilk rota başarılı olmazsa veya HTTP 200 harici bir kod dönerse otomatik olarak bir sonraki rotaya geçilir.
- `/api/chat` uç noktası araçları doğrudan desteklemediği için, bu adrese istek atılmadan önce `prepare_legacy_chat_payload` fonksiyonu ile `tools` anahtarı payload'dan temizlenir.
