---
tags: [concept]
date: 2026-06-05
sources: [project/tests/]
external_refs: []
status: active
---

# Test ve Birim Standartları

Bu döküman, projedeki test gereksinimlerini, birim standartlarını ve mock stratejilerini açıklar.

## Test Altyapısı ve Komutlar

Projede testler için `pytest` kütüphanesi kullanılır. Test dosyaları `project/tests/` ve `project/tests_v3/` dizinlerinde yer alır.
- **Tüm testleri çalıştırma:** `pytest project/tests/` (veya `PYTHONPATH=project/src pytest project/tests/`)
- **Verbose modda çalıştırma:** `pytest -v project/tests/`
- **Tek bir testi çalıştırma:** `pytest project/tests/test_engineering_calculator.py::test_turning_calculations`

---

## Test Yazım Kuralları

Yeni bir formül veya hesaplama eklendiğinde aşağıdaki kurallara uyulmalıdır:

### 1. Float Karşılaştırmaları (`pytest.approx`)
Hassas sayısal hesaplamalarda yuvarlama hatalarını engellemek için doğrudan `==` operatörü yerine `pytest.approx()` kullanılmalıdır:
```python
assert pytest.approx(res_speed["value"], 0.01) == 157.08
```

### 2. Hata Durumlarının Test Edilmesi (`pytest.raises`)
Geçersiz girdi veya eksik parametre durumlarında fırlatılan istisnaların (ValueError) doğru şekilde yakalandığı test edilmelidir:
```python
with pytest.raises(ValueError, match="Invalid shape"):
    ec.calculate_material_mass("invalid_shape", 7.85, 10, 20)
```

### 3. Ollama ve API İsteklerinin Mock'lanması
Ağ bağımlılığını kesmek için Ollama API istekleri testler sırasında mutlaka mock'lanmalıdır (`requests_mock` veya `unittest.mock` yardımıyla). Testler gerçek bir Ollama sunucusuna ihtiyaç duymadan başarıyla sonlanmalıdır.

---

## Birim Tutarlılığı (Unit Consistency)

Hesaplamalarda aşağıdaki birimler standart olarak kabul edilmiştir:
- **Uzunluk (Internal Length):** mm. Ekran gösterimlerinde gerektiğinde dönüştürülür.
- **Hacim (Volume):** Dahili hesaplamalarda mm³, kütle hesaplaması için ise cm³ cinsine dönüştürülür ($1 cm^3 = 1000 mm^3$).
- **Kütle (Mass):** Gram (g). Formül çıktıları gram cinsinden üretilir.
- **Hızlar:** m/min (kesme hızı Vc), rpm (iş mili hızı n).
- **İlerleme Oranları:** mm/rev (devir başına), mm/min (tabla ilerleme hızı Vf).
- **Talaş Kaldırma Oranı (MRR):** cm³/min.
