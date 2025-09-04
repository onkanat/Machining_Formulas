# TODO Planı ve Geliştirici Promptu

Bu dosya, proje için önceliklendirilmiş görevler, kabul kriterleri ve yardımcı arama komutlarını içerir. Aşağıdaki promptu kullanarak yapay zekaya görev üretimi/sentezi yaptırabilirsiniz.

Geliştirici Promptu
- Rol: Kıdemli Python geliştiricisi ve masaüstü/LLM entegrasyonu uzmanı.
- Kaynaklar: [`EngineeringCalculator`](engineering_calculator.py), [`AdvancedCalculator`](horz_gui.py), [README](README.md), [tooltips.json](tooltips.json).
- Kısıtlar:
  - Birim tutarlılığı (mm, cm³, m/min, rpm).
  - Mevcut API: Ollama `/api/chat`, araç tanımları `_get_calculator_tools_definition`, `handle_tool_calls` ile yürütme.
  - Kod örnekleri dört backtick + `// filepath:` ile gelsin.
  - TR mesajları ve GUI etiketleri korunur.
- Çıktı: Her görev için
  - Başlık, Öncelik (P0/P1/P2), Etki, Risk, Tahmin (S/M/L)
  - Teknik adımlar (liste)
  - Kabul kriterleri (checklist)
  - Gerekli testler
  - İlgili dosyalar ve semboller linkleri

P0 (Kritik)
1) Model URL ve README tutarlılığı
- Sorun: GUI varsayılanı IP ve `/api/chat` arasında tutarsız; README `http://localhost:11434` diyor.
- Adımlar:
  - `horz_gui.py` içinde tek bir varsayılan belirle: `http://localhost:11434/api/chat`
  - README’yi buna göre güncelle.
  - Hata/timeout mesajlarını kullanıcı-dostu hale getir (örn. bağlantı başarısız ipucu).
- Kabul:
  - Varsayılan alanlar aynı
  - README talimatı birebir çalışıyor
- İlgili: [`AdvancedCalculator.__init__`](horz_gui.py), [README.md](README.md)

2) Ollama model listesini dinamik çek
- Adımlar:
  - `/api/tags` çağrısı ile model adlarını topla, `Combobox`’a yükle.
  - Hata halinde mevcut sabit listeye geri dön.
- Kabul:
  - Ağ varsa liste doluyor; yoksa graceful fallback
- Test:
  - Başarılı/başarısız HTTP yanıtlarda davranış
- İlgili: [`AdvancedCalculator.__init__`](horz_gui.py), [`requests`](horz_gui.py)

3) Ağ çağrılarında timeout ve sağlam hata işleme
- Adımlar:
  - `requests.post(..., timeout=20)` kullan
  - `RequestException`’da kullanıcıya kısa TR mesaj, loga teknik detay
- Kabul:
  - Sunucu yoksa uygulama donmuyor
- İlgili: [`AdvancedCalculator.call_ollama_api`](horz_gui.py), [`AdvancedCalculator.handle_tool_calls`](horz_gui.py)

4) Tool-calling döngüsü için kalıcı ve temiz geçmiş modellemesi
- Adımlar:
  - `get_conversation_history` sade metin yerine yapılandırılmış bir liste/alan tutsun (örn. sınıf üyesi `self.history`)
  - Tool sonuçları `role=tool` olarak eklenmeli
- Kabul:
  - En az 2 tur tool-calling ardışık çalışıp doğru yanıta ulaşıyor
- İlgili: [`AdvancedCalculator.get_conversation_history`](horz_gui.py), [`AdvancedCalculator.handle_tool_calls`](horz_gui.py)

P1 (Önemli)
5) Şekil formüllerinin doğrulanması ve parametre isimlendirmesi
- Not: [`trapezium`](engineering_calculator.py) formülü kodda “alışılmadık” olarak not düşülmüş.
- Adımlar:
  - Yamuk için tabana uygun alan: A = (a+b)/2*h; ekstrüzyonda V = A*length olacak şekilde argüman sırası yeniden düzenlenebilir (geri uyumluluk notu)
  - Gerekirse yeni anahtar (`trapezoid`) ekle ve eskisini “deprecated” yap
- Kabul:
  - Birim testlerle doğrulama (bilinen örneklerle ±1e-6 hassasiyet)
- İlgili: `shape_definitions` içinde `trapezium`, [`EngineeringCalculator.get_shape_parameters`](engineering_calculator.py)

6) Birim testleri ekle (pytest)
- Adımlar:
  - `tests/test_engineering_calculator.py`: triangle/circle/kare hacim/kütle, turning/milling örnekleri
  - Hata yolları: geçersiz shape, eksik arg, tip hatası
- Kabul:
  - Tüm testler geçer; temel kapsam > %80 çekirdek hesaplarda
- İlgili: [`EngineeringCalculator.*`](engineering_calculator.py)

7) `execute_mode` güvenliği ve UX
- Adımlar:
  - “Açık uyarı” başlığı ve kısa rehber
  - Uzun seçimlerde eval iptali; hatalarda güvenli kapanış
- Kabul:
  - Hatalı kodda uygulama stabil, mod her zaman kapanıyor
- İlgili: [`AdvancedCalculator.execute_calculation`](horz_gui.py)

8) Tool parametre isimlerinin belirsizliklerini azaltma
- Adımlar:
  - Kütle hesabında şekil-özel parametrelere daha belirgin açıklama: `_get_calculator_tools_definition` açıklamalarını genişlet
  - Gerekirse şekil-başı ayrı tool tanımları üret (isteğe bağlı)
- Kabul:
  - Model yanlış parametre adı üretmiyor (manüel test)
- İlgili: [`AdvancedCalculator._get_calculator_tools_definition`](horz_gui.py), [`EngineeringCalculator.get_shape_parameters`](engineering_calculator.py)

P2 (İyileştirmeler)
9) Akış (stream) desteği
- Adımlar:
  - `stream=True` yolunu deneysel ekle; parça-parça çıktı ile `result_text`’e yaz
- Kabul:
  - Tool-calling ile çakışmadan çalışır veya devre dışı bırakılır
- İlgili: [`AdvancedCalculator.call_ollama_api`](horz_gui.py)

10) Loglama ve tanılama
- Adımlar:
  - Basit `logging` ekle, GUI’ye “Geliştirici Modu” ile log düzeyi seçimi
- Kabul:
  - Hata analizi kolaylaşır, kullanıcıya gürültü yapılmaz

11) Paketleme ve CLI
- Adımlar:
  - Basit CLI komutları: örn. `--turning "Cutting speed" --Dm 120 --n 100`
- Kabul:
  - GUI olmadan hesaplama yapılabilir

Kabul Kriterleri ve Testler için Şablon
- [ ] Formül/birim doğruluğu örnekle test edildi
- [ ] Hata mesajları TR ve anlaşılır
- [ ] Değişiklikler README veya dosya içi docstring ile belgelendi
- [ ] Pytest hedefleri geçiyor

VS Code Arama Sorguları
- Trapezium incele:
  - `files to include: **/engineering_calculator.py` | `regex: trapezium`
- Model URL tutarlılığı:
  - `files to include: **/horz_gui.py` | `query: 11434`
  - `files to include: **/README.md` | `query: localhost:11434`
- Tool-calling alanları:
  - `files to include: **/horz_gui.py` | `query: tool_calls`
  - `files to include: **/horz_gui.py` | `query: _get_calculator_tools_definition`
- Hata mesajları:
  - `files to include: **/*.py` | `query: messagebox.showerror`

Terminal Komutları (macOS)
- Sanal ortam (opsiyonel):
  - `python3 -m venv .venv && source .venv/bin/activate`
- Bağımlılıklar:
  - `pip install -r requirements.txt pytest`
- Testler:
  - `python -m pytest -q`

İlgili Dosyalar
- Çekirdek: [`engineering_calculator.py`](engineering_calculator.py)
- GUI/LLM: [`horz_gui.py`](horz_gui.py)
- Dokümantasyon: [`README.md`](README.md), [`tooltips.json`](tooltips.json)