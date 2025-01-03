import tkinter as tk
from tkinter import ttk, messagebox
from EngineeringCalculator import EngineeringCalculator
import json
import os

ec = EngineeringCalculator()

# Tooltips dosyası yükleme
tooltips_path = os.path.join(os.path.dirname(__file__), 'tooltips.json')
try:
    with open(tooltips_path) as f:
        tips = json.load(f)
except FileNotFoundError:
    tips = {"tip01": "", "tip02": "", "tip03": ""}
    messagebox.showerror("Hata", f"Tooltips dosyası bulunamadı: {tooltips_path}")

# Malzeme yoğunlukları sözlüğünü kontrol et
try:
    material_density = dict(ec.material_density)
    if not material_density:
        raise ValueError("Malzeme yoğunlukları boş!")
except Exception as e:
    messagebox.showerror("Hata", f"Malzeme yoğunlukları yüklenemedi: {str(e)}")
    material_density = {}

# Ana pencere oluşturma
root = tk.Tk()
root.title("Mühendislik Hesaplamaları ve Verimlilik")

# Fonksiyonlar
def calculate_mass():
    try:
        shape = shape_var.get()
        material = material_var.get()
        density = float(material_density[material])
        geos_str = geo_entry.get()
        
        # Hem virgül hem boşlukla ayır
        geos = [float(geo.strip()) for geo in geos_str.replace(',', ' ').split()]
        
        print(f"Seçilen Şekil: {shape}")
        print(f"Seçilen Malzeme: {material}")
        print(f"Yoğunluk: {density}")
        print(f"Ölçüler: {geos}")
        
        # Argümanları tek tek geç
        mass_value = ec.calculate_material_mass(shape, density, *geos)
        mass_result.set(f"Kütle: {mass_value/1000:.3f} kg")
    except ValueError as ve:
        messagebox.showerror("Hata", f"Geçersiz ölçü değerleri! Lütfen sayısal değerler girin.\nHata: {str(ve)}")
    except Exception as e:
        messagebox.showerror("Hata", f"Hesaplama hatası: {str(e)}")

# Malzeme ve şekil seçimleri
shape_definitions = list(ec.shape_definitions.keys())

material_var = tk.StringVar(value=list(material_density.keys())[0] if material_density else "")
shape_var = tk.StringVar(value=shape_definitions[0] if shape_definitions else "")

material_label = tk.Label(root, text="Malzeme Yoğunlukları")
material_label.pack()
material_menu = ttk.Combobox(root, textvariable=material_var, values=list(material_density.keys()))
material_menu.pack()

shape_label = tk.Label(root, text="Malzeme Şekilleri")
shape_label.pack()
shape_menu = ttk.Combobox(root, textvariable=shape_var, values=shape_definitions)
shape_menu.pack()

# Ölçü girişi
geo_label = tk.Label(root, text="Malzeme Ölçülerini Gir.")
geo_label.pack()
geo_entry = tk.Entry(root)
geo_entry.pack()

# Sonuç alanı
mass_result = tk.StringVar()
mass_result_label = tk.Label(root, textvariable=mass_result)
mass_result_label.pack()

# Hesapla butonu
calculate_button = tk.Button(root, text="AĞIRLIK HESAPLA", command=calculate_mass)
calculate_button.pack()

# Çıkış butonu
exit_button = tk.Button(root, text="ÇIKIŞ", command=root.quit)
exit_button.pack()

root.mainloop()
