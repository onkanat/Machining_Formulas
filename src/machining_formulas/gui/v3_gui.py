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
import re
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox
from tkinter import ttk
from typing import Any, Dict, List, Optional
from PIL import Image, ImageTk

from machining_formulas.assets import asset_path
from machining_formulas.core.engineering_calculator import EngineeringCalculator
from machining_formulas.gui.advanced_calculator import AdvancedCalculator
from machining_formulas.gui.execute_mode import ExecuteModeMixin
from machining_formulas.llm.ollama_utils import build_calculator_tools_definition, normalize_chat_url
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
        self.root.withdraw()  # macOS ve diger platformlarda baslangictaki kucuk/konumsuz pencereyi gizle
        self.tooltips = tooltips

        # Tool-calling assistant (LLM -> tools -> compute -> final answer)
        self._tool_assistant = AdvancedCalculator()

        # Keep references to PhotoImage instances
        self._header_images: Dict[str, tk.PhotoImage] = {}

        # State containers for dynamic calculation UIs (turning/milling)
        self._dynamic_calc_state: Dict[str, dict] = {}

        # Initialize workspace buffer
        self.workspace_buffer = WorkspaceBuffer()

        # Model configuration
        self.current_model_url = "http://localhost:11434"
        self.current_model_name = ""
        self.ollama_models: List[str] = []

        # Cache frequently used data for performance
        self._initialize_cached_data()

        # Setup UI
        self.setup_ui()

        # Force UI update before geometry calculations
        self.root.update_idletasks()
        self._apply_default_geometry()

        # Initialize model connection asynchronously to prevent startup UI freezing
        self.root.after(100, self.refresh_model_list)

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

        self.root.after(100, self._setup_navigation_bindings)
        self.root.after(150, self._setup_keyboard_shortcuts)
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
        model_frame.pack(fill="x", expand=False, padx=10, pady=10)

        url_frame = ttk.Frame(model_frame, style="Calc.TFrame")
        url_frame.pack(fill="x", padx=10, pady=6)

        ttk.Label(url_frame, text="URL:", width=8).pack(side="left")
        self.model_url_entry = ttk.Entry(url_frame, width=30)
        self.model_url_entry.pack(side="left", fill="x", expand=True, padx=(5, 0))
        self.model_url_entry.insert(0, self.current_model_url)

        ttk.Button(url_frame, text="🔄", command=self.refresh_model_list, width=3).pack(
            side="right", padx=(5, 0)
        )

        model_frame_inner = ttk.Frame(model_frame, style="Calc.TFrame")
        model_frame_inner.pack(fill="x", padx=10, pady=6)

        ttk.Label(model_frame_inner, text="Model:", width=8).pack(side="left")
        self.model_selection_combo = ttk.Combobox(
            model_frame_inner, width=25, style="Calc.TCombobox"
        )
        self.model_selection_combo.pack(side="left", fill="x", expand=True, padx=(5, 0))

        ttk.Button(
            model_frame_inner, text="🔗", command=self.test_model_connection, width=3
        ).pack(side="right", padx=(5, 0))

        ttk.Separator(calc_frame, orient="horizontal").pack(fill="x", padx=10, pady=10)

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
        self.mass_density.bind("<Return>", lambda _e: self._calculate_mass())
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

        self._init_dynamic_calc_ui(
            parent=drilling_frame,
            calc_category_key="drilling",
            calc_type_display="Delik Delme Hesaplamaları",
            state_key="drilling",
        )

    def _assets_image_path(self, image_filename: str) -> Path:
        """Resolve an image under assets/images/ relative to repository root."""
        return asset_path(f"images/{image_filename}")

    def _add_tab_header(self, parent: ttk.Widget, image_filename: str, fallback_text: str) -> None:
        """Add a top header canvas with a symbolic PNG image (or fallback text)."""
        header_frame = ttk.Frame(parent, style="Calc.TFrame")
        header_frame.pack(fill="x", padx=5, pady=(5, 0))

        canvas = tk.Canvas(header_frame, height=120, highlightthickness=0, bg="white", cursor="hand2")
        canvas.pack(fill="x", expand=False)

        image_path = self._assets_image_path(image_filename)
        if image_path.exists():
            try:
                pil_img = Image.open(image_path)
                # Resize image to fit height=120 while keeping aspect ratio
                h_size = 120
                w_percent = h_size / float(pil_img.size[1])
                w_size = int(float(pil_img.size[0]) * float(w_percent))
                pil_img_resized = pil_img.resize((w_size, h_size), Image.Resampling.LANCZOS)
                
                photo = ImageTk.PhotoImage(pil_img_resized)
                self._header_images[str(image_path)] = photo

                canvas.update_idletasks()
                canvas_width = max(canvas.winfo_width(), 1)
                x = max((canvas_width - w_size) // 2, 0)
                canvas.create_image(x, 0, anchor="nw", image=photo)

                # Kullaniciya fareyle uzerine gelindiginde buyuyecegini gosteren minik bilgi metni ekle
                canvas.create_rectangle(canvas_width - 150, 95, canvas_width - 5, 115, fill="#1a1a1a", outline="", stipple="gray50")
                canvas.create_text(
                    canvas_width - 77,
                    105,
                    text="🔍 Büyütmek için üzerine gelin",
                    fill="white",
                    font=("Arial", 8, "bold")
                )

                # Fare ile hover edildiginde acilacak yüksek kaliteli popup mantigi
                def on_enter(event):
                    # Eger halihazirda acik bir popup varsa temizle
                    if hasattr(self, "_active_hover_popup") and self._active_hover_popup:
                        try:
                            self._active_hover_popup.destroy()
                        except Exception:
                            pass
                    
                    try:
                        # Orijinal gorseli yukle ve maksimum 480x480 olacak sekilde en-boy oranini koruyarak olcekle
                        pil_img_large = Image.open(image_path)
                        max_size = 480
                        w_l, h_l = pil_img_large.size
                        ratio = min(max_size / w_l, max_size / h_l)
                        new_w = int(w_l * ratio)
                        new_h = int(h_l * ratio)
                        pil_img_large_resized = pil_img_large.resize((new_w, new_h), Image.Resampling.LANCZOS)
                        
                        photo_large = ImageTk.PhotoImage(pil_img_large_resized)
                        
                        # Sadece gorsel ve baslik barindiran çerçevesiz (borderless) premium pencere
                        popup = tk.Toplevel(self.root)
                        popup.overrideredirect(True)
                        popup.attributes("-topmost", True)
                        popup.config(bg="#1a1a1a", padx=4, pady=4)
                        
                        frame_inner = tk.Frame(popup, bg="#1a1a1a")
                        frame_inner.pack(fill="both", expand=True)
                        
                        lbl_img = tk.Label(frame_inner, image=photo_large, bg="#1a1a1a")
                        lbl_img.pack()
                        
                        lbl_text = tk.Label(
                            frame_inner, 
                            text="🔧 Referans Teknik Görsel (Büyük Boyut)", 
                            bg="#1a1a1a", 
                            fg="#00d2ff", 
                            font=("Arial", 10, "bold"),
                            pady=5
                        )
                        lbl_text.pack()
                        
                        # Ekranda cursor'in hemen sag altinda konumlandir (titremeyi onlemek icin 25px safe offset)
                        px = event.x_root + 25
                        py = event.y_root + 15
                        
                        # Ekran disina tasmayi engelle
                        screen_w = self.root.winfo_screenwidth()
                        screen_h = self.root.winfo_screenheight()
                        if px + new_w > screen_w:
                            px = event.x_root - new_w - 25
                        if py + new_h + 35 > screen_h:
                            py = event.y_root - new_h - 45
                        
                        popup.geometry(f"{new_w}x{new_h + 30}+{px}+{py}")
                        
                        self._active_hover_popup = popup
                        self._active_popup_photo = photo_large
                        
                    except Exception as ex:
                        print(f"Popup olusturma hatasi: {ex}")

                def on_leave(event):
                    if hasattr(self, "_active_hover_popup") and self._active_hover_popup:
                        try:
                            self._active_hover_popup.destroy()
                        except Exception:
                            pass
                        self._active_hover_popup = None
                        self._active_popup_photo = None

                canvas.bind("<Enter>", on_enter)
                canvas.bind("<Leave>", on_leave)
                # Garbage collection korumasi
                canvas.on_enter = on_enter
                canvas.on_leave = on_leave
                return
            except Exception as e:
                print(f"Error loading image {image_filename} with Pillow: {e}")

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
            entry.bind("<Return>", lambda _e, sk=state_key: self._dynamic_calc_calculate(sk))

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
            elif state["category"] == "drilling":
                result_dict = ec.calculate_drilling(method_key, *args)
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
        import sys
        is_mac = sys.platform == "darwin"
        mod_text = "Cmd+" if is_mac else "Ctrl+"

        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Dosya", menu=file_menu)
        file_menu.add_command(label="Yeni Çalışma Alanı", accelerator=f"{mod_text}N", command=self._new_workspace)
        file_menu.add_command(label="Aç...", accelerator=f"{mod_text}O", command=self._open_workspace)
        file_menu.add_command(label="Kaydet...", accelerator=f"{mod_text}S", command=self._save_workspace)
        file_menu.add_separator()
        file_menu.add_command(label="Dışa Aktar...", accelerator=f"{mod_text}E", command=self._export_workspace)
        file_menu.add_separator()
        file_menu.add_command(label="Çıkış", accelerator=f"{mod_text}Q", command=self.root.quit)

        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Düzenle", menu=edit_menu)
        edit_menu.add_command(label="Geri Al", accelerator=f"{mod_text}Z", command=self.workspace_editor._undo)
        edit_menu.add_command(label="İleri Al", accelerator=f"{mod_text}Shift+Z" if is_mac else f"{mod_text}Y", command=self.workspace_editor._redo)
        edit_menu.add_separator()
        edit_menu.add_command(label="Temizle", accelerator=f"{mod_text}L", command=self.workspace_editor._clear_workspace)

        model_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Model", menu=model_menu)
        model_menu.add_command(label="Bağlantı Testi", accelerator=f"{mod_text}Shift+T", command=self.test_model_connection)
        model_menu.add_command(label="Modelleri Yenile", accelerator=f"{mod_text}R", command=self.refresh_model_list)
        model_menu.add_separator()
        model_menu.add_command(label="Çalışma Alanını Analiz Et", accelerator=f"{mod_text}Shift+A", command=self._analyze_workspace)

    def _setup_keyboard_shortcuts(self):
        """Configure macOS-prioritized, cross-platform keyboard shortcuts for menus and tabs."""
        import sys
        is_mac = sys.platform == "darwin"

        def _bind(key, callback, is_shift=False):
            shift_str = "Shift-" if is_shift else ""

            # Control bindings
            self.root.bind_all(f"<Control-{shift_str}{key.lower()}>", lambda event: callback())
            if len(key) == 1 and key.isalpha():
                self.root.bind_all(f"<Control-{shift_str}{key.upper()}>", lambda event: callback())

            # Command bindings on macOS
            if is_mac:
                self.root.bind_all(f"<Command-{shift_str}{key.lower()}>", lambda event: callback())
                if len(key) == 1 and key.isalpha():
                    self.root.bind_all(f"<Command-{shift_str}{key.upper()}>", lambda event: callback())

        # File Operations
        _bind("n", self._new_workspace)
        _bind("o", self._open_workspace)
        _bind("s", self._save_workspace)
        _bind("e", self._export_workspace)
        _bind("q", lambda: self.root.quit())

        # Edit Operations
        _bind("z", self.workspace_editor._undo)
        _bind("y", self.workspace_editor._redo)
        _bind("z", self.workspace_editor._redo, is_shift=True)  # Cmd+Shift+Z for macOS
        _bind("l", self.workspace_editor._clear_workspace)

        # Model & AI Operations
        _bind("t", self.test_model_connection, is_shift=True)  # Cmd+Shift+T
        _bind("r", self.refresh_model_list)
        _bind("a", self._analyze_workspace, is_shift=True)  # Cmd+Shift+A

        # Tab Navigation
        _bind("1", lambda: self.calc_notebook.select(0))
        _bind("2", lambda: self.calc_notebook.select(1))
        _bind("3", lambda: self.calc_notebook.select(2))
        _bind("4", lambda: self.calc_notebook.select(3))

        # Help Shortcuts (F1, Cmd+Slash, Cmd+Shift+Slash)
        self.root.bind_all("<F1>", lambda event: self._show_shortcuts_help())
        self.root.bind_all("<Help>", lambda event: self._show_shortcuts_help())
        _bind("slash", self._show_shortcuts_help)
        _bind("question", self._show_shortcuts_help)

    def _show_shortcuts_help(self):
        """Display a comprehensive help dialog for keyboard shortcuts."""
        import sys
        mod = "Cmd" if sys.platform == "darwin" else "Ctrl"

        help_text = (
            "⌨️ Klavye Kısayolları (Keyboard Shortcuts)\n"
            "==========================================\n\n"
            "📂 Dosya İşlemleri:\n"
            f"  • {mod}+N : Yeni Çalışma Alanı\n"
            f"  • {mod}+O : Aç...\n"
            f"  • {mod}+S : Kaydet...\n"
            f"  • {mod}+E : Dışa Aktar...\n"
            f"  • {mod}+Q : Çıkış\n\n"
            "📝 Düzenleme ve Düzenleyici:\n"
            f"  • {mod}+Z : Geri Al\n"
            f"  • {mod}+Y veya {mod}+Shift+Z : İleri Al\n"
            f"  • {mod}+L : Çalışma Alanını Temizle\n\n"
            "🤖 Yapay Zeka ve Model İşlemleri:\n"
            f"  • {mod}+Shift+A : Çalışma Alanını Analiz Et\n"
            f"  • {mod}+Shift+T : Model Bağlantı Testi\n"
            f"  • {mod}+R : Modelleri Yenile\n\n"
            "🗂️ Hesaplama Sekmeleri Arasında Geçiş:\n"
            f"  • {mod}+1 : Tornalama Sekmesi\n"
            f"  • {mod}+2 : Frezeleme Sekmesi\n"
            f"  • {mod}+3 : Malzeme Sekmesi\n"
            f"  • {mod}+4 : Delme Sekmesi\n\n"
            "⚡ Diğer Kolaylıklar:\n"
            "  • Enter (Giriş) : Sayısal parametre alanlarında doğrudan Hesapla tetikler\n"
            "  • Esc : Çıkan diyalog veya popup pencereleri kapatır\n"
            "  • F1 veya Cmd+/ : Bu kısayol yardım menüsünü açar\n"
        )
        messagebox.showinfo("Klavye Kısayolları", help_text)

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
            entry.bind("<Return>", lambda _e: self._calculate_mass())

            self.mass_param_widgets[param_name] = entry

        if shape_key != "sphere":
            length_frame = ttk.Frame(self.mass_params_frame, style="Calc.TFrame")
            length_frame.pack(fill="x", pady=1)
            ttk.Label(length_frame, text="Uzunluk:", width=15).pack(side="left")
            length_entry = ttk.Entry(length_frame, width=15)
            length_entry.pack(side="left", padx=(5, 0))
            length_entry.bind("<Return>", lambda _e: self._calculate_mass())
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

        # Eğer metin bir hesap sorusu gibi görünüyorsa: tools ile yanıtla
        if self._should_use_tools_for_text(context):
            try:
                self.update_status_bar("Hesaplama (tool) yanıtı hazırlanıyor...")

                if not hasattr(self, "_tool_assistant") or self._tool_assistant is None:
                    self._tool_assistant = AdvancedCalculator()

                chat_url = normalize_chat_url(self.current_model_url)
                tools_def = build_calculator_tools_definition(ec)

                system_prompt = (
                    "Sen uzman bir talaşlı imalat hesap asistanısın. "
                    "DİKKAT: Sayısal hesap veya kütle/hacim hesabı gereken durumlarda KESİNLİKLE araçları (tools) kullanmalısın! "
                    "Eğer sayısal veri varsa hesaplamayı sen YAPMA, sadece aracı çağır. Kendi kendine sayısal tahmin veya yuvarlama yapma, araçtan dönen hassas değerleri referans al.\n\n"
                    "Yanıtını her zaman son derece profesyonel, temiz bir mühendislik raporu formatında sun. "
                    "Eğer bir hesaplama yapıldıysa, aşağıdaki şablonu tam olarak kullanarak raporla:\n\n"
                    "📊 MÜHENDİSLİK HESAPLAMA RAPORU\n"
                    "==================================\n"
                    "- **İşlem Türü**: [Buraya hesaplama türünü yazın, örn: Malzeme Kütle Hesabı]\n"
                    "- **Kullanılan Parametreler**:\n"
                    "  * [Parametre 1]: [Değer] [Birim]\n"
                    "  * [Parametre 2]: [Değer] [Birim]\n"
                    "- **Hesaplanan Hassas Değer**: [Araçtan gelen tam sayısal sonuç] [Birim]\n"
                    "- **Mühendislik Analizi**: [Hesaplama sonucunun kısa, teknik ve net bir açıklaması]\n"
                    "=================================="
                )

                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": context},
                ]

                assistant_msg, _updated = self._tool_assistant.chat_with_tools(
                    chat_url,
                    self.current_model_name,
                    messages,
                    tools_def,
                    timeout=60,
                )

                answer = str(assistant_msg.get("content", "")).strip() or "(boş yanıt)"

                # Bazı modeller tools varken bile doğrudan (ve bazen yanlış birimle) yanıt verebiliyor.
                # Bu durumda sık sorulan kalıplar için yerel/araç tabanlı fallback uygula.
                fallback = self._try_local_tool_fallback(context, messages, answer)
                if fallback:
                    answer = fallback

                # Workspace'e ekle (append şeklinde)
                current_content = self.workspace_editor.get_current_content()
                suffix = ("\n\n" if current_content.strip() else "") + f"Soru: {context}\nYanıt: {answer}\n"
                self.workspace_buffer.suggest_edit(len(current_content), len(current_content), suffix)
                self.workspace_editor._show_suggestions()

                self.update_status_bar("Tool yanıtı eklendi")
                return

            except Exception as e:
                messagebox.showerror("Hata", f"Tool yanıtı alınamadı: {str(e)}")
                self.update_status_bar("Tool yanıtı başarısız")
                return

        # Aksi halde: mevcut davranış (metni iyileştir)
        try:
            self.update_status_bar("Model önerisi (tool destekli) isteniyor...")

            if not hasattr(self, "_tool_assistant") or self._tool_assistant is None:
                self._tool_assistant = AdvancedCalculator()

            chat_url = normalize_chat_url(self.current_model_url)
            tools_def = build_calculator_tools_definition(ec)

            prompt = (
                "Aşağıdaki çalışma alanı metnini düzenle, teknik olarak daha okunabilir ve yapılandırılmış hale getir. "
                "Eğer metinde ham hesaplama verileri, peş peşe eklenmiş sonuçlar veya düzensiz notlar varsa, "
                "bunları uyumlu bir mühendislik raporu/notu formatında toparla.\n\n"
                "Metni düzenlerken, metinde geçen hesaplamaları (kesme hızı, kütle vb.) tespit et ve bu değerleri doğrulamak için MUTLAKA araçları (tools) çağır. Eğer metindeki değer hatalıysa, araçtan dönen doğru sonucu kullanarak metni düzelt.\n\n"
                "ÇOK ÖNEMLİ KURALLAR:\n"
                "1. SADECE düzenlenmiş metni döndür. Kod bloğu (```) bile kullanma, doğrudan metni yaz.\n"
                "2. 'İşte metnin düzenlenmiş hali', 'Değişikliklerin Gerekçesi', 'Açıklama' gibi sohbet, giriş ve çıkış cümleleri KESİNLİKLE KULLANMA.\n"
                "3. Kendi yorumunu veya fazladan açıklamaları metne katma, sadece var olan bilgiyi şıklaştır.\n\n"
                "Düzenlenecek Metin:\n"
                f"{context}"
            )

            messages = [
                {"role": "user", "content": prompt},
            ]

            assistant_msg, _updated = self._tool_assistant.chat_with_tools(
                chat_url,
                self.current_model_name,
                messages,
                tools_def,
                timeout=120,
            )

            response = str(assistant_msg.get("content", "")).strip() or context

            current_content = self.workspace_editor.get_current_content()
            self.workspace_buffer.suggest_edit(0, len(current_content), response)

            self.workspace_editor._show_suggestions()
            self.update_status_bar("Model önerisi eklendi")

        except Exception as e:
            messagebox.showerror("Hata", f"Model önerisi alınamadı: {str(e)}")
            self.update_status_bar("Model önerisi başarısız")

    def _try_local_tool_fallback(
        self,
        question_text: str,
        messages_history: List[Dict[str, Any]],
        model_answer: str,
    ) -> Optional[str]:
        """If model doesn't call tools (or returns unit-mismatched answer), compute locally.

        Şu an için hedef: 'kesme hızı' gibi temel sorularda birim hatalarını engellemek.
        """

        q = (question_text or "").lower()
        a = (model_answer or "").lower()

        # Turning cutting speed: Dm (mm) + n (rpm) -> m/min
        if "kesme hızı" in q or "cutting speed" in q:
            # Eğer model mm/dakika gibi birimlerle (1000x büyük) cevapladıysa düzelt.
            unit_suspect = any(u in a for u in ("mm/dak", "mm/dk", "mm/min", "mm/dakika"))
            missing_expected_unit = ("m/min" not in a) and ("ft/min" not in a)

            dm = self._extract_number_for_dm(question_text)
            n = self._extract_number_for_rpm(question_text)
            if dm is None or n is None:
                return None

            if unit_suspect or missing_expected_unit:
                try:
                    if not hasattr(self, "_tool_assistant") or self._tool_assistant is None:
                        self._tool_assistant = AdvancedCalculator()

                    tool_result = self._tool_assistant._execute_tool(
                        "calculate_turning_cutting_speed",
                        {"Dm": dm, "n": n},
                        messages_history,
                    )
                    return tool_result.content
                except Exception:
                    return None

        return None

    def _extract_number_for_dm(self, text: str) -> Optional[float]:
        """Extract machined diameter (Dm) in mm from free text."""
        patterns = (
            r"(?:çap[ıi]?|dm|diameter)\s*[:=]?\s*(\d+(?:[\.,]\d+)?)",
            r"(\d+(?:[\.,]\d+)?)\s*mm\s*(?:çap|dm)",
        )
        return self._extract_first_number(text, patterns)

    def _extract_number_for_rpm(self, text: str) -> Optional[float]:
        """Extract spindle speed (n) in rpm from free text."""
        patterns = (
            r"(?:rpm|n)\s*[:=]?\s*(\d+(?:[\.,]\d+)?)",
            r"(?:devir\s*/\s*dakika|devir/dakika|devir)\D*(\d+(?:[\.,]\d+)?)",
            r"(\d+(?:[\.,]\d+)?)\s*(?:rpm|devir\s*/\s*dakika|devir/dakika|devir)",
        )
        return self._extract_first_number(text, patterns)

    def _extract_first_number(self, text: str, patterns: tuple[str, ...]) -> Optional[float]:
        for pat in patterns:
            m = re.search(pat, text, flags=re.IGNORECASE)
            if not m:
                continue
            raw = (m.group(1) or "").strip().replace(",", ".")
            try:
                return float(raw)
            except ValueError:
                continue
        return None

    def _should_use_tools_for_text(self, text: str) -> bool:
        """Heuristic: if it looks like a machining or mass calculation request, prefer tool-calling."""
        t = (text or "").lower()
        
        # Soru eki, soru işareti veya hesaplama komut fiilleri var mı kontrol et
        is_request = (
            "?" in t 
            or any(cmd in t for cmd in ("hesapla", "bul", "nedir", "kaç", "calculate", "compute", "find"))
        )
        if not is_request:
            return False
            
        keywords = (
            "kesme hızı",
            "cutting speed",
            "devir",
            "rpm",
            "çap",
            "mm",
            "ilerleme",
            "fz",
            "table feed",
            "feed per tooth",
            "kütle",
            "kütlesi",
            "mass",
            "ağırlık",
            "ağırlığı",
            "weight",
            "yoğunluk",
            "density",
            "hacim",
            "volume",
        )
        return any(k in t for k in keywords)

    def _analyze_workspace(self):
        """Analyze entire workspace with model."""
        if not self.current_model_name or not self.current_model_url:
            messagebox.showwarning("Uyarı", "Lütfen önce model URL'sini ve model seçin.")
            return

        try:
            self.update_status_bar("Çalışma alanı (tool destekli) analiz ediliyor...")

            if not hasattr(self, "_tool_assistant") or self._tool_assistant is None:
                self._tool_assistant = AdvancedCalculator()

            chat_url = normalize_chat_url(self.current_model_url)
            tools_def = build_calculator_tools_definition(ec)

            content = self.workspace_editor.get_current_content()
            
            system_prompt = (
                "Sen uzman bir talaşlı imalat hesap analistisin. Görevin, sana verilen çalışma alanındaki tüm hesaplamaları tespit etmek, "
                "bu hesaplamaları doğrulamak için paralel olarak araçları (tools) çağırmak ve bir analiz raporu oluşturmaktır.\n\n"
                "ANALİZ VE YARATICILIK KURALLARI:\n"
                "1. Metindeki matematiksel parametreleri bul ve doğrulamak için öncelikle sana sunulan mevcut gerçek araçları (tools) kullan.\n"
                "2. Eğer çalışma alanında sayısal veriler veya formüller yoksa, ya da kullanıcının girdiği bağlam çok sınırlıysa (örn: sadece bir başlık varsa), "
                "bunu katı bir şekilde reddetmek yerine olumlu bir çabayla bir analiz taslağı (şablon referans) oluştur. "
                "Bu taslakta, konunun gerektirebileceği teorik parametreleri varsayılan taslak değerlerle göster ve analiz sürecinin nasıl mükemmel bir referans olacağını açıkla.\n"
                "3. KESİNLİKLE gerçek araç çağrıları ile kendi ürettiğin taslak değerleri birbirine karıştırma! Eğer bir değeri doğrulamak için gerçek bir araç (tool) KULLANMADIYSAN, "
                "raporda veya tabloda bunu 'Taslak/Simüle' olarak açıkça belirt.\n"
                "4. Eğer doğrulamak istediğin bir parametre için sana sunulan araç listesinde uygun bir araç yoksa (örneğin Tezgah Rijitliği veya Malzeme Mukavemeti için), "
                "bunu simüle etmek yerine 'Böyle bir araca (örn: Machine Rigidity Calculator) ihtiyaç duyulmaktadır, sisteme eklenmesi önerilir' şeklinde tarif et ve geliştiricilerden talep et.\n"
                "5. Nihai Doğrulama Tablosunda durumları şu şekilde etiketle:\n"
                "   - '✅ Gerçek Araçla Doğrulandı' (Sana sunulan mevcut araçlarla doğrulananlar için)\n"
                "   - '💡 Yeni Araç Önerisi' (Mevcut listemizde olmayıp sisteme eklenmesini önerdiğin araçlar için)\n"
                "   - '📝 Taslak/Referans' (Teorik olarak varsaydığın veya simüle ettiğin değerler için)"
            )
            
            user_prompt = f"Çalışma alanı içeriği:\n\n{content}"

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]

            assistant_msg, _updated = self._tool_assistant.chat_with_tools(
                chat_url,
                self.current_model_name,
                messages,
                tools_def,
                timeout=120,
            )

            response = str(assistant_msg.get("content", "")).strip() or "Analiz sonucunda modelden geçerli bir yanıt alınamadı."

            self._show_analysis_result(response)
            self.update_status_bar("Analiz tamamlandı")

        except Exception as e:
            messagebox.showerror("Hata", f"Analiz sırasında hata: {str(e)}")
            self.update_status_bar("Analiz başarısız")

    def _show_analysis_result(self, result_text: str):
        """Show analysis result in a beautiful scrollable dialog."""
        from tkinter import scrolledtext

        # Create Toplevel window
        dialog = tk.Toplevel(self.root)
        dialog.title("Çalışma Alanı Analizi ve Öneriler")

        # Premium layout geometry: 800x650 centered relative to main window
        width = 800
        height = 650

        # Get parent geometry
        parent_x = self.root.winfo_x()
        parent_y = self.root.winfo_y()
        parent_w = self.root.winfo_width()
        parent_h = self.root.winfo_height()

        # Calculate center position
        x = parent_x + (parent_w - width) // 2
        y = parent_y + (parent_h - height) // 2

        # Check coordinates validity
        if x < 0: x = 100
        if y < 0: y = 100

        dialog.geometry(f"{width}x{height}+{x}+{y}")
        dialog.minsize(600, 500)
        dialog.configure(background="#f8f9fa")

        # Make the window active and modal
        dialog.transient(self.root)
        dialog.grab_set()

        # Main container with nice padding
        main_frame = tk.Frame(dialog, bg="#f8f9fa")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Premium Header
        header_label = tk.Label(
            main_frame,
            text="🔍 Mühendislik Analiz Raporu",
            font=("Arial", 14, "bold"),
            bg="#f8f9fa",
            fg="#2b3e50",
            anchor="w"
        )
        header_label.pack(fill=tk.X, pady=(0, 5))

        sub_header = tk.Label(
            main_frame,
            text="Yapay zeka tarafından çalışma alanınızdaki veriler incelendi ve aşağıdaki öneriler hazırlandı:",
            font=("Arial", 10),
            bg="#f8f9fa",
            fg="#6c757d",
            anchor="w"
        )
        sub_header.pack(fill=tk.X, pady=(0, 15))

        # Text container with border
        text_frame = tk.Frame(main_frame, bg="#e9ecef", bd=1, relief=tk.SOLID)
        text_frame.pack(fill=tk.BOTH, expand=True)

        # ScrolledText widget for rich scrollable view
        text_area = scrolledtext.ScrolledText(
            text_frame,
            wrap=tk.WORD,
            font=("Arial", 11),
            bg="white",
            fg="#212529",
            insertbackground="#212529",
            padx=15,
            pady=15,
            bd=0,
            highlightthickness=0
        )
        text_area.pack(fill=tk.BOTH, expand=True)

        # Configure tags for styling
        text_area.tag_configure("h2", font=("Arial", 13, "bold"), foreground="#2b3e50")
        text_area.tag_configure("h3", font=("Arial", 11, "bold"), foreground="#1e293b")
        text_area.tag_configure("h4", font=("Arial", 10, "bold"), foreground="#334155")
        text_area.tag_configure("bold", font=("Arial", 11, "bold"), foreground="#0f172a")
        text_area.tag_configure("italic", font=("Arial", 11, "italic"))
        text_area.tag_configure("code", font=("Consolas", 10), background="#f1f5f9", foreground="#0f172a")
        text_area.tag_configure("bullet", font=("Arial", 11), lmargin1=20, lmargin2=30)
        text_area.tag_configure("separator", font=("Arial", 6), foreground="#cbd5e1")
        text_area.tag_configure("math_block", font=("Consolas", 10, "bold"), background="#f8fafc", foreground="#0f172a", lmargin1=40, lmargin2=40)

        # Populate the text area initially
        self._populate_analysis_text(text_area, result_text)

        # Actions implementation
        def do_copy():
            """Copy entire text content of the report to the clipboard."""
            content = text_area.get("1.0", tk.END).strip()
            self.root.clipboard_clear()
            self.root.clipboard_append(content)
            self.update_status_bar("Rapor panoya kopyalandı")
            messagebox.showinfo("Başarılı", "Rapor içeriği başarıyla panoya kopyalandı!")

        def do_refresh():
            """Re-fetch the workspace analysis and refresh the UI content."""
            # Set loading state
            text_area.configure(state=tk.NORMAL)
            text_area.delete("1.0", tk.END)
            text_area.insert(tk.END, "🔄 Çalışma alanı analiz ediliyor... Lütfen bekleyin.\n\n", "bold")
            text_area.configure(state=tk.DISABLED)
            dialog.update()

            try:
                self.update_status_bar("Çalışma alanı yeniden analiz ediliyor...")
                content = self.workspace_editor.get_current_content()
                context = f"Bu mühendislik çalışma alanını analiz et ve öneriler sun: {content}"

                new_response = single_chat_request(
                    self.current_model_url,
                    self.current_model_name,
                    context,
                    timeout=120,
                )

                self._populate_analysis_text(text_area, str(new_response))
                self.update_status_bar("Yeniden analiz tamamlandı")
            except Exception as ex:
                text_area.configure(state=tk.NORMAL)
                text_area.insert(tk.END, f"\n❌ Yeniden analiz sırasında hata oluştu:\n{str(ex)}", "bold")
                text_area.configure(state=tk.DISABLED)
                self.update_status_bar("Yeniden analiz başarısız")

        # Action Button Frame
        btn_frame = tk.Frame(main_frame, bg="#f8f9fa")
        btn_frame.pack(fill=tk.X, pady=(15, 0))

        # Horizontal side-by-side action icons subframe
        icons_subframe = tk.Frame(btn_frame, bg="#f8f9fa")
        icons_subframe.pack(side=tk.RIGHT)

        # Refresh Button (↻)
        refresh_btn = tk.Button(
            icons_subframe,
            text="↻",
            font=("Arial", 14, "bold"),
            bg="#f1f5f9",
            fg="#334155",
            activebackground="#e2e8f0",
            activeforeground="#334155",
            relief=tk.FLAT,
            width=3,
            height=1,
            bd=0,
            command=do_refresh,
            cursor="hand2"
        )
        refresh_btn.pack(side=tk.LEFT, padx=5)

        # Copy Button (📋)
        copy_btn = tk.Button(
            icons_subframe,
            text="📋",
            font=("Arial", 14),
            bg="#f1f5f9",
            fg="#334155",
            activebackground="#e2e8f0",
            activeforeground="#334155",
            relief=tk.FLAT,
            width=3,
            height=1,
            bd=0,
            command=do_copy,
            cursor="hand2"
        )
        copy_btn.pack(side=tk.LEFT, padx=5)

        # Close Button (✕)
        close_btn = tk.Button(
            icons_subframe,
            text="✕",
            font=("Arial", 14, "bold"),
            bg="#fee2e2",
            fg="#ef4444",
            activebackground="#fca5a5",
            activeforeground="#ef4444",
            relief=tk.FLAT,
            width=3,
            height=1,
            bd=0,
            command=dialog.destroy,
            cursor="hand2"
        )
        close_btn.pack(side=tk.LEFT, padx=5)

        # Esc key binding to close the window
        dialog.bind("<Escape>", lambda e: dialog.destroy())

        # Focus on the text area for quick keyboard navigation
        text_area.focus_set()

    def _populate_analysis_text(self, text_area, text_content: str):
        """Parse and populate markdown/formula text in text area."""
        text_area.configure(state=tk.NORMAL)
        text_area.delete("1.0", tk.END)

        lines = text_content.split("\n")
        in_code_block = False

        for line in lines:
            # Code block toggle
            if line.strip().startswith("```"):
                in_code_block = not in_code_block
                continue

            if in_code_block:
                text_area.insert(tk.END, line + "\n", "code")
                continue

            # Check for block equations
            if line.strip().startswith("$$") and line.strip().endswith("$$") and len(line.strip()) > 4:
                math_content = line.strip()[2:-2].strip()
                text_area.insert(tk.END, f"   {math_content}\n\n", "math_block")
                continue

            # Check for horizontal rule
            if line.strip() == "---" or line.strip() == "--- ":
                text_area.insert(tk.END, "────────────────────────────────────────────────────────────────────────────────\n\n", "separator")
                continue

            # Check for headers
            if line.startswith("## "):
                text_area.insert(tk.END, line[3:] + "\n\n", "h2")
                continue
            elif line.startswith("### "):
                text_area.insert(tk.END, line[4:] + "\n\n", "h3")
                continue
            elif line.startswith("#### "):
                text_area.insert(tk.END, line[5:] + "\n\n", "h4")
                continue

            # Check for bullet points
            is_bullet = False
            bullet_prefix = ""
            if line.strip().startswith("- ") or line.strip().startswith("* ") or line.strip().startswith("• "):
                is_bullet = True
                # Get the leading spaces to preserve indent level
                leading_spaces = len(line) - len(line.lstrip())
                bullet_prefix = " " * leading_spaces + "• "
                line_content = line.strip()[2:]
            else:
                line_content = line

            # Parse inline styles like **bold** and `code` and $math$
            parts = re.split(r"(\*\*.*?\*\*|`.*?`|\$.*?\$)", line_content)

            if is_bullet:
                text_area.insert(tk.END, bullet_prefix, "bullet")

            for part in parts:
                if part.startswith("**") and part.endswith("**"):
                    text_area.insert(tk.END, part[2:-2], ("bold", "bullet" if is_bullet else ""))
                elif part.startswith("`") and part.endswith("`"):
                    text_area.insert(tk.END, f" {part[1:-1]} ", ("code", "bullet" if is_bullet else ""))
                elif part.startswith("$") and part.endswith("$"):
                    text_area.insert(tk.END, part[1:-1], ("code", "bullet" if is_bullet else ""))
                else:
                    text_area.insert(tk.END, part, "bullet" if is_bullet else "")

            text_area.insert(tk.END, "\n")

        text_area.configure(state=tk.DISABLED)

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
            model_url = self.model_url_entry.get().strip()
            self.current_model_url = model_url

            self.ollama_models = get_available_models(model_url)

            if self.ollama_models:
                self.model_selection_combo["values"] = self.ollama_models
                if not self.current_model_name or self.current_model_name not in self.ollama_models:
                    self.model_selection_combo.set(self.ollama_models[0])
                    self.current_model_name = self.ollama_models[0]
                else:
                    self.model_selection_combo.set(self.current_model_name)
                self.update_status_bar(f"Modeller yenilendi: {len(self.ollama_models)} model bulundu")
            else:
                # Hata/bağlantı yok durumunda fallback modeller atanmalıdır
                fallback_models = ["llama3", "gemma2", "mistral"]
                self.model_selection_combo["values"] = fallback_models
                self.model_selection_combo.set(fallback_models[0])
                self.current_model_name = fallback_models[0]
                self.update_status_bar("Model bağlantısı kurulamadı; varsayılan model listesi (fallback) yüklendi.")

        except Exception as e:
            fallback_models = ["llama3", "gemma2", "mistral"]
            self.model_selection_combo["values"] = fallback_models
            self.model_selection_combo.set(fallback_models[0])
            self.current_model_name = fallback_models[0]
            messagebox.showerror("Hata", f"Modeller alınırken hata oluştu: {str(e)}")
            self.update_status_bar("Model yenileme başarısız, varsayılan liste atandı")

    def test_model_connection(self):
        """Test connection to model with detailed Turkish troubleshooting."""
        try:
            model_url = self.model_url_entry.get().strip()
            if test_connection(model_url):
                messagebox.showinfo("Bağlantı Başarılı", "Ollama sunucusuna bağlantı başarılı!")
                self.update_status_bar("Bağlantı başarılı")
            else:
                messagebox.showerror(
                    "Bağlantı Başarısız",
                    "Ollama sunucusuna bağlanılamadı!\n\n"
                    "Lütfen şunları kontrol edin:\n"
                    "1. Ollama sunucusunun çalıştığından emin olun (örneğin terminalde 'ollama serve' çalışıyor mu?).\n"
                    "2. Model URL adresinin doğru olduğunu doğrulayın (varsayılan: http://localhost:11434).\n"
                    "3. Bilgisayarınızın internet/ağ bağlantısını ve güvenlik duvarı ayarlarını kontrol edin."
                )
                self.update_status_bar("Bağlantı başarısız")
        except Exception as e:
            messagebox.showerror("Hata", f"Bağlantı testi sırasında beklenmeyen hata: {str(e)}")
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
        """Apply default window geometry exactly (1400x900) centered and brought to front."""
        def set_geo():
            self.root.update_idletasks()
            width = DEFAULT_WINDOW_SIZE[0]
            height = DEFAULT_WINDOW_SIZE[1]
            
            # Ekran boyutu tespiti yap, macOS launcher gibi ortamlardaki uninitialized durumlari yakala
            screen_w = self.root.winfo_screenwidth()
            screen_h = self.root.winfo_screenheight()
            if screen_w < 800: screen_w = 1920
            if screen_h < 600: screen_h = 1080
            
            x = (screen_w // 2) - (width // 2)
            y = (screen_h // 2) - (height // 2)
            if x < 0: x = 50
            if y < 0: y = 50
            
            # Pencere boyutunu ve konumunu kesin olarak uygula
            self.root.geometry(f"{width}x{height}+{x}+{y}")
            
            # Pencereyi göster ve en öne çıkar
            self.root.deiconify()
            self.root.lift()
            self.root.attributes("-topmost", True)
            self.root.focus_force()
            
            # 300ms sonra topmost kilidini kaldır (pencerenin hep en üstte kilitli kalmaması için)
            self.root.after(300, lambda: self.root.attributes("-topmost", False))

        # macOS pencere yöneticisinin hazır olması için 200ms gecikmeyle çağırıyoruz
        self.root.after(200, set_geo)


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
