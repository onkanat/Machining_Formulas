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

# Ollama integration
from ollama_utils_v2 import get_available_models, single_chat_request, test_connection

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

        # Keep references to PhotoImage instances
        self._header_images: Dict[str, tk.PhotoImage] = {}

        # State containers for dynamic calculation UIs (turning/milling)
        self._dynamic_calc_state: Dict[str, dict] = {}

        # Initialize workspace buffer
        self.workspace_buffer = WorkspaceBuffer()

        # Model configuration
        self.current_model_url = "http://192.168.1.14:11434"
        self.current_model_name = ""
        self.ollama_models: List[str] = []

        # Cache frequently used data for performance
        self._initialize_cached_data()

        # Setup UI
        self.setup_ui()

        # Force UI update before geometry calculations
        self.root.update_idletasks()
        self._apply_default_geometry()

        # Initialize model connection
        self.refresh_model_list()

    def _initialize_cached_data(self):
        """Initialize cached data for better performance."""
        # Cache shape mappings
        self.available_shapes_map = ec.get_available_shapes()
        self.reverse_shape_names = {v: k for k, v in self.available_shapes_map.items()}

        # Cache material data
        self.material_names = list(ec.material_density.keys())
        self.material_densities = ec.material_density.copy()

        # Cache parameter mappings
        self.param_to_gui_key_map = {
            "radius": "Yarıçap",
            "width": "Genişlik",
            "height": "Yükseklik",
            "outer_radius": "Dış Yarıçap",
            "inner_radius": "İç Yarıçap",
            "diagonal1": "Köşegen 1",
            "diagonal2": "Köşegen 2",
        }

    def setup_ui(self):
        """Setup the main V3 interface."""
        # Configure root window
        self.root.title("🔧 Mühendislik Hesaplayıcı V3 - Çalışma Alanı")
        self.root.geometry(f"{DEFAULT_WINDOW_SIZE[0]}x{DEFAULT_WINDOW_SIZE[1]}")

        # Configure styles first (before creating widgets)
        self._setup_styles()

        # Create main layout first
        self._create_main_layout()

        # Create menu bar
        self._create_menu_bar()

        # Create status bar
        self._create_status_bar()

        # Configure focus and keyboard handling after widgets are created
        self.root.focus_set()

        # Enable proper focus traversal (after widgets are created)
        try:
            self.root.tk.call("tkwait", "visibility", self.root)
        except:
            # Fallback for systems that don't support tkwait
            pass

        # Bind Tab key for navigation (after widgets are created)
        self.root.after(100, self._setup_navigation_bindings)

        # Setup focus management after all widgets are created
        self.root.after(1000, self._setup_focus_management)

    def _setup_navigation_bindings(self):
        """Setup navigation bindings after widgets are created."""
        try:
            # Bind Tab key for navigation
            self.root.bind("<Tab>", self._handle_tab_navigation)
            self.root.bind("<Shift-Tab>", self._handle_shift_tab_navigation)
            # Bind mouse click to ensure focus
            self.root.bind("<Button-1>", self._handle_root_click)
        except Exception:
            pass  # Ignore binding errors

    def _setup_focus_management(self):
        """Setup focus management for better keyboard/mouse interaction."""
        try:
            # Enable focus traversal for all widgets
            self.root.focus_set()

            # Make sure all Entry widgets can receive focus
            for widget in self.root.winfo_children():
                self._enable_widget_focus(widget)

            # Set initial focus to first input field after a delay
            self.root.after(200, self._set_initial_focus)

        except Exception as e:
            print(f"Focus setup error: {e}")

    def _set_initial_focus(self):
        """Set initial focus to first available input field."""
        try:
            if hasattr(self, "vc_diameter"):
                self.vc_diameter.focus_set()
                self.vc_diameter.select_range(0, tk.END)
            elif hasattr(self, "model_url_entry"):
                self.model_url_entry.focus_set()
        except Exception:
            pass

    def _handle_root_click(self, event):
        """Handle root window click to ensure proper focus."""
        try:
            # Get the widget that was clicked
            widget = event.widget
            if widget and widget != self.root:
                widget.focus_set()
        except Exception:
            pass

    def _enable_widget_focus(self, widget):
        """Recursively enable focus for all widgets."""
        try:
            # Enable focus for Entry and Text widgets
            if isinstance(widget, (tk.Entry, tk.Text)):
                widget.config(takefocus=1)
                widget.bind("<Button-1>", lambda e, w=widget: w.focus_set())
                widget.bind("<FocusIn>", lambda e: None)  # Ensure focus events work

            # Enable focus for ttk.Entry and ttk.Combobox
            elif isinstance(widget, (ttk.Entry, ttk.Combobox)):
                widget.configure(takefocus=True)
                widget.bind("<Button-1>", lambda e, w=widget: w.focus_set())
                widget.bind("<FocusIn>", lambda e: None)  # Ensure focus events work

            # Enable focus for buttons
            elif isinstance(widget, (ttk.Button, tk.Button)):
                widget.configure(takefocus=True)
                widget.bind("<Button-1>", lambda e, w=widget: w.focus_set())

            # Recursively process children
            for child in widget.winfo_children():
                self._enable_widget_focus(child)

        except Exception:
            pass

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

        # Configure focus styles for better visibility
        try:
            style.map(
                "TEntry",
                focuscolor=[("focus", "blue")],
                fieldbackground=[("focus", "white")],
            )
            style.map(
                "TCombobox",
                focuscolor=[("focus", "blue")],
                fieldbackground=[("focus", "white")],
            )
        except:
            # Fallback for older ttk versions
            pass

    def _create_main_layout(self):
        """Create main layout with paned windows."""
        # Main container
        main_container = ttk.Frame(self.root, style="Calc.TFrame")
        main_container.pack(fill="both", expand=True)

        # Create horizontal paned window with explicit sizing
        self.paned_window = ttk.PanedWindow(main_container, orient="horizontal")
        self.paned_window.pack(fill="both", expand=True, padx=5, pady=5)

        # Left panel - Calculation tools
        self._create_calculation_panel()

        # Right panel - Workspace editor
        self._create_workspace_panel()

        # Force final update after panels are added
        self.paned_window.update_idletasks()

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
        model_frame.pack(fill="x", expand=True, padx=5, pady=5)

        # Model URL
        url_frame = ttk.Frame(model_frame, style="Calc.TFrame")
        url_frame.pack(fill="x", padx=5, pady=2)

        ttk.Label(url_frame, text="URL:", width=8).pack(side="left")
        self.model_url_entry = ttk.Entry(url_frame, width=30)
        self.model_url_entry.pack(side="left", fill="x", expand=True, padx=(5, 0))
        self.model_url_entry.insert(0, "http://192.168.1.14:11434")

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

        # Header canvas (PNG if available)
        self._add_tab_header(turning_frame, image_filename="turning.png", fallback_text="Tornalama")

        # Dynamic calculation form (dropdown -> params)
        self._init_dynamic_calc_ui(
            parent=turning_frame,
            calc_category_key="turning",
            calc_type_display="Tornalama Hesaplamaları",
            state_key="turning",
        )

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

        # Header canvas (PNG if available)
        self._add_tab_header(milling_frame, image_filename="milling.png", fallback_text="Frezeleme")

        # Dynamic calculation form (dropdown -> params)
        self._init_dynamic_calc_ui(
            parent=milling_frame,
            calc_category_key="milling",
            calc_type_display="Frezeleme Hesaplamaları",
            state_key="milling",
        )

    def _create_milling_table_feed_calc(self, parent):
        """Create milling table feed calculation."""
        frame = ttk.LabelFrame(parent, text="Tabla İlerlemesi", style="Calc.TFrame")
        frame.pack(fill="x", padx=5, pady=5)

        # Feed per tooth input
        feed_frame = ttk.Frame(frame, style="Calc.TFrame")
        feed_frame.pack(fill="x", padx=5, pady=2)
        ttk.Label(feed_frame, text="Diş Başı İlerleme:", width=15).pack(side="left")
        self.milling_feed_per_tooth = ttk.Entry(feed_frame, width=15)
        self.milling_feed_per_tooth.pack(side="left", padx=(5, 0))
        ttk.Label(feed_frame, text="mm/diş").pack(side="left", padx=(2, 0))

        # Number of teeth input
        teeth_frame = ttk.Frame(frame, style="Calc.TFrame")
        teeth_frame.pack(fill="x", padx=5, pady=2)
        ttk.Label(teeth_frame, text="Diş Sayısı:", width=15).pack(side="left")
        self.milling_num_teeth = ttk.Entry(teeth_frame, width=15)
        self.milling_num_teeth.pack(side="left", padx=(5, 0))
        ttk.Label(teeth_frame, text="adet").pack(side="left", padx=(2, 0))

        # RPM input
        rpm_frame = ttk.Frame(frame, style="Calc.TFrame")
        rpm_frame.pack(fill="x", padx=5, pady=2)
        ttk.Label(rpm_frame, text="İş Mili Devri:", width=15).pack(side="left")
        self.milling_rpm = ttk.Entry(rpm_frame, width=15)
        self.milling_rpm.pack(side="left", padx=(5, 0))
        ttk.Label(rpm_frame, text="rpm").pack(side="left", padx=(2, 0))

        # Calculate button
        ttk.Button(
            frame, text="Hesapla", command=self._calculate_milling_table_feed
        ).pack(pady=5)

        # Result display
        self.milling_table_feed_result = ttk.Label(
            frame, text="", font=("Arial", 10, "bold"), foreground="blue"
        )
        self.milling_table_feed_result.pack(pady=2)

        # Inject to workspace button
        ttk.Button(
            frame,
            text="📝 Çalışma Alanına Ekle",
            command=self._inject_milling_table_feed,
        ).pack(pady=2)

    def _create_milling_cutting_speed_calc(self, parent):
        """Create milling cutting speed calculation."""
        frame = ttk.LabelFrame(parent, text="Kesme Hızı", style="Calc.TFrame")
        frame.pack(fill="x", padx=5, pady=5)

        # Diameter input
        diam_frame = ttk.Frame(frame, style="Calc.TFrame")
        diam_frame.pack(fill="x", padx=5, pady=2)
        ttk.Label(diam_frame, text="Çap (D):", width=15).pack(side="left")
        self.milling_cutting_diameter = ttk.Entry(diam_frame, width=15)
        self.milling_cutting_diameter.pack(side="left", padx=(5, 0))
        ttk.Label(diam_frame, text="mm").pack(side="left", padx=(2, 0))

        # RPM input
        rpm_frame = ttk.Frame(frame, style="Calc.TFrame")
        rpm_frame.pack(fill="x", padx=5, pady=2)
        ttk.Label(rpm_frame, text="İş Mili Devri:", width=15).pack(side="left")
        self.milling_cutting_rpm = ttk.Entry(rpm_frame, width=15)
        self.milling_cutting_rpm.pack(side="left", padx=(5, 0))
        ttk.Label(rpm_frame, text="rpm").pack(side="left", padx=(2, 0))

        # Calculate button
        ttk.Button(
            frame, text="Hesapla", command=self._calculate_milling_cutting_speed
        ).pack(pady=5)

        # Result display
        self.milling_cutting_speed_result = ttk.Label(
            frame, text="", font=("Arial", 10, "bold"), foreground="blue"
        )
        self.milling_cutting_speed_result.pack(pady=2)

        # Inject to workspace button
        ttk.Button(
            frame,
            text="📝 Çalışma Alanına Ekle",
            command=self._inject_milling_cutting_speed,
        ).pack(pady=2)

    def _create_milling_spindle_speed_calc(self, parent):
        """Create milling spindle speed calculation."""
        frame = ttk.LabelFrame(parent, text="İş Mili Devri", style="Calc.TFrame")
        frame.pack(fill="x", padx=5, pady=5)

        # Cutting speed input
        speed_frame = ttk.Frame(frame, style="Calc.TFrame")
        speed_frame.pack(fill="x", padx=5, pady=2)
        ttk.Label(speed_frame, text="Kesme Hızı:", width=15).pack(side="left")
        self.milling_spindle_cutting_speed = ttk.Entry(speed_frame, width=15)
        self.milling_spindle_cutting_speed.pack(side="left", padx=(5, 0))
        ttk.Label(speed_frame, text="m/dak").pack(side="left", padx=(2, 0))

        # Diameter input
        diam_frame = ttk.Frame(frame, style="Calc.TFrame")
        diam_frame.pack(fill="x", padx=5, pady=2)
        ttk.Label(diam_frame, text="Çap (D):", width=15).pack(side="left")
        self.milling_spindle_diameter = ttk.Entry(diam_frame, width=15)
        self.milling_spindle_diameter.pack(side="left", padx=(5, 0))
        ttk.Label(diam_frame, text="mm").pack(side="left", padx=(2, 0))

        # Calculate button
        ttk.Button(
            frame, text="Hesapla", command=self._calculate_milling_spindle_speed
        ).pack(pady=5)

        # Result display
        self.milling_spindle_speed_result = ttk.Label(
            frame, text="", font=("Arial", 10, "bold"), foreground="blue"
        )
        self.milling_spindle_speed_result.pack(pady=2)

        # Inject to workspace button
        ttk.Button(
            frame,
            text="📝 Çalışma Alanına Ekle",
            command=self._inject_milling_spindle_speed,
        ).pack(pady=2)

    def _create_milling_feed_per_tooth_calc(self, parent):
        """Create milling feed per tooth calculation."""
        frame = ttk.LabelFrame(parent, text="Diş Başı İlerleme", style="Calc.TFrame")
        frame.pack(fill="x", padx=5, pady=5)

        # Table feed input
        feed_frame = ttk.Frame(frame, style="Calc.TFrame")
        feed_frame.pack(fill="x", padx=5, pady=2)
        ttk.Label(feed_frame, text="Tabla İlerlemesi:", width=15).pack(side="left")
        self.milling_fz_table_feed = ttk.Entry(feed_frame, width=15)
        self.milling_fz_table_feed.pack(side="left", padx=(5, 0))
        ttk.Label(feed_frame, text="mm/dak").pack(side="left", padx=(2, 0))

        # Number of teeth input
        teeth_frame = ttk.Frame(frame, style="Calc.TFrame")
        teeth_frame.pack(fill="x", padx=5, pady=2)
        ttk.Label(teeth_frame, text="Diş Sayısı:", width=15).pack(side="left")
        self.milling_fz_num_teeth = ttk.Entry(teeth_frame, width=15)
        self.milling_fz_num_teeth.pack(side="left", padx=(5, 0))
        ttk.Label(teeth_frame, text="adet").pack(side="left", padx=(2, 0))

        # RPM input
        rpm_frame = ttk.Frame(frame, style="Calc.TFrame")
        rpm_frame.pack(fill="x", padx=5, pady=2)
        ttk.Label(rpm_frame, text="İş Mili Devri:", width=15).pack(side="left")
        self.milling_fz_rpm = ttk.Entry(rpm_frame, width=15)
        self.milling_fz_rpm.pack(side="left", padx=(5, 0))
        ttk.Label(rpm_frame, text="rpm").pack(side="left", padx=(2, 0))

        # Calculate button
        ttk.Button(
            frame, text="Hesapla", command=self._calculate_milling_feed_per_tooth
        ).pack(pady=5)

        # Result display
        self.milling_feed_per_tooth_result = ttk.Label(
            frame, text="", font=("Arial", 10, "bold"), foreground="blue"
        )
        self.milling_feed_per_tooth_result.pack(pady=2)

        # Inject to workspace button
        ttk.Button(
            frame,
            text="📝 Çalışma Alanına Ekle",
            command=self._inject_milling_feed_per_tooth,
        ).pack(pady=2)

    def _create_milling_feed_per_revolution_calc(self, parent):
        """Create milling feed per revolution calculation."""
        frame = ttk.LabelFrame(parent, text="Devir Başı İlerleme", style="Calc.TFrame")
        frame.pack(fill="x", padx=5, pady=5)

        # Table feed input
        feed_frame = ttk.Frame(frame, style="Calc.TFrame")
        feed_frame.pack(fill="x", padx=5, pady=2)
        ttk.Label(feed_frame, text="Tabla İlerlemesi:", width=15).pack(side="left")
        self.milling_fn_table_feed = ttk.Entry(feed_frame, width=15)
        self.milling_fn_table_feed.pack(side="left", padx=(5, 0))
        ttk.Label(feed_frame, text="mm/dak").pack(side="left", padx=(2, 0))

        # RPM input
        rpm_frame = ttk.Frame(frame, style="Calc.TFrame")
        rpm_frame.pack(fill="x", padx=5, pady=2)
        ttk.Label(rpm_frame, text="İş Mili Devri:", width=15).pack(side="left")
        self.milling_fn_rpm = ttk.Entry(rpm_frame, width=15)
        self.milling_fn_rpm.pack(side="left", padx=(5, 0))
        ttk.Label(rpm_frame, text="rpm").pack(side="left", padx=(2, 0))

        # Calculate button
        ttk.Button(
            frame, text="Hesapla", command=self._calculate_milling_feed_per_revolution
        ).pack(pady=5)

        # Result display
        self.milling_feed_per_revolution_result = ttk.Label(
            frame, text="", font=("Arial", 10, "bold"), foreground="blue"
        )
        self.milling_feed_per_revolution_result.pack(pady=2)

        # Inject to workspace button
        ttk.Button(
            frame,
            text="📝 Çalışma Alanına Ekle",
            command=self._inject_milling_feed_per_revolution,
        ).pack(pady=2)

    def _create_milling_mrr_calc(self, parent):
        """Create milling metal removal rate calculation."""
        frame = ttk.LabelFrame(parent, text="Talaş Debisi", style="Calc.TFrame")
        frame.pack(fill="x", padx=5, pady=5)

        # Cutting speed input
        speed_frame = ttk.Frame(frame, style="Calc.TFrame")
        speed_frame.pack(fill="x", padx=5, pady=2)
        ttk.Label(speed_frame, text="Kesme Hızı:", width=15).pack(side="left")
        self.milling_mrr_cutting_speed = ttk.Entry(speed_frame, width=15)
        self.milling_mrr_cutting_speed.pack(side="left", padx=(5, 0))
        ttk.Label(speed_frame, text="m/dak").pack(side="left", padx=(2, 0))

        # Feed per tooth input
        feed_frame = ttk.Frame(frame, style="Calc.TFrame")
        feed_frame.pack(fill="x", padx=5, pady=2)
        ttk.Label(feed_frame, text="Diş Başı İlerleme:", width=15).pack(side="left")
        self.milling_mrr_feed_per_tooth = ttk.Entry(feed_frame, width=15)
        self.milling_mrr_feed_per_tooth.pack(side="left", padx=(5, 0))
        ttk.Label(feed_frame, text="mm/diş").pack(side="left", padx=(2, 0))

        # Number of teeth input
        teeth_frame = ttk.Frame(frame, style="Calc.TFrame")
        teeth_frame.pack(fill="x", padx=5, pady=2)
        ttk.Label(teeth_frame, text="Diş Sayısı:", width=15).pack(side="left")
        self.milling_mrr_num_teeth = ttk.Entry(teeth_frame, width=15)
        self.milling_mrr_num_teeth.pack(side="left", padx=(5, 0))
        ttk.Label(teeth_frame, text="adet").pack(side="left", padx=(2, 0))

        # Calculate button
        ttk.Button(frame, text="Hesapla", command=self._calculate_milling_mrr).pack(
            pady=5
        )

        # Result display
        self.milling_mrr_result = ttk.Label(
            frame, text="", font=("Arial", 10, "bold"), foreground="blue"
        )
        self.milling_mrr_result.pack(pady=2)

        # Inject to workspace button
        ttk.Button(
            frame, text="📝 Çalışma Alanına Ekle", command=self._inject_milling_mrr
        ).pack(pady=2)

    def _create_milling_net_power_calc(self, parent):
        """Create milling net power calculation."""
        frame = ttk.LabelFrame(parent, text="Net Güç", style="Calc.TFrame")
        frame.pack(fill="x", padx=5, pady=5)

        # Cutting speed input
        speed_frame = ttk.Frame(frame, style="Calc.TFrame")
        speed_frame.pack(fill="x", padx=5, pady=2)
        ttk.Label(speed_frame, text="Kesme Hızı:", width=15).pack(side="left")
        self.milling_power_cutting_speed = ttk.Entry(speed_frame, width=15)
        self.milling_power_cutting_speed.pack(side="left", padx=(5, 0))
        ttk.Label(speed_frame, text="m/dak").pack(side="left", padx=(2, 0))

        # Feed per tooth input
        feed_frame = ttk.Frame(frame, style="Calc.TFrame")
        feed_frame.pack(fill="x", padx=5, pady=2)
        ttk.Label(feed_frame, text="Diş Başı İlerleme:", width=15).pack(side="left")
        self.milling_power_feed_per_tooth = ttk.Entry(feed_frame, width=15)
        self.milling_power_feed_per_tooth.pack(side="left", padx=(5, 0))
        ttk.Label(feed_frame, text="mm/diş").pack(side="left", padx=(2, 0))

        # Number of teeth input
        teeth_frame = ttk.Frame(frame, style="Calc.TFrame")
        teeth_frame.pack(fill="x", padx=5, pady=2)
        ttk.Label(teeth_frame, text="Diş Sayısı:", width=15).pack(side="left")
        self.milling_power_num_teeth = ttk.Entry(teeth_frame, width=15)
        self.milling_power_num_teeth.pack(side="left", padx=(5, 0))
        ttk.Label(teeth_frame, text="adet").pack(side="left", padx=(2, 0))

        # Calculate button
        ttk.Button(
            frame, text="Hesapla", command=self._calculate_milling_net_power
        ).pack(pady=5)

        # Result display
        self.milling_net_power_result = ttk.Label(
            frame, text="", font=("Arial", 10, "bold"), foreground="blue"
        )
        self.milling_net_power_result.pack(pady=2)

        # Inject to workspace button
        ttk.Button(
            frame,
            text="📝 Çalışma Alanına Ekle",
            command=self._inject_milling_net_power,
        ).pack(pady=2)

    def _create_milling_torque_calc(self, parent):
        """Create milling torque calculation."""
        frame = ttk.LabelFrame(parent, text="Tork", style="Calc.TFrame")
        frame.pack(fill="x", padx=5, pady=5)

        # Cutting speed input
        speed_frame = ttk.Frame(frame, style="Calc.TFrame")
        speed_frame.pack(fill="x", padx=5, pady=2)
        ttk.Label(speed_frame, text="Kesme Hızı:", width=15).pack(side="left")
        self.milling_torque_cutting_speed = ttk.Entry(speed_frame, width=15)
        self.milling_torque_cutting_speed.pack(side="left", padx=(5, 0))
        ttk.Label(speed_frame, text="m/dak").pack(side="left", padx=(2, 0))

        # Feed per tooth input
        feed_frame = ttk.Frame(frame, style="Calc.TFrame")
        feed_frame.pack(fill="x", padx=5, pady=2)
        ttk.Label(feed_frame, text="Diş Başı İlerleme:", width=15).pack(side="left")
        self.milling_torque_feed_per_tooth = ttk.Entry(feed_frame, width=15)
        self.milling_torque_feed_per_tooth.pack(side="left", padx=(5, 0))
        ttk.Label(feed_frame, text="mm/diş").pack(side="left", padx=(2, 0))

        # Number of teeth input
        teeth_frame = ttk.Frame(frame, style="Calc.TFrame")
        teeth_frame.pack(fill="x", padx=5, pady=2)
        ttk.Label(teeth_frame, text="Diş Sayısı:", width=15).pack(side="left")
        self.milling_torque_num_teeth = ttk.Entry(teeth_frame, width=15)
        self.milling_torque_num_teeth.pack(side="left", padx=(5, 0))
        ttk.Label(teeth_frame, text="adet").pack(side="left", padx=(2, 0))

        # Calculate button
        ttk.Button(frame, text="Hesapla", command=self._calculate_milling_torque).pack(
            pady=5
        )

        # Result display
        self.milling_torque_result = ttk.Label(
            frame, text="", font=("Arial", 10, "bold"), foreground="blue"
        )
        self.milling_torque_result.pack(pady=2)

        # Inject to workspace button
        ttk.Button(
            frame, text="📝 Çalışma Alanına Ekle", command=self._inject_milling_torque
        ).pack(pady=2)

    def _create_material_tab(self):
        """Create material calculations tab."""
        material_frame = ttk.Frame(self.calc_notebook, style="Calc.TFrame")
        self.calc_notebook.add(material_frame, text="Malzeme")

        # Header canvas (PNG if available)
        self._add_tab_header(material_frame, image_filename="material.png", fallback_text="Malzeme")

        # Mass calculation
        self._create_mass_calc(material_frame)

    def _create_mass_calc(self, parent):
        """Create mass calculation."""
        frame = ttk.LabelFrame(parent, text="Kütle Hesabı", style="Calc.TFrame")
        frame.pack(fill="x", expand=True, padx=5, pady=5)

        # Use cached shape data
        shape_display_names = list(self.available_shapes_map.values())

        # Shape selection
        shape_frame = ttk.Frame(frame, style="Calc.TFrame")
        shape_frame.pack(fill="x", padx=5, pady=2)
        ttk.Label(shape_frame, text="Şekil:", width=15).pack(side="left")
        self.mass_shape = ttk.Combobox(shape_frame, width=20, style="Calc.TCombobox")
        self.mass_shape.pack(side="left", padx=(5, 0))
        self.mass_shape["values"] = shape_display_names
        if shape_display_names:
            self.mass_shape.set(shape_display_names[0])  # Default to first shape
        self.mass_shape.bind("<<ComboboxSelected>>", self._update_mass_params)

        # Dynamic parameters frame
        self.mass_params_frame = ttk.Frame(frame, style="Calc.TFrame")
        self.mass_params_frame.pack(fill="x", expand=True, padx=5, pady=5)

        # Material selection and density input
        density_frame = ttk.Frame(frame, style="Calc.TFrame")
        density_frame.pack(fill="x", padx=5, pady=2)

        ttk.Label(density_frame, text="Yoğunluk:", width=15).pack(side="left")
        self.mass_density = ttk.Entry(density_frame, width=15)
        self.mass_density.pack(side="left", padx=(5, 0))
        ttk.Label(density_frame, text="g/cm³").pack(side="left", padx=(2, 0))

        # Material selection dropdown using cached data
        self.mass_material = ttk.Combobox(
            density_frame, values=self.material_names, state="readonly", width=15
        )
        self.mass_material.pack(side="left", padx=(10, 0))

        def _on_material_select(event=None):
            mat = self.mass_material.get()
            if mat in self.material_densities:
                self.mass_density.delete(0, "end")
                self.mass_density.insert(0, str(self.material_densities[mat]))

        self.mass_material.bind("<<ComboboxSelected>>", _on_material_select)
        if self.material_names:
            self.mass_material.set(self.material_names[0])
            _on_material_select()

        # Initialize with first shape parameters
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

    # Milling calculation methods
    def _calculate_milling_table_feed(self):
        """Calculate milling table feed."""
        try:
            feed_per_tooth = float(self.milling_feed_per_tooth.get())
            num_teeth = float(self.milling_num_teeth.get())
            rpm = float(self.milling_rpm.get())

            result_dict = ec.calculate_milling(
                "Table feed", feed_per_tooth, num_teeth, rpm
            )
            result = result_dict["value"]
            self.milling_table_feed_result.config(text=f"Sonuç: {result:.2f} mm/dak")

        except ValueError:
            messagebox.showerror("Hata", "Lütfen geçerli sayısal değerler girin.")
        except Exception as e:
            messagebox.showerror("Hata", f"Hesaplama hatası: {str(e)}")

    def _calculate_milling_cutting_speed(self):
        """Calculate milling cutting speed."""
        try:
            diameter = float(self.milling_cutting_diameter.get())
            rpm = float(self.milling_cutting_rpm.get())

            result_dict = ec.calculate_milling("Cutting speed", diameter, rpm)
            result = result_dict["value"]
            self.milling_cutting_speed_result.config(text=f"Sonuç: {result:.2f} m/dak")

        except ValueError:
            messagebox.showerror("Hata", "Lütfen geçerli sayısal değerler girin.")
        except Exception as e:
            messagebox.showerror("Hata", f"Hesaplama hatası: {str(e)}")

    def _calculate_milling_spindle_speed(self):
        """Calculate milling spindle speed."""
        try:
            cutting_speed = float(self.milling_spindle_cutting_speed.get())
            diameter = float(self.milling_spindle_diameter.get())

            result_dict = ec.calculate_milling("Spindle speed", cutting_speed, diameter)
            result = result_dict["value"]
            self.milling_spindle_speed_result.config(text=f"Sonuç: {result:.0f} rpm")

        except ValueError:
            messagebox.showerror("Hata", "Lütfen geçerli sayısal değerler girin.")
        except Exception as e:
            messagebox.showerror("Hata", f"Hesaplama hatası: {str(e)}")

    def _calculate_milling_feed_per_tooth(self):
        """Calculate milling feed per tooth."""
        try:
            table_feed = float(self.milling_fz_table_feed.get())
            num_teeth = float(self.milling_fz_num_teeth.get())
            rpm = float(self.milling_fz_rpm.get())

            result_dict = ec.calculate_milling(
                "Feed per tooth", table_feed, num_teeth, rpm
            )
            result = result_dict["value"]
            self.milling_feed_per_tooth_result.config(
                text=f"Sonuç: {result:.3f} mm/diş"
            )

        except ValueError:
            messagebox.showerror("Hata", "Lütfen geçerli sayısal değerler girin.")
        except Exception as e:
            messagebox.showerror("Hata", f"Hesaplama hatası: {str(e)}")

    def _calculate_milling_feed_per_revolution(self):
        """Calculate milling feed per revolution."""
        try:
            table_feed = float(self.milling_fn_table_feed.get())
            rpm = float(self.milling_fn_rpm.get())

            result_dict = ec.calculate_milling("Feed per revolution", table_feed, rpm)
            result = result_dict["value"]
            self.milling_feed_per_revolution_result.config(
                text=f"Sonuç: {result:.3f} mm/dev"
            )

        except ValueError:
            messagebox.showerror("Hata", "Lütfen geçerli sayısal değerler girin.")
        except Exception as e:
            messagebox.showerror("Hata", f"Hesaplama hatası: {str(e)}")

    def _calculate_milling_mrr(self):
        """Calculate milling metal removal rate."""
        try:
            cutting_speed = float(self.milling_mrr_cutting_speed.get())
            feed_per_tooth = float(self.milling_mrr_feed_per_tooth.get())
            num_teeth = float(self.milling_mrr_num_teeth.get())

            result_dict = ec.calculate_milling(
                "Metal removal rate", cutting_speed, feed_per_tooth, num_teeth
            )
            result = result_dict["value"]
            self.milling_mrr_result.config(text=f"Sonuç: {result:.2f} cm³/dak")

        except ValueError:
            messagebox.showerror("Hata", "Lütfen geçerli sayısal değerler girin.")
        except Exception as e:
            messagebox.showerror("Hata", f"Hesaplama hatası: {str(e)}")

    def _calculate_milling_net_power(self):
        """Calculate milling net power."""
        try:
            cutting_speed = float(self.milling_power_cutting_speed.get())
            feed_per_tooth = float(self.milling_power_feed_per_tooth.get())
            num_teeth = float(self.milling_power_num_teeth.get())

            result_dict = ec.calculate_milling(
                "Net power", cutting_speed, feed_per_tooth, num_teeth
            )
            result = result_dict["value"]
            self.milling_net_power_result.config(text=f"Sonuç: {result:.2f} kW")

        except ValueError:
            messagebox.showerror("Hata", "Lütfen geçerli sayısal değerler girin.")
        except Exception as e:
            messagebox.showerror("Hata", f"Hesaplama hatası: {str(e)}")

    def _calculate_milling_torque(self):
        """Calculate milling torque."""
        try:
            cutting_speed = float(self.milling_torque_cutting_speed.get())
            feed_per_tooth = float(self.milling_torque_feed_per_tooth.get())
            num_teeth = float(self.milling_torque_num_teeth.get())

            result_dict = ec.calculate_milling(
                "Torque", cutting_speed, feed_per_tooth, num_teeth
            )
            result = result_dict["value"]
            self.milling_torque_result.config(text=f"Sonuç: {result:.2f} Nm")

        except ValueError:
            messagebox.showerror("Hata", "Lütfen geçerli sayısal değerler girin.")
        except Exception as e:
            messagebox.showerror("Hata", f"Hesaplama hatası: {str(e)}")

    # Inject methods for milling calculations
    def _inject_milling_table_feed(self):
        """Inject milling table feed calculation into workspace."""
        try:
            # Check if calculation has been performed
            if not hasattr(
                self, "milling_table_feed_result"
            ) or not self.milling_table_feed_result.cget("text"):
                messagebox.showerror("Hata", "Lütfen önce hesaplama yapın.")
                return

            # Get calculation result
            result_text = self.milling_table_feed_result.cget("text")
            if not result_text or "Sonuç:" not in result_text:
                messagebox.showerror("Hata", "Lütfen önce hesaplama yapın.")
                return

            # Extract result value
            try:
                result_value = float(result_text.split(":")[1].strip().split()[0])
            except (IndexError, ValueError):
                messagebox.showerror("Hata", "Lütfen önce hesaplama yapın.")
                return

            feed_per_tooth = float(self.milling_feed_per_tooth.get())
            num_teeth = float(self.milling_num_teeth.get())
            rpm = float(self.milling_rpm.get())

            self.workspace_editor.insert_calculation_result(
                "Frezeleme Hesaplamaları",
                "Tabla İlerlemesi",
                {"fz": feed_per_tooth, "z": num_teeth, "n": rpm},
                result_value,
                "mm/dak",
            )

        except Exception as e:
            messagebox.showerror("Hata", f"Lütfen önce hesaplama yapın: {str(e)}")

    def _inject_milling_cutting_speed(self):
        """Inject milling cutting speed calculation into workspace."""
        try:
            # Check if calculation has been performed
            if not hasattr(
                self, "milling_cutting_speed_result"
            ) or not self.milling_cutting_speed_result.cget("text"):
                messagebox.showerror("Hata", "Lütfen önce hesaplama yapın.")
                return

            # Get calculation result
            result_text = self.milling_cutting_speed_result.cget("text")
            if not result_text or "Sonuç:" not in result_text:
                messagebox.showerror("Hata", "Lütfen önce hesaplama yapın.")
                return

            # Extract result value
            try:
                result_value = float(result_text.split(":")[1].strip().split()[0])
            except (IndexError, ValueError):
                messagebox.showerror("Hata", "Lütfen önce hesaplama yapın.")
                return

            diameter = float(self.milling_cutting_diameter.get())
            rpm = float(self.milling_cutting_rpm.get())

            self.workspace_editor.insert_calculation_result(
                "Frezeleme Hesaplamaları",
                "Kesme Hızı",
                {"D": diameter, "n": rpm},
                result_value,
                "m/dak",
            )

        except Exception as e:
            messagebox.showerror("Hata", f"Lütfen önce hesaplama yapın: {str(e)}")

    def _inject_milling_spindle_speed(self):
        """Inject milling spindle speed calculation into workspace."""
        try:
            # Check if calculation has been performed
            if not hasattr(
                self, "milling_spindle_speed_result"
            ) or not self.milling_spindle_speed_result.cget("text"):
                messagebox.showerror("Hata", "Lütfen önce hesaplama yapın.")
                return

            # Get calculation result
            result_text = self.milling_spindle_speed_result.cget("text")
            if not result_text or "Sonuç:" not in result_text:
                messagebox.showerror("Hata", "Lütfen önce hesaplama yapın.")
                return

            # Extract result value
            try:
                result_value = float(result_text.split(":")[1].strip().split()[0])
            except (IndexError, ValueError):
                messagebox.showerror("Hata", "Lütfen önce hesaplama yapın.")
                return

            cutting_speed = float(self.milling_spindle_cutting_speed.get())
            diameter = float(self.milling_spindle_diameter.get())

            self.workspace_editor.insert_calculation_result(
                "Frezeleme Hesaplamaları",
                "İş Mili Devri",
                {"Vc": cutting_speed, "D": diameter},
                result_value,
                "rpm",
            )

        except Exception as e:
            messagebox.showerror("Hata", f"Lütfen önce hesaplama yapın: {str(e)}")

    def _inject_milling_feed_per_tooth(self):
        """Inject milling feed per tooth calculation into workspace."""
        try:
            # Check if calculation has been performed
            if not hasattr(
                self, "milling_feed_per_tooth_result"
            ) or not self.milling_feed_per_tooth_result.cget("text"):
                messagebox.showerror("Hata", "Lütfen önce hesaplama yapın.")
                return

            # Get calculation result
            result_text = self.milling_feed_per_tooth_result.cget("text")
            if not result_text or "Sonuç:" not in result_text:
                messagebox.showerror("Hata", "Lütfen önce hesaplama yapın.")
                return

            # Extract result value
            try:
                result_value = float(result_text.split(":")[1].strip().split()[0])
            except (IndexError, ValueError):
                messagebox.showerror("Hata", "Lütfen önce hesaplama yapın.")
                return

            table_feed = float(self.milling_fz_table_feed.get())
            num_teeth = float(self.milling_fz_num_teeth.get())
            rpm = float(self.milling_fz_rpm.get())

            self.workspace_editor.insert_calculation_result(
                "Frezeleme Hesaplamaları",
                "Diş Başı İlerleme",
                {"Vf": table_feed, "z": num_teeth, "n": rpm},
                result_value,
                "mm/diş",
            )

        except Exception as e:
            messagebox.showerror("Hata", f"Lütfen önce hesaplama yapın: {str(e)}")

    def _inject_milling_feed_per_revolution(self):
        """Inject milling feed per revolution calculation into workspace."""
        try:
            # Check if calculation has been performed
            if not hasattr(
                self, "milling_feed_per_revolution_result"
            ) or not self.milling_feed_per_revolution_result.cget("text"):
                messagebox.showerror("Hata", "Lütfen önce hesaplama yapın.")
                return

            # Get calculation result
            result_text = self.milling_feed_per_revolution_result.cget("text")
            if not result_text or "Sonuç:" not in result_text:
                messagebox.showerror("Hata", "Lütfen önce hesaplama yapın.")
                return

            # Extract result value
            try:
                result_value = float(result_text.split(":")[1].strip().split()[0])
            except (IndexError, ValueError):
                messagebox.showerror("Hata", "Lütfen önce hesaplama yapın.")
                return

            table_feed = float(self.milling_fn_table_feed.get())
            rpm = float(self.milling_fn_rpm.get())

            self.workspace_editor.insert_calculation_result(
                "Frezeleme Hesaplamaları",
                "Devir Başı İlerleme",
                {"Vf": table_feed, "n": rpm},
                result_value,
                "mm/dev",
            )

        except Exception as e:
            messagebox.showerror("Hata", f"Lütfen önce hesaplama yapın: {str(e)}")

    def _inject_milling_mrr(self):
        """Inject milling metal removal rate calculation into workspace."""
        try:
            # Check if calculation has been performed
            if not hasattr(
                self, "milling_mrr_result"
            ) or not self.milling_mrr_result.cget("text"):
                messagebox.showerror("Hata", "Lütfen önce hesaplama yapın.")
                return

            # Get calculation result
            result_text = self.milling_mrr_result.cget("text")
            if not result_text or "Sonuç:" not in result_text:
                messagebox.showerror("Hata", "Lütfen önce hesaplama yapın.")
                return

            # Extract result value
            try:
                result_value = float(result_text.split(":")[1].strip().split()[0])
            except (IndexError, ValueError):
                messagebox.showerror("Hata", "Lütfen önce hesaplama yapın.")
                return

            cutting_speed = float(self.milling_mrr_cutting_speed.get())
            feed_per_tooth = float(self.milling_mrr_feed_per_tooth.get())
            num_teeth = float(self.milling_mrr_num_teeth.get())

            self.workspace_editor.insert_calculation_result(
                "Frezeleme Hesaplamaları",
                "Talaş Debisi",
                {"Vc": cutting_speed, "fz": feed_per_tooth, "z": num_teeth},
                result_value,
                "cm³/dak",
            )

        except Exception as e:
            messagebox.showerror("Hata", f"Lütfen önce hesaplama yapın: {str(e)}")

    def _inject_milling_net_power(self):
        """Inject milling net power calculation into workspace."""
        try:
            # Check if calculation has been performed
            if not hasattr(
                self, "milling_net_power_result"
            ) or not self.milling_net_power_result.cget("text"):
                messagebox.showerror("Hata", "Lütfen önce hesaplama yapın.")
                return

            # Get calculation result
            result_text = self.milling_net_power_result.cget("text")
            if not result_text or "Sonuç:" not in result_text:
                messagebox.showerror("Hata", "Lütfen önce hesaplama yapın.")
                return

            # Extract result value
            try:
                result_value = float(result_text.split(":")[1].strip().split()[0])
            except (IndexError, ValueError):
                messagebox.showerror("Hata", "Lütfen önce hesaplama yapın.")
                return

            cutting_speed = float(self.milling_power_cutting_speed.get())
            feed_per_tooth = float(self.milling_power_feed_per_tooth.get())
            num_teeth = float(self.milling_power_num_teeth.get())

            self.workspace_editor.insert_calculation_result(
                "Frezeleme Hesaplamaları",
                "Net Güç",
                {"Vc": cutting_speed, "fz": feed_per_tooth, "z": num_teeth},
                result_value,
                "kW",
            )

        except Exception as e:
            messagebox.showerror("Hata", f"Lütfen önce hesaplama yapın: {str(e)}")

    def _inject_milling_torque(self):
        """Inject milling torque calculation into workspace."""
        try:
            # Check if calculation has been performed
            if not hasattr(
                self, "milling_torque_result"
            ) or not self.milling_torque_result.cget("text"):
                messagebox.showerror("Hata", "Lütfen önce hesaplama yapın.")
                return

            # Get calculation result
            result_text = self.milling_torque_result.cget("text")
            if not result_text or "Sonuç:" not in result_text:
                messagebox.showerror("Hata", "Lütfen önce hesaplama yapın.")
                return

            # Extract result value
            try:
                result_value = float(result_text.split(":")[1].strip().split()[0])
            except (IndexError, ValueError):
                messagebox.showerror("Hata", "Lütfen önce hesaplama yapın.")
                return

            cutting_speed = float(self.milling_torque_cutting_speed.get())
            feed_per_tooth = float(self.milling_torque_feed_per_tooth.get())
            num_teeth = float(self.milling_torque_num_teeth.get())

            self.workspace_editor.insert_calculation_result(
                "Frezeleme Hesaplamaları",
                "Tork",
                {"Vc": cutting_speed, "fz": feed_per_tooth, "z": num_teeth},
                result_value,
                "Nm",
            )

        except Exception as e:
            messagebox.showerror("Hata", f"Lütfen önce hesaplama yapın: {str(e)}")

    def _create_drilling_tab(self):
        """Create drilling calculations tab."""
        drilling_frame = ttk.Frame(self.calc_notebook, style="Calc.TFrame")
        self.calc_notebook.add(drilling_frame, text="Delme")

        # Header canvas (PNG if available)
        self._add_tab_header(drilling_frame, image_filename="drilling.png", fallback_text="Delme")

        # Add drilling calculations here
        ttk.Label(
            drilling_frame,
            text="Delme hesaplamaları yakında eklenecek...",
            font=("Arial", 10),
        ).pack(pady=20)

    def _assets_image_path(self, image_filename: str) -> Path:
        """Resolve an image under assets/images/ relative to repository root."""
        return Path(__file__).resolve().parent / "assets" / "images" / image_filename

    def _add_tab_header(self, parent: ttk.Widget, image_filename: str, fallback_text: str) -> None:
        """Add a top header canvas with a symbolic PNG image (or fallback text)."""
        header_frame = ttk.Frame(parent, style="Calc.TFrame")
        header_frame.pack(fill="x", padx=5, pady=(5, 0))

        canvas = tk.Canvas(header_frame, height=120, highlightthickness=0, bg="white")
        canvas.pack(fill="x", expand=False)

        image_path = self._assets_image_path(image_filename)
        if image_path.exists():
            try:
                photo = tk.PhotoImage(file=str(image_path))
                # Keep a reference to avoid GC
                self._header_images[str(image_path)] = photo

                # Center the image horizontally
                canvas.update_idletasks()
                canvas_width = max(canvas.winfo_width(), 1)
                img_width = photo.width() if photo.width() > 0 else 1
                x = max((canvas_width - img_width) // 2, 0)
                canvas.create_image(x, 0, anchor="nw", image=photo)
                return
            except tk.TclError:
                # Unsupported/invalid image; fall back to text
                pass

        # Fallback: simple symbolic banner
        canvas.create_rectangle(0, 0, 5000, 120, fill="#f5f7fb", outline="")
        canvas.create_text(
            20,
            60,
            anchor="w",
            text=f"{fallback_text} (görsel bulunamadı)",
            fill="#2c3e50",
            font=("Arial", 14, "bold"),
        )

    def _init_dynamic_calc_ui(
        self,
        parent: ttk.Widget,
        calc_category_key: str,
        calc_type_display: str,
        state_key: str,
    ) -> None:
        """Create a dropdown-driven dynamic calculation form."""
        container = ttk.Frame(parent, style="Calc.TFrame")
        container.pack(fill="both", expand=True, padx=5, pady=5)

        # Method selector
        selector_frame = ttk.LabelFrame(container, text="Hesap Türü", style="Calc.TFrame")
        selector_frame.pack(fill="x", padx=5, pady=5)

        ttk.Label(selector_frame, text="Seçim:", width=10).pack(side="left", padx=(5, 0), pady=5)

        available = ec.get_available_calculations().get(calc_category_key, [])
        method_var = tk.StringVar(value=available[0] if available else "")

        method_combo = ttk.Combobox(
            selector_frame,
            textvariable=method_var,
            values=available,
            state="readonly" if available else "disabled",
            style="Calc.TCombobox",
        )
        method_combo.pack(side="left", fill="x", expand=True, padx=5, pady=5)

        # Params
        params_frame = ttk.LabelFrame(container, text="Parametreler", style="Calc.TFrame")
        params_frame.pack(fill="x", padx=5, pady=5)

        # Actions + result
        actions_frame = ttk.Frame(container, style="Calc.TFrame")
        actions_frame.pack(fill="x", padx=5, pady=(5, 0))

        result_label = ttk.Label(actions_frame, text="", font=("Arial", 10, "bold"), foreground="blue")
        result_label.pack(side="right", padx=5)

        ttk.Button(actions_frame, text="Hesapla", command=lambda: self._dynamic_calc_calculate(state_key)).pack(
            side="left", padx=(0, 5)
        )
        ttk.Button(
            actions_frame,
            text="📝 Çalışma Alanına Ekle",
            command=lambda: self._dynamic_calc_inject(state_key),
        ).pack(side="left")

        self._dynamic_calc_state[state_key] = {
            "category": calc_category_key,
            "type_display": calc_type_display,
            "method_var": method_var,
            "method_combo": method_combo,
            "params_frame": params_frame,
            "param_entries": {},
            "result_label": result_label,
            "last_result": None,
        }

        method_combo.bind("<<ComboboxSelected>>", lambda _e: self._dynamic_calc_rebuild_params(state_key))
        self._dynamic_calc_rebuild_params(state_key)

    def _dynamic_calc_rebuild_params(self, state_key: str) -> None:
        """Rebuild parameter entry widgets based on current dropdown selection."""
        state = self._dynamic_calc_state.get(state_key)
        if not state:
            return

        params_frame: ttk.Frame = state["params_frame"]
        for widget in params_frame.winfo_children():
            widget.destroy()

        state["param_entries"] = {}
        state["last_result"] = None
        state["result_label"].config(text="")

        method_key = state["method_var"].get()
        if not method_key:
            ttk.Label(params_frame, text="Hesap türü bulunamadı.", foreground="red").pack(padx=10, pady=10)
            return

        try:
            param_details = ec.get_calculation_params(state["category"], method_key)
        except Exception as exc:
            ttk.Label(params_frame, text=f"Parametreler yüklenemedi: {exc}", foreground="red").pack(
                padx=10, pady=10
            )
            return

        if not param_details:
            ttk.Label(params_frame, text="Bu hesap için parametre yok.").pack(padx=10, pady=10)
            return

        for p in param_details:
            row = ttk.Frame(params_frame, style="Calc.TFrame")
            row.pack(fill="x", pady=2, padx=5)

            label_text = p.get("display_text_turkish") or p["name"]
            ttk.Label(row, text=f"{label_text}:", width=22).pack(side="left")

            entry = ttk.Entry(row, width=15)
            entry.pack(side="left", padx=(5, 0))

            unit = p.get("unit", "")
            if unit:
                ttk.Label(row, text=unit).pack(side="left", padx=(5, 0))

            state["param_entries"][p["name"]] = entry

    def _dynamic_calc_calculate(self, state_key: str) -> None:
        """Calculate the selected dynamic calculation using core parameter metadata."""
        state = self._dynamic_calc_state.get(state_key)
        if not state:
            return

        method_key = state["method_var"].get()
        if not method_key:
            messagebox.showerror("Hata", "Lütfen bir hesap türü seçin.")
            return

        try:
            param_details = ec.get_calculation_params(state["category"], method_key)
            args: List[float] = []
            params_dict: Dict[str, float] = {}

            for p in param_details:
                name = p["name"]
                entry = state["param_entries"].get(name)
                if entry is None:
                    raise ValueError(f"Eksik parametre alanı: {name}")

                val_str = entry.get().strip()
                if val_str == "":
                    raise ValueError(f"{name} için değer girin")

                val = float(val_str)
                args.append(val)
                params_dict[name] = val

            if state["category"] == "turning":
                result_dict = ec.calculate_turning(method_key, *args)
            elif state["category"] == "milling":
                result_dict = ec.calculate_milling(method_key, *args)
            else:
                raise ValueError(f"Desteklenmeyen kategori: {state['category']}")

            value = float(result_dict["value"])
            unit = str(result_dict.get("units", ""))
            state["last_result"] = {"value": value, "unit": unit, "params": params_dict, "method": method_key}

            unit_text = f" {unit}" if unit else ""
            state["result_label"].config(text=f"Sonuç: {value:.4g}{unit_text}")

        except ValueError as exc:
            messagebox.showerror("Hata", f"Lütfen geçerli sayısal değerler girin: {exc}")
        except Exception as exc:
            messagebox.showerror("Hata", f"Hesaplama hatası: {exc}")

    def _dynamic_calc_inject(self, state_key: str) -> None:
        """Inject the last dynamic calculation result into the workspace."""
        state = self._dynamic_calc_state.get(state_key)
        if not state:
            return

        if not state.get("last_result"):
            messagebox.showerror("Hata", "Lütfen önce hesaplama yapın.")
            return

        last = state["last_result"]
        self.workspace_editor.insert_calculation_result(
            state["type_display"],
            last["method"],
            last["params"],
            last["value"],
            last["unit"],
        )

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

        # Get Turkish shape name and convert to internal key
        shape_turkish = self.mass_shape.get()
        shape_key = self.reverse_shape_names.get(shape_turkish)

        if not shape_key:
            # Show error message in the parameters frame
            error_frame = ttk.Frame(self.mass_params_frame, style="Calc.TFrame")
            error_frame.pack(fill="x", pady=1)

            error_label = ttk.Label(
                error_frame,
                text=f"Hata: {shape_turkish} şekli desteklenmiyor",
                foreground="red",
                font=("Arial", 9),
            )
            error_label.pack(side="left")
            self.mass_param_widgets = {}
            return

        try:
            param_names = ec.get_shape_parameters(shape_key)
        except ValueError as e:
            # Show error message in the parameters frame
            error_frame = ttk.Frame(self.mass_params_frame, style="Calc.TFrame")
            error_frame.pack(fill="x", pady=1)

            error_label = ttk.Label(
                error_frame,
                text=f"Hata: {shape_turkish} şekli desteklenmiyor",
                foreground="red",
                font=("Arial", 9),
            )
            error_label.pack(side="left")
            self.mass_param_widgets = {}
            return

        self.mass_param_widgets = {}
        self.current_shape_key = shape_key  # Store for calculation

        for param_name in param_names:
            frame = ttk.Frame(self.mass_params_frame, style="Calc.TFrame")
            frame.pack(fill="x", pady=1)

            # Use cached Turkish display names
            display_name = self.param_to_gui_key_map.get(
                param_name,
                ec.PARAM_TURKISH_NAMES.get(param_name, param_name.capitalize()),
            )
            label_text = f"{display_name}:"
            ttk.Label(frame, text=label_text, width=15).pack(side="left")

            entry = ttk.Entry(frame, width=15)
            entry.pack(side="left", padx=(5, 0))

            self.mass_param_widgets[param_name] = entry

        # Add length parameter for all shapes except sphere
        if shape_key != "sphere":
            length_frame = ttk.Frame(self.mass_params_frame, style="Calc.TFrame")
            length_frame.pack(fill="x", pady=1)
            ttk.Label(length_frame, text="Uzunluk:", width=15).pack(side="left")
            length_entry = ttk.Entry(length_frame, width=15)
            length_entry.pack(side="left", padx=(5, 0))
            self.mass_param_widgets["length"] = length_entry

        # Force update after all parameter widgets are created
        self.mass_params_frame.update_idletasks()

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
            shape_key = self.current_shape_key
            density = float(self.mass_density.get())

            # Get shape parameters in correct order
            param_names = ec.get_shape_parameters(shape_key)
            param_values = []

            # Add shape parameters
            for param_name in param_names:
                if param_name in self.mass_param_widgets:
                    param_values.append(
                        float(self.mass_param_widgets[param_name].get())
                    )
                else:
                    raise ValueError(f"Parameter {param_name} not found")

            # Add length parameter for all shapes except sphere
            if shape_key != "sphere" and "length" in self.mass_param_widgets:
                param_values.append(float(self.mass_param_widgets["length"].get()))

            # Calculate mass using correct API
            result = ec.calculate_material_mass(shape_key, density, *param_values)

            self.mass_result.config(text=f"Sonuç: {result:.2f} g")

        except ValueError as e:
            messagebox.showerror(
                "Hata", f"Lütfen geçerli sayısal değerler girin: {str(e)}"
            )
        except Exception as e:
            messagebox.showerror("Hata", f"Hesaplama hatası: {str(e)}")

    def _inject_cutting_speed(self):
        """Inject cutting speed calculation into workspace."""
        try:
            # Check if calculation has been performed
            if not hasattr(self, "vc_result") or not self.vc_result.cget("text"):
                messagebox.showerror("Hata", "Lütfen önce hesaplama yapın.")
                return

            # Get calculation result
            result_text = self.vc_result.cget("text")
            if not result_text or "Sonuç:" not in result_text:
                messagebox.showerror("Hata", "Lütfen önce hesaplama yapın.")
                return

            # Extract result value
            try:
                result_value = float(result_text.split(":")[1].strip().split()[0])
            except (IndexError, ValueError):
                messagebox.showerror("Hata", "Lütfen önce hesaplama yapın.")
                return

            diameter = float(self.vc_diameter.get())
            rpm = float(self.vc_rpm.get())

            self.workspace_editor.insert_calculation_result(
                "Tornalama Hesaplamaları",
                "Kesme Hızı",
                {"Dm": diameter, "n": rpm},
                result_value,
                "m/dak",
            )

        except Exception as e:
            messagebox.showerror("Hata", f"Lütfen önce hesaplama yapın: {str(e)}")

    def _inject_spindle_speed(self):
        """Inject spindle speed calculation into workspace."""
        try:
            # Check if calculation has been performed
            if not hasattr(self, "n_result") or not self.n_result.cget("text"):
                messagebox.showerror("Hata", "Lütfen önce hesaplama yapın.")
                return

            # Get calculation result
            result_text = self.n_result.cget("text")
            if not result_text or "Sonuç:" not in result_text:
                messagebox.showerror("Hata", "Lütfen önce hesaplama yapın.")
                return

            # Extract result value
            try:
                result_value = float(result_text.split(":")[1].strip().split()[0])
            except (IndexError, ValueError):
                messagebox.showerror("Hata", "Lütfen önce hesaplama yapın.")
                return

            cutting_speed = float(self.n_cutting_speed.get())
            diameter = float(self.n_diameter.get())

            self.workspace_editor.insert_calculation_result(
                "Tornalama Hesaplamaları",
                "İş Mili Hızı",
                {"Vc": cutting_speed, "Dm": diameter},
                result_value,
                "rpm",
            )

        except Exception as e:
            messagebox.showerror("Hata", f"Lütfen önce hesaplama yapın: {str(e)}")

    def _inject_feed_rate(self):
        """Inject feed rate calculation into workspace."""
        try:
            # Check if calculation has been performed
            if not hasattr(self, "feed_result") or not self.feed_result.cget("text"):
                messagebox.showerror("Hata", "Lütfen önce hesaplama yapın.")
                return

            # Get calculation result
            result_text = self.feed_result.cget("text")
            if not result_text or "Sonuç:" not in result_text:
                messagebox.showerror("Hata", "Lütfen önce hesaplama yapın.")
                return

            # Extract result value
            try:
                result_value = float(result_text.split(":")[1].strip().split()[0])
            except (IndexError, ValueError):
                messagebox.showerror("Hata", "Lütfen önce hesaplama yapın.")
                return

            feed_per_tooth = float(self.feed_per_tooth.get())
            num_teeth = float(self.num_teeth.get())
            rpm = float(self.feed_rpm.get())

            self.workspace_editor.insert_calculation_result(
                "Frezeleme Hesaplamaları",
                "Besleme Oranı",
                {"fz": feed_per_tooth, "z": num_teeth, "n": rpm},
                result_value,
                "mm/dak",
            )

        except Exception as e:
            messagebox.showerror("Hata", f"Lütfen önce hesaplama yapın: {str(e)}")

    def _inject_mass(self):
        """Inject mass calculation into workspace."""
        try:
            # Check if calculation has been performed by checking if result exists
            if not hasattr(self, "mass_result") or not self.mass_result.cget("text"):
                messagebox.showerror("Hata", "Lütfen önce hesaplama yapın.")
                return

            # Get calculation result
            result_text = self.mass_result.cget("text")
            if not result_text or "Sonuç:" not in result_text:
                messagebox.showerror("Hata", "Lütfen önce hesaplama yapın.")
                return

            # Extract result value
            try:
                result_value = float(result_text.split(":")[1].strip().split()[0])
            except (IndexError, ValueError):
                messagebox.showerror("Hata", "Lütfen önce hesaplama yapın.")
                return

            shape = self.mass_shape.get()
            density = float(self.mass_density.get())

            # Get shape parameters
            params = {}
            for param_name, entry in self.mass_param_widgets.items():
                params[param_name] = float(entry.get())

            self.workspace_editor.insert_calculation_result(
                "Malzeme Hesaplamaları",
                "Kütle Hesabı",
                {"shape": shape, "density": density, **params},
                result_value,
                "g",
            )

        except Exception as e:
            messagebox.showerror("Hata", f"Lütfen önce hesaplama yapın: {str(e)}")

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
                timeout=120,
            )

            # Add as suggestion to workspace
            current_content = self.workspace_editor.get_current_content()
            suggestion = self.workspace_buffer.suggest_edit(
                0, len(current_content), str(response)
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
                self.current_model_url, self.current_model_name, context, timeout=120
            )

            messagebox.showinfo("Çalışma Alanı Analizi", str(response))
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
            self.current_model_url = model_url
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

    def _handle_tab_navigation(self, event):
        """Handle Tab key navigation between widgets."""
        try:
            # Get current focused widget
            current = self.root.focus_get()
            if current is None:
                return event

            # Get all focusable widgets
            focusable_widgets = self._get_focusable_widgets()

            if current in focusable_widgets:
                current_index = focusable_widgets.index(current)
                next_index = (current_index + 1) % len(focusable_widgets)
                next_widget = focusable_widgets[next_index]
                next_widget.focus_set()
                return "break"  # Prevent default Tab behavior
        except Exception:
            pass

        return event

    def _handle_shift_tab_navigation(self, event):
        """Handle Shift+Tab key navigation between widgets."""
        try:
            # Get current focused widget
            current = self.root.focus_get()
            if current is None:
                return event

            # Get all focusable widgets
            focusable_widgets = self._get_focusable_widgets()

            if current in focusable_widgets:
                current_index = focusable_widgets.index(current)
                prev_index = (current_index - 1) % len(focusable_widgets)
                prev_widget = focusable_widgets[prev_index]
                prev_widget.focus_set()
                return "break"  # Prevent default Tab behavior
        except Exception:
            pass

        return event

    def _get_focusable_widgets(self):
        """Get list of focusable widgets in order."""
        widgets = []

        # Add input fields from calculation tools
        if hasattr(self, "vc_diameter"):
            widgets.extend([self.vc_diameter, self.vc_rpm])
        if hasattr(self, "n_cutting_speed"):
            widgets.extend([self.n_cutting_speed, self.n_diameter])
        if hasattr(self, "feed_per_tooth"):
            widgets.extend([self.feed_per_tooth, self.num_teeth, self.feed_rpm])

        # Add milling input fields
        if hasattr(self, "milling_feed_per_tooth"):
            widgets.extend(
                [self.milling_feed_per_tooth, self.milling_num_teeth, self.milling_rpm]
            )
        if hasattr(self, "milling_cutting_diameter"):
            widgets.extend([self.milling_cutting_diameter, self.milling_cutting_rpm])
        if hasattr(self, "milling_spindle_cutting_speed"):
            widgets.extend(
                [self.milling_spindle_cutting_speed, self.milling_spindle_diameter]
            )

        # Add material input fields
        if hasattr(self, "mass_shape"):
            widgets.append(self.mass_shape)
        if hasattr(self, "mass_density"):
            widgets.append(self.mass_density)
        if hasattr(self, "mass_material"):
            widgets.append(self.mass_material)

        # Add dynamic material parameter fields
        if hasattr(self, "mass_param_widgets"):
            widgets.extend(list(self.mass_param_widgets.values()))

        # Add model configuration fields
        if hasattr(self, "model_url_entry"):
            widgets.append(self.model_url_entry)
        if hasattr(self, "model_selection_combo"):
            widgets.append(self.model_selection_combo)

        # Add workspace editor text widget
        if hasattr(self, "workspace_editor") and hasattr(
            self.workspace_editor, "text_widget"
        ):
            widgets.append(self.workspace_editor.text_editor)

        return widgets

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
    try:
        root = tk.Tk()

        # Load tooltips
        try:
            repo_root = Path(__file__).resolve().parent
            candidates = [
                repo_root / "assets" / "tooltips.json",
                repo_root / "tooltips.json",  # backward compatibility
            ]

            tooltips = {}
            for p in candidates:
                if p.exists():
                    with open(p, "r", encoding="utf-8") as f:
                        tooltips = json.load(f)
                    break
        except FileNotFoundError:
            tooltips = {}

        # Create V3 GUI instance
        app = V3Calculator(root, tooltips)

        # Start GUI
        root.mainloop()

    except Exception as e:
        print(f"V3 GUI başlatma hatası: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
