"""V3 GUI - Workspace Buffer Based Interface.

Bu modül Tkinter tabanlı V3 arayüzünü sağlar.
- Tornalama/Frezeleme: dropdown -> seçime göre dinamik parametre formu
- Her sekmenin üstünde PNG header (Pillow yok, tk.PhotoImage)
- Çalışma alanı: WorkspaceBuffer + WorkspaceEditor
"""

# -*- coding : utf-8 -*-
# Autor: Hakan KILIÇASLAN 2025
# flake8: noqa

from __future__ import annotations

import json
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox
from tkinter import ttk
from typing import Dict, List

from machining_formulas.assets import asset_path
from machining_formulas.core.engineering_calculator import EngineeringCalculator
from machining_formulas.gui.execute_mode import ExecuteModeMixin
from machining_formulas.llm.ollama_utils_v2 import (
    get_available_models,
    single_chat_request,
    test_connection,
)
from machining_formulas.workspace.workspace_buffer import WorkspaceBuffer
from machining_formulas.workspace.workspace_editor import WorkspaceEditor


DEFAULT_WINDOW_SIZE: tuple[int, int] = (1400, 900)
SUPPORTED_PROMPT_ATTACHMENT_EXTENSIONS: set[str] = {".txt", ".md", ".py", ".c", ".cpp"}

# Global instance
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
        except Exception:
            pass

        self.root.after(100, self._setup_navigation_bindings)
        self.root.after(1000, self._setup_focus_management)

    def _setup_navigation_bindings(self):
        """Setup navigation bindings after widgets are created."""
        try:
            self.root.bind("<Tab>", self._handle_tab_navigation)
            self.root.bind("<Shift-Tab>", self._handle_shift_tab_navigation)
            self.root.bind("<Button-1>", self._handle_root_click)
        except Exception:
            pass

    def _setup_focus_management(self):
        """Setup focus management for better keyboard/mouse interaction."""
        try:
            self.root.focus_set()
            for widget in self.root.winfo_children():
                self._enable_widget_focus(widget)
            self.root.after(200, self._set_initial_focus)
        except Exception:
            pass

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
            widget = event.widget
            if widget and widget != self.root:
                widget.focus_set()
        except Exception:
            pass

    def _enable_widget_focus(self, widget):
        """Recursively enable focus for all widgets."""
        try:
            if isinstance(widget, (tk.Entry, tk.Text)):
                widget.config(takefocus=1)
                widget.bind("<Button-1>", lambda e, w=widget: w.focus_set())
                widget.bind("<FocusIn>", lambda e: None)
            elif isinstance(widget, (ttk.Entry, ttk.Combobox)):
                widget.configure(takefocus=True)
                widget.bind("<Button-1>", lambda e, w=widget: w.focus_set())
                widget.bind("<FocusIn>", lambda e: None)
            elif isinstance(widget, (ttk.Button, tk.Button)):
                widget.configure(takefocus=True)
                widget.bind("<Button-1>", lambda e, w=widget: w.focus_set())

            for child in widget.winfo_children():
                self._enable_widget_focus(child)
        except Exception:
            pass

    def _setup_styles(self):
        """Setup ttk styles."""
        style = ttk.Style()
        style.theme_use("clam")

        style.configure("Calc.TFrame", background="#f0f0f0")
        style.configure("Calc.TLabel", background="#f0f0f0", font=("Arial", 10))
        style.configure(
            "Header.TLabel", background="#f0f0f0", font=("Arial", 12, "bold")
        )
        style.configure("Calc.TButton", font=("Arial", 9))
        style.configure("Calc.TCombobox", fieldbackground="white", font=("Arial", 9))

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
        except Exception:
            pass

    def _create_main_layout(self):
        """Create main layout with paned windows."""
        main_container = ttk.Frame(self.root, style="Calc.TFrame")
        main_container.pack(fill="both", expand=True)

        self.paned_window = ttk.PanedWindow(main_container, orient="horizontal")
        self.paned_window.pack(fill="both", expand=True, padx=5, pady=5)

        self._create_calculation_panel()
        self._create_workspace_panel()

        self.paned_window.update_idletasks()

    def _create_calculation_panel(self):
        """Create calculation tools panel."""
        calc_frame = ttk.Frame(self.paned_window, style="Calc.TFrame")
        self.paned_window.add(calc_frame, weight=1)

        header_frame = ttk.Frame(calc_frame, style="Calc.TFrame")
        header_frame.pack(fill="x", padx=5, pady=5)

        ttk.Label(
            header_frame, text="🧮 HESAPLAMA ARAÇLARI", font=("Arial", 11, "bold")
        ).pack(side="left")

        model_frame = ttk.LabelFrame(
            calc_frame, text="🤖 Model Yapılandırması", style="Calc.TFrame"
        )
        model_frame.pack(fill="x", expand=True, padx=5, pady=5)

        url_frame = ttk.Frame(model_frame, style="Calc.TFrame")
        url_frame.pack(fill="x", padx=5, pady=2)

        ttk.Label(url_frame, text="URL:", width=8).pack(side="left")
        self.model_url_entry = ttk.Entry(url_frame, width=30)
        self.model_url_entry.pack(side="left", fill="x", expand=True, padx=(5, 0))
        self.model_url_entry.insert(0, self.current_model_url)

        ttk.Button(url_frame, text="🔄", command=self.refresh_model_list, width=3).pack(
            side="right", padx=(5, 0)
        )

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

        ttk.Separator(calc_frame, orient="horizontal").pack(fill="x", padx=5, pady=10)

        self._create_calculation_categories(calc_frame)

    def _create_calculation_categories(self, parent):
        """Create calculation categories and tools."""
        self.calc_notebook = ttk.Notebook(parent)
        self.calc_notebook.pack(fill="both", expand=True, padx=5, pady=5)

        self._create_turning_tab()
        self._create_milling_tab()
        self._create_material_tab()
        self._create_drilling_tab()

    def _create_turning_tab(self):
        """Create turning calculations tab."""
        turning_frame = ttk.Frame(self.calc_notebook, style="Calc.TFrame")
        self.calc_notebook.add(turning_frame, text="Tornalama")

        self._add_tab_header(
            turning_frame, image_filename="turning.png", fallback_text="Tornalama"
        )

        self._init_dynamic_calc_ui(
            parent=turning_frame,
            calc_category_key="turning",
            calc_type_display="Tornalama Hesaplamaları",
            state_key="turning",
        )

    def _create_milling_tab(self):
        """Create milling calculations tab."""
        milling_frame = ttk.Frame(self.calc_notebook, style="Calc.TFrame")
        self.calc_notebook.add(milling_frame, text="Frezeleme")

        self._add_tab_header(
            milling_frame, image_filename="milling.png", fallback_text="Frezeleme"
        )

        self._init_dynamic_calc_ui(
            parent=milling_frame,
            calc_category_key="milling",
            calc_type_display="Frezeleme Hesaplamaları",
            state_key="milling",
        )

    def _create_material_tab(self):
        """Create material calculations tab."""
        material_frame = ttk.Frame(self.calc_notebook, style="Calc.TFrame")
        self.calc_notebook.add(material_frame, text="Malzeme")

        self._add_tab_header(
            material_frame, image_filename="material.png", fallback_text="Malzeme"
        )

        self._create_mass_calc(material_frame)

    def _create_mass_calc(self, parent):
        """Create mass calculation."""
        frame = ttk.LabelFrame(parent, text="Kütle Hesabı", style="Calc.TFrame")
        frame.pack(fill="x", expand=True, padx=5, pady=5)

        shape_display_names = list(self.available_shapes_map.values())

        shape_frame = ttk.Frame(frame, style="Calc.TFrame")
        shape_frame.pack(fill="x", padx=5, pady=2)
        ttk.Label(shape_frame, text="Şekil:", width=15).pack(side="left")
        self.mass_shape = ttk.Combobox(shape_frame, width=20, style="Calc.TCombobox")
        self.mass_shape.pack(side="left", padx=(5, 0))
        self.mass_shape["values"] = shape_display_names
        if shape_display_names:
            self.mass_shape.set(shape_display_names[0])
        self.mass_shape.bind("<<ComboboxSelected>>", self._update_mass_params)

        self.mass_params_frame = ttk.Frame(frame, style="Calc.TFrame")
        self.mass_params_frame.pack(fill="x", expand=True, padx=5, pady=5)

        density_frame = ttk.Frame(frame, style="Calc.TFrame")
        density_frame.pack(fill="x", padx=5, pady=2)

        ttk.Label(density_frame, text="Yoğunluk:", width=15).pack(side="left")
        self.mass_density = ttk.Entry(density_frame, width=15)
        self.mass_density.pack(side="left", padx=(5, 0))
        ttk.Label(density_frame, text="g/cm³").pack(side="left", padx=(2, 0))

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

        self._update_mass_params()

        ttk.Button(frame, text="Hesapla", command=self._calculate_mass).pack(pady=5)

        self.mass_result = ttk.Label(
            frame, text="", font=("Arial", 10, "bold"), foreground="blue"
        )
        self.mass_result.pack(pady=2)

        ttk.Button(frame, text="📝 Çalışma Alanına Ekle", command=self._inject_mass).pack(
            pady=2
        )

    def _create_drilling_tab(self):
        """Create drilling calculations tab."""
        drilling_frame = ttk.Frame(self.calc_notebook, style="Calc.TFrame")
        self.calc_notebook.add(drilling_frame, text="Delme")

        self._add_tab_header(
            drilling_frame, image_filename="drilling.png", fallback_text="Delme"
        )

        ttk.Label(
            drilling_frame,
            text="Delme hesaplamaları yakında eklenecek...",
            font=("Arial", 10),
        ).pack(pady=20)

    def _assets_image_path(self, image_filename: str) -> Path:
        """Resolve an image under assets/images/ relative to repository root."""
        return asset_path(f"images/{image_filename}")

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
                self._header_images[str(image_path)] = photo

                canvas.update_idletasks()
                canvas_width = max(canvas.winfo_width(), 1)
                img_width = photo.width() if photo.width() > 0 else 1
                x = max((canvas_width - img_width) // 2, 0)
                canvas.create_image(x, 0, anchor="nw", image=photo)
                return
            except tk.TclError:
                pass

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

        params_frame = ttk.LabelFrame(container, text="Parametreler", style="Calc.TFrame")
        params_frame.pack(fill="x", padx=5, pady=5)

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

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Dosya", menu=file_menu)
        file_menu.add_command(label="Yeni Çalışma Alanı", command=self._new_workspace)
        file_menu.add_command(label="Aç...", command=self._open_workspace)
        file_menu.add_command(label="Kaydet...", command=self._save_workspace)
        file_menu.add_separator()
        file_menu.add_command(label="Dışa Aktar...", command=self._export_workspace)
        file_menu.add_separator()
        file_menu.add_command(label="Çıkış", command=self.root.quit)

        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Düzenle", menu=edit_menu)
        edit_menu.add_command(label="Geri Al", command=self.workspace_editor._undo)
        edit_menu.add_command(label="İleri Al", command=self.workspace_editor._redo)
        edit_menu.add_separator()
        edit_menu.add_command(label="Temizle", command=self.workspace_editor._clear_workspace)

        model_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Model", menu=model_menu)
        model_menu.add_command(label="Bağlantı Testi", command=self.test_model_connection)
        model_menu.add_command(label="Modelleri Yenile", command=self.refresh_model_list)
        model_menu.add_separator()
        model_menu.add_command(label="Çalışma Alanını Analiz Et", command=self._analyze_workspace)

    def _create_status_bar(self):
        """Create status bar."""
        self.status_frame = ttk.Frame(self.root, style="Calc.TFrame")
        self.status_frame.pack(fill="x", side="bottom")

        self.status_var = tk.StringVar()
        self.status_var.set("Hazır")

        status_label = ttk.Label(self.status_frame, textvariable=self.status_var, relief="sunken")
        status_label.pack(fill="x", padx=2, pady=2)

    def _update_mass_params(self, event=None):
        """Update mass calculation parameters based on shape."""
        for widget in self.mass_params_frame.winfo_children():
            widget.destroy()

        shape_turkish = self.mass_shape.get()
        shape_key = self.reverse_shape_names.get(shape_turkish)

        if not shape_key:
            error_frame = ttk.Frame(self.mass_params_frame, style="Calc.TFrame")
            error_frame.pack(fill="x", pady=1)
            ttk.Label(
                error_frame,
                text=f"Hata: {shape_turkish} şekli desteklenmiyor",
                foreground="red",
                font=("Arial", 9),
            ).pack(side="left")
            self.mass_param_widgets = {}
            return

        try:
            param_names = ec.get_shape_parameters(shape_key)
        except ValueError:
            error_frame = ttk.Frame(self.mass_params_frame, style="Calc.TFrame")
            error_frame.pack(fill="x", pady=1)
            ttk.Label(
                error_frame,
                text=f"Hata: {shape_turkish} şekli desteklenmiyor",
                foreground="red",
                font=("Arial", 9),
            ).pack(side="left")
            self.mass_param_widgets = {}
            return

        self.mass_param_widgets = {}
        self.current_shape_key = shape_key

        for param_name in param_names:
            frame = ttk.Frame(self.mass_params_frame, style="Calc.TFrame")
            frame.pack(fill="x", pady=1)

            display_name = self.param_to_gui_key_map.get(
                param_name,
                ec.PARAM_TURKISH_NAMES.get(param_name, param_name.capitalize()),
            )
            ttk.Label(frame, text=f"{display_name}:", width=15).pack(side="left")

            entry = ttk.Entry(frame, width=15)
            entry.pack(side="left", padx=(5, 0))

            self.mass_param_widgets[param_name] = entry

        if shape_key != "sphere":
            length_frame = ttk.Frame(self.mass_params_frame, style="Calc.TFrame")
            length_frame.pack(fill="x", pady=1)
            ttk.Label(length_frame, text="Uzunluk:", width=15).pack(side="left")
            length_entry = ttk.Entry(length_frame, width=15)
            length_entry.pack(side="left", padx=(5, 0))
            self.mass_param_widgets["length"] = length_entry

        self.mass_params_frame.update_idletasks()

    def _calculate_mass(self):
        """Calculate mass."""
        try:
            shape_key = self.current_shape_key
            density = float(self.mass_density.get())

            param_names = ec.get_shape_parameters(shape_key)
            param_values = []

            for param_name in param_names:
                if param_name in self.mass_param_widgets:
                    param_values.append(float(self.mass_param_widgets[param_name].get()))
                else:
                    raise ValueError(f"Parameter {param_name} not found")

            if shape_key != "sphere" and "length" in self.mass_param_widgets:
                param_values.append(float(self.mass_param_widgets["length"].get()))

            result = ec.calculate_material_mass(shape_key, density, *param_values)
            self.mass_result.config(text=f"Sonuç: {result:.2f} g")

        except ValueError as e:
            messagebox.showerror("Hata", f"Lütfen geçerli sayısal değerler girin: {str(e)}")
        except Exception as e:
            messagebox.showerror("Hata", f"Hesaplama hatası: {str(e)}")

    def _inject_mass(self):
        """Inject mass calculation into workspace."""
        try:
            if not hasattr(self, "mass_result") or not self.mass_result.cget("text"):
                messagebox.showerror("Hata", "Lütfen önce hesaplama yapın.")
                return

            result_text = self.mass_result.cget("text")
            if not result_text or "Sonuç:" not in result_text:
                messagebox.showerror("Hata", "Lütfen önce hesaplama yapın.")
                return

            try:
                result_value = float(result_text.split(":")[1].strip().split()[0])
            except (IndexError, ValueError):
                messagebox.showerror("Hata", "Lütfen önce hesaplama yapın.")
                return

            shape = self.mass_shape.get()
            density = float(self.mass_density.get())

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
            messagebox.showwarning("Uyarı", "Lütfen önce model URL'sini ve model seçin.")
            return

        try:
            self.update_status_bar("Model önerisi isteniyor...")

            response = single_chat_request(
                self.current_model_url,
                self.current_model_name,
                f"Bu metni düzenle veya iyileştir: {context}",
                timeout=120,
            )

            current_content = self.workspace_editor.get_current_content()
            self.workspace_buffer.suggest_edit(0, len(current_content), str(response))

            self.workspace_editor._show_suggestions()
            self.update_status_bar("Model önerisi eklendi")

        except Exception as e:
            messagebox.showerror("Hata", f"Model önerisi alınamadı: {str(e)}")
            self.update_status_bar("Model önerisi başarısız")

    def _analyze_workspace(self):
        """Analyze entire workspace with model."""
        if not self.current_model_name or not self.current_model_url:
            messagebox.showwarning("Uyarı", "Lütfen önce model URL'sini ve model seçin.")
            return

        try:
            self.update_status_bar("Çalışma alanı analiz ediliyor...")

            content = self.workspace_editor.get_current_content()
            context = f"Bu mühendislik çalışma alanını analiz et ve öneriler sun: {content}"

            response = single_chat_request(
                self.current_model_url,
                self.current_model_name,
                context,
                timeout=120,
            )

            messagebox.showinfo("Çalışma Alanı Analizi", str(response))
            self.update_status_bar("Analiz tamamlandı")

        except Exception as e:
            messagebox.showerror("Hata", f"Analiz sırasında hata: {str(e)}")
            self.update_status_bar("Analiz başarısız")

    def _on_workspace_change(self, content: str):
        """Handle workspace content change."""
        return

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
            filetypes=[("Text files", "*.txt"), ("Markdown files", "*.md"), ("All files", "*.*")],
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
                if not self.current_model_name or self.current_model_name not in self.ollama_models:
                    self.model_selection_combo.set(self.ollama_models[0])
                    self.current_model_name = self.ollama_models[0]
                else:
                    self.model_selection_combo.set(self.current_model_name)
            else:
                self.model_selection_combo.set("")
                self.current_model_name = ""

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

    def _handle_tab_navigation(self, event):
        """Handle Tab key navigation between widgets."""
        try:
            current = self.root.focus_get()
            if current is None:
                return event

            focusable_widgets = self._get_focusable_widgets()
            if current in focusable_widgets:
                current_index = focusable_widgets.index(current)
                next_index = (current_index + 1) % len(focusable_widgets)
                focusable_widgets[next_index].focus_set()
                return "break"
        except Exception:
            pass

        return event

    def _handle_shift_tab_navigation(self, event):
        """Handle Shift+Tab key navigation between widgets."""
        try:
            current = self.root.focus_get()
            if current is None:
                return event

            focusable_widgets = self._get_focusable_widgets()
            if current in focusable_widgets:
                current_index = focusable_widgets.index(current)
                prev_index = (current_index - 1) % len(focusable_widgets)
                focusable_widgets[prev_index].focus_set()
                return "break"
        except Exception:
            pass

        return event

    def _get_focusable_widgets(self):
        """Get list of focusable widgets in order."""
        widgets = []

        if hasattr(self, "mass_shape"):
            widgets.append(self.mass_shape)
        if hasattr(self, "mass_density"):
            widgets.append(self.mass_density)
        if hasattr(self, "mass_material"):
            widgets.append(self.mass_material)

        if hasattr(self, "mass_param_widgets"):
            widgets.extend(list(self.mass_param_widgets.values()))

        if hasattr(self, "model_url_entry"):
            widgets.append(self.model_url_entry)
        if hasattr(self, "model_selection_combo"):
            widgets.append(self.model_selection_combo)

        if hasattr(self, "workspace_editor") and hasattr(self.workspace_editor, "text_editor"):
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


def main() -> None:
    """Main entry point for V3 GUI."""
    try:
        root = tk.Tk()

        tooltips: Dict[str, str] = {}
        try:
            p = asset_path("tooltips.json")
            if p.exists():
                with open(p, "r", encoding="utf-8") as f:
                    tooltips = json.load(f)
        except Exception:
            tooltips = {}

        app = V3Calculator(root, tooltips)
        root.mainloop()

    except Exception as e:
        print(f"V3 GUI başlatma hatası: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
