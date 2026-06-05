# LLM Coder Pattern Guide

Bu dosya, projede çalışan yapay zeka etmenlerinin (AI Agents) projenin mimarisini ve tasarım kararlarını unutmadan, sıfır halüsinasyonla çalışmasını sağlayan **LLM Coder (Agent-First)** yazılım geliştirme örüntüsünü açıklar.

## Felsefe: "Kod Gövdedir, Wiki Zihindir"

Büyük kod tabanlarında tüm kodun bağlama (context) yüklenmesi token tüketimini şişirir ve etmenin odaklanmasını zorlaştırır. LLM Coder düzeninde etmenler:
1. Kod tabanını canlı değiştirmek üzere `project/` dizininde çalışır.
2. Kodun "hafızası" ve mimari kararlarını ise `wiki/` dizininde saklar.

---

## Proje Yapısı (Project Structure)

```
Machining_Formulas/
├── project/                  # Projenin Canlı Kod Tabanı (Yazılabilir)
│   ├── src/                  # Kaynak kodlar
│   ├── tests/                # Birim ve entegrasyon testleri
│   └── ...
├── wiki/                     # Kodun Mimarisi ve Hafızası (Etmen Tarafından Yönetilir)
│   ├── index.md              # Kod Fihristi - Hangi modül nerede, ne işe yarar?
│   ├── log.md                # Geliştirme Günlüğü (Kronolojik)
│   ├── synthesis.md          # Mimari sentez ve teknik borçlar (Tech Debt)
│   ├── entities/             # Kod Bileşenleri (Sınıflar, modeller, API uçları)
│   ├── concepts/             # Tasarım Kalıpları ve Proje Kuralları
│   └── queries/              # Çözülen Buglar ve Teknik Analiz Arşivi
├── CLAUDE.md                 # Projeye Özgü Çalışma ve Komut Yönergesi
└── llmcoder.md               # Bu rehber dokümanı
```

---

## Temel İş Akışları (Workflows)

### 1. Algı, Hizalama ve Onay (Alignment & Gateway)
Geliştirici yeni bir özellik veya değişiklik istediğinde doğrudan kod yazmaya başlanmaz:
1. **Dinamik Getirme:** İlk olarak `wiki/index.md` fihristini okuyup, ilgili modülleri tespit edin ve sadece göreve özgü 2-3 dokümanı bağlama (context) dahil edin.
2. **Kuralları Kontrol Etme:** `CLAUDE.md` dosyasındaki proje kurallarına ve `wiki/concepts/` altındaki mimari standartlara bakın.
3. **Onay Bariyeri:** Yapılacak mimari değişiklikleri ve kod planını geliştiriciye sunun. Geliştiriciden onay almadan kod yazmaya geçmeyin.

### 2. Korumalı Kodlama ve Senkronizasyon (Ingest & Sync)
Geliştirici planı onayladıktan sonra:
1. Değişiklikleri `project/` dizini altındaki kod tabanına uygulayın.
2. Projeye uygun derleme, formatlama ve test komutlarını (`CLAUDE.md` içinde belirtilen) çalıştırarak doğruluğu test edin. Testi geçemeyen kodu işlemeyin.
3. Değişen sınıflar, fonksiyonlar veya veri modelleri için `wiki/entities/` altında ilgili dökümanı güncelleyin veya oluşturun.
4. Yapılan teknik değişikliği kronolojik olarak `wiki/log.md` dosyasına tek satırlık bir girdi olarak ekleyin.
5. Değişen dizin veya modül yapılarına göre `wiki/index.md` fihristini güncel tutun.

### 3. Kod Kalitesi ve Denetim (Lint & Audit)
Periyodik olarak projeyi analiz etmek ve teknik borçları belirlemek için:
1. `wiki/` altındaki mimari kararlar ile `project/` altındaki fiili kodu karşılaştırın.
2. Koddaki tutarsızlıkları, tamamlanmamış `TODO` ve teknik borçları yakalayın.
3. Bulgularınızı `wiki/synthesis.md` altındaki **"Teknik Borçlar"** başlığına kaydedin.

---

## Dokümantasyon Standartları (Documentation Standards)

1. **YAML Frontmatter Zorunluluğu:** Tüm `wiki/` markdown dosyaları şu başlıkla başlamalıdır:
   ```yaml
   ---
   tags: [entity/concept/query/log]
   date: YYYY-MM-DD
   sources: [ilgili-kod-dosyalari]
   external_refs: [katalog-linkleri/pdf-referanslari/api-dokumanlari]
   status: [active/draft/deprecated]
   ---
   ```
2. **Sayfa Bağlantıları:** Sayfalar arası geçişlerde Obsidian tarzı `[[sayfa-adi]]` veya standard markdown `[sayfa-adi](link)` bağlantı biçimi kullanılmalıdır.
3. **Dış Kaynak Referansları:** Donanım spesifikasyonları, kataloglar, PDF'ler veya üçüncü parti API dökümanları mutlaka YAML frontmatter içerisindeki `external_refs` alanında kayıt altına alınmalıdır.
