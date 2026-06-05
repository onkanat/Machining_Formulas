---
tags: [index]
date: 2026-06-05
sources: []
external_refs: []
status: active
---

# Machining Formulas - Wiki İndeksi (Kod Fihristi)

Machining Formulas projesinin teknik mimari dokümantasyonuna hoş geldiniz. Bu wiki, projenin yapısını, sınıflarını ve tasarım standartlarını özetleyen zihinsel haritadır.

## Proje Yapısı ve Modüller

Proje, canlı kod tabanını `project/` klasöründe tutmaktadır. Ana kaynak kodları `project/src/machining_formulas/` altındadır:

1. **`core/`**: Mühendislik hesaplama mantığının ve formüllerin bulunduğu çekirdek modül.
   - [EngineeringCalculator](file:///Users/hakankilicaslan/GitHub/Machining_Formulas/project/src/machining_formulas/core/engineering_calculator.py)
   - İlgili Entity Dokümanı: [[wiki/entities/engineering_calculator]]
2. **`gui/`**: Tkinter tabanlı V3 grafik kullanıcı arayüzü ve pencere yönetimi.
   - [v3_gui.py](file:///Users/hakankilicaslan/GitHub/Machining_Formulas/project/src/machining_formulas/gui/v3_gui.py)
   - [advanced_calculator.py](file:///Users/hakankilicaslan/GitHub/Machining_Formulas/project/src/machining_formulas/gui/advanced_calculator.py)
   - [execute_mode.py](file:///Users/hakankilicaslan/GitHub/Machining_Formulas/project/src/machining_formulas/gui/execute_mode.py)
   - İlgili Entity Dokümanı: [[wiki/entities/v3_gui]], [[wiki/entities/advanced_calculator]]
3. **`workspace/`**: İşbirlikçi düzenleme ve sürüm yönetimi sağlayan arabellek katmanı.
   - [workspace_buffer.py](file:///Users/hakankilicaslan/GitHub/Machining_Formulas/project/src/machining_formulas/workspace/workspace_buffer.py)
   - [workspace_editor.py](file:///Users/hakankilicaslan/GitHub/Machining_Formulas/project/src/machining_formulas/workspace/workspace_editor.py)
   - [workspace_manager.py](file:///Users/hakankilicaslan/GitHub/Machining_Formulas/project/src/machining_formulas/workspace/workspace_manager.py)
   - İlgili Entity Dokümanı: [[wiki/entities/workspace]]
4. **`llm/`**: Ollama entegrasyonu ve araç (tool) şemalarının dinamik üretilmesi.
   - [ollama_utils.py](file:///Users/hakankilicaslan/GitHub/Machining_Formulas/project/src/machining_formulas/llm/ollama_utils.py)
   - [ollama_utils_v2.py](file:///Users/hakankilicaslan/GitHub/Machining_Formulas/project/src/machining_formulas/llm/ollama_utils_v2.py)
   - [material_utils.py](file:///Users/hakankilicaslan/GitHub/Machining_Formulas/project/src/machining_formulas/llm/material_utils.py)
   - İlgili Konsept Dokümanı: [[wiki/concepts/llm_integration]]

---

## Tasarım Kavramları ve Standartlar

Projede uyulması gereken mimari kurallar ve test pratikleri aşağıdaki dokümanlarda açıklanmıştır:
- **Test ve Birim Standartları:** [[wiki/concepts/testing]]
- **Ollama ve Tool-Calling Entegrasyonu:** [[wiki/concepts/llm_integration]]

## Günlükler ve Sentez

- **Kronolojik Geliştirme Günlüğü:** [[wiki/log]]
- **Teknik Borçlar ve Mimari Durum:** [[wiki/synthesis]]
