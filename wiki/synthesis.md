---
tags: [synthesis]
date: 2026-06-05
sources: []
external_refs: []
status: active
---

# Machining Formulas - Mimari Sentez ve Teknik Borçlar

Bu sayfa projenin genel mimari durumunu, tasarım kararlarını ve çözülmesi gereken teknik borçları listeler.

## Mevcut Mimari Durum
Proje, **V3** sürümüyle birlikte modern bir mimariye kavuşmuştur:
- **Core-GUI Ayrımı:** Hesaplama formülleri ve mantığı `EngineeringCalculator` içinde soyutlanmıştır. GUI katmanı (`v3_gui.py`) ve LLM araç entegrasyonu (`AdvancedCalculator`) bu katmanı kullanır.
- **İşbirlikçi Çalışma Alanı (Workspace):** Sürüm geçmişi, AI önerileri ve eş zamanlı olmayan tamponlama yapısı `workspace/` altında başarılı şekilde ayrıştırılmıştır.
- **Dinamik Araç Tanımları:** Ollama için araç (tool) tanımları, calculator sınıfı metotlarından dinamik olarak yansıma (reflection) yoluyla üretilmektedir.

---

## Teknik Borçlar (Tech Debt)

### 1. Legacy Kod Temizliği (Çözüldü)
- **Açıklama:** Kök dizinde veya `project/` altında bulunabilecek eski GUI komut dosyaları (örn. `horz_gui.py`, `v3_gui_direct.py`) temizlenmiştir.
- **Çözüm:** Proje genelinde yapılan kontrollerle bu dosyaların tamamen silindiği ve V3 mimarisine geçişin tamamlandığı doğrulanmıştır.

### 2. Ollama API Hata Yönetimi & Hız Limitleri (Kısmen Çözüldü)
- **Açıklama:** Ollama sunucusuyla iletişim kurarken ağ kesintileri veya yavaş yanıtlar için arayüzde graceful hata yakalama (MessageBox, loglama) sağlanmıştır. Ancak retry mekanizmaları henüz eklenmemiştir.
- **Çözüm:** Arayüz katmanındaki `try...except` blokları doğrulanmıştır. Daha kapsamlı retry mantığı `ollama_utils_v2.py` içine eklenebilir.
- **Güncelleme (2026-11-03):** Tüm GUI ağ çağrıları `_run_background()` yardımcısıyla arka plan thread'ine taşındı ve sonuçlar `root.after` ile ana thread'e aktarıldı.
- **Güncelleme (2026-11-03):** Sohbet zaman aşımı 20 s'den `OLLAMA_CHAT_TIMEOUT = (10, 300)`'e çıkarıldı; Ollama'nın soğuk başlangıçta modeli belleğe yüklemesi artık zaman aşımına düşmüyor. Model listesi ve bağlantı testi de arka plana alındı (15 s / 10 s).
- **Güncelleme (2026-11-17):** Sunucu protokolü genişletildi — OpenAI-uyumlu uç noktalar (`/v1/chat/completions`, `/v1/models`) ve Ollama (`/api/chat`, `/api/tags`) birlikte desteklenir; yazılan uç nokta ilk denenir. Anahtar korumalı gateway'ler için `Authorization: Bearer` başlığı eklendi (arayüz alanı → `MACHINING_FORMULAS_API_KEY` → `STRATA_API_KEY`).

### 3. Testlerde Ollama Bağımlılığı (Çözüldü)
- **Açıklama:** Testlerin ağ erişimi veya canlı Ollama API'si olmadan çalışabilmesi gerekmektedir.
- **Çözüm:** Tüm testlerin (61 passed) mock yapısı veya izole calculator sınıflarıyla çalıştığı, canlı ağ çağrıları yapmadığı doğrulanmıştır.

### 4. Ollama Sunucu Adresi Kalıcılığı (Çözüldü)
- **Açıklama:** Varsayılan bağlantı adresi `http://localhost:11434` olarak güncellenmiş ve kullanıcının başarılı olarak bağlandığı sunucu adresi ile seçtiği model adı `settings.json` dosyası aracılığıyla kalıcı hale getirilmiştir.
- **Çözüm:** `v3_gui.py` içine `_load_settings()` ve `_save_settings()` metotları entegre edilmiştir. Uygulama açılışında son kaydedilen ayarlar yüklenmekte, her başarılı bağlantı testinde, model listesi güncellemesinde veya model değişiminde (`<<ComboboxSelected>>`) ayarlar `settings.json` dosyasına yazılmaktadır.
- **Güncelleme (2026-11-03):** Ayarlar artık kaynak ağacına değil `~/.config/machining_formulas/settings.json` konumuna atomik olarak (tmp + `os.replace`) yazılmaktadır. Konum `MACHINING_FORMULAS_CONFIG_DIR` ile değiştirilebilir.

### 5. Çokgen Şekillerde `width` Parametresi (Açık)
- **Açıklama:** `pentagon`…`decagon` hacim formülleri `width` değerini **kenar uzunluğu** olarak kullanır, ancak arayüzde alan "Genişlik" etiketiyle gösterilir. Kullanıcı bu alanı karşı köşe ölçüsü (AF) sanabilir.
- **Öneri:** Alanın `side` olarak yeniden adlandırılması ve/veya AF→kenar dönüşümü eklenmesi. Tool şemalarını da etkileyeceği için ürün kararı gerektirir.

