# TODO Planı ve Geliştirici Promptu

Bu dosya, proje için önceliklendirilmiş görevler, kabul kriterleri ve yardımcı arama komutlarını içerir. Aşağıdaki promptu kullanarak yapay zekaya görev üretimi/sentezi yaptırabilirsiniz.

Geliştirici Promptu
- Rol: Kıdemli Python geliştiricisi ve masaüstü/LLM entegrasyonu uzmanı.
- Kaynaklar: [`EngineeringCalculator`](engineering_calculator.py), [`AdvancedCalculator`](horz_gui.py), [`ollama_utils`](ollama_utils.py), [`material_utils`](material_utils.py), [`execute_mode`](execute_mode.py), [README](README.md), [tooltips.json](tooltips.json).
- Kısıtlar:
  - Birim tutarlılığı (mm, cm³, m/min, rpm).
  - Ollama entegrasyonu `ollama_utils` yardımcılarıyla yönetilir; varsayılan chat endpoint’i `http://localhost:11434/v1/chat`, `/api/chat` yedeği mevcut.
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
- Sorun: Varsayılan `http://localhost:11434/v1/chat` yönergeleri ve README henüz tam eşitlenmedi.
- Adımlar:
  - README’deki kurulum ve ekran görüntüsü açıklamalarını `v1/chat` değerine göre güncelle.
  - `Model URL` giriş alanı ipucu ve hata/timeout mesajlarında kullanıcıya bağlantı önerileri (örn. Ollama ayakta mı?) ekle.
  - Manual QA: GUI’den varsayılan değerle başarılı istek atılabildiğini doğrula.
- Kabul:
  - Varsayılan URL tüm belgelerde aynı.
  - Kullanıcı hata mesajında nasıl düzelteceğini anlıyor.
- İlgili: [`AdvancedCalculator.__init__`](horz_gui.py), [`AdvancedCalculator._handle_request_error`](horz_gui.py), [README.md](README.md)

2) Model listesi ve URL yardımcılarının test edilmesi
- Adımlar:
  - `ollama_utils` fonksiyonları için ünite testleri yaz (`normalize_chat_url`, `candidate_chat_urls`, `candidate_tags_urls`).
  - `refresh_model_list` çağrısı için başarısız HTTP senaryosunu taklit eden test ekle.
  - Başarılı ve başarısız durumlarda Combobox içeriğini doğrula.
- Kabul:
  - Testler hem `/v1` hem `/api` senaryolarını kapsıyor.
  - Hata durumunda fallback listesi atanıyor.
- İlgili: [`ollama_utils.py`](ollama_utils.py), [`AdvancedCalculator.refresh_model_list`](horz_gui.py), [`tests/`](tests)

3) Ağ çağrılarında timeout ve kullanıcı dostu hata işleme
- Adımlar:
  - `call_ollama_api` ve `handle_tool_calls` içinde timeout’u `20s` olarak sabitle, status bar mesajlarını güncelle.
  - `requests.exceptions.RequestException` ve JSON parse hataları için Türkçe kısa mesaj + log detayı ekle.
  - Manuel test: Sunucu kapalıyken GUI donmadan toparlanıyor.
- Kabul:
  - Timeout sonrası tek seferlik yeniden deneme çalışıyor veya kullanıcıya net uyarı veriliyor.
  - Loglar teknik ayrıntıyı, GUI ise sade mesajı içeriyor.
- İlgili: [`AdvancedCalculator.call_ollama_api`](horz_gui.py), [`AdvancedCalculator.handle_tool_calls`](horz_gui.py)

4) Tool-calling döngüsü için çok turlu regresyonlar
- Adımlar:
  - `tests/test_handle_tool_calls.py` gezinmesini genişlet: art arda iki tool çağrısı ve fallback senaryosu.
  - `material_utils.prepare_material_mass_arguments` için edge-case testleri (eksik uzunluk, çap metin eşlemesi) ekle.
  - `self.history` içine role=tool kayıtlarının sırasını doğrula.
- Kabul:
  - Başarılı + başarısız tool çağrıları doğru sayıda history girdisi üretiyor.
  - fallback kütle hesabı doğru birimlerde sonuç dönüyor.
- İlgili: [`AdvancedCalculator.handle_tool_calls`](horz_gui.py), [`material_utils.py`](material_utils.py), [`tests/test_handle_tool_calls.py`](tests/test_handle_tool_calls.py)

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
  - ExecuteModeMixin’de uyarı metinlerini konsolide et; GUI’ye kısa rehber ekle.
  - Çok satırlı seçimlerde 2 kB sınırı koy ve kullanıcıya uyarı göster.
- Kabul:
  - Hatalı kodda uygulama stabil, mod her zaman kapanıyor.
  - Limit aşımında eval tetiklenmeden güvenli şekilde kapanıyor.
- İlgili: [`execute_mode.py`](execute_mode.py), [`AdvancedCalculator.enable_execute_mode`](horz_gui.py)

8) Tool parametre isimlerinin belirsizliklerini azaltma
- Adımlar:
  - `ollama_utils.build_calculator_tools_definition` açıklamalarını, şekil-özel parametreler için Türkçe karşılıklarla zenginleştir.
  - Material mass tool’u için örnek argüman seti ekle (docs ölçülü).
- Kabul:
  - Model yanlış parametre adı üretmiyor (manüel test).
- İlgili: [`ollama_utils.py`](ollama_utils.py), [`EngineeringCalculator.get_shape_parameters`](engineering_calculator.py)

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
  - `files to include: **/horz_gui.py` | `query: v1/chat`
  - `files to include: **/ollama_utils.py` | `query: DEFAULT_CHAT_URL`
  - `files to include: **/README.md` | `query: localhost:11434`
- Tool-calling alanları:
  - `files to include: **/horz_gui.py` | `query: tool_calls`
  - `files to include: **/horz_gui.py` | `query: _parse_tool_call`
  - `files to include: **/ollama_utils.py` | `query: build_calculator_tools_definition`
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
- Yardımcılar: [`ollama_utils.py`](ollama_utils.py), [`material_utils.py`](material_utils.py), [`execute_mode.py`](execute_mode.py)
- Dokümantasyon: [`README.md`](README.md), [`tooltips.json`](tooltips.json)