MATERIAL_CALCS = {
    'Kütle Hesabı': {
        'params': ['shape', 'density', 'width', 'height', 'length'],
        'units': ['', 'g/cm³', 'mm', 'mm', 'mm']
    }
}

TURNING_CALCS = {
    'Kesme Hızı': {
        'method': 'Cutting speed',
        'params': ['Dm', 'n'],
        'units': ['mm', 'rpm']
    },
    'İş Mili Devri': {
        'method': 'Spindle speed',
        'params': ['Vc', 'Dm'],
        'units': ['m/min', 'mm']
    }
}

MILLING_CALCS = {
    'Tabla İlerlemesi': {
        'method': 'Table feed',
        'params': ['fz', 'n', 'ZEFF'],
        'units': ['mm', 'rpm', 'adet']
    }
}

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from engineering_calculator import EngineeringCalculator
import json
import os
import markdown
import re
import math
from tkinter import font

ec = EngineeringCalculator()

class AdvancedCalculator:
    def __init__(self, root):
        self.root = root
        self.root.title("Mühendislik Hesaplamaları ve Analiz")
        self.root.geometry("1200x800")

        style = ttk.Style()
        style.configure('Calc.TFrame', background='#f0f0f0')
        style.configure('Calc.TLabel', background='#f0f0f0', font=('Arial', 10))
        style.configure('Calc.TButton', font=('Arial', 10))

        self.main_frame = ttk.Frame(root, style='Calc.TFrame')
        self.main_frame.pack(fill='both', expand=True, padx=10, pady=10)

        self.left_frame = ttk.Frame(self.main_frame, style='Calc.TFrame')
        self.left_frame.pack(side='left', fill='y', padx=5)

        self.calc_types = {
            'Malzeme Hesaplamaları': MATERIAL_CALCS,
            'Tornalama Hesaplamaları': TURNING_CALCS,
            'Frezeleme Hesaplamaları': MILLING_CALCS
        }

        ttk.Label(self.left_frame, text="Hesaplama Türü", style='Calc.TLabel').pack(pady=5)
        self.calc_type = ttk.Combobox(self.left_frame, values=list(self.calc_types.keys()))
        self.calc_type.pack(fill='x', pady=5)
        self.calc_type.bind('<<ComboboxSelected>>', self.update_calculations)

        ttk.Label(self.left_frame, text="Hesaplama", style='Calc.TLabel').pack(pady=5)
        self.calculation = ttk.Combobox(self.left_frame)
        self.calculation.pack(fill='x', pady=5)

        self.params_frame = ttk.Frame(self.left_frame)
        self.params_frame.pack(fill='x', pady=10)

        self.right_frame = ttk.Frame(self.main_frame)
        self.right_frame.pack(side='right', fill='both', expand=True, padx=5)

        self.result_text = scrolledtext.ScrolledText(self.right_frame, wrap=tk.WORD,
                                                   width=60, height=30,
                                                   font=('Courier', 12))
        self.result_text.pack(fill='both', expand=True)

        self.root.bind('<Control-e>', self.enable_execute_mode)
        self.root.bind('<Control-c>', self.execute_calculation)

        ttk.Button(self.left_frame, text="HESAPLA",
                  command=self.calculate, style='Calc.TButton').pack(pady=10)

    def update_calculations(self, event=None):
        calc_type = self.calc_type.get()
        if calc_type in self.calc_types:
            calcs = self.calc_types[calc_type]
            self.calculation['values'] = list(calcs.keys())
            self.calculation.set(list(calcs.keys())[0])
            self.calculation.bind('<<ComboboxSelected>>', self.update_input_fields)
            self.update_input_fields()

    def calculate(self):
        try:
            calc_type = self.calc_type.get()
            calculation = self.calculation.get()

            values = {}
            for param, field in self.input_fields.items():
                value = field.get()
                try:
                    if param != 'Şekil':
                        value = float(value)
                except ValueError:
                    raise ValueError(f"{param} için geçerli bir değer giriniz!")
                values[param] = value

            result = self.perform_calculation(calc_type, calculation, values)
            self.update_result_display({
                'calculation': calculation,
                'parameters': values,
                'result': result
            })

        except Exception as e:
            messagebox.showerror("Hata", str(e))

    def perform_calculation(self, calc_type, calculation, values):
        if calc_type == 'Malzeme Hesaplamaları':
            if calculation == 'Kütle Hesabı':
                shape_names = {
                    'triangle': 'Üçgen',
                    'circle': 'Daire',
                    'square': 'Kare',
                    'rectangle': 'Dikdörtgen',
                    'trapezium': 'Yamuk',
                    'parallelogram': 'Paralelkenar',
                    'semi-circle': 'Yarım Daire',
                    'rhombus': 'Eşkenar Dörtgen',
                    'kite': 'Uçurtma',
                    'pentagon': 'Beşgen',
                    'hexagon': 'Altıgen',
                    'octagon': 'Sekizgen',
                    'nonagon': 'Dokuzgen',
                    'decagon': 'Ongen'
                }

                shape = values['Şekil']
                shape_key = [k for k, v in shape_names.items() if v == shape][0]
                density = float(values['Yoğunluk'])

                if shape_key in ['circle', 'semi-circle']:
                    result = ec.calculate_material_mass(
                        shape_key,
                        density,
                        float(values['Yarıçap']),
                        float(values['Uzunluk'])
                    )
                else:
                    result = ec.calculate_material_mass(
                        shape_key,
                        density,
                        float(values['Genişlik']),
                        float(values['Yükseklik']),
                        float(values['Uzunluk'])
                    )
                return f"{result:.2f} gram"

        elif calc_type == 'Tornalama Hesaplamaları':
            method = self.calc_types[calc_type][calculation]['method']
            params = [float(values[p]) for p in self.calc_types[calc_type][calculation]['params']]
            result = ec.calculate_turning(method, *params)
            return f"{result['value']:.2f} {result['units']}"

        elif calc_type == 'Frezeleme Hesaplamaları':
            method = self.calc_types[calc_type][calculation]['method']
            params = [float(values[p]) for p in self.calc_types[calc_type][calculation]['params']]
            result = ec.calculate_milling(method, *params)
            return f"{result['value']:.2f} {result['units']}"

    def enable_execute_mode(self, event):
        self.result_text.config(bg='#ffffd0')
        self.execute_mode = True

    def execute_calculation(self, event):
        if not hasattr(self, 'execute_mode') or not self.execute_mode:
            return

        try:
            code = self.result_text.get('sel.first', 'sel.last')
            if code:
                local_vars = {'calc': ec, 'ec': ec, 'pi': math.pi}
                result = eval(code, {'__builtins__': {}}, local_vars)
                self.result_text.insert('insert', f'\nSonuç: {result}')
        except Exception as e:
            messagebox.showerror("Hata", f"Hesaplama hatası: {str(e)}")
        finally:
            self.execute_mode = False
            self.result_text.config(bg='white')

    def update_input_fields(self, event=None):
        # Tüm mevcut widget'ları temizle
        for widget in self.params_frame.winfo_children():
            widget.destroy()

        self.input_fields = {}  # input_fields'ı sıfırla

        calc_type = self.calc_type.get()
        calculation = self.calculation.get()

        if calc_type == 'Malzeme Hesaplamaları' and calculation == 'Kütle Hesabı':
            self.shape_names = {
                'triangle': 'Üçgen',
                'circle': 'Daire',
                'square': 'Kare',
                'rectangle': 'Dikdörtgen',
                'trapezium': 'Yamuk',
                'parallelogram': 'Paralelkenar',
                'semi-circle': 'Yarım Daire',
                'rhombus': 'Eşkenar Dörtgen',
                'kite': 'Uçurtma',
                'pentagon': 'Beşgen',
                'hexagon': 'Altıgen',
                'octagon': 'Sekizgen',
                'nonagon': 'Dokuzgen',
                'decagon': 'Ongen'
            }

            self.reverse_shape_names = {v: k for k, v in self.shape_names.items()}
            shape_values = list(self.shape_names.values())

            # Ana çerçeve
            self.params_container = ttk.Frame(self.params_frame)
            self.params_container.pack(fill='x', expand=True)

            # Şekil seçim alanı
            shape_frame = ttk.Frame(self.params_container)
            shape_frame.pack(fill='x', pady=2)
            ttk.Label(shape_frame, text="Şekil").pack(side='left')
            self.shape_combo = ttk.Combobox(shape_frame, values=shape_values)
            self.shape_combo.pack(side='right')
            self.shape_combo.set(shape_values[0])

            def update_parameters(*args):
                # Parametre alanlarını temizle
                for widget in self.params_container.winfo_children():
                    if widget != shape_frame:
                        widget.destroy()

                # input_fields'ı güncelle
                self.input_fields = {}
                self.input_fields['Şekil'] = self.shape_combo

                # Yoğunluk alanı
                density_frame = ttk.Frame(self.params_container)
                density_frame.pack(fill='x', pady=2)
                ttk.Label(density_frame, text="Malzeme/Yoğunluk [g/cm³]").pack(side='left')
                density_entry = ttk.Entry(density_frame)
                density_entry.pack(side='right')

                # Malzeme listesi için Combobox
                material_combo = ttk.Combobox(density_frame, values=list(ec.material_density.keys()))
                material_combo.pack(side='right', padx=5)

                def update_density(event=None):
                    selected_material = material_combo.get()
                    if selected_material in ec.material_density:
                        density_entry.delete(0, tk.END)
                        density_entry.insert(0, str(ec.material_density[selected_material]))

                material_combo.bind('<<ComboboxSelected>>', update_density)
                self.input_fields['Yoğunluk'] = density_entry

                # Şekle özel parametreler
                selected_shape = self.shape_combo.get()
                shape_key = self.reverse_shape_names.get(selected_shape)

                if shape_key in ['circle', 'semi-circle']:
                    params = [('Yarıçap', 'mm'), ('Uzunluk', 'mm')]
                else:
                    params = [('Genişlik', 'mm'), ('Yükseklik', 'mm'), ('Uzunluk', 'mm')]

                for param, unit in params:
                    param_frame = ttk.Frame(self.params_container)
                    param_frame.pack(fill='x', pady=2)
                    ttk.Label(param_frame, text=f"{param} [{unit}]").pack(side='left')
                    entry = ttk.Entry(param_frame)
                    entry.pack(side='right')
                    self.input_fields[param] = entry

                # Widget'ları güncelle
                self.params_container.update()

            # Şekil değişikliğini izle
            self.shape_combo.bind('<<ComboboxSelected>>', update_parameters)

            # İlk parametreleri oluştur
            update_parameters()

        else:
            calc_params = self.calc_types[calc_type][calculation]['params']
            calc_units = self.calc_types[calc_type][calculation]['units']

            for param, unit in zip(calc_params, calc_units):
                frame = ttk.Frame(self.params_frame)
                frame.pack(fill='x', pady=2)
                ttk.Label(frame, text=f"{param} [{unit}]").pack(side='left')
                entry = ttk.Entry(frame)
                entry.pack(side='right')
                self.input_fields[param] = entry

    def update_result_display(self, result_data):
        # Parametreleri daha detaylı göster
        params = result_data['parameters']
        param_text = "\n".join([f"- {k}: {v}" for k,v in params.items()])

        # Yeni hesaplama içeriği
        new_content = f"""## Giriş Parametreleri
    - Hesaplama Tipi: {self.calc_type.get()}
    - Hesaplama: {result_data['calculation']}

    ## Kullanılan Değerler
    {param_text}

    ## Sonuç
    ```plaintext
    {result_data['result']}
    ```
    """

        # İlk çalıştırmada başlığı ekle
        if not self.result_text.get(1.0, tk.END).strip():
            self.result_text.insert(1.0, "# Hesaplama Sonucu\n\n")

        # Yeni veriyi ekle
        self.result_text.insert(tk.END, new_content)

        # En sonda notu ekle
        if "## Not" not in self.result_text.get(1.0, tk.END):
            self.result_text.insert(tk.END, "\n## Not\nHesaplanan değerler yaklaşık değerlerdir.\n")


if __name__ == "__main__":
    root = tk.Tk()
    app = AdvancedCalculator(root)
    root.mainloop()
