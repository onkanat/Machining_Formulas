#! /opt/miniconda3/bin/python
# -*- coding : utf-8 -*-#
# Autor:Hakan KILIÇASLAN 2025

MATERIAL_CALCS = {'Kütle Hesabı': {
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
    },
    'İlerleme Hızı': {
        'method': 'Feed rate',
        'params': ['f', 'n'],
        'units': ['mm/dev', 'rpm']
    },
    'Talaş Debisi': {
        'method': 'Metal removal rate',
        'params': ['Vc', 'ap', 'fn'],
        'units': ['m/min', 'mm', 'mm/dev']
    },
    'Net Güç': {
        'method': 'Net power',
        'params': ['Vc', 'ap', 'fn', 'kc'],  # kc parametresi eklendi
        'units': ['m/min', 'mm', 'mm/dev', 'N/mm²']
    },
    'İşleme Süresi': {
        'method': 'Machining time',
        'params': ['L', 'f', 'n'],
        'units': ['mm', 'mm/dev', 'rpm']
    }
}

MILLING_CALCS = {
    'Tabla İlerlemesi': {
        'method': 'Table feed',
        'params': ['fz', 'n', 'ZEFF'],
        'units': ['mm', 'rpm', 'adet']
    },
    'Kesme Hızı': {
        'method': 'Cutting speed',
        'params': ['D', 'n'],
        'units': ['mm', 'rpm']
    },
    'İş Mili Devri': {
        'method': 'Spindle speed',
        'params': ['Vc', 'D'],
        'units': ['m/min', 'mm']
    },
    'Talaş Debisi': {
        'method': 'Metal removal rate',
        'params': ['ap', 'ae', 'Vf'],
        'units': ['mm', 'mm', 'mm/min']
    },
    'Diş Başına İlerleme': {
        'method': 'Feed per tooth',
        'params': ['Vf', 'n', 'z'],
        'units': ['mm/min', 'rpm', 'adet']
    },
    'Net Güç': {
        'method': 'Net power',
        'params': ['ae', 'ap', 'Vf', 'kc'],  # kc parametresi eklendi
        'units': ['mm', 'mm', 'mm/min', 'N/mm²']
    },
    'Tork': {
        'method': 'Torque',
        'params': ['Pc', 'n'],
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
import math
from tkinter import font

ec = EngineeringCalculator()
class AdvancedToolTip:
    """
    A class to create advanced tooltips for Tkinter widgets.
    Attributes:
    -----------
    widget : tkinter.Widget
        The widget to which the tooltip is attached.
    text : str
        The text to be displayed in the tooltip.
    delay : float
        The delay in seconds before the tooltip is shown.
    background : str
        The background color of the tooltip.
    foreground : str
        The foreground (text) color of the tooltip.
    font : tuple
        The font of the tooltip text.
    tooltip : tkinter.Toplevel
        The tooltip window.
    id : str
        The id of the scheduled tooltip.
    Methods:
    --------
    __init__(self, widget, text='', delay=0.5, background='#ffffe0', foreground='black', font=('tahoma', 8, 'normal')):
        Initializes the AdvancedToolTip with the given parameters.
    enter(self, event=None):
        Schedules the tooltip to be shown when the mouse enters the widget.
    leave(self, event=None):
        Unschedules and hides the tooltip when the mouse leaves the widget.
    schedule(self):
        Schedules the tooltip to be shown after the specified delay.
    unschedule(self):
        Unschedules the tooltip if it is scheduled.
    show(self):
        Displays the tooltip.
    hide(self):
        Hides the tooltip.
    """
    
    def __init__(self, widget, text='', delay=0.5, background='#ffffe0', foreground='black', font=('tahoma', 8, 'normal')):
        self.widget = widget
        self.text = text
        self.delay = delay
        self.background = background
        self.foreground = foreground
        self.font = font
        self.tooltip = None
        self.id = None

        self.widget.bind('<Enter>', self.enter)
        self.widget.bind('<Leave>', self.leave)
        self.widget.bind('<Button>', self.leave)

    def enter(self, event=None):
        self.schedule()

    def leave(self, event=None):
        self.unschedule()
        self.hide()

    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(int(self.delay * 1000), self.show)

    def unschedule(self):
        if self.id:
            self.widget.after_cancel(self.id)
            self.id = None

    def show(self):
        if self.tooltip:
            return

        x = y = 0
        x, y, _, _ = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20

        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)

        label = tk.Label(self.tooltip, text=self.text,
                      justify='left',
                      background=self.background,
                      foreground=self.foreground,
                      font=self.font,
                      relief='solid',
                      borderwidth=1)
        label.pack()

        self.tooltip.wm_geometry(f"+{x}+{y}")

    def hide(self):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None

def load_tooltips(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return json.load(file)

class AdvancedCalculator():
    '''A class to create an advanced calculator GUI application for engineering calculations.

Attributes:
    root (tk.Tk): The root window for the calculator application.
    tooltips (dict): A dictionary containing tooltips for various UI elements.
    calc_types (dict): A dictionary containing different types of calculations.
    main_frame (ttk.Frame): The main frame of the application.
    left_frame (ttk.Frame): The left frame containing calculation type and parameters.
    right_frame (ttk.Frame): The right frame displaying the results.
    result_text (tk.scrolledtext.ScrolledText): The text area for displaying results.
    input_fields (dict): A dictionary to store input fields for parameters.
    shape_names (dict): A dictionary mapping shape keys to their names.
    reverse_shape_names (dict): A dictionary mapping shape names to their keys.
    params_container (ttk.Frame): A frame to contain parameter input fields.
    shape_combo (ttk.Combobox): A combobox for selecting shapes.
    execute_mode (bool): A flag to indicate if execute mode is enabled.

Methods:
    __init__(self, root, tooltips):
        Initializes the AdvancedCalculator with the given root window and tooltips.

    update_calculations(self, event=None):

    calculate(self):

    calculate_material_mass(self, calculation, values):
        Calculates the material mass based on the selected shape and parameters.

    calculate_turning(self, calculation, values):
        Calculates turning parameters based on the selected calculation and parameters.

    calculate_milling(self, calculation, values):
        Calculates milling parameters based on the selected calculation and parameters.

    perform_calculation(self, calc_type, calculation, values):

    enable_execute_mode(self, event):

    execute_calculation(self, event):

    update_input_fields(self, event=None):

    update_result_display(self, result_data):
'''
    def __init__(self, root,tooltips):
        '''
            Initializes the AdvancedCalculator with the given root window and tooltips.

            tooltips: A dictionary containing tooltips for various UI elements.

        Key Bindings:
            <Control-e>: Enables execute mode.
            <Control-c>: Executes the calculation.
        '''
        super().__init__()

        self.tooltips = tooltips

        """
        Initializes the AdvancedCalculator with the given root window.

        Args:
            root: The root window for the calculator application.
        """
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
        AdvancedToolTip(self.calc_type, self.tooltips.get("Hesaplama", "Tooltip bulunamadı"))
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
        """
        Updates the available calculations based on the selected calculation type.

        Args:
            event: The event that triggered this method (default is None).
        """
        calc_type = self.calc_type.get()
        if calc_type in self.calc_types:
            calcs = self.calc_types[calc_type]
            self.calculation['values'] = list(calcs.keys())
            self.calculation.set(list(calcs.keys())[0])
            self.calculation.bind('<<ComboboxSelected>>', self.update_input_fields)
            self.update_input_fields()

    def calculate(self):
        """
        Performs the calculation based on the selected parameters and displays the result.
        """
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

    def calculate_material_mass(self, calculation, values):
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

    def calculate_turning(self, calculation, values):
        method = self.calc_types['Tornalama Hesaplamaları'][calculation]['method']
        params = [float(values[p]) for p in self.calc_types['Tornalama Hesaplamaları'][calculation]['params']]
        result = ec.calculate_turning(method, *params)

        units = {
            'Kesme Hızı': 'm/min',
            'İş Mili Devri': 'rpm',
            'İlerleme Hızı': 'mm/min',
            'Talaş Debisi': 'cm³/min',
            'Net Güç': 'kW',
            'İşleme Süresi': 'min'
        }

        return f"{result['value']:.2f} {units[calculation]}"

    def calculate_milling(self, calculation, values):
        method = self.calc_types['Frezeleme Hesaplamaları'][calculation]['method']
        params = [float(values[p]) for p in self.calc_types['Frezeleme Hesaplamaları'][calculation]['params']]
        result = ec.calculate_milling(method, *params)

        units = {
            'Tabla İlerlemesi': 'mm/min',
            'Kesme Hızı': 'm/min',
            'İş Mili Devri': 'rpm',
            'Talaş Debisi': 'cm³/min',
            'Diş Başına İlerleme': 'mm',
            'Net Güç': 'kW',
            'Tork': 'Nm'
        }

        return f"{result['value']:.2f} {units[calculation]}"

    def perform_calculation(self, calc_type, calculation, values):
        """
        Performs the specific calculation based on the calculation type and parameters.

        Args:
            calc_type: The type of calculation to perform.
            calculation: The specific calculation to perform.
            values: A dictionary of parameter values for the calculation.

        Returns:
            The result of the calculation as a formatted string.
        """
        if calc_type == 'Malzeme Hesaplamaları':
            return self.calculate_material_mass(calculation, values)
        elif calc_type == 'Tornalama Hesaplamaları':
            return self.calculate_turning(calculation, values)
        elif calc_type == 'Frezeleme Hesaplamaları':
            return self.calculate_milling(calculation, values)
        else:
            raise ValueError(f"Unknown calculation type: {calc_type}")

    def enable_execute_mode(self, event):
        """
        Enables the execute mode for evaluating code snippets in the result text area.

        Args:
            event: The event that triggered this method.
        """
        self.result_text.config(bg='#ffffd0')
        self.execute_mode = True

    def execute_calculation(self, event):
        """
        Executes the selected code snippet from the result text area if execute mode is enabled.

        Args:
            event: The event that triggered this method.
        """
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
        """
        Updates the input fields based on the selected calculation type and calculation.

        Args:
            event: The event that triggered this method (default is None).
        """
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
                """
                Updates the parameter input fields based on the selected shape.

                Args:
                    *args: Variable length argument list.
                """
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
                    """
                    Updates the density entry based on the selected material.

                    Args:
                        event: The event that triggered this method (default is None).
                    """
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

            if calc_type == 'Frezeleme Hesaplamaları' and calculation == 'Net Güç':
                calc_params.extend(['fn', 'kc'])  # fn ve kc parametrelerini ekle
                calc_units.extend(['mm/dev', 'N/mm²'])  # Birimleri ekle

            for param, unit in zip(calc_params, calc_units):
                frame = ttk.Frame(self.params_frame)
                frame.pack(fill='x', pady=2)
                ttk.Label(frame, text=f"{param} [{unit}]").pack(side='left')
                entry = ttk.Entry(frame)
                entry.pack(side='right')
                self.input_fields[param] = entry

    def update_result_display(self, result_data):
        """
        Updates the result display area with the calculation results.

        Args:
            result_data: A dictionary containing the calculation results and parameters.
        """
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
    tooltips = load_tooltips('tooltips.json')
    root = tk.Tk()
    app = AdvancedCalculator(root,tooltips)
    root.mainloop()
