# PySimpleGUI Hızlı Başvuru Rehberi (Cheat Sheet)

PySimpleGUI, kullanıcı arayüzü oluşturmak için kolay ve hızlı bir yol sunan bir Python kütüphanesidir. İşte temel bileşenler ve kullanım örnekleri:

## Pencere Oluşturma

```python
import PySimpleGUI as sg

layout = [  # Pencere düzeni
    [sg.Text("Merhaba PySimpleGUI!")],
    [sg.Button("Tıkla Beni")]
]

window = sg.Window("Başlık", layout)  # Pencere oluştur
```

## Butonlara Tıklama

```python
event, values = window.read()  # Kullanıcının tıklamalarını oku

if event == sg.WIN_CLOSED:
    break  # Pencereyi kapat
elif event == "Tıkla Beni":
    sg.popup("Butona Tıklandı!")
```

## Giriş Kutuları

```python
layout = [
    [sg.Text("Adınız"), sg.InputText(key="ad")],
    [sg.Button("Gönder")]
]

window = sg.Window("Form", layout)

event, values = window.read()

if event == "Gönder":
    ad = values["ad"]
    sg.popup(f"Hoşgeldin, {ad}!")
```

## Tablolar

 ```python
 import pandas as pd

data = {'Ad': ['Ali', 'Ayşe', 'Mehmet'],
        'Soyad': ['Yılmaz', 'Kara', 'Demir']}

df = pd.DataFrame(data)

layout = [
    [sg.Table(values=df.values.tolist(),
               headings=df.columns.tolist(),
               auto_size_columns=False,
               display_row_numbers=True)],
    [sg.Button("Kapat")]
]

window = sg.Window("Tablo Örneği", layout)

event, values = window.read()

if event == "Kapat" or event == sg.WIN_CLOSED:
    window.close()
 ```

## Mesaj Pencereleri

 ```python
 sg.popup("Merhaba, bu bir mesaj penceresidir.")

response = sg.popup_yes_no("Devam etmek istiyor musunuz?", title="Onay")
if response == "Yes":
    sg.popup("Devam ediliyor...")
else:
    sg.popup("İptal edildi.")
```
