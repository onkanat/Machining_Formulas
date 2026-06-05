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

### 1. Legacy Kod Temizliği
- **Açıklama:** Kök dizinde yer alabilecek eski GUI komut dosyaları (örneğin `horz_gui.py`, `v3_gui_direct.py`) varsa, bunlar V3 mimarisinin yerine geçmemelidir.
- **Çözüm:** Bu dosyalar analiz edilmeli ve işlevleri tamamen V3'e aktarıldıktan sonra silinmelidir.

### 2. Ollama API Hata Yönetimi & Hız Limitleri
- **Açıklama:** Ollama sunucusuyla iletişim kurarken ağ kesintileri veya yavaş yanıtlar için timeout 20 saniye olarak belirlenmiştir. Ancak sunucu çevrimdışı olduğunda kullanıcı arayüzünde daha yumuşak (graceful) hata mesajları gösterilmelidir.
- **Çözüm:** `ollama_utils_v2.py` içindeki API çağrılarına daha kapsamlı hata yakalama ve retry mekanizmaları eklenmelidir.

### 3. Testlerde Ollama Bağımlılığı
- **Açıklama:** Bazı testler Ollama API'sinin ayakta olmasını bekleyebilir veya varsayabilir.
- **Çözüm:** Ollama bağımlı testlerin tamamının ağ erişimi gerektirmeyecek şekilde mock'landığından emin olunmalıdır.
