#! .venv/bin/python
# -*- coding : utf-8 -*-
# V2 GUI - Single Page Workspace Interface
# Autor: Hakan KILIÇASLAN 2025
# flake8: noqa

import json
import logging
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path

# Core calculation logic (PRESERVED FROM V1)
from engineering_calculator import EngineeringCalculator
from material_utils import MaterialMassParameters, prepare_material_mass_arguments

# V2 Components
from workspace_manager import WorkspaceManager
from context_builder import ContextBuilder
from ollama_utils_v2 import (
    single_chat_request, 
    analyze_workspace_request,
    get_available_models,
    test_connection,
    build_v2_tools_definition
)
from ui_components import (
    WorkspaceDisplay, 
    V2ControlPanel,
    AdvancedToolTip
)

# V1 Components (PRESERVED)
from execute_mode import ExecuteModeMixin

# Constants (PRESERVED FROM V1)
DEFAULT_WINDOW_SIZE: tuple[int, int] = (1400, 900)
SUPPORTED_PROMPT_ATTACHMENT_EXTENSIONS: set[str] = {
    ".txt", ".md", ".py", ".c", ".cpp"
}

# Material calculations constant (PRESERVED FROM V1)
MATERIAL_CALCS = {
    'Kütle Hesabı': {  # Turkish: "Mass Calculation"
        # 'params' and 'units' for Kütle Hesabı are handled dynamically by _update_material_params
        # based on shape selection and EngineeringCalculator.get_shape_parameters().
        # This entry mainly serves to list "Kütle Hesabı" under "Malzeme Hesaplamaları".
    }
}

# Global instance (PRESERVED FROM V1)
ec = EngineeringCalculator()


class V2Calculator(ExecuteModeMixin):
    """V2 Calculator with single-page workspace interface."""
    
    def __init__(self, root: tk.Tk, tooltips: dict):
        """Initialize V2 Calculator."""
        super().__init__()
        
        self.root = root
        self.tooltips = tooltips
        self.root.title("Mühendislik Hesaplamaları V2 - Tek Sayfa Çalışma Alanı")
        
        # Set window size
        default_width, default_height = DEFAULT_WINDOW_SIZE
        self.root.geometry(f"{default_width}x{default_height}")
        
        # V2 Components
        self.workspace_manager = WorkspaceManager()
        self.context_builder = ContextBuilder()
        
        # Model settings
        self.current_model_name = None
        self.current_model_url = None
        self.ollama_models = []
        
        # Setup styling
        self.setup_styling()
        
        # Create main layout
        self.create_main_layout()
        
        # Setup dynamic fields
        self.input_fields = {}
        self.reverse_shape_names = {}
        self.shape_combo = None
        
        # Initialize calculation types (PRESERVED FROM V1)
        self.initialize_calculation_types()
        
        # Initialize first calculation type
        if list(self.calc_types.keys()):
            self.calc_type.set(list(self.calc_types.keys())[0])
            self.update_calculations()
        
        # Try to fetch available models
        self.refresh_model_list()
        
        # Apply default geometry
        self.root.after(0, self._apply_default_geometry)
    
    def setup_styling(self):
        """Setup GUI styling."""
        style = ttk.Style()
        style.configure('Calc.TFrame', background='#f0f0f0')
        style.configure('Calc.TLabel', background='#f0f0f0', font=('Arial', 10))
        style.configure('Calc.TButton', font=('Arial', 10))
    
    def create_main_layout(self):
        """Create main V2 layout."""
        # Main container
        self.main_frame = ttk.Frame(self.root, style='Calc.TFrame')
        self.main_frame.pack(side='top', fill='both', expand=True, padx=10, pady=10)
        
        # Left panel - Calculation controls (PRESERVED FROM V1)
        self.create_left_panel()
        
        # Right panel - Workspace display (NEW V2)
        self.create_right_panel()
        
        # Bottom panel - Model controls (NEW V2)
        self.create_bottom_panel()
        
        # Status bar (PRESERVED FROM V1)
        self.create_status_bar()
    
    def create_left_panel(self):
        """Create left calculation panel (PRESERVED FROM V1)."""
        self.left_frame = ttk.Frame(self.main_frame, style='Calc.TFrame')
        self.left_frame.pack(side='left', fill='y', padx=(0, 10))
        
        # Calculation type selection (PRESERVED FROM V1)
        ttk.Label(self.left_frame, text="Hesaplama Türü:", style='Calc.TLabel').pack(
            pady=(5, 0), anchor='w')
        self.calc_type = ttk.Combobox(self.left_frame, state="readonly")
        self.calc_type.pack(fill='x', pady=(0, 10))
        AdvancedToolTip(self.calc_type, self.tooltips.get("HesaplamaTuru", "Bir hesaplama türü seçin."))
        self.calc_type.bind('<<ComboboxSelected>>', self.update_calculations)
        
        # Calculation selection (PRESERVED FROM V1)
        ttk.Label(self.left_frame, text="Hesaplama Seçimi:", style='Calc.TLabel').pack(
            pady=(5, 0), anchor='w')
        self.calculation = ttk.Combobox(self.left_frame, state="readonly")
        self.calculation.pack(fill='x', pady=(0, 10))
        AdvancedToolTip(self.calculation, self.tooltips.get("HesaplamaSecimi", "Bir hesaplama seçin."))
        
        # Parameters frame (PRESERVED FROM V1)
        self.params_frame = ttk.Frame(self.left_frame, style='Calc.TFrame')
        self.params_frame.pack(fill='x', pady=5)
        self.params_container = ttk.Frame(self.params_frame, style='Calc.TFrame')
        self.params_container.pack(fill='x', expand=True)
        
        # Calculate button (PRESERVED FROM V1)
        self.calculate_btn = ttk.Button(
            self.left_frame, 
            text="🔷 HESAPLA",
            command=self.calculate
        )
        self.calculate_btn.pack(fill='x', pady=10)
        AdvancedToolTip(self.calculate_btn, self.tooltips.get("HesaplaButonu", "Seçili hesaplamayı gerçekleştir."))
        
        # Clear button (NEW V2)
        self.clear_params_btn = ttk.Button(
            self.left_frame,
            text="🗑️ TEMİZLE", 
            command=self.clear_parameters
        )
        self.clear_params_btn.pack(fill='x', pady=(0, 10))
        AdvancedToolTip(self.clear_params_btn, "Parametre alanlarını temizle.")
    
    def create_right_panel(self):
        """Create right workspace panel (NEW V2)."""
        self.right_frame = ttk.Frame(self.main_frame, style='Calc.TFrame')
        self.right_frame.pack(side='left', fill='both', expand=True)
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.right_frame)
        self.notebook.pack(fill='both', expand=True)
        
        # Workspace tab
        self.workspace_frame = ttk.Frame(self.notebook, style='Calc.TFrame')
        self.notebook.add(self.workspace_frame, text="🔧 Çalışma Alanı")
        
        # Create workspace display
        self.workspace_display = WorkspaceDisplay(
            self.workspace_frame,
            on_add_note=self.handle_add_note,
            on_request_analysis=self.handle_request_analysis,
            on_remove_calculation=self.handle_remove_calculation,
            tooltips=self.tooltips
        )
        self.workspace_display.pack(fill='both', expand=True)
        
        # Control panel tab
        self.control_frame = ttk.Frame(self.notebook, style='Calc.TFrame')
        self.notebook.add(self.control_frame, text="🎛️ Kontrol Paneli")
        
        self.control_panel = V2ControlPanel(
            self.control_frame,
            on_general_analysis=self.handle_general_analysis,
            on_compare_calculations=self.handle_compare_calculations,
            tooltips=self.tooltips
        )
        self.control_panel.pack(fill='both', expand=True)
    
    def create_bottom_panel(self):
        """Create bottom model control panel (NEW V2)."""
        self.bottom_frame = ttk.Frame(self.root, style='Calc.TFrame')
        self.bottom_frame.pack(side='bottom', fill='x', padx=10, pady=(0, 5))
        
        # Model selection frame
        model_frame = ttk.Frame(self.bottom_frame, style='Calc.TFrame')
        model_frame.pack(side='left', fill='x', expand=True)
        
        # Model URL
        ttk.Label(model_frame, text="Model URL:", style='Calc.TLabel').pack(side='left', padx=(0, 5))
        self.model_url_entry = ttk.Entry(model_frame, width=30)
        self.model_url_entry.pack(side='left', padx=(0, 10))
        self.model_url_entry.insert(0, "http://localhost:11434")
        
        # Model selection
        ttk.Label(model_frame, text="Model:", style='Calc.TLabel').pack(side='left', padx=(0, 5))
        self.model_selection_combo = ttk.Combobox(model_frame, width=20, state="readonly")
        self.model_selection_combo.pack(side='left', padx=(0, 10))
        
        # Refresh models button
        self.refresh_models_btn = ttk.Button(
            model_frame,
            text="🔄",
            width=3,
            command=self.refresh_model_list
        )
        self.refresh_models_btn.pack(side='left')
        AdvancedToolTip(self.refresh_models_btn, "Modelleri yenile")
        
        # Test connection button
        self.test_connection_btn = ttk.Button(
            model_frame,
            text="🔗",
            width=3,
            command=self.test_model_connection
        )
        self.test_connection_btn.pack(side='left', padx=(10, 0))
        AdvancedToolTip(self.test_connection_btn, "Bağlantıyı test et")
    
    def create_status_bar(self):
        """Create status bar (PRESERVED FROM V1)."""
        self.status_frame = ttk.Frame(self.root, style='Calc.TFrame')
        self.status_frame.pack(side='bottom', fill='x')
        
        self.status_var = tk.StringVar(value="Hazır - V2")
        self.status_label = ttk.Label(
            self.status_frame, 
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W
        )
        self.status_label.pack(side='left', fill='x', expand=True)
    
    def initialize_calculation_types(self):
        """Initialize calculation types (PRESERVED FROM V1)."""
        self.calc_types = {
            'Malzeme Hesaplamaları': MATERIAL_CALCS,
            'Tornalama Hesaplamaları': {key: {} for key in ec.turning_definitions.keys()},
            'Frezeleme Hesaplamaları': {key: {} for key in ec.milling_definitions.keys()}
        }
        
        # Update calc_type combobox values
        self.calc_type['values'] = list(self.calc_types.keys())
    
    # === PRESERVED METHODS FROM V1 ===
    
    def update_calculations(self, event=None):
        """Update calculations dropdown (PRESERVED FROM V1)."""
        selected_calc_type = self.calc_type.get()
        if selected_calc_type in self.calc_types:
            available_calcs = self.calc_types[selected_calc_type]
            self.calculation['values'] = list(available_calcs.keys())
            
            if list(available_calcs.keys()):
                self.calculation.set(list(available_calcs.keys())[0])
                self.calculation.config(state="readonly")
            else:
                self.calculation.set("")
                self.calculation.config(state="disabled")
            
            self.calculation.bind('<<ComboboxSelected>>', self.update_input_fields)
            self.update_input_fields()
        else:
            self.calculation['values'] = []
            self.calculation.set("")
            self.calculation.config(state="disabled")
            self.update_input_fields()
    
    def update_input_fields(self, event=None):
        """Update input fields dynamically (PRESERVED FROM V1)."""
        # Clear existing fields
        for widget in self.params_container.winfo_children():
            widget.destroy()
        self.input_fields = {}
        self.shape_combo = None
        
        calc_category = self.calc_type.get()
        selected_calculation = self.calculation.get()
        if not calc_category or not selected_calculation:
            return
        
        if calc_category == 'Malzeme Hesaplamaları' and selected_calculation == 'Kütle Hesabı':
            self._setup_material_calculation_fields()
        else:
            self._setup_turning_milling_fields(calc_category, selected_calculation)
    
    def _setup_material_calculation_fields(self):
        """Setup material calculation fields (PRESERVED FROM V1)."""
        available_shapes_map = ec.get_available_shapes()
        self.reverse_shape_names = {v: k for k, v in available_shapes_map.items()}
        shape_display_names = list(available_shapes_map.values())
        
        shape_frame = ttk.Frame(self.params_container, style='Calc.TFrame')
        shape_frame.pack(fill='x', pady=2, padx=5)
        ttk.Label(shape_frame, text="Şekil:", style='Calc.TLabel').pack(side='left', padx=(0, 5))
        self.shape_combo = ttk.Combobox(shape_frame, values=shape_display_names, state="readonly")
        self.shape_combo.pack(side='left', fill='x', expand=True)
        if shape_display_names:
            self.shape_combo.set(shape_display_names[0])
        self.shape_combo.bind('<<ComboboxSelected>>', self._update_material_params)
        self.input_fields['Şekil'] = self.shape_combo
        AdvancedToolTip(self.shape_combo, self.tooltips.get("Şekil", "Şekil seçin."))
        self._update_material_params()
    
    def _setup_turning_milling_fields(self, calc_category, selected_calculation):
        """Setup turning/milling calculation fields (PRESERVED FROM V1)."""
        category_to_internal_key = {
            'Tornalama Hesaplamaları': 'turning',
            'Frezeleme Hesaplamaları': 'milling'
        }
        calc_category_internal = category_to_internal_key.get(calc_category)
        
        if calc_category_internal:
            try:
                param_info_list = ec.get_calculation_params(calc_category_internal, selected_calculation)
                for param_info in param_info_list:
                    param_input_frame = ttk.Frame(self.params_container, style='Calc.TFrame')
                    param_input_frame.pack(fill='x', pady=2, padx=5)
                    
                    label_text = f"{param_info['display_text_turkish']} [{param_info['unit']}]:"
                    label_widget = ttk.Label(param_input_frame, text=label_text, style='Calc.TLabel')
                    label_widget.pack(side='left', padx=(0, 5))
                    
                    entry = ttk.Entry(param_input_frame)
                    entry.pack(side='left', fill='x', expand=True)
                    self.input_fields[param_info['name']] = entry
                    
                    tooltip_key = param_info['name']
                    tooltip_text = self.tooltips.get(
                        tooltip_key, 
                        self.tooltips.get(param_info['display_text_turkish'], f"{param_info['display_text_turkish']} girin.")
                    )
                    AdvancedToolTip(entry, tooltip_text)
            except ValueError:
                ttk.Label(
                    self.params_container, 
                    text="Bu hesaplama için parametre tanımlanmamış.", 
                    style='Calc.TLabel'
                ).pack()
    
    def _update_material_params(self, event=None):
        """Update material parameters (PRESERVED FROM V1)."""
        widgets = list(self.params_container.winfo_children())
        if len(widgets) > 1:
            for widget in widgets[1:]:
                widget.destroy()
        
        if 'Şekil' not in self.input_fields or self.input_fields['Şekil'] is None:
            return
        
        current_shape_selection = self.input_fields['Şekil'].get()
        self.input_fields = {'Şekil': self.input_fields['Şekil']}
        
        shape_internal_key = self.reverse_shape_names.get(current_shape_selection)
        if not shape_internal_key:
            return
        
        # Add density field
        density_frame = ttk.Frame(self.params_container, style='Calc.TFrame')
        density_frame.pack(fill='x', pady=2, padx=5)
        ttk.Label(density_frame, text="Yoğunluk [g/cm³]:", style='Calc.TLabel').pack(side='left', padx=(0, 5))
        density_entry = ttk.Entry(density_frame)
        density_entry.pack(side='left', fill='x', expand=True)
        self.input_fields['density'] = density_entry
        AdvancedToolTip(density_entry, self.tooltips.get("Yoğunluk", "Malzemenin yoğunluğunu girin."))
        
        # Add length field
        length_frame = ttk.Frame(self.params_container, style='Calc.TFrame')
        length_frame.pack(fill='x', pady=2, padx=5)
        ttk.Label(length_frame, text="Uzunluk [mm]:", style='Calc.TLabel').pack(side='left', padx=(0, 5))
        length_entry = ttk.Entry(length_frame)
        length_entry.pack(side='left', fill='x', expand=True)
        self.input_fields['length'] = length_entry
        AdvancedToolTip(length_entry, self.tooltips.get("Uzunluk", "Şeklin uzunluğunu girin."))
        
        # Add shape-specific parameters
        shape_params = ec.get_shape_parameters(shape_internal_key)
        for param_name in shape_params:
            param_frame = ttk.Frame(self.params_container, style='Calc.TFrame')
            param_frame.pack(fill='x', pady=2, padx=5)
            
            # Use Turkish display name if available
            display_name = self.tooltips.get(param_name, param_name)
            label_text = f"{display_name} [mm]:"
            label_widget = ttk.Label(param_frame, text=label_text, style='Calc.TLabel')
            label_widget.pack(side='left', padx=(0, 5))
            
            entry = ttk.Entry(param_frame)
            entry.pack(side='left', fill='x', expand=True)
            self.input_fields[param_name] = entry
            
            tooltip_text = self.tooltips.get(param_name, f"{param_name} değerini girin.")
            AdvancedToolTip(entry, tooltip_text)
    
    def calculate(self):
        """Perform calculation (PRESERVED FROM V1 with V2 integration)."""
        try:
            calc_type = self.calc_type.get()
            calculation_name = self.calculation.get()
            
            if not calc_type or not calculation_name:
                messagebox.showwarning("Uyarı", "Lütfen bir hesaplama türü ve hesaplama seçin.")
                return
            
            # Collect input values (PRESERVED FROM V1)
            input_values = {}
            for param_key, field_widget in self.input_fields.items():
                value_str = field_widget.get()
                if not value_str:
                    messagebox.showerror("Hata", f"'{param_key}' için değer girilmemiş.")
                    return
                try:
                    if param_key != 'Şekil':
                        input_values[param_key] = float(value_str)
                    else:
                        input_values[param_key] = value_str
                except ValueError:
                    messagebox.showerror("Hata", f"'{param_key}' için geçersiz sayısal değer: {value_str}")
                    return
            
            # Perform calculation (PRESERVED FROM V1)
            calculation_result = self.perform_calculation(calc_type, calculation_name, input_values)
            
            # V2: Add to workspace
            calc_id = self.workspace_manager.add_calculation(
                calc_type=calc_type,
                calc_name=calculation_name,
                params=input_values,
                result=calculation_result['value'],
                unit=calculation_result['unit']
            )
            
            # V2: Update workspace display
            calculation_entry = self.workspace_manager.get_calculation(calc_id)
            self.workspace_display.add_calculation_card(calculation_entry)
            
            # Update status
            self.update_status_bar(f"Hesaplama eklendi: {calculation_result['value']} {calculation_result['unit']}")
            
        except Exception as e:
            messagebox.showerror("Hata", f"Hesaplama sırasında hata oluştu: {str(e)}")
    
    def perform_calculation(self, calc_category, calc_name, params_values):
        """Perform calculation (PRESERVED FROM V1)."""
        if calc_category == 'Malzeme Hesaplamaları':
            return self.calculate_material_mass(calc_name, params_values)
        elif calc_category == 'Tornalama Hesaplamaları':
            return self.calculate_turning(calc_name, params_values)
        elif calc_category == 'Frezeleme Hesaplamaları':
            return self.calculate_milling(calc_name, params_values)
        else:
            raise ValueError(f"Bilinmeyen hesaplama kategorisi: {calc_category}")
    
    def calculate_material_mass(self, calc_name, params_values):
        """Calculate material mass (PRESERVED FROM V1)."""
        if calc_name != 'Kütle Hesabı':
            raise ValueError(f"Bilinmeyen malzeme hesaplaması: {calc_name}")
        
        # Convert shape name to internal key
        shape_name_turkish = params_values.get('Şekil', '')
        shape_key = self.reverse_shape_names.get(shape_name_turkish, shape_name_turkish)
        
        # Prepare arguments using material utils
        mass_params = prepare_material_mass_arguments(
            ec, 
            {
                'shape_key': shape_key,
                'density': params_values.get('density', 0),
                'length': params_values.get('length', 0),
                **{k: v for k, v in params_values.items() if k not in ['Şekil', 'density', 'length']}
            },
            []
        )
        
        # Calculate mass
        mass = ec.calculate_material_mass(
            mass_params.shape_key,
            mass_params.density,
            *(mass_params.dimensions + [mass_params.length])
        )
        
        return {'value': mass, 'unit': 'g'}
    
    def calculate_turning(self, calc_name, params_values):
        """Calculate turning operation (PRESERVED FROM V1)."""
        calc_info = ec.turning_definitions.get(calc_name)
        if not calc_info:
            raise ValueError(f"Bilinmeyen tornalama hesaplaması: {calc_name}")
        
        result = calc_info['formula'](**params_values)
        unit = calc_info['units']['result']
        
        return {'value': result, 'unit': unit}
    
    def calculate_milling(self, calc_name, params_values):
        """Calculate milling operation (PRESERVED FROM V1)."""
        calc_info = ec.milling_definitions.get(calc_name)
        if not calc_info:
            raise ValueError(f"Bilinmeyen frezeleme hesaplaması: {calc_name}")
        
        result = calc_info['formula'](**params_values)
        unit = calc_info['units']['result']
        
        return {'value': result, 'unit': unit}
    
    def clear_parameters(self):
        """Clear all parameter fields (NEW V2)."""
        for field_widget in self.input_fields.values():
            if hasattr(field_widget, 'delete'):
                field_widget.delete(0, tk.END)
            elif hasattr(field_widget, 'set'):
                field_widget.set('')
    
    # === V2 NEW METHODS ===
    
    def handle_add_note(self, calc_id: str, note: str):
        """Handle adding note to calculation."""
        success = self.workspace_manager.add_user_note(calc_id, note)
        if success:
            self.workspace_display.update_calculation_card(calc_id)
            self.update_status_bar("Not eklendi")
        else:
            messagebox.showerror("Hata", "Not eklenemedi")
    
    def handle_request_analysis(self, calc_id: str = None):
        """Handle model analysis request."""
        if not self.current_model_name or not self.current_model_url:
            messagebox.showwarning("Uyarı", "Lütfen önce model URL'sini ve model seçin.")
            return
        
        try:
            if calc_id:
                # Single calculation analysis
                calculation = self.workspace_manager.get_calculation(calc_id)
                if not calculation:
                    messagebox.showerror("Hata", "Hesaplama bulunamadı")
                    return
                
                context = self.context_builder.build_calculation_review_context(calculation)
            else:
                # General workspace analysis
                context = self.context_builder.build_general_review_context(self.workspace_manager.workspace)
            
            self.update_status_bar("Model analizi isteniyor...")
            
            # Request analysis
            response = analyze_workspace_request(
                self.current_model_url,
                self.current_model_name,
                context,
                timeout=60
            )
            
            # Add model comment
            if calc_id:
                self.workspace_manager.add_model_comment(calc_id, response)
                self.workspace_display.update_calculation_card(calc_id)
            else:
                # For general analysis, we could show in a dialog or add as general comment
                messagebox.showinfo("Genel Analiz", response)
            
            self.update_status_bar("Model analizi tamamlandı")
            
        except Exception as e:
            messagebox.showerror("Hata", f"Model analizi sırasında hata: {str(e)}")
            self.update_status_bar("Model analizi başarısız")
    
    def handle_remove_calculation(self, calc_id: str = None):
        """Handle calculation removal."""
        if calc_id is None:
            # Clear all
            self.workspace_manager.clear_workspace()
            self.workspace_display.clear_all_cards()
            self.update_status_bar("Çalışma alanı temizlendi")
        else:
            # Remove single calculation
            success = self.workspace_manager.remove_calculation(calc_id)
            if success:
                self.workspace_display.remove_calculation_card(calc_id)
                self.update_status_bar("Hesaplama kaldırıldı")
            else:
                messagebox.showerror("Hata", "Hesaplama kaldırılamadı")
    
    def handle_general_analysis(self):
        """Handle general workspace analysis."""
        self.handle_request_analysis(None)
    
    def handle_compare_calculations(self):
        """Handle calculation comparison."""
        calculations = self.workspace_manager.get_all_calculations()
        if len(calculations) < 2:
            messagebox.showinfo("Bilgi", "Karşılaştırma için en az 2 hesaplama gerekli.")
            return
        
        # For now, use general analysis for comparison
        # In future, implement specific comparison dialog
        context = self.context_builder.build_comparison_context(calculations)
        
        if not self.current_model_name or not self.current_model_url:
            messagebox.showwarning("Uyarı", "Lütfen önce model URL'sini ve model seçin.")
            return
        
        try:
            self.update_status_bar("Karşılaştırma analiz edilir...")
            response = analyze_workspace_request(
                self.current_model_url,
                self.current_model_name,
                context,
                timeout=60
            )
            
            messagebox.showinfo("Karşılaştırma Sonucu", response)
            self.update_status_bar("Karşılaştırma tamamlandı")
            
        except Exception as e:
            messagebox.showerror("Hata", f"Karşılaştırma sırasında hata: {str(e)}")
            self.update_status_bar("Karşılaştırma başarısız")
    
    def refresh_model_list(self):
        """Refresh available models."""
        try:
            model_url = self.model_url_entry.get()
            self.ollama_models = get_available_models(model_url)
            self.model_selection_combo['values'] = self.ollama_models
            
            if self.ollama_models:
                if not self.current_model_name or self.current_model_name not in self.ollama_models:
                    self.model_selection_combo.set(self.ollama_models[0])
                    self.current_model_name = self.ollama_models[0]
                else:
                    self.model_selection_combo.set(self.current_model_name)
            else:
                self.model_selection_combo.set("")
                self.current_model_name = None
            
            self.update_status_bar(f"Modeller yenilendi: {len(self.ollama_models)} model bulundu")
            
        except Exception as e:
            messagebox.showerror("Hata", f"Modeller alınırken hata: {str(e)}")
            self.update_status_bar("Model yenileme başarısız")
    
    def test_model_connection(self):
        """Test connection to model."""
        try:
            model_url = self.model_url_entry.get()
            if test_connection(model_url):
                messagebox.showinfo("Bağlantı Başarılı", "Ollama sunucusuna bağlantı başarılı!")
                self.update_status_bar("Bağlantı başarılı")
            else:
                messagebox.showerror("Bağlantı Başarısız", "Ollama sunucusuna bağlanılamadı!")
                self.update_status_bar("Bağlantı başarısız")
        except Exception as e:
            messagebox.showerror("Hata", f"Bağlantı testi sırasında hata: {str(e)}")
            self.update_status_bar("Bağlantı testi başarısız")
    
    def update_status_bar(self, message: str):
        """Update status bar message."""
        self.status_var.set(message)
        self.root.update_idletasks()
    
    def export_workspace(self):
        """Export workspace to file."""
        try:
            file_path = filedialog.asksaveasfilename(
                title="Çalışma Alanını Dışa Aktar",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if file_path:
                data = self.workspace_manager.export_session()
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                
                messagebox.showinfo("Başarılı", f"Çalışma alanı dışa aktarıldı:\n{file_path}")
                self.update_status_bar("Dışa aktarma başarılı")
        except Exception as e:
            messagebox.showerror("Hata", f"Dışa aktarma sırasında hata: {str(e)}")
            self.update_status_bar("Dışa aktarma başarısız")
    
    def _apply_default_geometry(self):
        """Apply default window geometry."""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")


def main():
    """Main entry point for V2 GUI."""
    root = tk.Tk()
    
    # Load tooltips
    try:
        with open('tooltips.json', 'r', encoding='utf-8') as f:
            tooltips = json.load(f)
    except FileNotFoundError:
        tooltips = {}
    
    # Create V2 GUI
    app = V2Calculator(root, tooltips)
    
    # Handle model selection changes
    def on_model_select(event=None):
        app.current_model_name = app.model_selection_combo.get()
        app.current_model_url = app.model_url_entry.get()
    
    app.model_selection_combo.bind('<<ComboboxSelected>>', on_model_select)
    app.model_url_entry.bind('<FocusOut>', on_model_select)
    
    # Start GUI
    root.mainloop()


if __name__ == "__main__":
    main()
