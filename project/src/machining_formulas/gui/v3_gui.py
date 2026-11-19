"""V3 GUI - Workspace Buffer Based Interface.

Bu modül Tkinter tabanlı V3 arayüzünü sağlar.
- Tornalama/Frezeleme: dropdown -> seçime göre dinamik parametre formu
- Her sekmenin üstünde PNG header (Pillow yok, tk.PhotoImage)
- Çalışma alanı: WorkspaceBuffer + WorkspaceEditor
"""

# -*- coding : utf-8 -*-
# Autor: Hakan KILIÇASLAN 2025
# Uzun Türkçe LLM istemleri bilinçli olarak tek satırda tutuluyor.
# flake8: noqa: E501

from __future__ import annotations

import json
import logging
import os
import re
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, scrolledtext
from tkinter import ttk
from typing import Any, Callable, Dict, List, Optional
try:
    from PIL import Image, ImageTk
except ImportError:  # Pillow opsiyonel: yoksa başlık görselleri metin fallback'ine düşer
    Image = None  # type: ignore[assignment]
    ImageTk = None  # type: ignore[assignment]

from machining_formulas.assets import asset_path, settings_path
from machining_formulas.core.engineering_calculator import EngineeringCalculator
from machining_formulas.gui.advanced_calculator import AdvancedCalculator
from machining_formulas.gui.execute_mode import ExecuteModeMixin
from machining_formulas.llm.ollama_utils import (
    OLLAMA_CHAT_TIMEOUT,
    build_calculator_tools_definition,
    normalize_chat_url,
)
from machining_formulas.llm.ollama_utils_v2 import (
    get_available_models,
    single_chat_request,
    test_connection,
)
from machining_formulas.workspace.workspace_buffer import WorkspaceBuffer
from machining_formulas.workspace.workspace_editor import (
    MODE_INSERT,
    ModelRequest,
    WorkspaceEditor,
    format_answer_block,
)


DEFAULT_WINDOW_SIZE: tuple[int, int] = (1400, 900)
SUPPORTED_PROMPT_ATTACHMENT_EXTENSIONS: set[str] = {".txt", ".md", ".py", ".c", ".cpp"}

logger = logging.getLogger(__name__)

# Global instance
ec = EngineeringCalculator()


def parse_user_number(raw: Any, label: str) -> float:
    """Parse a user-entered number and raise a Turkish ValueError when invalid.

    Kullanıcı Türkçe ondalık ayırıcısını (virgül) da yazabilir: "12,5". Binlik
    nokta ile birlikte gelirse ("1.234,5") nokta atılır.
    """
    text = str(raw).strip().replace(" ", "")
    if "," in text:
        if "." in text:
            text = text.replace(".", "").replace(",", ".")
        else:
            text = text.replace(",", ".")
    try:
        return float(text)
    except (TypeError, ValueError) as exc:
        raise ValueError(f"'{label}' geçerli bir sayı olmalıdır.") from exc


class V3Calculator(ExecuteModeMixin):
    """V3 Calculator with workspace buffer interface."""

    def __init__(self, root: tk.Tk, tooltips: Dict[str, str]):
        self.root = root
        self.root.withdraw()  # macOS ve diger platformlarda baslangictaki kucuk/konumsuz pencereyi gizle
        self.tooltips = tooltips

        # Tool-calling assistant (LLM -> tools -> compute -> final answer)
        self._tool_assistant = AdvancedCalculator()

        # Keep references to PhotoImage instances
        self._header_images: Dict[str, ImageTk.PhotoImage | tk.PhotoImage] = {}

        # State containers for dynamic calculation UIs (turning/milling)
        self._dynamic_calc_state: Dict[str, dict] = {}

        # Hover popups states
        self._active_hover_popup: tk.Toplevel | None = None
        self._active_popup_photo: ImageTk.PhotoImage | None = None

        # Execute modu durumu (ExecuteModeMixin sağlar)
        super().__init__()

        # Initialize workspace buffer
        self.workspace_buffer = WorkspaceBuffer()

        # Model configuration
        settings = self._load_settings()
        self.current_model_url = settings.get("ollama_url", "http://localhost:11434")
        self.current_model_name = settings.get("model_name", "")
        self.current_api_key = settings.get("api_key", "")
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

    def setup_ui(self):
        """Setup the main V3 interface."""
        self.root.title("🔧 Mühendislik Hesaplayıcı V3 - Çalışma Alanı")
        self.root.report_callback_exception = self._report_callback_exception

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
            if isinstance(widget, tk.Text):
                widget.config(takefocus=1)
                # add="+" mevcut widget bağlamalarını (imleç, seçim, tıklama) korur.
                widget.bind("<Button-1>", lambda e, w=widget: w.focus_set(), add="+")
                widget.bind("<FocusIn>", lambda e: None, add="+")
                # Editörde Tab girinti ekler; alandan çıkmak için Shift+Tab kullanılır.
                widget.bind("<Tab>", self._insert_indent_at_cursor, add="+")
            elif isinstance(widget, tk.Entry):
                widget.config(takefocus=1)
                widget.bind("<Button-1>", lambda e, w=widget: w.focus_set(), add="+")
                widget.bind("<FocusIn>", lambda e: None, add="+")
            elif isinstance(widget, (ttk.Entry, ttk.Combobox)):
                widget.configure(takefocus=True)
                widget.bind("<Button-1>", lambda e, w=widget: w.focus_set(), add="+")
                widget.bind("<FocusIn>", lambda e: None, add="+")
            elif isinstance(widget, (ttk.Button, tk.Button)):
                widget.configure(takefocus=True)
                widget.bind("<Button-1>", lambda e, w=widget: w.focus_set(), add="+")

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

        key_frame = ttk.Frame(model_frame, style="Calc.TFrame")
        key_frame.pack(fill="x", padx=10, pady=6)

        ttk.Label(key_frame, text="API Key:", width=8).pack(side="left")
        self.api_key_entry = ttk.Entry(key_frame, width=30, show="*")
        self.api_key_entry.pack(side="left", fill="x", expand=True, padx=(5, 0))
        self.api_key_entry.insert(0, self.current_api_key)
        ttk.Label(
            key_frame,
            text="(boşsa MACHINING_FORMULAS_API_KEY / STRATA_API_KEY)",
            font=("TkDefaultFont", 9),
        ).pack(side="right", padx=(5, 0))

        model_frame_inner = ttk.Frame(model_frame, style="Calc.TFrame")
        model_frame_inner.pack(fill="x", padx=10, pady=6)

        ttk.Label(model_frame_inner, text="Model:", width=8).pack(side="left")
        self.model_selection_combo = ttk.Combobox(
            model_frame_inner, width=25, style="Calc.TCombobox"
        )
        self.model_selection_combo.pack(side="left", fill="x", expand=True, padx=(5, 0))
        self.model_selection_combo.bind("<<ComboboxSelected>>", self._on_model_selection_change)

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
        self._create_console_tab()

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

        self.mass_calc_button = ttk.Button(frame, text="Hesapla", command=self._calculate_mass)
        self.mass_calc_button.pack(pady=5)

        self._update_mass_params()

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

    def _create_console_tab(self):
        """Create the experimental execute-mode console tab."""
        console_frame = ttk.Frame(self.calc_notebook, style="Calc.TFrame")
        self.calc_notebook.add(console_frame, text="Konsol")
        self._console_frame = console_frame

        ttk.Label(
            console_frame,
            text=(
                "Deneysel: bir ifade yazıp seçin, sonra Cmd/Ctrl+Enter ile değerlendirin. "
                "Yalnızca 'calc.<hesap>(...)' çağrıları ve sayısal aritmetik desteklenir."
            ),
            style="Calc.TLabel",
            wraplength=360,
        ).pack(fill="x", padx=6, pady=(6, 2))

        self.result_text = tk.Text(
            console_frame,
            height=10,
            wrap="word",
            font=("Consolas", 10),
            bg="white",
            fg="#212529",
            insertbackground="#212529",
            padx=6,
            pady=6,
        )
        self.result_text.pack(fill="both", expand=True, padx=6, pady=(2, 6))

        # Widget düzeyinde bağlanır: Text sınıfının <Return> bağlaması satır
        # eklemeden önce çalışsın diye "break" döndürülür.
        for prefix in ("Control", "Command"):
            self.result_text.bind(f"<{prefix}-Return>", self._run_exec_shortcut)
            self.result_text.bind(
                f"<{prefix}-Shift-Return>", self._run_exec_shortcut
            )

    def _get_exec_mode_calculator(self) -> EngineeringCalculator:
        """Provider required by ExecuteModeMixin."""
        return ec

    def _open_exec_mode(self) -> None:
        """Toggle execute mode and reveal the console tab when turning it on."""
        if getattr(self, "execute_mode", False):
            self.disable_execute_mode()
            return
        try:
            self.calc_notebook.select(self._console_frame)
        except tk.TclError:
            pass
        self.enable_execute_mode()

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
        if Image is not None and ImageTk is not None and image_path.exists():
            try:
                pil_img = Image.open(image_path)
                # Resize image to fit height=120 while keeping aspect ratio
                h_size = 120
                w_percent = h_size / pil_img.size[1]
                w_size = int(pil_img.size[0] * w_percent)
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
                        logger.warning("Açılır önizleme oluşturulamadı: %s", ex)

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
                setattr(canvas, "on_enter", on_enter)
                setattr(canvas, "on_leave", on_leave)
                return
            except Exception as e:
                logger.warning("Başlık görseli yüklenemedi (%s): %s", image_filename, e)

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

                val = parse_user_number(val_str, name)
                args.append(val)
                params_dict[name] = val

            result_dict = ec.calculate(state["category"], method_key, *args)

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
            on_model_request=self._handle_model_request,
            on_content_change=self._on_workspace_change,
            tooltips=self.tooltips,
        )
        self.workspace_editor.pack(fill="both", expand=True)

    def _create_menu_bar(self):
        """Create menu bar."""
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

        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Araçlar", menu=tools_menu)
        tools_menu.add_command(label="Execute Modu Aç/Kapat (Deneysel)", accelerator=f"{mod_text}Shift+X", command=self._open_exec_mode)
        tools_menu.add_command(label="Seçili Kodu Çalıştır", accelerator=f"{mod_text}Return", command=self.execute_calculation)

    def _setup_keyboard_shortcuts(self):
        """Configure macOS-prioritized, cross-platform keyboard shortcuts for menus and tabs."""
        is_mac = sys.platform == "darwin"
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        def _bind(key, callback, is_shift=False, guard_typing=False):
            shift_str = "Shift-" if is_shift else ""

            def _handler(_event):
                # Metin alanında yazarken kısayolun düzenleme tuşunu ezmesini engelle
                # (ör. Cmd+A "tümünü seç" veya Cmd+E "satır sonu").
                if guard_typing and self._text_has_focus():
                    return None
                callback()
                return None

            # Control bindings
            self.root.bind_all(f"<Control-{shift_str}{key.lower()}>", _handler)
            if len(key) == 1 and key.isalpha():
                self.root.bind_all(f"<Control-{shift_str}{key.upper()}>", _handler)

            # Command bindings on macOS
            if is_mac:
                self.root.bind_all(f"<Command-{shift_str}{key.lower()}>", _handler)
                if len(key) == 1 and key.isalpha():
                    self.root.bind_all(f"<Command-{shift_str}{key.upper()}>", _handler)

        # File Operations
        _bind("n", self._new_workspace, guard_typing=True)
        _bind("o", self._open_workspace, guard_typing=True)
        _bind("s", self._save_workspace)
        _bind("e", self._export_workspace, guard_typing=True)
        _bind("q", self._on_close)

        # Edit Operations
        _bind("z", self.workspace_editor._undo)
        _bind("y", self.workspace_editor._redo)
        _bind("z", self.workspace_editor._redo, is_shift=True)  # Cmd+Shift+Z for macOS
        _bind("l", self.workspace_editor._clear_workspace, guard_typing=True)

        # Model & AI Operations
        _bind("t", self.test_model_connection, is_shift=True)  # Cmd+Shift+T
        _bind("r", self.refresh_model_list, guard_typing=True)
        _bind("a", self._analyze_workspace, is_shift=True, guard_typing=True)  # Cmd+Shift+A

        # Execute Mode (Deneysel)
        _bind("x", self._open_exec_mode, is_shift=True)
        for prefix in ("Control", "Command"):
            self.root.bind_all(f"<{prefix}-Return>", self._run_exec_shortcut)
            self.root.bind_all(f"<{prefix}-Shift-Return>", self._run_exec_shortcut)

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

    def _run_exec_shortcut(self, _event=None):
        """Execute the console selection without letting the shortcut insert a newline."""
        self.execute_calculation()
        return "break"

    def _report_callback_exception(self, exc_type, exc_value, exc_tb) -> None:
        """Log uncaught Tk callback errors and tell the user instead of failing silently."""
        logger.error("Arayüz geri çağrısında hata", exc_info=(exc_type, exc_value, exc_tb))
        try:
            messagebox.showerror("Beklenmeyen Hata", f"İşlem tamamlanamadı: {exc_value}")
        except tk.TclError:
            pass

    def _text_has_focus(self) -> bool:
        """Return True when a text widget owns the keyboard focus."""
        try:
            return isinstance(self.root.focus_get(), tk.Text)
        except (KeyError, tk.TclError):
            return False

    def _show_shortcuts_help(self):
        """Display a comprehensive help dialog for keyboard shortcuts."""
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
            "🧪 Konsol (Deneysel):\n"
            f"  • {mod}+Shift+X : Execute modunu aç/kapat (Konsol sekmesi)\n"
            f"  • {mod}+Enter : Konsolda seçili ifadeyi çalıştır\n\n"
            "⚡ Diğer Kolaylıklar:\n"
            "  • Enter (Giriş) : Sayısal parametre alanlarında doğrudan Hesapla tetikler\n"
            "  • Esc : Çıkan diyalog veya popup pencereleri kapatır\n"
            f"  • F1 veya {mod}+/ : Bu kısayol yardım menüsünü açar\n"
            f"  • Metin düzenlerken {mod}+A, {mod}+E, {mod}+L, {mod}+N, {mod}+O, {mod}+R\n"
            "    devre dışıdır; bu tuşlar metin alanının kendi işlevini korur\n"
            "  • Tab / Shift+Tab : Alanlar arasında ileri/geri geçiş\n"
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
            self._mark_unsupported_shape(shape_turkish)
            return

        try:
            param_names = ec.get_shape_parameters(shape_key)
        except ValueError:
            self._mark_unsupported_shape(shape_turkish)
            return

        self.mass_param_widgets = {}
        self.current_shape_key = shape_key
        if hasattr(self, "mass_calc_button"):
            self.mass_calc_button.state(["!disabled"])

        for param_name in param_names:
            frame = ttk.Frame(self.mass_params_frame, style="Calc.TFrame")
            frame.pack(fill="x", pady=1)

            display_name = ec.PARAM_TURKISH_NAMES.get(
                param_name, param_name.capitalize()
            )
            ttk.Label(frame, text=f"{display_name}:", width=15).pack(side="left")
            entry = ttk.Entry(frame, width=15)
            entry.pack(side="left", padx=(5, 0))
            entry.bind("<Return>", lambda _e: self._calculate_mass())

            self.mass_param_widgets[param_name] = entry

        if shape_key != "sphere":
            length_frame = ttk.Frame(self.mass_params_frame, style="Calc.TFrame")
            length_frame.pack(fill="x", pady=1)
            length_label = ec.PARAM_TURKISH_NAMES.get("length", "Uzunluk")
            ttk.Label(length_frame, text=f"{length_label}:", width=15).pack(side="left")
            length_entry = ttk.Entry(length_frame, width=15)
            length_entry.pack(side="left", padx=(5, 0))
            length_entry.bind("<Return>", lambda _e: self._calculate_mass())
            self.mass_param_widgets["length"] = length_entry

        self.mass_params_frame.update_idletasks()

    def _mark_unsupported_shape(self, shape_turkish: str) -> None:
        """Show a hint and disable calculation for an unsupported shape."""
        error_frame = ttk.Frame(self.mass_params_frame, style="Calc.TFrame")
        error_frame.pack(fill="x", pady=1)
        ttk.Label(
            error_frame,
            text=f"Hata: {shape_turkish} şekli desteklenmiyor",
            foreground="red",
            font=("Arial", 9),
        ).pack(side="left")
        self.mass_param_widgets = {}
        self.current_shape_key = None
        if hasattr(self, "mass_calc_button"):
            self.mass_calc_button.state(["disabled"])

    def _calculate_mass(self):
        """Calculate mass."""
        if not self.current_shape_key:
            messagebox.showerror("Hata", "Lütfen desteklenen bir şekil seçin.")
            return
        try:
            shape_key = self.current_shape_key
            density = parse_user_number(self.mass_density.get(), "Yoğunluk")

            param_names = ec.get_shape_parameters(shape_key)
            param_values = []
            params_dict: Dict[str, float] = {}

            for param_name in param_names:
                entry = self.mass_param_widgets.get(param_name)
                if entry is None:
                    display = ec.PARAM_TURKISH_NAMES.get(param_name, param_name)
                    raise ValueError(f"'{display}' alanı bulunamadı.")
                value = parse_user_number(entry.get(), param_name)
                param_values.append(value)
                params_dict[param_name] = value

            if shape_key != "sphere" and "length" in self.mass_param_widgets:
                length_label = ec.PARAM_TURKISH_NAMES.get("length", "Uzunluk")
                length = parse_user_number(
                    self.mass_param_widgets["length"].get(), length_label
                )
                param_values.append(length)
                params_dict["length"] = length

            result = ec.calculate_material_mass(shape_key, density, *param_values)
            self.mass_last_result = {
                "value": result,
                "unit": "g",
                "shape": shape_key,
                "density": density,
                "params": params_dict,
            }
            self.mass_result.config(text=f"Sonuç: {result:.2f} g")

        except ValueError as e:
            messagebox.showerror("Hata", f"Lütfen geçerli sayısal değerler girin: {str(e)}")
        except Exception as e:
            messagebox.showerror("Hata", f"Hesaplama hatası: {str(e)}")

    def _inject_mass(self):
        """Inject the last mass calculation into the workspace."""
        last = getattr(self, "mass_last_result", None)
        if not last:
            messagebox.showerror("Hata", "Lütfen önce hesaplama yapın.")
            return

        try:
            self.workspace_editor.insert_calculation_result(
                "Malzeme Hesaplamaları",
                "Kütle Hesabı",
                {"shape": last["shape"], "density": last["density"], **last["params"]},
                last["value"],
                last["unit"],
            )
        except Exception as exc:
            logger.error("Kütle sonucu çalışma alanına aktarılamadı", exc_info=exc)
            messagebox.showerror("Hata", f"Sonuç çalışma alanına aktarılamadı: {exc}")

    def _handle_model_request(self, request: ModelRequest) -> None:
        """Route an editor request to a calculation answer or a text edit."""
        if not self.current_model_name or not self.current_model_url:
            messagebox.showwarning("Uyarı", "Lütfen önce model URL'sini ve model seçin.")
            self.workspace_editor.finish_request("Model seçilmedi")
            return

        question = (request.question or "").strip()
        # Düzenleme yolu ham seçimi kullanır: kırpılan metnin uzunluğu, seçimin
        # gerçek ofsetiyle eşleşmediği için yanlış aralığı değiştirirdi.
        source_text = request.source_text or ""

        if not question and not source_text.strip():
            self.workspace_editor.finish_request("Boş istek")
            return

        if question:
            self._answer_workspace_question(question, source_text.strip(), request)
        else:
            self._edit_workspace_text(source_text, request)

    def _answer_workspace_question(
        self,
        question: str,
        source_text: str,
        request: ModelRequest,
    ) -> None:
        """Answer a question typed in the editor's question bar."""
        self.update_status_bar("Soru yanıtlanıyor...")

        if not hasattr(self, "_tool_assistant") or self._tool_assistant is None:
            self._tool_assistant = AdvancedCalculator()

        chat_url = normalize_chat_url(self.current_model_url)
        tools_def = build_calculator_tools_definition(ec)
        model_name = self.current_model_name
        api_key = self._api_key_value()

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

        # Belgenin tümü "Soru" olarak gönderilmez; yalnızca soru ve (varsa) seçim.
        user_content = question
        if source_text:
            user_content = f"{question}\n\nBağlam (seçili metin):\n{source_text}"

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ]

        def work() -> str:
            assistant_msg, _updated = self._tool_assistant.chat_with_tools(
                chat_url,
                model_name,
                messages,
                tools_def,
                timeout=OLLAMA_CHAT_TIMEOUT,
                api_key=api_key,
            )
            answer = str(assistant_msg.get("content", "")).strip() or "(boş yanıt)"
            # Bazı modeller tools varken bile doğrudan (ve bazen yanlış birimle) yanıt verebiliyor.
            # Bu durumda sık sorulan kalıplar için yerel/araç tabanlı fallback uygula.
            # Model yanıtı korunur; yerel araç sonucu ayrı bir satırda gösterilir.
            fallback = self._try_local_tool_fallback(question, messages, answer)
            if fallback and fallback.strip() not in answer:
                return f"{answer}\n\n🧮 Yerel araç doğrulaması: {fallback.strip()}"
            return answer

        def apply(answer: str) -> None:
            block = format_answer_block(question, answer)
            if not block:
                self.workspace_editor.finish_request("Modelden boş yanıt geldi")
                return
            self._add_workspace_suggestion(block, request)
            self.update_status_bar("Yanıt incelemeye hazır")

        def fail(exc: Exception) -> None:
            logger.error("Soru yanıtlanamadı", exc_info=exc)
            messagebox.showerror("Hata", f"Soru yanıtlanamadı: {exc}")
            self.update_status_bar("Soru yanıtlanamadı")
            self.workspace_editor.finish_request("Soru yanıtlanamadı")

        self._run_background(work, apply, fail)

    def _edit_workspace_text(self, source_text: str, request: ModelRequest) -> None:
        """Ask the model to rewrite the selection (or the whole document)."""
        self.update_status_bar("Düzenleme önerisi (tool destekli) isteniyor...")

        if not hasattr(self, "_tool_assistant") or self._tool_assistant is None:
            self._tool_assistant = AdvancedCalculator()

        chat_url = normalize_chat_url(self.current_model_url)
        tools_def = build_calculator_tools_definition(ec)
        model_name = self.current_model_name
        api_key = self._api_key_value()

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
            f"{source_text}"
        )

        messages = [
            {"role": "user", "content": prompt},
        ]

        def work() -> str:
            assistant_msg, _updated = self._tool_assistant.chat_with_tools(
                chat_url,
                model_name,
                messages,
                tools_def,
                timeout=OLLAMA_CHAT_TIMEOUT,
                api_key=api_key,
            )
            return str(assistant_msg.get("content", "")).strip()

        def apply(response: str) -> None:
            if not response:
                self.workspace_editor.finish_request("Modelden boş yanıt geldi")
                return
            if response.strip() == source_text.strip():
                self.workspace_editor.finish_request("Öneri mevcut metinle aynı")
                return
            self._add_workspace_suggestion(response, request, replacement=source_text)
            self.update_status_bar("Düzenleme önerisi incelemeye hazır")

        def fail(exc: Exception) -> None:
            logger.error("Düzenleme önerisi alınamadı", exc_info=exc)
            messagebox.showerror("Hata", f"Düzenleme önerisi alınamadı: {exc}")
            self.update_status_bar("Düzenleme başarısız")
            self.workspace_editor.finish_request("Düzenleme başarısız")

        self._run_background(work, apply, fail)

    def _add_workspace_suggestion(
        self,
        text: str,
        request: ModelRequest,
        replacement: Optional[str] = None,
    ) -> None:
        """Create a pending suggestion and open it in the review panel."""
        content = self.workspace_editor.get_current_content()

        if replacement is not None:
            start = max(0, min(request.offset, len(content)))
            end = start + len(replacement)
            if content[start:end] != replacement:
                # Model yanıtı beklerken belge değişti; bayat ofsetle öneri üretme.
                self.workspace_editor.finish_request(
                    "Metin değişti — öneri oluşturulmadı, lütfen yeniden gönderin"
                )
                return
            edit = self.workspace_buffer.suggest_edit(start, end, text)
        elif request.mode == MODE_INSERT:
            offset = max(0, min(request.offset, len(content)))
            edit = self.workspace_buffer.suggest_edit(offset, offset, text)
        else:
            prefix = "\n\n" if content.strip() else ""
            edit = self.workspace_buffer.suggest_edit(
                len(content), len(content), prefix + text, at_end=True
            )

        self.workspace_editor.open_review(edit.id)
        self.workspace_editor.finish_request("Öneri hazır — inceleme panelinde")

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

                    tool_result = self._tool_assistant.execute_tool(
                        "calculate_turning_cutting_speed",
                        {"Dm": dm, "n": n},
                        messages_history,
                    )
                    return tool_result.content
                except Exception as exc:
                    logger.warning("Yerel araç yedeği başarısız: %s", exc)
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

    def _analyze_workspace(self):
        """Analyze entire workspace with model."""
        if not self.current_model_name or not self.current_model_url:
            messagebox.showwarning("Uyarı", "Lütfen önce model URL'sini ve model seçin.")
            return

        self.update_status_bar("Çalışma alanı (tool destekli) analiz ediliyor...")

        if not hasattr(self, "_tool_assistant") or self._tool_assistant is None:
            self._tool_assistant = AdvancedCalculator()

        chat_url = normalize_chat_url(self.current_model_url)
        tools_def = build_calculator_tools_definition(ec)
        model_name = self.current_model_name
        api_key = self._api_key_value()

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

        def work() -> str:
            assistant_msg, _updated = self._tool_assistant.chat_with_tools(
                chat_url,
                model_name,
                messages,
                tools_def,
                timeout=OLLAMA_CHAT_TIMEOUT,
                api_key=api_key,
            )
            return (
                str(assistant_msg.get("content", "")).strip()
                or "Analiz sonucunda modelden geçerli bir yanıt alınamadı."
            )

        def apply(response: str) -> None:
            self._show_analysis_result(response)
            self.update_status_bar("Analiz tamamlandı")

        def fail(exc: Exception) -> None:
            logger.error("Çalışma alanı analizi başarısız", exc_info=exc)
            messagebox.showerror("Hata", f"Analiz sırasında hata: {exc}")
            self.update_status_bar("Analiz başarısız")

        self._run_background(work, apply, fail)

    def _show_analysis_result(self, result_text: str):
        """Show analysis result in a beautiful scrollable dialog."""
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

        # Diyalog kapandıktan sonra gelen yanıtlar var olmayan widget'lara yazmamalı.
        closed = {"value": False}

        def _on_destroy(event):
            if event.widget is dialog:
                closed["value"] = True

        dialog.bind("<Destroy>", _on_destroy, add="+")

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
            refresh_btn.configure(state=tk.DISABLED)
            text_area.configure(state=tk.NORMAL)
            text_area.delete("1.0", tk.END)
            text_area.insert(tk.END, "🔄 Çalışma alanı analiz ediliyor... Lütfen bekleyin.\n\n", "bold")
            text_area.configure(state=tk.DISABLED)
            dialog.update()

            self.update_status_bar("Çalışma alanı yeniden analiz ediliyor...")
            content = self.workspace_editor.get_current_content()
            context = f"Bu mühendislik çalışma alanını analiz et ve öneriler sun: {content}"
            model_url = self.current_model_url
            model_name = self.current_model_name
            api_key = self._api_key_value()

            def work() -> str:
                result = single_chat_request(
                    model_url,
                    model_name,
                    context,
                    timeout=OLLAMA_CHAT_TIMEOUT,
                    api_key=api_key,
                )
                if isinstance(result, dict):
                    raise RuntimeError(result.get("error", "Modelden yanıt alınamadı"))
                return str(result).strip() or "Analiz sonucunda modelden geçerli bir yanıt alınamadı."

            def apply(new_response: str) -> None:
                if closed["value"]:
                    return
                refresh_btn.configure(state=tk.NORMAL)
                self._populate_analysis_text(text_area, new_response)
                self.update_status_bar("Yeniden analiz tamamlandı")

            def fail(exc: Exception) -> None:
                if closed["value"]:
                    return
                refresh_btn.configure(state=tk.NORMAL)
                logger.error("Yeniden analiz başarısız", exc_info=exc)
                text_area.configure(state=tk.NORMAL)
                text_area.insert(tk.END, f"\n❌ Yeniden analiz sırasında hata oluştu:\n{exc}", "bold")
                text_area.configure(state=tk.DISABLED)
                self.update_status_bar("Yeniden analiz başarısız")

            self._run_background(work, apply, fail)

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

    def _confirm_discard_changes(self, action: str) -> bool:
        """Ask what to do with unsaved edits; return False to cancel ``action``."""
        if not self.workspace_editor.is_dirty():
            return True
        answer = messagebox.askyesnocancel(
            "Kaydedilmemiş Değişiklikler",
            "Çalışma alanında kaydedilmemiş değişiklikler var.\n\n"
            f"{action} öncesinde kaydetmek ister misiniz?",
        )
        if answer is None:
            return False
        if answer:
            return self._save_workspace()
        return True

    def _on_close(self) -> None:
        """Close the application, guarding unsaved workspace content."""
        if not self._confirm_discard_changes("Çıkış"):
            return
        self.root.destroy()

    def _new_workspace(self):
        """Create new workspace."""
        if not self._confirm_discard_changes("Yeni çalışma alanı oluşturma"):
            return
        self.workspace_buffer.clear_all()
        self.workspace_editor._load_content()
        self.workspace_editor.mark_saved()
        self.update_status_bar("Yeni çalışma alanı oluşturuldu")

    def _open_workspace(self):
        """Open workspace from file."""
        file_path = filedialog.askopenfilename(
            title="Çalışma Alanını Aç",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )

        if file_path and self._confirm_discard_changes("Dosya açma"):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                if self.workspace_buffer.import_session(data):
                    self.workspace_editor._load_content()
                    # Açılan dosya temiz başlar; ilk değişiklikte kirlenir.
                    self.workspace_editor.mark_saved()
                    self.update_status_bar(f"Çalışma alanı açıldı: {file_path}")
                else:
                    messagebox.showerror("Hata", "Çalışma alanı açılamadı.")

            except Exception as e:
                messagebox.showerror("Hata", f"Dosya açılırken hata: {str(e)}")

    def _save_workspace(self) -> bool:
        """Save workspace to file; return True when the document was saved."""
        file_path = filedialog.asksaveasfilename(
            title="Çalışma Alanını Kaydet",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )

        if not file_path:
            return False
        try:
            data = self.workspace_buffer.export_session()
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            self.workspace_editor.mark_saved()
            self.update_status_bar(f"Çalışma alanı kaydedildi: {file_path}")
            return True

        except Exception as e:
            messagebox.showerror("Hata", f"Dosya kaydedilirken hata: {str(e)}")
            return False

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
        """Refresh available models off the Tk thread."""
        model_url = self.model_url_entry.get().strip()
        self.current_model_url = model_url
        api_key = self._api_key_value()

        def apply(models: List[str]) -> None:
            self.ollama_models = models
            if models:
                self.model_selection_combo.configure(state="readonly")
                self.model_selection_combo["values"] = models
                if not self.current_model_name or self.current_model_name not in models:
                    self.model_selection_combo.set(models[0])
                    self.current_model_name = models[0]
                else:
                    self.model_selection_combo.set(self.current_model_name)
                self.update_status_bar(f"Modeller yenilendi: {len(models)} model bulundu")
                self._save_settings()
            else:
                self._clear_model_list(
                    "Model sunucusundan model listesi alınamadı. URL, API anahtarı ve sunucu durumunu kontrol edin."
                )

        def fail(exc: Exception) -> None:
            logger.error("Model listesi yenilenemedi", exc_info=exc)
            self._clear_model_list("Model yenileme başarısız; bağlantıyı kontrol edin.")

        self.update_status_bar("Model listesi alınıyor...")
        self._run_background(lambda: get_available_models(model_url, api_key), apply, fail)

    def _clear_model_list(self, status_message: str) -> None:
        """Reset the model selector instead of inventing fallback models."""
        self.ollama_models = []
        self.model_selection_combo["values"] = []
        self.model_selection_combo.set("")
        self.model_selection_combo.configure(state="disabled")
        self.current_model_name = ""
        self.update_status_bar(status_message)

    def test_model_connection(self):
        """Test the Ollama connection off the Tk thread."""
        model_url = self.model_url_entry.get().strip()
        api_key = self._api_key_value()

        def apply(ok: bool) -> None:
            if ok:
                self.current_model_url = model_url
                self._save_settings()
                messagebox.showinfo("Bağlantı Başarılı", "Model sunucusuna bağlantı başarılı!")
                self.update_status_bar("Bağlantı başarılı")
            else:
                messagebox.showerror(
                    "Bağlantı Başarısız",
                    "Model sunucusuna bağlanılamadı!\n\n"
                    "Lütfen şunları kontrol edin:\n"
                    "1. Sunucunun çalıştığından emin olun (Ollama için terminalde 'ollama serve' çalışıyor mu?).\n"
                    "2. Model URL adresinin doğru olduğunu doğrulayın (varsayılan: http://localhost:11434).\n"
                    "3. Bilgisayarınızın internet/ağ bağlantısını ve güvenlik duvarı ayarlarını kontrol edin.\n"
                    "4. macOS kullanıyorsanız Sistem Ayarları > Gizlilik ve Güvenlik > Yerel Ağ iznini kontrol edin.\n"
                    "5. Sunucu API anahtarı istiyorsa API Key alanını doldurun veya MACHINING_FORMULAS_API_KEY "
                    "/ STRATA_API_KEY ortam değişkenini tanımlayın."
                )
                self.update_status_bar("Bağlantı başarısız")

        def fail(exc: Exception) -> None:
            logger.error("Bağlantı testi başarısız", exc_info=exc)
            messagebox.showerror("Hata", f"Bağlantı testi sırasında beklenmeyen hata: {exc}")
            self.update_status_bar("Bağlantı testi başarısız")

        self.update_status_bar("Bağlantı test ediliyor...")
        self._run_background(lambda: test_connection(model_url, api_key), apply, fail)

    def update_status_bar(self, message: str):
        """Update status bar message."""
        self.status_var.set(message)

    def _run_background(
        self,
        work: Callable[[], Any],
        on_success: Callable[[Any], None],
        on_error: Callable[[Exception], None],
    ) -> None:
        """Run blocking network work off the Tk thread; apply results on it.

        Tkinter widgets must only be touched from the main thread, so ``work``
        must be side-effect free and the callbacks are dispatched via
        ``root.after``.
        """

        def runner() -> None:
            try:
                result = work()
            except Exception as exc:  # noqa: BLE001 - reported through on_error
                # exc is cleared when the block exits, so bind it to the lambda.
                self.root.after(0, lambda error=exc: on_error(error))
                return
            self.root.after(0, lambda: on_success(result))

        threading.Thread(target=runner, daemon=True).start()

    def _insert_indent_at_cursor(self, event):
        """Insert a tab stop into the focused text widget."""
        try:
            event.widget.insert(tk.INSERT, "\t")
        except (AttributeError, tk.TclError):
            return None
        return "break"

    def _handle_tab_navigation(self, event):
        """Move focus forward using Tk's own traversal order."""
        return self._focus_relative(forward=True)

    def _handle_shift_tab_navigation(self, event):
        """Move focus backward using Tk's own traversal order."""
        return self._focus_relative(forward=False)

    def _focus_relative(self, forward: bool):
        """Focus the next or previous widget; return None to keep the default."""
        try:
            current = self.root.focus_get()
            if current is None:
                return None
            target = current.tk_focusNext() if forward else current.tk_focusPrev()
            if target is not None and target is not current:
                target.focus_set()
                return "break"
        except (KeyError, tk.TclError):
            pass
        return None

    def _api_key_value(self) -> str:
        """Return the API key field content (main thread only)."""
        if hasattr(self, "api_key_entry"):
            return self.api_key_entry.get().strip()
        return getattr(self, "current_api_key", "")

    def _load_settings(self) -> dict[str, str]:
        """Load settings from the per-user config file."""
        settings_file = settings_path()
        try:
            if settings_file.exists():
                with open(settings_file, "r", encoding="utf-8") as f:
                    return json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            logger.warning("Ayarlar okunamadı (%s): %s", settings_file, e)
        return {}

    def _save_settings(self):
        """Persist settings atomically in the per-user config directory."""
        settings_file = settings_path()
        try:
            settings_file.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "ollama_url": self.current_model_url,
                "model_name": self.current_model_name,
                "api_key": self._api_key_value(),
            }
            tmp_file = settings_file.with_suffix(".json.tmp")
            with open(tmp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            # Anahtar düz metin tutulduğu için dosya yalnızca sahibine okunur olsun.
            os.chmod(tmp_file, 0o600)
            os.replace(tmp_file, settings_file)
        except OSError as e:
            logger.warning("Ayarlar kaydedilemedi (%s): %s", settings_file, e)
            self.update_status_bar("Ayarlar kaydedilemedi; ayrıntılar için loglara bakın.")

    def _on_model_selection_change(self, event=None):
        """Handle model combobox selection change."""
        self.current_model_name = self.model_selection_combo.get().strip()
        self._save_settings()

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
    logging.basicConfig(level=logging.WARNING)
    try:
        root = tk.Tk()

        tooltips: Dict[str, str] = {}
        try:
            p = asset_path("tooltips.json")
            if p.exists():
                with open(p, "r", encoding="utf-8") as f:
                    tooltips = json.load(f)
        except (OSError, json.JSONDecodeError):
            tooltips = {}

        app = V3Calculator(root, tooltips)
        root.mainloop()

    except Exception:
        logger.exception("V3 GUI başlatma hatası")


if __name__ == "__main__":
    main()
