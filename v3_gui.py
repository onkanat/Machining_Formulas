"""
V3 GUI - Workspace Buffer Based Interface

This module provides the new V3 interface with collaborative workspace buffer
where users and models can edit content together.
"""

# -*- coding : utf-8 -*-
# V3 GUI - Workspace Buffer Interface
# Autor: Hakan KILIÇASLAN 2025
# flake8: noqa

import json
import logging
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from typing import Dict, List

# Core calculation logic (PRESERVED FROM V1)
from engineering_calculator import EngineeringCalculator
from material_utils import MaterialMassParameters, prepare_material_mass_arguments

# V3 Components
from workspace_buffer import WorkspaceBuffer
from workspace_editor import WorkspaceEditor
from ollama_utils_v2 import (
    single_chat_request,
    get_available_models,
    test_connection,
)

# V1 Components (PRESERVED)
from execute_mode import ExecuteModeMixin

# Constants (PRESERVED FROM V1)
DEFAULT_WINDOW_SIZE: tuple[int, int] = (1400, 900)
SUPPORTED_PROMPT_ATTACHMENT_EXTENSIONS: set[str] = {".txt", ".md", ".py", ".c", ".cpp"}

# Material calculations constant (PRESERVED FROM V1)
MATERIAL_CALCS = {
    "Kütle Hesabı": {  # Turkish: "Mass Calculation"
        # 'params' and 'units' for Kütle Hesabı are handled dynamically by _update_material_params
        # based on shape selection and EngineeringCalculator.get_shape_parameters().
        # This entry mainly serves to list "Kütle Hesabı" under "Malzeme Hesaplamaları".
    }
}

# Global instance (PRESERVED FROM V1)
ec = EngineeringCalculator()


class V3Calculator(ExecuteModeMixin):
    """V3 Calculator with workspace buffer interface."""

    def __init__(self, root: tk.Tk, tooltips: Dict[str, str]):
        self.root = root
        self.tooltips = tooltips

        # Initialize workspace buffer
        self.workspace_buffer = WorkspaceBuffer()

        # Model configuration
        self.current_model_url = ""
        self.current_model_name = ""
        self.ollama_models: List[str] = []

        # Setup UI
        self.setup_ui()
        self._apply_default_geometry()

        # Initialize model connection
        self.refresh_model_list()

    def setup_ui(self):
        """Setup the main V3 interface."""
        # Configure root window
        self.root.title("🔧 Mühendislik Hesaplayıcı V3 - Çalışma Alanı")
        self.root.geometry(f"{DEFAULT_WINDOW_SIZE[0]}x{DEFAULT_WINDOW_SIZE[1]}")

        # Configure styles
        self._setup_styles()

        # Create main layout
        self._create_main_layout()

        # Create menu bar
        self._create_menu_bar()

        # Create status bar
        self._create_status_bar()

    def _setup_styles(self):
        """Setup ttk styles."""
        style = ttk.Style()
        style.theme_use("clam")

        # Configure custom styles
        style.configure("Calc.TFrame", background="#f0f0f0")
        style.configure("Calc.TLabel", background="#f0f0f0", font=("Arial", 10))
        style.configure(
            "Header.TLabel", background="#f0f0f0", font=("Arial", 12, "bold")
        )
        style.configure("Calc.TButton", font=("Arial", 9))

        # Configure combobox style
        style.configure("Calc.TCombobox", fieldbackground="white", font=("Arial", 9))

    def _create_main_layout(self):
        """Create main layout with paned windows."""
        # Main container
        main_container = ttk.Frame(self.root, style="Calc.TFrame")
        main_container.pack(fill="both", expand=True)

        # Create horizontal paned window
        self.paned_window = ttk.PanedWindow(main_container, orient="horizontal")
        self.paned_window.pack(fill="both", expand=True, padx=5, pady=5)

        # Left panel - Calculation tools
        self._create_calculation_panel()

        # Right panel - Workspace editor
        self._create_workspace_panel()

    def _create_calculation_panel(self):
        """Create calculation tools panel."""
        calc_frame = ttk.Frame(self.paned_window, style="Calc.TFrame")
        self.paned_window.add(calc_frame, weight=1)

        # Calculation tools header
        header_frame = ttk.Frame(calc_frame, style="Calc.TFrame")
        header_frame.pack(fill="x", padx=5, pady=5)

        ttk.Label(
            header_frame, text="🧮 HESAPLAMA ARAÇLARI", font=("Arial", 11, "bold")
        ).pack(side="left")

        # Model configuration
        model_frame = ttk.LabelFrame(
            calc_frame, text="🤖 Model Yapılandırması", style="Calc.TFrame"
        )
        model_frame.pack(fill="x", padx=5, pady=5)

        # Model URL
        url_frame = ttk.Frame(model_frame, style="Calc.TFrame")
        url_frame.pack(fill="x", padx=5, pady=2)

        ttk.Label(url_frame, text="URL:", width=8).pack(side="left")
        self.model_url_entry = ttk.Entry(url_frame, width=30)
        self.model_url_entry.pack(side="left", fill="x", expand=True, padx=(5, 0))
        self.model_url_entry.insert(0, "http://localhost:11434")

        ttk.Button(url_frame, text="🔄", command=self.refresh_model_list, width=3).pack(
            side="right", padx=(5, 0)
        )

        # Model selection
        model_frame_inner = ttk.Frame(model_frame, style="Calc.TFrame")
        model_frame_inner.pack(fill="x", padx=5, pady=2)

        ttk.Label(model_frame_inner, text="Model:", width=8).pack(side="left")
        self.model_selection_combo = ttk.Combobox(
            model_frame_inner, width=25, style="Calc.TCombobox"
        )
        self.model_selection_combo.pack(side="left", fill="x", expand=True, padx=(5, 0))

        ttk.Button(
            model_frame_inner, text="🔗", command=self.test_model_connection, width=3
        ).pack(side="right", padx=(5, 0))

        # Separator
        ttk.Separator(calc_frame, orient="horizontal").pack(fill="x", padx=5, pady=10)

        # Calculation categories
        self._create_calculation_categories(calc_frame)

    def _create_calculation_categories(self, parent):
        """Create calculation categories and tools."""
        # Create notebook for categories
        self.calc_notebook = ttk.Notebook(parent)
        self.calc_notebook.pack(fill="both", expand=True, padx=5, pady=5)

        # Turning calculations
        self._create_turning_tab()

        # Milling calculations
        self._create_milling_tab()

        # Material calculations
        self._create_material_tab()

        # Drilling calculations
        self._create_drilling_tab()

    def _create_turning_tab(self):
        """Create turning calculations tab."""
        turning_frame = ttk.Frame(self.calc_notebook, style="Calc.TFrame")
        self.calc_notebook.add(turning_frame, text="Tornalama")

        # Cutting speed calculation
        self._create_cutting_speed_calc(turning_frame)

        # Spindle speed calculation
        self._create_spindle_speed_calc(turning_frame)

        # Feed rate calculation
        self._create_feed_rate_calc(turning_frame)

    def _create_cutting_speed_calc(self, parent):
        """Create cutting speed calculation."""
        frame = ttk.LabelFrame(parent, text="Kesme Hızı (Vc)", style="Calc.TFrame")
        frame.pack(fill="x", padx=5, pady=5)

        # Diameter input
        diam_frame = ttk.Frame(frame, style="Calc.TFrame")
        diam_frame.pack(fill="x", padx=5, pady=2)
        ttk.Label(diam_frame, text="Çap (Dm):", width=15).pack(side="left")
        self.vc_diameter = ttk.Entry(diam_frame, width=15)
        self.vc_diameter.pack(side="left", padx=(5, 0))
        ttk.Label(diam_frame, text="mm").pack(side="left", padx=(2, 0))

        # RPM input
        rpm_frame = ttk.Frame(frame, style="Calc.TFrame")
        rpm_frame.pack(fill="x", padx=5, pady=2)
        ttk.Label(rpm_frame, text="Devir (n):", width=15).pack(side="left")
        self.vc_rpm = ttk.Entry(rpm_frame, width=15)
        self.vc_rpm.pack(side="left", padx=(5, 0))
        ttk.Label(rpm_frame, text="rpm").pack(side="left", padx=(2, 0))

        # Calculate button
        ttk.Button(frame, text="Hesapla", command=self._calculate_cutting_speed).pack(
            pady=5
        )

        # Result display
        self.vc_result = ttk.Label(
            frame, text="", font=("Arial", 10, "bold"), foreground="blue"
        )
        self.vc_result.pack(pady=2)

        # Inject to workspace button
        ttk.Button(
            frame, text="📝 Çalışma Alanına Ekle", command=self._inject_cutting_speed
        ).pack(pady=2)

    def _create_spindle_speed_calc(self, parent):
        """Create spindle speed calculation."""
        frame = ttk.LabelFrame(parent, text="İş Mili Hızı (n)", style="Calc.TFrame")
        frame.pack(fill="x", padx=5, pady=5)

        # Cutting speed input
        speed_frame = ttk.Frame(frame, style="Calc.TFrame")
        speed_frame.pack(fill="x", padx=5, pady=2)
        ttk.Label(speed_frame, text="Kesme Hızı (Vc):", width=15).pack(side="left")
        self.n_cutting_speed = ttk.Entry(speed_frame, width=15)
        self.n_cutting_speed.pack(side="left", padx=(5, 0))
        ttk.Label(speed_frame, text="m/dak").pack(side="left", padx=(2, 0))

        # Diameter input
        diam_frame = ttk.Frame(frame, style="Calc.TFrame")
        diam_frame.pack(fill="x", padx=5, pady=2)
        ttk.Label(diam_frame, text="Çap (Dm):", width=15).pack(side="left")
        self.n_diameter = ttk.Entry(diam_frame, width=15)
        self.n_diameter.pack(side="left", padx=(5, 0))
        ttk.Label(diam_frame, text="mm").pack(side="left", padx=(2, 0))

        # Calculate button
        ttk.Button(frame, text="Hesapla", command=self._calculate_spindle_speed).pack(
            pady=5
        )

        # Result display
        self.n_result = ttk.Label(
            frame, text="", font=("Arial", 10, "bold"), foreground="blue"
        )
        self.n_result.pack(pady=2)

        # Inject to workspace button
        ttk.Button(
            frame, text="📝 Çalışma Alanına Ekle", command=self._inject_spindle_speed
        ).pack(pady=2)

    def _create_feed_rate_calc(self, parent):
        """Create feed rate calculation."""
        frame = ttk.LabelFrame(parent, text="Besleme Oranı", style="Calc.TFrame")
        frame.pack(fill="x", padx=5, pady=5)

        # Feed per tooth input
        feed_frame = ttk.Frame(frame, style="Calc.TFrame")
        feed_frame.pack(fill="x", padx=5, pady=2)
        ttk.Label(feed_frame, text="Diş Başı Besleme:", width=15).pack(side="left")
        self.feed_per_tooth = ttk.Entry(feed_frame, width=15)
        self.feed_per_tooth.pack(side="left", padx=(5, 0))
        ttk.Label(feed_frame, text="mm/diş").pack(side="left", padx=(2, 0))

        # Number of teeth input
        teeth_frame = ttk.Frame(frame, style="Calc.TFrame")
        teeth_frame.pack(fill="x", padx=5, pady=2)
        ttk.Label(teeth_frame, text="Diş Sayısı (z):", width=15).pack(side="left")
        self.num_teeth = ttk.Entry(teeth_frame, width=15)
        self.num_teeth.pack(side="left", padx=(5, 0))

        # RPM input
        rpm_frame = ttk.Frame(frame, style="Calc.TFrame")
        rpm_frame.pack(fill="x", padx=5, pady=2)
        ttk.Label(rpm_frame, text="Devir (n):", width=15).pack(side="left")
        self.feed_rpm = ttk.Entry(rpm_frame, width=15)
        self.feed_rpm.pack(side="left", padx=(5, 0))
        ttk.Label(rpm_frame, text="rpm").pack(side="left", padx=(2, 0))

        # Calculate button
        ttk.Button(frame, text="Hesapla", command=self._calculate_feed_rate).pack(
            pady=5
        )

        # Result display
        self.feed_result = ttk.Label(
            frame, text="", font=("Arial", 10, "bold"), foreground="blue"
        )
        self.feed_result.pack(pady=2)

        # Inject to workspace button
        ttk.Button(
            frame, text="📝 Çalışma Alanına Ekle", command=self._inject_feed_rate
        ).pack(pady=2)

    def _create_milling_tab(self):
        """Create milling calculations tab."""
        milling_frame = ttk.Frame(self.calc_notebook, style="Calc.TFrame")
        self.calc_notebook.add(milling_frame, text="Frezeleme")

        # Add milling calculations here
        ttk.Label(
            milling_frame,
            text="Frezeleme hesaplamaları yakında eklenecek...",
            font=("Arial", 10),
        ).pack(pady=20)

    def _create_material_tab(self):
        """Create material calculations tab."""
        material_frame = ttk.Frame(self.calc_notebook, style="Calc.TFrame")
        self.calc_notebook.add(material_frame, text="Malzeme")

        # Mass calculation
        self._create_mass_calc(material_frame)

    def _create_mass_calc(self, parent):
        """Create mass calculation."""
        frame = ttk.LabelFrame(parent, text="Kütle Hesabı", style="Calc.TFrame")
        frame.pack(fill="x", padx=5, pady=5)

        # Shape selection
        shape_frame = ttk.Frame(frame, style="Calc.TFrame")
        shape_frame.pack(fill="x", padx=5, pady=2)
        ttk.Label(shape_frame, text="Şekil:", width=15).pack(side="left")
        self.mass_shape = ttk.Combobox(shape_frame, width=15, style="Calc.TCombobox")
        self.mass_shape.pack(side="left", padx=(5, 0))
        self.mass_shape["values"] = ("circle", "rectangle", "tube", "sphere")
        self.mass_shape.set("circle")
        self.mass_shape.bind("<<ComboboxSelected>>", self._update_mass_params)

        # Dynamic parameters frame
        self.mass_params_frame = ttk.Frame(frame, style="Calc.TFrame")
        self.mass_params_frame.pack(fill="x", padx=5, pady=5)

        # Density input
        density_frame = ttk.Frame(frame, style="Calc.TFrame")
        density_frame.pack(fill="x", padx=5, pady=2)
        ttk.Label(density_frame, text="Yoğunluk:", width=15).pack(side="left")
        self.mass_density = ttk.Entry(density_frame, width=15)
        self.mass_density.pack(side="left", padx=(5, 0))
        ttk.Label(density_frame, text="g/cm³").pack(side="left", padx=(2, 0))

        # Initialize with circle parameters
        self._update_mass_params()

        # Calculate button
        ttk.Button(frame, text="Hesapla", command=self._calculate_mass).pack(pady=5)

        # Result display
        self.mass_result = ttk.Label(
            frame, text="", font=("Arial", 10, "bold"), foreground="blue"
        )
        self.mass_result.pack(pady=2)

        # Inject to workspace button
        ttk.Button(
            frame, text="📝 Çalışma Alanına Ekle", command=self._inject_mass
        ).pack(pady=2)

    def _create_drilling_tab(self):
        """Create drilling calculations tab."""
        drilling_frame = ttk.Frame(self.calc_notebook, style="Calc.TFrame")
        self.calc_notebook.add(drilling_frame, text="Delme")

        # Add drilling calculations here
        ttk.Label(
            drilling_frame,
            text="Delme hesaplamaları yakında eklenecek...",
            font=("Arial", 10),
        ).pack(pady=20)

    def _create_workspace_panel(self):
        """Create workspace editor panel."""
        workspace_frame = ttk.Frame(self.paned_window, style="Calc.TFrame")
        self.paned_window.add(workspace_frame, weight=3)

        # Create workspace editor
        self.workspace_editor = WorkspaceEditor(
            workspace_frame,
            self.workspace_buffer,
            on_model_suggestion=self._handle_model_suggestion,
            on_content_change=self._on_workspace_change,
            tooltips=self.tooltips,
        )
        self.workspace_editor.pack(fill="both", expand=True)

    def _create_menu_bar(self):
        """Create menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Dosya", menu=file_menu)
        file_menu.add_command(label="Yeni Çalışma Alanı", command=self._new_workspace)
        file_menu.add_command(label="Aç...", command=self._open_workspace)
        file_menu.add_command(label="Kaydet...", command=self._save_workspace)
        file_menu.add_separator()
        file_menu.add_command(label="Dışa Aktar...", command=self._export_workspace)
        file_menu.add_separator()
        file_menu.add_command(label="Çıkış", command=self.root.quit)

        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Düzenle", menu=edit_menu)
        edit_menu.add_command(label="Geri Al", command=self.workspace_editor._undo)
        edit_menu.add_command(label="İleri Al", command=self.workspace_editor._redo)
        edit_menu.add_separator()
        edit_menu.add_command(
            label="Temizle", command=self.workspace_editor._clear_workspace
        )

        # Model menu
        model_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Model", menu=model_menu)
        model_menu.add_command(
            label="Bağlantı Testi", command=self.test_model_connection
        )
        model_menu.add_command(
            label="Modelleri Yenile", command=self.refresh_model_list
        )
        model_menu.add_separator()
        model_menu.add_command(
            label="Çalışma Alanını Analiz Et", command=self._analyze_workspace
        )

    def _create_status_bar(self):
        """Create status bar."""
        self.status_frame = ttk.Frame(self.root, style="Calc.TFrame")
        self.status_frame.pack(fill="x", side="bottom")

        self.status_var = tk.StringVar()
        self.status_var.set("Hazır")

        status_label = ttk.Label(
            self.status_frame, textvariable=self.status_var, relief="sunken"
        )
        status_label.pack(fill="x", padx=2, pady=2)

    def _update_mass_params(self, event=None):
        """Update mass calculation parameters based on shape."""
        # Clear existing parameter widgets
        for widget in self.mass_params_frame.winfo_children():
            widget.destroy()

        shape = self.mass_shape.get()
        param_names = ec.get_shape_parameters(shape)

        self.mass_param_widgets = {}

        for param_name in param_names:
            frame = ttk.Frame(self.mass_params_frame, style="Calc.TFrame")
            frame.pack(fill="x", pady=1)

            label_text = f"{param_name}:"
            ttk.Label(frame, text=label_text, width=15).pack(side="left")

            entry = ttk.Entry(frame, width=15)
            entry.pack(side="left", padx=(5, 0))

            self.mass_param_widgets[param_name] = entry

    def _calculate_cutting_speed(self):
        """Calculate cutting speed."""
        try:
            diameter = float(self.vc_diameter.get())
            rpm = float(self.vc_rpm.get())

            result_dict = ec.calculate_turning("Cutting speed", diameter, rpm)
            result = result_dict["value"]
            self.vc_result.config(text=f"Sonuç: {result:.2f} m/dak")

        except ValueError:
            messagebox.showerror("Hata", "Lütfen geçerli sayısal değerler girin.")
        except Exception as e:
            messagebox.showerror("Hata", f"Hesaplama hatası: {str(e)}")

    def _calculate_spindle_speed(self):
        """Calculate spindle speed."""
        try:
            cutting_speed = float(self.n_cutting_speed.get())
            diameter = float(self.n_diameter.get())

            result_dict = ec.calculate_turning("Spindle speed", cutting_speed, diameter)
            result = result_dict["value"]
            self.n_result.config(text=f"Sonuç: {result:.0f} rpm")

        except ValueError:
            messagebox.showerror("Hata", "Lütfen geçerli sayısal değerler girin.")
        except Exception as e:
            messagebox.showerror("Hata", f"Hesaplama hatası: {str(e)}")

    def _calculate_feed_rate(self):
        """Calculate feed rate."""
        try:
            feed_per_tooth = float(self.feed_per_tooth.get())
            num_teeth = float(self.num_teeth.get())
            rpm = float(self.feed_rpm.get())

            result_dict = ec.calculate_milling(
                "Table feed", feed_per_tooth, num_teeth, rpm
            )
            result = result_dict["value"]
            self.feed_result.config(text=f"Sonuç: {result:.2f} mm/dak")

        except ValueError:
            messagebox.showerror("Hata", "Lütfen geçerli sayısal değerler girin.")
        except Exception as e:
            messagebox.showerror("Hata", f"Hesaplama hatası: {str(e)}")

    def _calculate_mass(self):
        """Calculate mass."""
        try:
            shape = self.mass_shape.get()
            density = float(self.mass_density.get())

            # Get shape parameters
            params = {}
            for param_name, entry in self.mass_param_widgets.items():
                params[param_name] = float(entry.get())

            # Calculate mass using correct API
            param_values = list(params.values())
            result = ec.calculate_material_mass(shape, density, *param_values)

            self.mass_result.config(text=f"Sonuç: {result:.2f} g")

        except ValueError:
            messagebox.showerror("Hata", "Lütfen geçerli sayısal değerler girin.")
        except Exception as e:
            messagebox.showerror("Hata", f"Hesaplama hatası: {str(e)}")

    def _inject_cutting_speed(self):
        """Inject cutting speed calculation into workspace."""
        try:
            diameter = float(self.vc_diameter.get())
            rpm = float(self.vc_rpm.get())
            result_dict = ec.calculate_turning("Cutting speed", diameter, rpm)
            result = result_dict["value"]

            self.workspace_editor.insert_calculation_result(
                "Tornalama Hesaplamaları",
                "Kesme Hızı",
                {"Dm": diameter, "n": rpm},
                result,
                "m/dak",
            )

        except Exception:
            messagebox.showerror("Hata", "Lütfen önce hesaplama yapın.")

    def _inject_spindle_speed(self):
        """Inject spindle speed calculation into workspace."""
        try:
            cutting_speed = float(self.n_cutting_speed.get())
            diameter = float(self.n_diameter.get())
            result_dict = ec.calculate_turning("Spindle speed", cutting_speed, diameter)
            result = result_dict["value"]

            self.workspace_editor.insert_calculation_result(
                "Tornalama Hesaplamaları",
                "İş Mili Hızı",
                {"Vc": cutting_speed, "Dm": diameter},
                result,
                "rpm",
            )

        except Exception:
            messagebox.showerror("Hata", "Lütfen önce hesaplama yapın.")

    def _inject_feed_rate(self):
        """Inject feed rate calculation into workspace."""
        try:
            feed_per_tooth = float(self.feed_per_tooth.get())
            num_teeth = float(self.num_teeth.get())
            rpm = float(self.feed_rpm.get())
            result_dict = ec.calculate_milling(
                "Table feed", feed_per_tooth, num_teeth, rpm
            )
            result = result_dict["value"]

            self.workspace_editor.insert_calculation_result(
                "Frezeleme Hesaplamaları",
                "Besleme Oranı",
                {"fz": feed_per_tooth, "z": num_teeth, "n": rpm},
                result,
                "mm/dak",
            )

        except Exception:
            messagebox.showerror("Hata", "Lütfen önce hesaplama yapın.")

    def _inject_mass(self):
        """Inject mass calculation into workspace."""
        try:
            shape = self.mass_shape.get()
            density = float(self.mass_density.get())

            # Get shape parameters
            params = {}
            for param_name, entry in self.mass_param_widgets.items():
                params[param_name] = float(entry.get())

            # Calculate mass using correct API
            param_values = list(params.values())
            result = ec.calculate_material_mass(shape, density, *param_values)

            self.workspace_editor.insert_calculation_result(
                "Malzeme Hesaplamaları",
                "Kütle Hesabı",
                {"shape": shape, "density": density, **params},
                result,
                "g",
            )

        except Exception:
            messagebox.showerror("Hata", "Lütfen önce hesaplama yapın.")

    def _handle_model_suggestion(self, context: str):
        """Handle model suggestion request."""
        if not self.current_model_name or not self.current_model_url:
            messagebox.showwarning(
                "Uyarı", "Lütfen önce model URL'sini ve model seçin."
            )
            return

        try:
            self.update_status_bar("Model önerisi isteniyor...")

            # Request model suggestion
            response = single_chat_request(
                self.current_model_url,
                self.current_model_name,
                f"Bu metni düzenle veya iyileştir: {context}",
                timeout=60,
            )

            # Add as suggestion to workspace
            current_content = self.workspace_editor.get_current_content()
            suggestion = self.workspace_buffer.suggest_edit(
                0, len(current_content), response, "Model suggestion"
            )

            self.workspace_editor._show_suggestions()
            self.update_status_bar("Model önerisi eklendi")

        except Exception as e:
            messagebox.showerror("Hata", f"Model önerisi alınamadı: {str(e)}")
            self.update_status_bar("Model önerisi başarısız")

    def _analyze_workspace(self):
        """Analyze entire workspace with model."""
        if not self.current_model_name or not self.current_model_url:
            messagebox.showwarning(
                "Uyarı", "Lütfen önce model URL'sini ve model seçin."
            )
            return

        try:
            self.update_status_bar("Çalışma alanı analiz ediliyor...")

            content = self.workspace_editor.get_current_content()
            context = (
                f"Bu mühendislik çalışma alanını analiz et ve öneriler sun: {content}"
            )

            response = single_chat_request(
                self.current_model_url, self.current_model_name, context, timeout=60
            )

            messagebox.showinfo("Çalışma Alanı Analizi", response)
            self.update_status_bar("Analiz tamamlandı")

        except Exception as e:
            messagebox.showerror("Hata", f"Analiz sırasında hata: {str(e)}")
            self.update_status_bar("Analiz başarısız")

    def _on_workspace_change(self, content: str):
        """Handle workspace content change."""
        # Auto-save or other actions can be added here
        pass

    def _new_workspace(self):
        """Create new workspace."""
        if messagebox.askyesno(
            "Yeni Çalışma Alanı",
            "Mevcut çalışma alanını temizlemek istediğinizden emin misiniz?",
        ):
            self.workspace_buffer.clear_all()
            self.workspace_editor._load_content()
            self.update_status_bar("Yeni çalışma alanı oluşturuldu")

    def _open_workspace(self):
        """Open workspace from file."""
        file_path = filedialog.askopenfilename(
            title="Çalışma Alanını Aç",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )

        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                if self.workspace_buffer.import_session(data):
                    self.workspace_editor._load_content()
                    self.update_status_bar(f"Çalışma alanı açıldı: {file_path}")
                else:
                    messagebox.showerror("Hata", "Çalışma alanı açılamadı.")

            except Exception as e:
                messagebox.showerror("Hata", f"Dosya açılırken hata: {str(e)}")

    def _save_workspace(self):
        """Save workspace to file."""
        file_path = filedialog.asksaveasfilename(
            title="Çalışma Alanını Kaydet",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )

        if file_path:
            try:
                data = self.workspace_buffer.export_session()
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)

                self.update_status_bar(f"Çalışma alanı kaydedildi: {file_path}")

            except Exception as e:
                messagebox.showerror("Hata", f"Dosya kaydedilirken hata: {str(e)}")

    def _export_workspace(self):
        """Export workspace to text file."""
        file_path = filedialog.asksaveasfilename(
            title="Çalışma Alanını Dışa Aktar",
            defaultextension=".txt",
            filetypes=[
                ("Text files", "*.txt"),
                ("Markdown files", "*.md"),
                ("All files", "*.*"),
            ],
        )

        if file_path:
            try:
                content = self.workspace_editor.get_current_content()
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)

                self.update_status_bar(f"Çalışma alanı dışa aktarıldı: {file_path}")

            except Exception as e:
                messagebox.showerror("Hata", f"Dışa aktarma hatası: {str(e)}")

    def refresh_model_list(self):
        """Refresh available models."""
        try:
            model_url = self.model_url_entry.get()
            self.ollama_models = get_available_models(model_url)
            self.model_selection_combo["values"] = self.ollama_models

            if self.ollama_models:
                if (
                    not self.current_model_name
                    or self.current_model_name not in self.ollama_models
                ):
                    self.model_selection_combo.set(self.ollama_models[0])
                    self.current_model_name = (
                        self.ollama_models[0] if self.ollama_models else ""
                    )
                else:
                    self.model_selection_combo.set(self.current_model_name)
            else:
                self.model_selection_combo.set("")
                self.current_model_name = None

            self.update_status_bar(
                f"Modeller yenilendi: {len(self.ollama_models)} model bulundu"
            )

        except Exception as e:
            messagebox.showerror("Hata", f"Modeller alınırken hata: {str(e)}")
            self.update_status_bar("Model yenileme başarısız")

    def test_model_connection(self):
        """Test connection to model."""
        try:
            model_url = self.model_url_entry.get()
            if test_connection(model_url):
                messagebox.showinfo(
                    "Bağlantı Başarılı", "Ollama sunucusuna bağlantı başarılı!"
                )
                self.update_status_bar("Bağlantı başarılı")
            else:
                messagebox.showerror(
                    "Bağlantı Başarısız", "Ollama sunucusuna bağlanılamadı!"
                )
                self.update_status_bar("Bağlantı başarısız")
        except Exception as e:
            messagebox.showerror("Hata", f"Bağlantı testi sırasında hata: {str(e)}")
            self.update_status_bar("Bağlantı testi başarısız")

    def update_status_bar(self, message: str):
        """Update status bar message."""
        self.status_var.set(message)
        self.root.update_idletasks()

    def _apply_default_geometry(self):
        """Apply default window geometry."""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")


def main():
    """Main entry point for V3 GUI."""
    root = tk.Tk()

    # Load tooltips
    try:
        with open("tooltips.json", "r", encoding="utf-8") as f:
            tooltips = json.load(f)
    except FileNotFoundError:
        tooltips = {}

    # Create V3 GUI
    app = V3Calculator(root, tooltips)

    # Handle model selection changes
    def on_model_select(event=None):
        app.current_model_name = app.model_selection_combo.get()
        app.current_model_url = app.model_url_entry.get()

    app.model_selection_combo.bind("<<ComboboxSelected>>", on_model_select)
    app.model_url_entry.bind("<FocusOut>", on_model_select)

    # Start GUI
    root.mainloop()


if __name__ == "__main__":
    main()
