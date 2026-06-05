---
tags: [entity]
date: 2026-06-05
sources: [project/src/machining_formulas/workspace/workspace_buffer.py, project/src/machining_formulas/workspace/workspace_editor.py, project/src/machining_formulas/workspace/workspace_manager.py]
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
  - `suggest_edit(start, end, text, description)`: Modelin önerdiği bir değişikliği kaydeder (`accepted=False` olarak).
  - `accept_suggestion(edit_id)` / `reject_suggestion(edit_id)`: Modelin önerilerini kabul eder veya reddeder.
  - `restore_version(version_id)`: Eski bir sürüme geri döner (Undo/Redo mantığı).
  - `export_session()` / `import_session(data)`: Tüm oturumu JSON formatında kaydeder veya yükler.

### 2. `WorkspaceEditor`
Tkinter'in `Text` bileşenini sarmalayarak kullanıcı arayüzünü sunar:
- Metin değişikliklerini dinleyerek anlık olarak `WorkspaceBuffer`'ı günceller.
- Markdown metin biçimlendirmelerini destekler.
- Modelden gelen önerileri (suggestions) arayüzde özel renklerle (örneğin kabul edilmeyi bekleyen yeşil bloklar halinde) gösterir, kullanıcının "Kabul Et" veya "Reddet" butonlarına basabilmesi için arayüz sağlar.

### 3. `WorkspaceManager`
Çalışma alanının yerel dosyalarla olan ilişkisini yönetir:
- Oturumu kaydetme (`.json` formatında, tüm düzenleme geçmişi dahil).
- Oturumu geri yükleme.
- Metni dışa aktarma (`.md` formatında, sadece canlı metin çıktısı).
