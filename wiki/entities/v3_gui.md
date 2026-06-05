---
tags: [entity]
date: 2026-06-05
sources: [project/src/machining_formulas/gui/v3_gui.py]
external_refs: []
status: active
---

# V3 GUI (V3Calculator)

`V3Calculator`, uygulamanın Tkinter tabanlı gelişmiş masaüstü arayüzünü yöneten ana sınıftır. Gelişmiş pencere yönetimi, dinamik form oluşturma, etkileşimli referans görselleri ve işbirlikçi çalışma alanı panellerini barındırır.

## Temel Özellikler

### 1. Pencere Yönetimi (Window Management)
macOS ve Python Launcher ortamlarında kullanıcı deneyimini iyileştirmek için özel başlatma adımları içerir:
- **Gizleme (`withdraw`):** Uygulama başlarken konumlandırılmamış küçük pencerenin anlık görünmesini engellemek için ana pencere ilk etapta gizlenir.
- **Ortalama ve Boyutlandırma:** Ekran çözünürlüğü algılanarak varsayılan `1400x900` penceresi ekranın ortasında konumlandırılır.
- **Odak Yakalama:** Başlangıçta `-topmost` niteliği geçici olarak etkinleştirilerek odağın kesin bir şekilde uygulamaya gelmesi sağlanır.

### 2. Etkileşimli Referans Görselleri (Hover Popups)
Her talaşlı imalat sekmesinin (Tornalama, Frezeleme, Delme, Malzeme) üstünde referans bir grafik yer alır:
- **Pillow & Canvas:** Pillow kütüphanesi ile PNG görselleri dinamik ölçeklenir ve `tk.Canvas` üzerinde çizilir.
- **Büyütme Efekti:** Kullanıcı fareyi canvas üzerine getirdiğinde (`<Enter>` tetiklenmesi), `480x480` piksel sınırlarında yüksek kaliteli bir pop-up pencere açılır.
- **Güvenli Hizalama (Safe Offset):** Fare imleci ile pop-up arasında titremeyi (flickering) engellemek için 25 piksellik güvenli bir mesafe (offset) bırakılır.
- **Ekran Sınırı Kontrolü:** Pop-up'ın ekran dışına taşmasını engellemek için kenar hizalaması otomatik kontrol edilir.

### 3. Dinamik Hesaplama Formları
Tornalama, frezeleme ve delme işlemleri için dropdown listesinden bir metot seçildiğinde (`Spindle speed` vb.):
- `_dynamic_calc_rebuild_params` metodu, `EngineeringCalculator.get_calculation_params` meta verisini okuyarak ilgili form alanlarını (Entry) ve birim etiketlerini (Label) anında yeniden oluşturur.
- Giriş yapılan değerler "Hesapla" butonuna basıldığında doğrulanır ve çalışma alanına eklenebilecek duruma getirilir.

---

## Klavye Kısayolları (Shortcuts)

| Kısayol | İşlev |
| :--- | :--- |
| **Ctrl+N** (veya Cmd+N) | Yeni Çalışma Alanı |
| **Ctrl+O** (veya Cmd+O) | Çalışma Alanı Aç |
| **Ctrl+S** (veya Cmd+S) | Çalışma Alanı Kaydet |
| **Ctrl+E** (veya Cmd+E) | Markdown Olarak Dışa Aktar |
| **Ctrl+1 / 2 / 3 / 4** | Sekmeler Arası Geçiş (Tornalama, Frezeleme, Malzeme, Delme) |
| **Ctrl+Shift+A** | Çalışma Alanını AI ile Analiz Et |
| **Ctrl+Z / Y** | Düzenlemede Geri Al / İleri Al |
