---
tags: [entity]
date: 2026-06-05
sources: [project/src/machining_formulas/workspace/workspace_buffer.py, project/src/machining_formulas/workspace/workspace_editor.py]
external_refs: []
status: active
---

# Workspace (Çalışma Alanı Katmanı)

Workspace, kullanıcının talaşlı imalat hesaplamalarını topladığı, düzenlediği ve LLM modeliyle ortaklaşa çalışabildiği etkileşimli bir tampon (buffer) ve editör arayüzüdür.

## Modüller ve Sınıflar

### 1. `WorkspaceBuffer`
Çalışma alanının zihinsel durumunu ve geçmişini tutan çekirdek veri yapısıdır:
- **`WorkspaceEdit`**: Yapılan her bir ekleme, silme veya değiştirme işlemini temsil eder. İşlemin kimin tarafından yapıldığını (`author: "user" / "model"`), zaman damgasını (timestamp) ve kabul edilme durumunu (`accepted`, `rejected`) kaydeder.
- **`WorkspaceVersion`**: Çalışma alanındaki her bir değişikliğin ardından otomatik olarak oluşturulan içerik anlık görüntüsüdür (snapshot). Geri yükleme noktaları sağlar (son 100 sürümü hafızada tutar).
- **Metotlar:**
  - `insert_text(position, text, author)`: Belirtilen konuma metin ekler.
  - `delete_text(start, end, author)`: Metin siler.
  - `suggest_edit(start, end, text, description, *, at_end=False)`: Modelin önerdiği bir değişikliği kaydeder (`accepted=False` olarak). `old_text` boşsa `MODEL_INSERT`, doluysa `MODEL_REPLACE` üretir; aynı metin/konum için zaten bekleyen bir öneri varsa yenisini eklemez. `at_end=True` öneri, kullanıcı belgeyi sonradan düzenlemese bile kabul anında belgenin sonuna uygulanır.
  - `accept_suggestion(edit_id)` / `reject_suggestion(edit_id)`: Modelin önerilerini kabul eder veya reddeder; belge öneriden sonra değiştiyse (`stale`) kabul reddedilir.
  - `line_diff(old_text, new_text, context=2)`: `difflib.unified_diff` tabanlı satır farkı; `(" ", "-", "+", "@")` etiketli `(tag, text)` çiftleri döndürür (UI'dan bağımsız, test edilebilir).
  - `restore_version(version_id)`: Eski bir sürüme geri döner (Undo/Redo mantığı).
  - `export_session()` / `import_session(data)`: Tüm oturumu JSON formatında kaydeder veya yükler.

### 2. `WorkspaceEditor`
Tkinter'in `Text` bileşenini sarmalayarak kullanıcı arayüzünü sunar:
- Metin değişikliklerini dinleyerek anlık olarak `WorkspaceBuffer`'ı günceller; programatik yüklemeler (`_load_content`, `set_content`, `insert_calculation_result`) kullanıcı düzenlemesi olarak kaydedilmez.
- **Soru çubuğu**: `Soru:` alanı + `Ekleme:` listesi (`Sona ekle` / `İmlece ekle`) + `Gönder`. `Ctrl/Cmd+Return` de gönderir. Editör, GUI'ye `ModelRequest(question, source_text, mode, offset)` geçirir; seçim varsa yalnızca bağlam olarak gönderilir, tüm belge asla "Soru" olarak yollanmaz.
- **İnceleme paneli** (dikey `PanedWindow`'un alt bölümü, öneri gelince otomatik açılır): öneri seçici (`1/3 · Satır 12 · Ekleme (+420 karakter)`), satır satır renkli fark görünümü (`line_diff`; yeşil `+`, kırmızı `−`, mavi `@@`), `✅ Kabul Et` / `❌ Reddet` / `🔄` düğmeleri. Bayat öneride kabul engellenir ve Türkçe uyarı gösterilir.
- `format_answer_block(question, answer)` yalnızca kısa (≤500 karakter) sorularda `Soru:/Yanıt:` başlığı üretir; böylece belge her turda kendi kopyasını taşımaz.

Oturum kaydetme/geri yükleme ve `.md` dışa aktarma işlemleri `WorkspaceBuffer.export_session()`
/ `import_session()` metotları üzerinden yürür; bunlara ek bir `WorkspaceManager` katmanı yoktur.
