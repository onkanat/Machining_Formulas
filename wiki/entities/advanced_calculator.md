---
tags: [entity]
date: 2026-06-05
sources: [project/src/machining_formulas/gui/advanced_calculator.py]
external_refs: []
status: active
---

# AdvancedCalculator

`AdvancedCalculator`, Ollama LLM modellerinin araç çağrılarını (tool-calling) gerçekleştirmek, yönetmek ve sonuçlarını işlemek üzere tasarlanmış katmandır. `EngineeringCalculator`'ı sarmalayarak model ile hesaplama motoru arasında köprü kurar.

## Temel Özellikler

### 1. Ollama Uç Noktaları Yönetimi
Ollama'nın farklı sürümlerinde kullanılan API rotalarını dinamik olarak dener:
- `/v1/chat` (OpenAI uyumlu yeni araç çağırma API'si)
- `/api/chat` (Ollama legacy API'si)
- `force_legacy_chat` bayrağı ile API önceliği değiştirilebilir.

### 2. Araç Çağrılarının Yönetimi (`chat_with_tools`)
Modelden gelen `tool_calls` dizisini yakalar, ilgili araçları çalıştırır, sonuçları geçmişe ekler ve modelden nihai yanıtı üretmesini ister.

---

## Önemli Metotlar

### `handle_tool_calls(chat_url, model, messages_history, tool_calls, tools_definition)`
Gelen araç çağrılarını sırayla çalıştırır.
- Her bir çağrı için `_execute_tool` metodunu çağırarak hesaplama yapar.
- Hataları yakalar ve modelin çökmesini engellemek için hata mesajını `HATA: ...` olarak modele geri besler.
- Model sessiz kalırsa (boş içerik dönerse), `_build_silent_model_summary` aracılığıyla otomatik bir özet metni üretir.

### `_execute_tool(tool_name, arguments, messages_history)`
Gelen araç adına göre ilgili hesaplamayı yönlendirir:
- **`calculate_material_mass`**: `prepare_material_mass_arguments` yardımcı fonksiyonu ile argümanları hazırlar ve kütleyi hesaplar.
- **`calculate_turning_`**, **`calculate_milling_`**, **`calculate_drilling_`**: Metot adındaki soneki (`turning_cutting_speed` gibi) temizleyip `_slugify` yardımıyla `EngineeringCalculator` metotlarıyla eşleştirir ve çalıştırır.

### `_post_chat_with_legacy_support(url_candidates, payload, headers, timeout)`
Verilen aday URL'leri sırayla çağırır. HTTP 200 dönen ve geçerli JSON üreten ilk uç noktayı seçer. Bağlantı ve zaman aşımı hatalarını `ValueError` içinde paketler.
