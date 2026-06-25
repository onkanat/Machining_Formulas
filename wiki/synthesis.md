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

### 3. Testlerde Ollama Bağımlılığı (Çözüldü)
- **Açıklama:** Testlerin ağ erişimi veya canlı Ollama API'si olmadan çalışabilmesi gerekmektedir.
- **Çözüm:** Tüm testlerin (50 passed) mock yapısı veya izole calculator sınıflarıyla çalıştığı, canlı ağ çağrıları yapmadığı doğrulanmıştır.

### 4. Ollama Sunucu Adresi Kalıcılığı (Açık Teknik Borç)
- **Açıklama:** `ollama_utils.py` (L19) ve `v3_gui.py` (L70) dosyalarında varsayılan Ollama adresi olarak `http://192.168.1.14:11434` adresi hardcoded olarak tanımlanmıştır. Kullanıcının son başarılı bağlantı kurduğu adres kalıcı hale getirilmemektedir.
- **Çözüm:** Varsayılan olarak `localhost` adresi kullanılmalı ve son başarılı bağlantı adresi yerel bir yapılandırma dosyası (örn. `.config` veya `settings.json`) aracılığıyla saklanarak uygulama açılışında oradan yüklenmelidir.

