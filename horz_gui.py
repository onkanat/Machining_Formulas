# Global variables for calculation parameters and GUI controls
MATERIAL_CALCS = {
    'Kütle Hesabı': {
        'params': ['Şekil', 'Yoğunluk', 'Genişlik', 'Yükseklik', 'Uzunluk'],
        'units': ['', 'g/cm³', 'mm', 'mm', 'mm']
    },
    'Yoğunluk Hesabı': {
        'params': ['Kütle', 'Hacim'],
        'units': ['g', 'cm³']
    }
}

TURNING_CALCS = {
    'Kesme Hızı': {
        'params': ['İşlenen Çap', 'İş Mili Devri'],
        'units': ['mm', 'rpm']
    },
    'İş Mili Devri': {
        'params': ['Kesme Hızı', 'İşlenen Çap'],
        'units': ['m/min', 'mm']
    },
    'Metal Kaldırma': {
        'params': ['Kesme Hızı', 'Kesme Derinliği', 'İlerleme'],
        'units': ['m/min', 'mm', 'mm/r']
    }
}

MILLING_CALCS = {
    'Tabla İlerlemesi': {
        'params': ['Diş Başı İlerleme', 'İş Mili Devri', 'Efektif Diş Sayısı'],
        'units': ['mm', 'rpm', 'adet']
    },
    'Kesme Hızı': {
        'params': ['Kesici Çap', 'İş Mili Devri'],
        'units': ['mm', 'rpm']
    },
    'Tork': {
        'params': ['Net Güç', 'İş Mili Devri'],
        'units': ['kW', 'rpm']
    }
}

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from engineering_calculator import EngineeringCalculator
import json
import os
import markdown
import re
from tkinter import font

ec = EngineeringCalculator()

class AdvancedCalculator:
    def __init__(self, root):
        self.root = root
        self.root.title("Mühendislik Hesaplamaları ve Analiz")
        self.root.geometry("1200x800")

        # Stil ayarları
        style = ttk.Style()
        style.configure('Calc.TFrame', background='#f0f0f0')
        style.configure('Calc.TLabel', background='#f0f0f0', font=('Arial', 10))
        style.configure('Calc.TButton', font=('Arial', 10))

        # Ana frame
        self.main_frame = ttk.Frame(root, style='Calc.TFrame')
        self.main_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # Sol panel - Hesaplama kontrolleri
        self.left_frame = ttk.Frame(self.main_frame, style='Calc.TFrame')
        self.left_frame.pack(side='left', fill='y', padx=5)

        # Hesaplama türü seçimi
        self.calc_types = {
            'Malzeme Hesaplamaları': ['Kütle Hesabı', 'Yoğunluk Hesabı'],
            'Tornalama Hesaplamaları': ['Kesme Hızı', 'İş Mili Devri', 'Metal Kaldırma'],
            'Frezeleme Hesaplamaları': ['Tabla İlerlemesi', 'Kesme Hızı', 'Tork']
        }

        ttk.Label(self.left_frame, text="Hesaplama Türü", style='Calc.TLabel').pack(pady=5)
        self.calc_type = ttk.Combobox(self.left_frame, values=list(self.calc_types.keys()))
        self.calc_type.pack(fill='x', pady=5)
        self.calc_type.bind('<<ComboboxSelected>>', self.update_calculations)

        ttk.Label(self.left_frame, text="Hesaplama", style='Calc.TLabel').pack(pady=5)
        self.calculation = ttk.Combobox(self.left_frame)
        self.calculation.pack(fill='x', pady=5)

        # Parametre girişleri
        self.params_frame = ttk.Frame(self.left_frame)
        self.params_frame.pack(fill='x', pady=10)

        # Sağ panel - Sonuç ve markdown görüntüleme
        self.right_frame = ttk.Frame(self.main_frame)
        self.right_frame.pack(side='right', fill='both', expand=True, padx=5)

        # Markdown/LaTeX görüntüleme alanı
        self.result_text = scrolledtext.ScrolledText(self.right_frame, wrap=tk.WORD,
                                                   width=60, height=30,
                                                   font=('Courier', 12))
        self.result_text.pack(fill='both', expand=True)

        # Kısayol tuşları
        self.root.bind('<Control-e>', self.enable_execute_mode)
        self.root.bind('<Control-c>', self.execute_calculation)

        # Hesaplama butonu
        ttk.Button(self.left_frame, text="HESAPLA",
                  command=self.calculate, style='Calc.TButton').pack(pady=10)

    def update_calculations(self, event=None):
        calc_type = self.calc_type.get()
        if calc_type in self.calc_types:
            self.calculation['values'] = self.calc_types[calc_type]
            self.calculation.set(self.calc_types[calc_type][0])

    def calculate(self):
        try:
            calc_type = self.calc_type.get()
            calculation = self.calculation.get()

            result = self.perform_calculation(calc_type, calculation)

            # Markdown formatında sonuç oluştur
            md_text = f"""
# Hesaplama Sonucu

## Parametreler
- Hesaplama Türü: {calc_type}
- Hesaplama: {calculation}

## Sonuç
```python
{result}
```
"""
            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(1.0, md_text)

        except Exception as e:
            messagebox.showerror("Hata", str(e))

    def perform_calculation(self, calc_type, calculation):
        if calc_type == "Malzeme Hesaplamaları":
            return ec.calculate_material_mass("triangle", 7.85, 10, 20, 30)
        elif calc_type == "Tornalama Hesaplamaları":
            return ec.calculate_turning("Cutting speed", 120, 100)
        elif calc_type == "Frezeleme Hesaplamaları":
            return ec.calculate_milling("Table feed", 0.1, 100, 3)

def enable_execute_mode(self, event):
    """CTRL+E ile hesaplama modunu etkinleştir"""
    self.result_text.config(bg='#ffffd0')
    self.execute_mode = True

def execute_calculation(self, event):
    """CTRL+C ile seçili kodu çalıştır"""
    if not hasattr(self, 'execute_mode') or not self.execute_mode:
        return

    try:
        # Seçili metni al
        code = self.result_text.get('sel.first', 'sel.last')
        if code:
            # Güvenli hesaplama ortamı oluştur
            local_vars = {'calc': ec, 'ec': ec, 'pi': math.pi}
            result = eval(code, {'__builtins__': {}}, local_vars)

            # Sonucu ekle
            self.result_text.insert('insert', f'\nSonuç: {result}')

    except Exception as e:
        messagebox.showerror("Hata", f"Hesaplama hatası: {str(e)}")
    finally:
        self.execute_mode = False
        self.result_text.config(bg='white')

    def update_input_fields(self):
        # Mevcut giriş alanlarını temizle
        for widget in self.params_frame.winfo_children():
            widget.destroy()

        calc_type = self.calc_type.get()
        calculation = self.calculation.get()

        # Seçime göre gerekli giriş alanlarını oluştur
        if calc_type == "Malzeme Hesaplamaları":
            if calculation == "Kütle Hesabı":
                ttk.Label(self.params_frame, text="Şekil:").pack()
                self.shape_input = ttk.Combobox(self.params_frame,
                    values=list(ec.shape_definitions.keys()))
                self.shape_input.pack()

                ttk.Label(self.params_frame, text="Malzeme:").pack()
                self.material_input = ttk.Combobox(self.params_frame,
                    values=list(ec.material_density.keys()))
                self.material_input.pack()

                ttk.Label(self.params_frame, text="Boyutlar (mm):").pack()
                self.dimensions = []
                for i in range(3):
                    entry = ttk.Entry(self.params_frame)
                    entry.pack()
                    self.dimensions.append(entry)

    # markdown/LaTeX görünümü için text alanının geliştirilmesi.
    def update_result_display(self, result_data):
        md_text = f"""
    # Hesaplama Sonucu

    ## Giriş Parametreleri
    - Hesaplama: {result_data['calculation']}
    - Malzeme: {result_data.get('material', '-')}
    - Yoğunluk: {result_data.get('density', '-')} g/cm³

    ## Sonuç
    ```plaintext
    {result_data['result']} {result_data.get('units', '')}
    ```

    ## Formül
    $V = \\pi r^2 h$ (Örnek LaTeX formül)
    """
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(1.0, md_text)


if __name__ == "__main__":
    root = tk.Tk()
    app = AdvancedCalculator(root)
    root.mainloop()
