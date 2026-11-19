---
description: Projeyi baştan sona denetler (salt-okunur) ve önceliklendirilmiş bulgu raporu üretir
argument-hint: "[kapsam: alt dizin veya modül adı — boşsa tüm proje]"
allowed-tools: Read, Grep, Glob, Bash(git log:*), Bash(git diff:*), Bash(git status:*), Bash(find:*), Bash(wc:*), Bash(pytest:*), Bash(ruff:*)
---

# Proje Denetimi

Kapsam: **$ARGUMENTS**
(Argüman boşsa: `project/src/`, `project/tests/`, `project/tests_v3/` ve `CLAUDE.md`.)

Bu komut **salt-okunur** bir denetimdir. Bulgu bulsan bile bu turda **kod değiştirme,
dosya oluşturma veya silme**. Tek çıktı: aşağıdaki formatta rapor.

## Aşama 1 — Haritalama

Kod okumadan önce yapıyı çıkar ve rapora kısa bir "Harita" bölümü olarak ekle:

- Modül listesi ve her modülün tek cümlelik sorumluluğu
- Katman sınırları: GUI → hesaplama çekirdeği → LLM katmanı arasındaki çağrı zincirleri
- Giriş noktaları ve başlatma akışı
- Test dosyaları ile kaynak dosyalarının eşleşmesi; test edilmeyen modüller
- Tekrarlanan kod, ölü kod, kullanılmayan export'lar

## Aşama 2 — Boyut bazlı inceleme

Her boyutu **ayrı ayrı** ele al; bir boyutun bulgusunu diğerine karıştırma.
İlgili dosyaları gerçekten oku — okumadığın kod hakkında yorum yapma.

1. **Formül doğruluğu**
   - Birim tutarlılığı (mm iç uzunluk, cm³ kütle, m/min, rpm, cm³/min)
   - Kenar durumları: sıfır, negatif, eksik parametre, çok büyük değer, sıfıra bölme
   - Bilinen değerlerle akıl yürütme kontrolü (sonucu elle doğrula)

2. **Hata yönetimi ve girdi doğrulama**
   - `ValueError` kullanımı, mesajların kullanıcıya dönük Türkçe / geliştiriciye dönük İngilizce olması
   - Hataların yutulduğu (`except: pass`, sessiz fallback) yerler
   - Eksik doğrulama: tip, aralık, NaN/sonsuz değerler

3. **Güvenlik**
   - `eval`/`exec` kullanımı ve `ExecuteModeMixin` sınırları
   - LLM tool argümanlarının doğrudan çalıştırıcıya aktarılması
   - Tool parametrelerinin hesaplayıcı imzalarıyla birebir eşleşmemesi
   - Sır/anahtar sızıntısı, kullanıcı girdisinin loglanması

4. **Test gerçekliği**
   - Assert edilmeyen veya yalnızca çalıştığını doğrulayan testler
   - Mock'lanmamış dış bağımlılıklar (Ollama HTTP, GUI bileşenleri)
   - `pytest.approx()` kullanılmayan float karşılaştırmaları
   - `tests/` ile `tests_v3/` arasındaki kapsam çakışması veya boşluğu

5. **Proje standartlarına uyum (CLAUDE.md)**
   - Naming (`snake_case` / `PascalCase` / `UPPER_SNAKE_CASE`), Türkçe UI metni kuralı
   - Python 3.10+ type hint'leri, `from __future__ import annotations`
   - Import sırası: stdlib → third-party → local
   - Katman ihlalleri (GUI içinde iş mantığı, çekirdekte UI bağımlılığı)

## Aşama 3 — Rapor

Bulguları **öncelik sırasına** göre grupla. Her bulgu şu şablonu izlesin:

```
### [Kritik|Orta|İyileştirme] Kısa başlık
**Konum:** dosya:satır
**Sorun:** ne yanlış
**Neden önemli:** hangi senaryoda neyi bozar
**Öneri:** somut, uygulanabilir düzeltme
**Güven:** kesin | olası
```

Sonuna iki kısa bölüm ekle:

- **Özet tablo:** boyut başına bulgu sayısı (Kritik / Orta / İyileştirme)
- **Önerilen sıra:** en yüksek kazanç/risk oranına göre düzeltme sırası

## Kurallar

- Kanıtsız iddia üretme. Emin değilsen `olası` olarak işaretle; tahmini bulgu uydurma.
- Stil tercihini hata gibi raporlama — gerçek davranış bozukluğu ile tercih farkını ayır.
- Aynı kök nedene dayanan bulguları tek madde altında birleştir.
- Raporu sohbete yaz. Dosyaya yazma; kullanıcı ayrıca isterse o zaman kaydet.
