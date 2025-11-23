#! .venv/bin/python
# -*- coding : utf-8 -*-# # Standard Python encoding declaration.
# Autor:Hakan KILIÇASLAN 2025 # Author and year.
# flake8: noqa

# --- Constants for Calculation Definitions ---
# MATERIAL_CALCS is kept for 'Kütle Hesabı' (Mass Calculation) which has unique handling for shapes.
# TURNING_CALCS and MILLING_CALCS are removed as their parameter definitions
# will now be sourced directly from EngineeringCalculator.

import logging
import copy
import requests  # For making HTTP requests to the Ollama API.
# Regular expressions, possibly for text processing or input validation.
import re
import os  # Potentially for path operations (though not explicitly used here).
import json  # For loading tooltips from a JSON file.
from pathlib import Path
# Core calculation logic.
from engineering_calculator import EngineeringCalculator
from tkinter import ttk, messagebox, scrolledtext, filedialog
import tkinter as tk

from execute_mode import ExecuteModeMixin
from material_utils import MaterialMassParameters, prepare_material_mass_arguments
from ollama_utils import (
    build_calculator_tools_definition,
    candidate_chat_urls,
    candidate_tags_urls,
    prepare_legacy_chat_payload,
)
MATERIAL_CALCS = {
    'Kütle Hesabı': {  # Turkish: "Mass Calculation"
        # 'params' and 'units' for Kütle Hesabı are handled dynamically by _update_material_params
        # based on shape selection and EngineeringCalculator.get_shape_parameters().
        # This entry mainly serves to list "Kütle Hesabı" under "Malzeme Hesaplamaları".
    }
}

DEFAULT_WINDOW_SIZE: tuple[int, int] = (1200, 800)
SUPPORTED_PROMPT_ATTACHMENT_EXTENSIONS: set[str] = {
    ".txt",
    ".md",
    ".py",
    ".c",
    ".cpp",
}

# TURNING_CALCS and MILLING_CALCS are now removed.
# The UI will populate calculation names (keys) for Turning and Milling
# directly from ec.turning_definitions.keys() and ec.milling_definitions.keys().
# Parameter details (name, unit, display_text_turkish) for each calculation
# will be fetched using ec.get_calculation_params().


# --- Standard Library and Third-Party Imports ---


# --- Global Instance ---
# Create a single instance of the EngineeringCalculator to be used by the GUI.
ec = EngineeringCalculator()


# --- GUI Helper Classes ---
class AdvancedToolTip:
    """
    Creates a tooltip for a given Tkinter widget that appears after a delay.

    Attributes:
        widget: The Tkinter widget this tooltip is associated with.
        text (str): The text to display in the tooltip.
        delay (float): Time in seconds before the tooltip appears.
        background (str): Background color of the tooltip.
        foreground (str): Text color of the tooltip.
        font (tuple): Font configuration for the tooltip text.
        tooltip (tk.Toplevel | None): The Toplevel window used for the tooltip, or None if not visible.
        id (str | None): The ID of the scheduled `after` event for showing the tooltip.
    """

    def __init__(self, widget: tk.Widget, text: str = '', delay: float = 0.5,
                 background: str = '#ffffe0', foreground: str = 'black',
                 font: tuple = ('tahoma', 8, 'normal')):
        """
        Initializes the AdvancedToolTip.

        Args:
            widget: The widget to attach the tooltip to.
            text: The string to display in the tooltip.
            delay: The delay in seconds before the tooltip is shown on mouse hover.
            background: The background color of the tooltip window.
            foreground: The text color within the tooltip.
            font: The font used for the tooltip's text.
        """
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
        # Hide tooltip on button click as well.
        self.widget.bind('<Button>', self.leave)

    def enter(self, event=None):
        """Schedules the tooltip to appear when the mouse enters the widget."""
        self.schedule()

    def leave(self, event=None):
        """Unschedules and hides the tooltip when the mouse leaves the widget."""
        self.unschedule()
        self.hide()

    def schedule(self):
        """Schedules the `show` method to be called after `self.delay` milliseconds."""
        self.unschedule()  # Cancel any existing schedules.
        self.id = self.widget.after(int(self.delay * 1000), self.show)

    def unschedule(self):
        """Unschedules the näyttäminen of the tooltip if it's currently scheduled."""
        if self.id:
            self.widget.after_cancel(self.id)
            self.id = None

    def show(self):
        """Displays the tooltip window near the widget."""
        if self.tooltip:  # If tooltip is already shown, do nothing.
            return

        # Calculate tooltip position safely without relying on bbox (not supported by all widgets)
        try:
            x = self.widget.winfo_rootx() + 20
            y = self.widget.winfo_rooty() + self.widget.winfo_height() + 10
        except Exception:
            x, y = 100, 100

        # Create a Toplevel window for the tooltip.
        self.tooltip = tk.Toplevel(self.widget)
        # Remove window decorations (border, title bar).
        self.tooltip.wm_overrideredirect(True)

        # Create a label within the Toplevel to display the tooltip text.
        label = tk.Label(self.tooltip, text=self.text,
                         justify='left',
                         background=self.background,
                         foreground=self.foreground,
                         font=self.font,
                         relief='solid',  # Add a border to the tooltip.
                         borderwidth=1)
        label.pack()

        self.tooltip.wm_geometry(f"+{x}+{y}")  # Position the tooltip window.

    def hide(self):
        """Hides and destroys the tooltip window."""
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None


def load_tooltips(file_path: str) -> dict:
    """
    Loads tooltip data from a JSON file.

    Args:
        file_path (str): The path to the JSON file containing tooltip definitions.

    Returns:
        dict: A dictionary where keys are identifiers and values are tooltip texts.
              Returns an empty dictionary if the file is not found or is invalid.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"Warning: Tooltip file not found at {file_path}")
        return {}
    except json.JSONDecodeError:
        print(f"Warning: Could not decode JSON from tooltip file: {file_path}")
        return {}


class AdvancedCalculator(ExecuteModeMixin):
    """
    Main class for the Advanced Engineering Calculator GUI.

    This class sets up the Tkinter interface, handles user input,
    interacts with the `EngineeringCalculator` for performing calculations,
    and displays the results.

    Attributes:
        root (tk.Tk): The main Tkinter window.
        tooltips (dict): Tooltip texts loaded from an external file.
        calc_types (dict): Defines the structure of available calculation types and their specific calculations.
        main_frame (ttk.Frame): The primary container frame for all UI elements.
        left_frame (ttk.Frame): Frame for input controls (calculation type, parameters).
        right_frame (ttk.Frame): Frame for displaying results.
        result_text (scrolledtext.ScrolledText): Text area for showing calculation details and results.
        input_fields (dict): Stores Tkinter Entry widgets for dynamic parameter inputs.
                             Keys are parameter names (Turkish), values are Entry widgets.
        reverse_shape_names (dict): Maps Turkish shape names back to their internal keys (e.g., "Üçgen": "triangle").
                                    Populated dynamically.
        params_container (ttk.Frame): A sub-frame within `left_frame` to hold dynamically generated parameter fields.
        shape_combo (ttk.Combobox | None): Combobox for selecting shapes in material calculations. Initialized when needed.
        execute_mode (bool): Flag to enable/disable a special code execution mode in the results area.
    """

    def __init__(self, root: tk.Tk, tooltips: dict):
        """
        Initializes the AdvancedCalculator GUI.

        Sets up the main window, frames, widgets for selecting calculation types,
        parameter input areas, and the result display area.

        Args:
            root (tk.Tk): The root Tkinter window for the application.
            tooltips (dict): A dictionary containing tooltip strings for UI elements.
        """
        super().__init__()  # Though not inheriting from a specific base class here, good practice if refactored.

        self.root = root
        self.tooltips = tooltips
        # Turkish: Engineering Calculations and Analysis Application
        self.root.title("Mühendislik Hesaplamaları ve Analiz Uygulaması")
        default_width, default_height = DEFAULT_WINDOW_SIZE
        # Set initial window size.
        self.root.geometry(f"{default_width}x{default_height}")

        # --- Styling ---
        style = ttk.Style()
        # Custom style for frames.
        style.configure('Calc.TFrame', background='#f0f0f0')
        # Custom style for labels.
        style.configure('Calc.TLabel', background='#f0f0f0',
                        font=('Arial', 10))
        # Custom style for buttons.
        style.configure('Calc.TButton', font=('Arial', 10))

        # --- Main Layout Frames ---
        self.main_frame = ttk.Frame(root, style='Calc.TFrame')
        self.main_frame.pack(side='top', fill='both',
                             expand=True, padx=10, pady=10)

        # Left frame for input controls
        self.left_frame = ttk.Frame(self.main_frame, style='Calc.TFrame')
        self.left_frame.pack(side='left', fill='y', padx=5)

        # Right frame for results
        self.right_frame = ttk.Frame(self.main_frame)  # Default style
        self.right_frame.pack(side='right', fill='both', expand=True, padx=5)

        # --- Static UI Elements in Left Frame ---
        # Populate calculation types. Turning and Milling calculation names (keys)
        # are fetched directly from the EngineeringCalculator instance.
        # The empty dictionaries {} as values are placeholders; actual parameter details
        # will be fetched on demand by `update_input_fields` using `ec.get_calculation_params`.
        self.calc_types = {
            'Malzeme Hesaplamaları': MATERIAL_CALCS,  # Turkish: "Material Calculations"
            # Turkish: "Turning Calculations"
            'Tornalama Hesaplamaları': {key: {} for key in ec.turning_definitions.keys()},
            # Turkish: "Milling Calculations"
            'Frezeleme Hesaplamaları': {key: {} for key in ec.milling_definitions.keys()}
        }

        ttk.Label(self.left_frame, text="Hesaplama Türü:", style='Calc.TLabel').pack(
            pady=(5, 0), anchor='w')  # Turkish: "Calculation Type:"
        self.calc_type = ttk.Combobox(self.left_frame, values=list(
            self.calc_types.keys()), state="readonly")
        self.calc_type.pack(fill='x', pady=(0, 10))
        AdvancedToolTip(self.calc_type, self.tooltips.get(
            # Turkish: "Select a calculation type."
            "HesaplamaTuru", "Bir hesaplama türü seçin."))
        self.calc_type.bind('<<ComboboxSelected>>',
                            self.update_calculations)  # Event binding

        ttk.Label(self.left_frame, text="Hesaplama Seçimi:", style='Calc.TLabel').pack(
            pady=(5, 0), anchor='w')  # Turkish: "Calculation Selection:"
        self.calculation = ttk.Combobox(self.left_frame, state="readonly")
        self.calculation.pack(fill='x', pady=(0, 10))
        AdvancedToolTip(self.calculation, self.tooltips.get(
            "HesaplamaSecimi", "Bir hesaplama seçin."))  # Turkish: "Select a calculation."
        # Note: self.calculation.bind is set in update_calculations

        # Frame to hold dynamically generated parameter input fields
        self.params_frame = ttk.Frame(self.left_frame, style='Calc.TFrame')
        self.params_frame.pack(fill='x', pady=5)
        # Inner container for parameters
        self.params_container = ttk.Frame(
            self.params_frame, style='Calc.TFrame')
        self.params_container.pack(fill='x', expand=True)

        # --- Result Display Area in Right Frame ---
        self.result_text = scrolledtext.ScrolledText(self.right_frame, wrap=tk.WORD,
                                                     width=80, height=35,  # Adjusted size
                                                     # Using Courier for code-like display
                                                     font=('Courier New', 11))
        self.result_text.pack(fill='both', expand=True)
        # Initial content or placeholder for the results area
        # Turkish: Calculation Results and Details. Your calculation results will be displayed here.
        self.result_text.insert(
            tk.END, "# Hesaplama Sonuçları ve Detayları\n\nBurada hesaplama sonuçlarınız gösterilecektir.\n")

        # --- Status Bar ---
        self.status_var = tk.StringVar(value="Hazır")
        self.status_frame = ttk.Frame(root, style='Calc.TFrame')
        self.status_frame.pack(side='bottom', fill='x')
        self.status_label = ttk.Label(
            self.status_frame,
            textvariable=self.status_var,
            style='Calc.TLabel',
            anchor='w'
        )
        self.status_label.pack(fill='x', padx=5, pady=(0, 5))

        # --- Global Key Bindings ---
        # Enable code execution mode
        self.root.bind('<Control-e>', self.enable_execute_mode)
        # Execute selected code
        self.root.bind('<Control-c>', self.execute_calculation)

        # --- Calculate Button ---
        self.calculate_button = ttk.Button(self.left_frame, text="HESAPLA",
                                           command=self.calculate, style='Calc.TButton')  # Turkish: "CALCULATE"
        self.calculate_button.pack(
            pady=10, fill='x', ipady=5)  # Adjusted padding
        AdvancedToolTip(self.calculate_button, self.tooltips.get(
            # Turkish: "Perform the selected calculation."
            "HesaplaButonu", "Seçili hesaplamayı gerçekleştir."))

        # --- Separator ---
        ttk.Separator(self.left_frame, orient='horizontal').pack(
            fill='x', pady=10)

        # --- LLM Interaction UI Elements ---
        llm_frame = ttk.Frame(self.left_frame, style='Calc.TFrame')
        llm_frame.pack(fill='both', pady=5, expand=True)

        # Model URL
        ttk.Label(llm_frame, text="Model URL:", style='Calc.TLabel').pack(
            pady=(5, 0), anchor='w')
        self.model_url_entry = ttk.Entry(llm_frame)
        self.model_url_entry.pack(fill='x', pady=(0, 5))
        # Unified default: Ollama chat endpoint on localhost
        self.model_url_entry.insert(0, "http://192.168.1.14:11434/v1/chat")
        AdvancedToolTip(self.model_url_entry, self.tooltips.get(
            "ModelURL", "Kullanılacak Ollama modelinin URL'si."))

        # Model Selection
        ttk.Label(llm_frame, text="Model Seçin:",
                  style='Calc.TLabel').pack(pady=(5, 0), anchor='w')
        self.model_selection_combo = ttk.Combobox(llm_frame, state="readonly")
        self.model_selection_combo.pack(fill='x', pady=(0, 5))
        # Model list is populated dynamically from Ollama /api/tags with graceful fallback
        self.model_selection_combo['values'] = []
        # We'll attempt to fetch models after widgets are set
        AdvancedToolTip(self.model_selection_combo, self.tooltips.get(
            "ModelSecimi", "Kullanılacak LLM modelini seçin."))
        # Reset conversation when model changes
        self.model_selection_combo.bind(
            '<<ComboboxSelected>>', self.on_model_change)

        # Chat Prompt Input
        ttk.Label(llm_frame, text="Soru / Prompt:",
                  style='Calc.TLabel').pack(pady=(5, 0), anchor='w')
        self.chat_prompt_text = scrolledtext.ScrolledText(
            llm_frame, wrap=tk.WORD, height=5, font=('Arial', 10))
        self.chat_prompt_text.pack(fill='both', expand=True, pady=(0, 5))
        AdvancedToolTip(self.chat_prompt_text, self.tooltips.get(
            "ChatPrompt", "Modele göndermek istediğiniz soru veya komut."))

        # Attachment and Send Buttons
        button_row = ttk.Frame(llm_frame, style='Calc.TFrame')
        button_row.pack(fill='x', pady=10)

        self.attach_prompt_button = ttk.Button(
            button_row,
            text="Dosya Ekle",
            command=self.attach_file_to_prompt,
            style='Calc.TButton'
        )
        self.attach_prompt_button.pack(
            side='left', fill='x', expand=True, padx=(0, 5), ipady=5)
        AdvancedToolTip(self.attach_prompt_button, self.tooltips.get(
            "DosyaEkleButonu", "Desteklenen dosyaları prompt alanına ekleyin."))

        self.send_prompt_button = ttk.Button(
            button_row,
            text="Gönder",
            command=self.send_prompt_to_model,
            style='Calc.TButton'
        )
        self.send_prompt_button.pack(
            side='left', fill='x', expand=True, ipady=5)
        AdvancedToolTip(self.send_prompt_button, self.tooltips.get(
            "GonderButonu", "Soruyu modele gönder."))

        # Track current model/chat session state
        self.current_model_name = None
        self.current_chat_url = None
        self.reset_history_next_prompt = False
        # Also consider URL changes as a reset signal
        self.model_url_entry.bind('<FocusOut>', self.on_model_url_change)
        self.model_url_entry.bind('<Return>', self.on_model_url_change)
        # --- Conversation History (structured) ---
        # Holds list of {role: 'user'|'assistant'|'tool', content: str, ...}
        # System mesajı, her istekte başa eklenir; bu listede tutulmaz.
        self.history = []
        self.force_legacy_chat = False
        self.legacy_notice_shown = False
        self.debug_show_raw_model_responses = False
        self._last_tool_run_details: dict | None = None
        self._tool_loop_limit: int = 4

        # --- Initialize dynamic fields ---
        self.input_fields = {}
        self.reverse_shape_names = {}
        self.shape_combo = None  # Will be created in update_input_fields if needed

        # Initialize first calculation type
        if list(self.calc_types.keys()):
            self.calc_type.set(list(self.calc_types.keys())[0])
            self.update_calculations()

        # Try to fetch available models now
        try:
            self.refresh_model_list()
        except Exception:
            # Fallback to a small static list if fetch fails
            self.ollama_models = ["gemma3:1b-it-qat", "qwen2.5", "gemma2"]
            self.model_selection_combo['values'] = self.ollama_models
            if self.ollama_models:
                self.model_selection_combo.set(self.ollama_models[0])

        # Ensure target geometry is applied after widgets are realized
        self.root.after(0, self._apply_default_geometry)

    def send_prompt_to_model(self):
        """
        Handles sending the prompt from chat_prompt_text to the selected LLM.
        For now, it just displays the intended action and user prompt in the result_text.
        Actual model communication will be implemented in backend logic.
        """
        model_url = self.model_url_entry.get()
        selected_model = self.model_selection_combo.get()
        user_prompt = self.chat_prompt_text.get("1.0", tk.END).strip()

        if not model_url or not selected_model or not user_prompt:
            messagebox.showwarning(
                "Eksik Bilgi", "Lütfen Model URL, Model ve Prompt girdiğinizden emin olun.")
            return

        # Add user's prompt to the shared workspace (result_text)
        self.add_to_workspace("Kullanıcı", user_prompt)

        # Actual backend call
        self.call_ollama_api(model_url, selected_model, user_prompt)

        # Clear the prompt input area
        self.chat_prompt_text.delete("1.0", tk.END)

    def attach_file_to_prompt(self) -> None:
        """Allow the user to attach supported files and append their contents to the prompt area."""
        filetypes = [
            ("Desteklenen Dosyalar", "*.txt *.md *.py *.c *.cpp"),
            ("Metin Dosyaları", "*.txt"),
            ("Markdown Dosyaları", "*.md"),
            ("Python Dosyaları", "*.py"),
            ("C Kaynak Dosyaları", "*.c"),
            ("C++ Kaynak Dosyaları", "*.cpp"),
            ("Tüm Dosyalar", "*.*"),
        ]

        try:
            selected_files = filedialog.askopenfilenames(
                parent=self.root,
                title="Dosya Seç",
                filetypes=filetypes
            )
        except Exception as exc:  # pragma: no cover - GUI error path
            logging.exception("Dosya seçim penceresi açılamadı: %s", exc)
            messagebox.showerror(
                "Dosya Seçimi", "Dosya seçme işlemi başlatılamadı.")
            return

        if not selected_files:
            return

        appended_files: list[str] = []
        skipped_files: list[str] = []
        prepend_separator = bool(
            self.chat_prompt_text.get("1.0", tk.END).strip())

        for file_path in selected_files:
            path_obj = Path(file_path)
            extension = path_obj.suffix.lower()

            if extension not in SUPPORTED_PROMPT_ATTACHMENT_EXTENSIONS:
                skipped_files.append(path_obj.name)
                continue

            try:
                with open(file_path, "r", encoding="utf-8") as file_handle:
                    file_content = file_handle.read()
            except UnicodeDecodeError:
                try:
                    with open(file_path, "r", encoding="utf-8", errors="replace") as file_handle:
                        file_content = file_handle.read()
                except OSError as exc:
                    logging.exception(
                        "Dosya okuma hatası (%s): %s", file_path, exc)
                    skipped_files.append(path_obj.name)
                    continue
            except OSError as exc:
                logging.exception("Dosya açılamadı (%s): %s", file_path, exc)
                skipped_files.append(path_obj.name)
                continue

            separator = "\n\n" if (prepend_separator or appended_files) else ""
            snippet_header = f"{separator}# Dosya: {path_obj.name}\n"
            self.chat_prompt_text.insert(tk.END, snippet_header + file_content)
            appended_files.append(path_obj.name)
            prepend_separator = True

        if appended_files:
            self.chat_prompt_text.see(tk.END)
            self.chat_prompt_text.focus_set()
            appended_summary = ", ".join(appended_files)
            self.update_status_bar(f"Eklenen dosya(lar): {appended_summary}")

        if skipped_files:
            skipped_summary = ", ".join(skipped_files)
            messagebox.showwarning(
                "Dosya Atlandı",
                "Desteklenmeyen veya okunamayan dosyalar atlandı: "
                f"{skipped_summary}."
            )

    def _get_exec_mode_calculator(self):
        """Provide calculator instance for ExecuteModeMixin."""
        return ec

    def get_conversation_history(self) -> list[dict]:
        """
        Yapılandırılmış konuşma geçmişini döndürür.
        Not: Sistem mesajı bu listede tutulmaz; her istekte başa ayrıca eklenir.
        """
        return list(self.history)

    def _notify_legacy_mode(self, message: str | None = None) -> None:
        """Inform the user that legacy Ollama endpoints are being used."""
        default_message = (
            "Sunucu eski Ollama API uç noktalarını kullanıyor. "
            "İstekler otomatik olarak uyumlandı."
        )
        notice = message or default_message
        logging.info("Legacy mode notice: %s", notice)
        self.update_status_bar(notice)
        if not self.legacy_notice_shown:
            self.add_to_workspace("Sistem", notice)
        self.legacy_notice_shown = True

    def _handle_legacy_transition(
        self,
        failed_url: str,
        next_url: str
    ) -> bool:
        """Handle transitions from /v1 to legacy /api endpoints."""
        if not next_url or "/api/" not in next_url:
            return False
        if "/v1/" not in failed_url:
            return False

        self.force_legacy_chat = True
        self._notify_legacy_mode()
        return True

    def _debug_log_raw_response(
        self,
        label: str,
        payload: dict | list | str
    ) -> None:
        """Log raw model responses without exposing them in the UI."""
        try:
            formatted = json.dumps(payload, indent=2, ensure_ascii=False)
        except (TypeError, ValueError):
            formatted = str(payload)
        logging.debug("%s: %s", label, formatted)
        if self.debug_show_raw_model_responses:
            self.add_to_workspace(label, formatted)

    def _extract_tool_calls_from_content(self, content: str | None) -> list[dict] | None:
        """Attempt to extract tool call array embedded in assistant content."""
        if not content or not isinstance(content, str):
            return None

        text = content.strip()
        # Handle fenced code blocks like ```json [...] ```
        fence_match = re.search(r"```(?:json)?\s*(\[[\s\S]*?\])\s*```", text)
        candidate_json = fence_match.group(1) if fence_match else None

        if not candidate_json:
            bracket_match = re.search(
                r"\[(?:\s|\S)*?\{\s*\"type\"\s*:\s*\"function\"(?:.|\n)*?\]\s*",
                text
            )
            candidate_json = bracket_match.group(0) if bracket_match else None

        if not candidate_json:
            return None

        try:
            parsed = json.loads(candidate_json)
        except Exception:
            return None

        if isinstance(parsed, list):
            return parsed
        return None

    def _build_tool_error_message(self) -> str:
        """Create a fallback summary when tools fail to produce a result."""

        details = self._last_tool_run_details or {}
        if details.get("successful"):
            success_message = self._build_tool_success_message()
            if success_message:
                return success_message

        error_messages = details.get("errors") or []
        if not error_messages:
            return "Modelden içerik alınamadı."

        unique_errors = list(dict.fromkeys(error_messages))

        missing_params: list[str] = []
        for err in unique_errors:
            if "parametre" not in err:
                continue
            match = re.search(r"'([^']+)'\s*\([^)]*\)\s*parametresi", err)
            if match:
                missing_params.append(match.group(1))
                continue
            marker = "' parametresi"
            if "'" in err and marker in err:
                start = err.find("'")
                end = err.find("'", start + 1)
                if start != -1 and end != -1 and end > start + 1:
                    missing_params.append(err[start + 1:end])

        lines = [
            "Model, araç çağrılarını çalıştırırken hatalarla karşılaştı ve "
            "nihai yanıt üretemedi.",
            "Son hata mesajları:",
        ]

        for err in unique_errors[-3:]:
            lines.append(f"- {err}")

        if missing_params:
            unique_params = ", ".join(dict.fromkeys(missing_params))
            lines.append(
                f"Eksik parametreleri sağlayıp tekrar deneyin: {unique_params}."
            )
        else:
            lines.append(
                "Lütfen girdileri kontrol ederek gerekli tüm değerleri "
                "ekleyin."
            )

        return "\n".join(lines)

    def _build_tool_success_message(self) -> str:
        """Create a user-facing summary when tool executions succeed."""

        details = self._last_tool_run_details or {}
        if not details.get("successful"):
            return ""

        tool_calls = {call.get("id"): call
                      for call in details.get("tool_calls") or []}
        tool_results = details.get("results") or []
        if not tool_results:
            return ""

        lines: list[str] = ["Araç sonuçları başarıyla alındı:"]

        for entry in tool_results:
            content = (entry.get("content") or "").strip()
            if not content:
                continue

            call_id = entry.get("tool_call_id")
            function_name = None
            if call_id and call_id in tool_calls:
                function_name = (
                    tool_calls[call_id]
                    .get("function", {})
                    .get("name")
                )

            label_prefix = ""
            if function_name:
                label_prefix = f"{function_name}: "

            gram_match = re.search(
                r"(-?\d+(?:[\.,]\d+)?)\s*gram\b", content, re.IGNORECASE
            )
            if gram_match:
                try:
                    grams = float(gram_match.group(1).replace(',', '.'))
                    kilograms = grams / 1000.0
                    content = f"{grams:.2f} g ({kilograms:.3f} kg)"
                except ValueError:
                    # If conversion fails, keep original content
                    pass

            lines.append(f"- {label_prefix}{content}")

        if len(lines) == 1:
            return ""

        return "\n".join(lines)

    def _process_assistant_message(
        self,
        model_url: str,
        model_name: str,
        tools_definition: list,
        messages_history: list,
        assistant_message: dict
    ) -> None:
        """Process assistant response, executing tool calls until final content."""

        pending_message = assistant_message or {}
        history_for_next_turn = list(messages_history)
        tool_loop_count = 0
        loop_limit = getattr(self, "_tool_loop_limit", 4)

        while True:
            tool_calls_payload = pending_message.get("tool_calls")
            parsed_from_content = None
            if not tool_calls_payload:
                parsed_from_content = self._extract_tool_calls_from_content(
                    pending_message.get("content")
                )

            active_tool_calls = tool_calls_payload or parsed_from_content

            if active_tool_calls:
                tool_loop_count += 1
                if tool_loop_count > max(1, loop_limit):
                    fallback_message = self._build_tool_error_message()
                    self.add_to_workspace("Model", fallback_message)
                    self.history.append({
                        "role": "assistant",
                        "content": fallback_message
                    })
                    break

                if tool_calls_payload:
                    self.add_to_workspace(
                        "Model", "Bir araç kullanmak istiyor...")
                else:
                    self.add_to_workspace(
                        "Model",
                        "İçerikte gömülü tool çağrıları bulundu, işleniyor..."
                    )

                self.history.append({
                    "role": "assistant",
                    "content": "",
                    "tool_calls": active_tool_calls
                })

                pending_message, history_for_next_turn = self.handle_tool_calls(
                    model_url,
                    model_name,
                    history_for_next_turn,
                    active_tool_calls,
                    tools_definition
                )
                pending_message = pending_message or {}
                continue

            content_final = (pending_message.get("content") or "").strip()
            if not content_final:
                content_final = self._build_tool_error_message()

            self.add_to_workspace("Model", content_final)
            self.history.append(
                {"role": "assistant", "content": content_final})

            preview = content_final.replace("\n", " ").strip()
            if preview:
                truncated = preview[:140]
                if len(preview) > 140:
                    truncated = f"{truncated}…"
                self.update_status_bar(f"Model: {truncated}")
            else:
                self.update_status_bar("Model yanıtı alındı")
            break

    def _post_chat_with_legacy_support(
        self,
        url_candidates: list[str],
        payload: dict,
        headers: dict,
        timeout: int = 120
    ) -> tuple[requests.Response, str, bool]:
        """Send chat request, retrying with legacy payload if needed."""

        candidate_list = list(url_candidates)
        if self.force_legacy_chat:
            candidate_list = sorted(
                candidate_list,
                key=lambda u: 0 if "/api/" in u else 1
            )

        def _perform_request(
            active_payload: dict
        ) -> tuple[requests.Response, str]:
            return self._request_with_fallback(
                "post",
                candidate_list,
                json=active_payload,
                headers=headers,
                timeout=timeout
            )

        if self.force_legacy_chat:
            legacy_payload = prepare_legacy_chat_payload(payload)
            response, used_url = _perform_request(legacy_payload)
            return response, used_url, "/api/chat" in used_url

        try:
            response, used_url = _perform_request(payload)
            legacy_endpoint = "/api/chat" in used_url
            if legacy_endpoint:
                self.force_legacy_chat = True
                self._notify_legacy_mode()
            return response, used_url, legacy_endpoint
        except requests.exceptions.HTTPError as exc:
            response_obj = getattr(exc, "response", None)
            response_url = getattr(response_obj, "url", "") or ""
            status_code = getattr(response_obj, "status_code", None)

            if status_code == 400 and "/api/chat" in response_url:
                legacy_payload = prepare_legacy_chat_payload(payload)
                self.force_legacy_chat = True
                self._notify_legacy_mode(
                    "Sunucu eski Ollama sohbet API'sini kullanıyor. "
                    "Tool çağrıları metin tabanlı moda geçirildi."
                )
                candidate_list = sorted(
                    candidate_list,
                    key=lambda u: 0 if "/api/" in u else 1
                )
                response, used_url = _perform_request(legacy_payload)
                return response, used_url, True

            raise

    def _request_with_fallback(self, method: str,
                               url_candidates: list[str], **kwargs):
        """Try each URL until one succeeds.

        Falls back to legacy endpoints when needed.
        """
        if not url_candidates:
            raise ValueError("En az bir URL adayı olmalı")

        fallback_status_codes = {404, 405, 501}
        last_exception: requests.exceptions.RequestException | None = None

        for idx, candidate in enumerate(url_candidates):
            try:
                response = requests.request(method, candidate, **kwargs)
            except requests.exceptions.RequestException as exc:
                last_exception = exc
                if idx + 1 < len(url_candidates):
                    next_url = url_candidates[idx + 1]
                    handled = self._handle_legacy_transition(
                        candidate,
                        next_url
                    )
                    warning_msg = (
                        f"{candidate} isteği başarısız ({exc}). "
                        f"Alternatif uç nokta deneniyor: {next_url}"
                    )
                    if handled:
                        logging.info(
                            "Legacy fallback sonrası istek yeniden "
                            "deneniyor: %s",
                            next_url
                        )
                    else:
                        self.add_to_workspace("Sistem Uyarısı", warning_msg)
                    continue
                raise

            status_code = response.status_code
            if (status_code in fallback_status_codes and
                    idx + 1 < len(url_candidates)):
                next_url = url_candidates[idx + 1]
                handled = self._handle_legacy_transition(
                    candidate,
                    next_url
                )
                warning_msg = (
                    f"{candidate} {status_code} döndürdü. "
                    f"Alternatif uç nokta deneniyor: {next_url}"
                )
                if handled:
                    logging.info(
                        "Legacy fallback %s -> %s, kod: %s",
                        candidate,
                        next_url,
                        status_code
                    )
                else:
                    self.add_to_workspace("Sistem Uyarısı", warning_msg)
                last_exception = requests.exceptions.HTTPError(
                    response=response
                )
                continue

            try:
                response.raise_for_status()
            except requests.exceptions.HTTPError as exc:
                last_exception = exc
                if idx + 1 < len(url_candidates):
                    next_url = url_candidates[idx + 1]
                    handled = self._handle_legacy_transition(
                        candidate,
                        next_url
                    )
                    warning_msg = (
                        f"{candidate} isteği başarısız ({exc}). "
                        f"Alternatif uç nokta deneniyor: {next_url}"
                    )
                    if handled:
                        logging.info(
                            "Legacy fallback (HTTPError) %s -> %s",
                            candidate,
                            next_url
                        )
                    else:
                        self.add_to_workspace("Sistem Uyarısı", warning_msg)
                    continue
                raise

            return response, candidate.rstrip('/')

        if last_exception:
            raise last_exception
        raise requests.exceptions.RequestException(
            "Ulaşılabilir Ollama uç noktası bulunamadı"
        )

    def refresh_model_list(self):
        """Fetch available Ollama models via /api/tags and populate the combobox with fallback."""
        tags_candidates = candidate_tags_urls(
            self.model_url_entry.get()
        )
        try:
            resp, used_tags_url = self._request_with_fallback(
                "get", tags_candidates, timeout=120
            )
            data = resp.json()
            models = []
            # Ollama returns {"models": [{"name": "llama3:8b", ...}, ...]}
            if isinstance(data, dict):
                items = data.get("models") or data.get("data") or []
                for m in items:
                    # Prefer 'name', fallback to 'model'
                    name = m.get("name") or m.get("model")
                    if isinstance(name, str):
                        models.append(name)
            # Fallback if parsing failed
            if not models:
                models = ["llama3.1", "qwen2.5", "gemma2"]
                self.add_to_workspace(
                    "Sistem Uyarısı",
                    "Model listesi alınamadı, varsayılan liste kullanılacak."
                )
            self.ollama_models = models
            self.model_selection_combo['values'] = self.ollama_models
            if (self.ollama_models and
                    self.model_selection_combo.get() not in self.ollama_models):
                self.model_selection_combo.set(self.ollama_models[0])
            if used_tags_url != tags_candidates[0]:
                info_msg = (
                    "Model listesi eski API uç noktasından alındı: "
                    f"{used_tags_url}"
                )
                self.update_status_bar(info_msg)
        except (requests.exceptions.RequestException,
                json.JSONDecodeError) as e:
            # Network or server error: fallback
            self.ollama_models = ["llama3.1", "qwen2.5", "gemma2"]
            self.model_selection_combo['values'] = self.ollama_models
            if (self.ollama_models and
                    self.model_selection_combo.get() not in self.ollama_models):
                self.model_selection_combo.set(self.ollama_models[0])
            warning_msg = (
                f"Model listesi alınamadı ({e}). Varsayılan liste kullanılıyor."
            )
            self.add_to_workspace("Sistem Uyarısı", warning_msg)

    def _build_system_message(self) -> dict:
        try:
            shapes_map = ec.get_available_shapes()
        except Exception:
            shapes_map = {}
        shapes_list = ", ".join(
            [f"{key} (TR: {value})" for key, value in shapes_map.items()]
        )

        try:
            densities = ec.material_density
        except Exception:
            densities = {}
        dens_list = ", ".join(
            [f"{name}: {val} g/cm³" for name, val in densities.items()]
        )

        system_instructions = f"""
Sen bir mühendislik hesaplama asistanısın. Kullanıcı isteklerini yanıtlamak için sana verilen araçları (tool) kullan.

Kritik kurallar (uygulamak ZORUNLU):
- Bir hesaplama istendiğinde, uygun aracı çağır ve ilk mesajında SADECE tool_calls döndür. Serbest metin yazma.
- Araç fonksiyon adlarını ve parametre isimlerini, araç tanımında (tools) verildiği şekilde birebir aynı kullan.
- Gerekli parametrelerin hepsini sağla, fazladan parametre yollama.
- Birimlere dikkat et: uzunluklar mm, yoğunluk g/cm³. Kütle aracı gram döndürür; nihai mesajında gr ve kg olarak sun.
- Bulunduğun ortam tool_calls özelliğini desteklemiyorsa, ilk cevabında sadece JSON formatında bir `tool_calls` dizisi yaz. Örnek:
    [
        {{
            "type": "function",
            "function": {{
                "name": "...",
                "arguments": {{...}}
            }}
        }}
    ]
    Hiç serbest metin ekleme.

Şekil ve malzeme ipuçları:
- Geçerli şekiller: {shapes_list}
- Türkçe→shape_key eşleştirme örnekleri: "yuvarlak"/"daire"→circle, "kare"→square, "dikdörtgen"→rectangle.
- "çap" verildiyse yarıçap = çap/2. circle için parametre adı radius olmalı.
- Malzeme yoğunluğu verilmemişse, bilinen Türkçe adıyla eşleştir: {dens_list}
  Örn: Çelik=7.85, Alüminyum=2.70 (g/cm³).

Cevaplama akışı:
1) Gerekliyse uygun aracı tool_calls ile çağır.
2) Tool sonucu geldikten sonra nihai Türkçe cevabı yaz; hem g hem kg göster (ör. 4712.39 g (4.712 kg)).

Örnek 1 (kütle hesabı):
Kullanıcı: "Çapı 100 mm olan yuvarlak çelik malzeme, boy 100 mm; ağırlığı?"
assistant (tool_calls): [{{"type":"function","function":{{"name":"calculate_material_mass","arguments":{{"shape_key":"circle","density":7.85,"radius":50,"length":100}}}}}}]
Tool sonrası: "Ağırlık: 61685.03 g (61.685 kg)" gibi.

Örnek 2 (tornalama kesme hızı):
assistant (tool_calls): [{{"type":"function","function":{{"name":"calculate_turning_cutting_speed","arguments":{{"Dm":50,"n":1000}}}}}}]
"""
        return {
            "role": "system",
            "content": system_instructions,
        }

    def _should_reset_session(self, model_name: str, chat_candidates: list[str]) -> bool:
        return (
            self.reset_history_next_prompt
            or (
                self.current_model_name is not None
                and self.current_model_name != model_name
            )
            or (
                self.current_chat_url is not None
                and self.current_chat_url not in chat_candidates
            )
        )

    def _reset_session_state(self) -> None:
        self.history = []
        self.add_to_workspace(
            "Sistem",
            "Yeni modele/URL'ye geçildi. Konuşma geçmişi bu istek için sıfırlandı.",
        )
        self.force_legacy_chat = False
        self.legacy_notice_shown = False

    @staticmethod
    def _prepare_chat_payload(
        model_name: str,
        current_messages: list,
        tools: list,
    ) -> dict:
        return {
            "model": model_name,
            "messages": current_messages,
            "stream": False,
            "tools": tools,
            "options": {"temperature": 0.2, "top_p": 0.9},
        }

    def _announce_prompt_stats(
        self,
        model_name: str,
        user_prompt: str,
        tools: list,
    ) -> None:
        prompt_char_count = len(user_prompt)
        prompt_line_count = user_prompt.count("\n") + 1 if user_prompt else 0
        tool_count = len(tools)

        info_lines = [
            f"'{model_name}' modeline gönderiliyor...",
            (
                "Prompt uzunluğu: "
                f"{prompt_char_count} karakter, {prompt_line_count} satır."
            ),
        ]

        if tool_count:
            info_lines.append(f"Aktif tool sayısı: {tool_count}.")

        self.update_status_bar("\n".join(info_lines))
        logging.debug("Gönderilen prompt:%s%s", os.linesep, user_prompt)

    def _send_chat_request(
        self,
        chat_candidates: list[str],
        payload: dict,
        headers: dict,
    ) -> tuple[dict, str, bool]:
        response, used_chat_url, legacy_used = self._post_chat_with_legacy_support(
            chat_candidates,
            payload,
            headers,
            timeout=120,
        )
        response_data = response.json()
        self._debug_log_raw_response("Model Ham Cevap", response_data)
        return response_data, used_chat_url, legacy_used

    def _report_url_redirect(
        self,
        chat_candidates: list[str],
        used_chat_url: str | None,
    ) -> None:
        if (used_chat_url and chat_candidates
                and used_chat_url != chat_candidates[0]):
            info_msg = (
                "Model URL otomatik olarak alternatif uç noktaya yönlendirildi: "
                f"{used_chat_url}"
            )
            self.update_status_bar(info_msg)

    def _handle_chat_response(
        self,
        response_data: dict,
        model_url: str,
        model_name: str,
        tools: list,
        current_messages: list,
    ) -> None:
        assistant_message = response_data.get("message", {}) or {}
        self._process_assistant_message(
            model_url,
            model_name,
            tools,
            current_messages,
            assistant_message,
        )

    def _handle_chat_success_state(
        self,
        used_chat_url: str | None,
        legacy_used: bool,
        model_name: str,
    ) -> None:
        self.current_model_name = model_name
        if used_chat_url:
            self.current_chat_url = used_chat_url
            if "/v1/" in used_chat_url:
                self.force_legacy_chat = False
                self.legacy_notice_shown = False
            elif legacy_used and "/api/" in used_chat_url:
                self.force_legacy_chat = True
                self._notify_legacy_mode()
        self.reset_history_next_prompt = False

    def _handle_request_error(self, error: requests.exceptions.RequestException) -> None:
        error_msg = f"API isteği başarısız: {error}"
        self.add_to_workspace("Sistem Hatası", error_msg)
        messagebox.showerror("API Hatası", error_msg)

    def _handle_json_error(self) -> None:
        error_msg = "API'den gelen cevap JSON formatında değil."
        self.add_to_workspace("Sistem Hatası", error_msg)
        messagebox.showerror("API Cevap Hatası", error_msg)

    def _handle_generic_exception(self, error: Exception) -> None:
        error_msg = f"Beklenmedik bir hata oluştu: {error}"
        self.add_to_workspace("Sistem Hatası", error_msg)
        messagebox.showerror("Genel Hata", error_msg)

    def _handle_timeout_retry(
        self,
        chat_candidates: list[str],
        headers: dict,
        model_url: str,
        model_name: str,
        tools: list,
        current_messages: list,
    ) -> None:
        self.add_to_workspace(
            "Sistem Uyarısı",
            "İstek zaman aşımına uğradı, tam geçmişle yeniden denenecek...",
        )
        retry_payload = self._prepare_chat_payload(
            model_name,
            current_messages,
            tools,
        )
        try:
            response_data, used_chat_url, legacy_used = self._send_chat_request(
                chat_candidates,
                retry_payload,
                headers,
            )
        except requests.exceptions.RequestException as exc:
            error_msg = f"Yeniden deneme de başarısız: {exc}"
            self.add_to_workspace("Sistem Hatası", error_msg)
            messagebox.showerror("API Hatası", error_msg)
            return
        except json.JSONDecodeError:
            self._handle_json_error()
            return
        except Exception as exc:
            error_msg = f"Yeniden deneme de başarısız: {exc}"
            self.add_to_workspace("Sistem Hatası", error_msg)
            messagebox.showerror("Genel Hata", error_msg)
            return

        self._report_url_redirect(chat_candidates, used_chat_url)
        self._handle_chat_success_state(used_chat_url, legacy_used, model_name)
        self._handle_chat_response(
            response_data,
            model_url,
            model_name,
            tools,
            current_messages,
        )

    def call_ollama_api(self, model_url: str, model_name: str, user_prompt: str):
        """Send prompt to Ollama, handling retries and tool execution."""
        headers = {"Content-Type": "application/json"}
        system_message = self._build_system_message()
        chat_candidates = candidate_chat_urls(
            model_url,
            force_legacy_first=self.force_legacy_chat,
        )

        if self._should_reset_session(model_name, chat_candidates):
            self._reset_session_state()

        self.history.append({"role": "user", "content": user_prompt})
        current_messages = [system_message] + self.get_conversation_history()
        tools = build_calculator_tools_definition(ec)
        payload = self._prepare_chat_payload(
            model_name, current_messages, tools)

        self._announce_prompt_stats(model_name, user_prompt, tools)

        try:
            response_data, used_chat_url, legacy_used = self._send_chat_request(
                chat_candidates,
                payload,
                headers,
            )
        except requests.exceptions.ReadTimeout:
            self._handle_timeout_retry(
                chat_candidates,
                headers,
                model_url,
                model_name,
                tools,
                current_messages,
            )
            return
        except requests.exceptions.RequestException as exc:
            self._handle_request_error(exc)
            return
        except json.JSONDecodeError:
            self._handle_json_error()
            return
        except Exception as exc:  # pylint: disable=broad-exception-caught
            self._handle_generic_exception(exc)
            return

        self._report_url_redirect(chat_candidates, used_chat_url)
        self._handle_chat_success_state(used_chat_url, legacy_used, model_name)
        self._handle_chat_response(
            response_data,
            model_url,
            model_name,
            tools,
            current_messages,
        )

    def _parse_tool_call(
        self,
        tool_call: dict,
    ) -> tuple[str, dict, str]:
        function_payload = tool_call.get("function") or {}
        function_name = function_payload.get("name")
        if not function_name:
            raise ValueError("Tool fonksiyon adı bulunamadı")

        raw_arguments = function_payload.get("arguments")
        if isinstance(raw_arguments, str):
            try:
                arguments = json.loads(raw_arguments) or {}
            except json.JSONDecodeError:
                arguments = {}
        elif isinstance(raw_arguments, dict):
            arguments = dict(raw_arguments)
        else:
            arguments = {}

        if not isinstance(arguments, dict):
            arguments = {}

        tool_call_id = tool_call.get("id")
        if not tool_call_id:
            import uuid

            tool_call_id = f"call_{uuid.uuid4()}"
            warning_msg = (
                "Tool çağrısı '%s' için model 'id' dönmedi. Geçici ID "
                "oluşturuldu: %s"
            ) % (function_name, tool_call_id)
            logging.warning(warning_msg)
            self.update_status_bar(warning_msg)
            if self.debug_show_raw_model_responses:
                self.add_to_workspace("Sistem Uyarısı", warning_msg)

        return function_name, arguments, tool_call_id

    def _log_tool_call_start(
        self,
        function_name: str,
        tool_call_id: str,
        arguments_preview: dict,
        friendly_label: str,
    ) -> None:
        call_info = (
            "Tool Çağrısı: %s | ID: %s | Argümanlar: %s"
            % (function_name, tool_call_id, arguments_preview)
        )
        logging.info(call_info)
        if self.debug_show_raw_model_responses:
            self.add_to_workspace("Sistem", call_info)

        preview_parts: list[str] = []
        for idx, (arg_key, arg_val) in enumerate(arguments_preview.items()):
            if idx >= 3:
                preview_parts.append("…")
                break
            preview_parts.append(f"{arg_key}={arg_val}")

        status_message = f"Tool çağrısı alındı: {friendly_label}"
        if preview_parts:
            status_message += f" ({', '.join(preview_parts)})"
        self.update_status_bar(status_message)

    def _collect_ordered_args(
        self,
        category: str,
        calc_name: str,
        arguments: dict,
    ) -> list[float]:
        param_info_list = ec.get_calculation_params(category, calc_name)
        ordered_args: list[float] = []
        for param_info in param_info_list:
            internal_name = param_info["name"]
            if internal_name not in arguments:
                raise ValueError(
                    f"'{param_info['display_text_turkish']}' parametresi için değer eksik."
                )
            ordered_args.append(float(arguments[internal_name]))
        return ordered_args

    def _match_definition_name(
        self,
        function_name: str,
        prefix: str,
        available_definitions: list[str],
        error_message: str,
    ) -> str:
        model_func_name_part = function_name.replace(prefix, "", 1)
        for key in available_definitions:
            key_func_part = key.replace(" ", "_").lower()
            if model_func_name_part == key_func_part:
                return key
        raise ValueError(error_message % function_name)

    def _execute_tool_call(
        self,
        function_name: str,
        arguments: dict,
        messages_history: list,
    ) -> tuple[str, str, bool]:
        if function_name.startswith("calculate_turning_"):
            actual_calc_name = self._match_definition_name(
                function_name,
                "calculate_turning_",
                list(ec.turning_definitions.keys()),
                "Geçersiz fonksiyon adı, bilinen bir tornalama hesabıyla "
                "eşleştirilemedi: %s",
            )
            ordered_args = self._collect_ordered_args(
                "turning",
                actual_calc_name,
                arguments,
            )
            calc_result = ec.calculate_turning(actual_calc_name, *ordered_args)
            result_content = (
                f"{calc_result['value']:.2f} {calc_result['units']}"
            )
            return result_content, f"Tornalama: {actual_calc_name}", True

        if function_name.startswith("calculate_milling_"):
            actual_calc_name = self._match_definition_name(
                function_name,
                "calculate_milling_",
                list(ec.milling_definitions.keys()),
                "Geçersiz fonksiyon adı, bilinen bir frezeleme hesabıyla "
                "eşleştirilemedi: %s",
            )
            ordered_args = self._collect_ordered_args(
                "milling",
                actual_calc_name,
                arguments,
            )
            calc_result = ec.calculate_milling(actual_calc_name, *ordered_args)
            result_content = (
                f"{calc_result['value']:.2f} {calc_result['units']}"
            )
            return result_content, f"Frezeleme: {actual_calc_name}", True

        if function_name == "calculate_material_mass":
            params: MaterialMassParameters = prepare_material_mass_arguments(
                ec,
                arguments,
                messages_history,
            )
            all_args = params.dimensions + [params.length]
            mass_val = ec.calculate_material_mass(
                params.shape_key,
                params.density,
                *all_args,
            )
            return f"{mass_val:.2f} gram", "Malzeme Kütlesi", True

        fallback = self._attempt_mass_fallback(
            function_name,
            arguments,
            messages_history,
        )
        if fallback is not None:
            return fallback[0], fallback[1], True

        return (
            f"Bilinmeyen fonksiyon: {function_name}",
            self._format_tool_label(function_name),
            False,
        )

    def _attempt_mass_fallback(
        self,
        function_name: str,
        arguments: dict,
        messages_history: list,
    ) -> tuple[str, str] | None:
        fname = str(function_name).lower()
        if not any(keyword in fname for keyword in ("cylinder", "circle", "volume")):
            return None

        fallback_args = dict(arguments)
        fallback_args.setdefault("shape_key", "circle")
        try:
            params = prepare_material_mass_arguments(
                ec,
                fallback_args,
                messages_history,
            )
        except ValueError:
            return None

        mass_val = ec.calculate_material_mass(
            params.shape_key,
            params.density,
            *(params.dimensions + [params.length]),
        )
        return f"{mass_val:.2f} gram", self._format_tool_label(function_name)

    def handle_tool_calls(
        self,
        model_url: str,
        model_name: str,
        messages_history: list,
        tool_calls: list,
        tools_definition: list,
    ) -> tuple[dict, list]:
        """Execute tool calls and return the model's follow-up message.

        Args:
            model_url: Base URL entered by the user.
            model_name: Selected Ollama model name.
            messages_history: Messages sent so far (system + conversation).
            tool_calls: Tool invocation payloads provided by the model.
            tools_definition: Tool schema sent to the model.

        Returns:
            tuple: (assistant_message, updated_messages_history)
                assistant_message: Model yanıtı. Yeni tool_calls veya nihai
                    içerik içerebilir.
                updated_messages_history: Tool çağrısı, tool sonuçları ve bu
                    yanıtı içeren konuşma listesi.
        """

        base_history = list(messages_history)
        assistant_stub = {
            "role": "assistant",
            "content": "",
            "tool_calls": tool_calls,
        }
        messages_for_next_turn = base_history + [assistant_stub]

        tool_results: list[dict] = []
        tool_errors: list[str] = []
        successful_calls = 0

        for tool_call in tool_calls:
            try:
                (
                    function_name,
                    arguments,
                    tool_call_id,
                ) = self._parse_tool_call(tool_call)
            except Exception as exc:  # pylint: disable=broad-exception-caught
                fallback_id = tool_call.get("id") or "unknown"
                error_str = f"Tool çağrısı ayrıştırılamadı: {exc}"
                self.add_to_workspace("Sistem Hatası", error_str)
                self.update_status_bar(error_str)
                tool_results.append({
                    "tool_call_id": fallback_id,
                    "role": "tool",
                    "content": error_str,
                })
                tool_errors.append(error_str)
                continue

            arguments_preview = copy.deepcopy(arguments)
            friendly_label = self._format_tool_label(function_name)
            self._log_tool_call_start(
                function_name,
                tool_call_id,
                arguments_preview,
                friendly_label,
            )

            try:
                (
                    result_content,
                    display_label,
                    was_successful,
                ) = self._execute_tool_call(
                    function_name,
                    arguments,
                    messages_history,
                )
                display_label = display_label or friendly_label
                tool_summary = f"{display_label}: {result_content}"
                self.add_to_workspace("Tool Sonucu", tool_summary)
                self.update_status_bar(f"Tool sonucu: {tool_summary}")

                tool_payload = {
                    "tool_call_id": tool_call_id,
                    "role": "tool",
                    "content": result_content,
                }
                tool_results.append(tool_payload)
                self.history.append(tool_payload)

                if was_successful:
                    successful_calls += 1
            except Exception as exc:  # pylint: disable=broad-exception-caught
                display_label = friendly_label or self._format_tool_label(
                    function_name,
                )
                error_str = f"Tool çalıştırma hatası ({display_label}): {exc}"
                self.add_to_workspace("Sistem Hatası", error_str)
                self.update_status_bar(error_str)
                tool_results.append({
                    "tool_call_id": tool_call_id,
                    "role": "tool",
                    "content": error_str,
                })
                tool_errors.append(error_str)

        # Send the tool results back to Ollama
        messages_for_next_turn_with_results = messages_for_next_turn + tool_results

        self._last_tool_run_details = {
            "tool_calls": tool_calls,
            "results": tool_results,
            "errors": tool_errors,
            "successful": successful_calls,
        }

        payload_after_tool_call = {
            "model": model_name,
            "messages": messages_for_next_turn_with_results,
            "stream": False,
            "tools": tools_definition,
            "options": {
                "temperature": 0.2,
                "top_p": 0.9
            }
        }

        self.update_status_bar("Tool sonuçları modele gönderiliyor...")
        chat_candidates = candidate_chat_urls(
            model_url,
            force_legacy_first=self.force_legacy_chat,
        )
        tool_headers = {"Content-Type": "application/json"}
        try:
            response, used_chat_url, legacy_used = self._post_chat_with_legacy_support(
                chat_candidates,
                payload_after_tool_call,
                tool_headers,
                timeout=120
            )
            if used_chat_url != chat_candidates[0]:
                info_msg = (
                    "Tool sonuçları için alternatif Ollama uç noktası "
                    f"kullanıldı: {used_chat_url}"
                )
                self.update_status_bar(info_msg)
            if "/v1/" in used_chat_url:
                self.force_legacy_chat = False
            final_response_data = response.json()

            self._debug_log_raw_response(
                "Model Ham Cevap (Tool Sonrası)",
                final_response_data
            )

            assistant_message = final_response_data.get("message") or {}
            if "role" not in assistant_message:
                assistant_message["role"] = "assistant"

            if (
                not assistant_message.get("tool_calls") and
                not assistant_message.get("content") and
                tool_errors and
                not successful_calls
            ):
                assistant_message["content"] = self._build_tool_error_message()
            elif (
                not assistant_message.get("tool_calls") and
                not assistant_message.get("content") and
                successful_calls
            ):
                success_summary = self._build_tool_success_message()
                if success_summary:
                    assistant_message["content"] = success_summary

            updated_history = messages_for_next_turn_with_results + \
                [assistant_message]

            if used_chat_url:
                self.current_chat_url = used_chat_url
            if legacy_used and used_chat_url and "/api/" in used_chat_url:
                self.force_legacy_chat = True

            return assistant_message, updated_history

        except requests.exceptions.ReadTimeout:
            # Retry once with same payload (tool results are deterministic)
            self.add_to_workspace(
                "Sistem Uyarısı", "Tool sonrası istek zaman aşımı; tek seferlik yeniden deneme yapılıyor...")
            try:
                response, used_chat_url, legacy_used = self._post_chat_with_legacy_support(
                    chat_candidates,
                    payload_after_tool_call,
                    tool_headers,
                    timeout=120
                )
                if used_chat_url != chat_candidates[0]:
                    info_msg = (
                        "Tool sonuçları için alternatif Ollama uç noktası "
                        f"kullanıldı: {used_chat_url}"
                    )
                    self.update_status_bar(info_msg)
                if "/v1/" in used_chat_url:
                    self.force_legacy_chat = False
                final_response_data = response.json()

                self._debug_log_raw_response(
                    "Model Ham Cevap (Tool Sonrası)",
                    final_response_data
                )

                assistant_message = final_response_data.get("message") or {}
                if "role" not in assistant_message:
                    assistant_message["role"] = "assistant"

                if (
                    not assistant_message.get("tool_calls") and
                    not assistant_message.get("content") and
                    tool_errors and
                    not successful_calls
                ):
                    assistant_message["content"] = self._build_tool_error_message(
                    )

                updated_history = messages_for_next_turn_with_results + \
                    [assistant_message]

                if used_chat_url:
                    self.current_chat_url = used_chat_url
                if legacy_used and used_chat_url and "/api/" in used_chat_url:
                    self.force_legacy_chat = True

                return assistant_message, updated_history
            except Exception as e2:
                error_msg = f"Tool sonrası yeniden deneme başarısız: {e2}"
                self.add_to_workspace("Sistem Hatası", error_msg)
                messagebox.showerror("API Hatası", error_msg)
        except requests.exceptions.RequestException as e:
            error_msg = f"Tool sonrası API isteği başarısız: {e}"
            self.add_to_workspace("Sistem Hatası", error_msg)
            messagebox.showerror("API Hatası", error_msg)
        except Exception as e:
            error_msg = f"Tool sonrası beklemedik hata: {e}"
            self.add_to_workspace("Sistem Hatası", error_msg)
            messagebox.showerror("Genel Hata", error_msg)

        return {}, messages_history

    def on_model_change(self, event=None):
        """Called when the user selects a different model. Flags history reset for next prompt."""
        try:
            new_model = self.model_selection_combo.get()
        except Exception:
            new_model = None
        self.reset_history_next_prompt = True
        self.force_legacy_chat = False
        self.legacy_notice_shown = False
        if new_model:
            self.add_to_workspace(
                "Sistem", f"Model değiştirildi: {new_model}. Bir sonraki istek yeni oturum olarak gönderilecek.")

    def on_model_url_change(self, event=None):
        """Called when the model URL field changes. Flags history reset for next prompt if URL differs."""
        try:
            candidates = candidate_chat_urls(
                self.model_url_entry.get(),
                force_legacy_first=self.force_legacy_chat,
            )
        except Exception:
            candidates = []
        new_url = candidates[0] if candidates else None
        if self.current_chat_url and self.current_chat_url in candidates:
            new_url = self.current_chat_url
        if new_url and new_url != self.current_chat_url:
            self.reset_history_next_prompt = True
            self.force_legacy_chat = False
            self.legacy_notice_shown = False
            message = (
                f"Model URL değişti: {new_url}. "
                "Bir sonraki istek yeni oturum olarak gönderilecek."
            )
            self.add_to_workspace("Sistem", message)

    def add_to_workspace(self, source: str, message: str):
        """
        Adds a message to the result_text (shared workspace) with a source prefix.

        Args:
            source (str): "Kullanıcı", "Model", "Sistem", "Hesaplama Sonucu", etc.
            message (str): The message content.
        """
        formatted_message = f"\n\n{source}: {message}\n"
        self.result_text.insert(tk.END, formatted_message)
        self.result_text.see(tk.END)  # Scroll to the end

    def _apply_default_geometry(self) -> None:
        """Reassert the default window size once the layout is ready."""

        if not hasattr(self, "root"):
            return

        try:
            self.root.update_idletasks()
            width, height = DEFAULT_WINDOW_SIZE
            self.root.geometry(f"{width}x{height}")
            self.root.minsize(width, height)
        except tk.TclError:
            # The window might already be destroyed (application closing).
            pass

    def _format_tool_label(self, function_name: str) -> str:
        """Create a user-friendly label for a tool function name."""

        if not function_name:
            return "Tool"

        if function_name.startswith("calculate_turning_"):
            base = function_name.replace("calculate_turning_", "")
            return f"Tornalama: {base.replace('_', ' ').title()}"

        if function_name.startswith("calculate_milling_"):
            base = function_name.replace("calculate_milling_", "")
            return f"Frezeleme: {base.replace('_', ' ').title()}"

        if function_name == "calculate_material_mass":
            return "Malzeme Kütlesi"

        if function_name.startswith("calculate_"):
            base = function_name.replace("calculate_", "")
            return base.replace('_', ' ').title()

        return function_name.replace('_', ' ').title()

    def update_status_bar(self, message: str | None):
        """Display short status updates in the dedicated status bar."""

        if not hasattr(self, "status_var"):
            return

        if message is None:
            cleaned = "Hazır"
        else:
            lines = [part.strip()
                     for part in str(message).splitlines()
                     if part and part.strip()]
            cleaned = " · ".join(lines).strip()
            if not cleaned:
                cleaned = "Hazır"

        try:
            self.status_var.set(cleaned)
            if hasattr(self, "status_label"):
                self.status_label.update_idletasks()
        except tk.TclError:
            # Widget might already be destroyed (e.g. during shutdown)
            pass

    def update_calculations(self, event=None):
        """
        Updates the second combobox (specific calculation) based on the selected calculation type.
        Called when the `self.calc_type` combobox value changes.

        Args:
            event: The Tkinter event that triggered this method (usually `<<ComboboxSelected>>`). Default is None.
        """
        selected_calc_type = self.calc_type.get()
        if selected_calc_type in self.calc_types:
            # Get the dictionary of specific calculations for the selected type
            available_calcs = self.calc_types[selected_calc_type]
            # Update values of the second combobox
            self.calculation['values'] = list(available_calcs.keys())

            if list(available_calcs.keys()):  # If there are calculations available
                self.calculation.set(list(available_calcs.keys())[
                                     0])  # Set to the first one
                self.calculation.config(state="readonly")
            else:  # No calculations for this type
                self.calculation.set("")
                self.calculation.config(state="disabled")

            # Bind event for updating input fields when a specific calculation is chosen
            self.calculation.bind('<<ComboboxSelected>>',
                                  self.update_input_fields)
            self.update_input_fields()  # Trigger update for the currently selected calculation
        else:  # Should not happen if combobox is properly populated
            self.calculation['values'] = []
            self.calculation.set("")
            self.calculation.config(state="disabled")
            self.update_input_fields()  # Clear input fields

    def calculate(self):
        """
        Handles the main calculation logic when the "HESAPLA" button is clicked.

        It retrieves selected calculation type, specific calculation, and input values,
        then calls `perform_calculation` and updates the result display.
        Includes error handling for invalid inputs or calculation issues.
        """
        try:
            # Selected calculation category (e.g., "Malzeme Hesaplamaları")
            calc_type = self.calc_type.get()
            # Specific calculation selected (e.g., "Kütle Hesabı")
            calculation_name = self.calculation.get()

            # Validate that a calculation is actually selected
            if not calc_type or not calculation_name:
                # Turkish: "Warning", "Please select a calculation type and a calculation."
                messagebox.showwarning(
                    "Uyarı", "Lütfen bir hesaplama türü ve hesaplama seçin.")
                return

            # Collect input values from dynamically generated fields
            input_values = {}
            for param_key, field_widget in self.input_fields.items():
                value_str = field_widget.get()
                if not value_str:  # Check for empty field
                    # Turkish: "Error", "Value not entered for '{param_key}'."
                    messagebox.showerror(
                        "Hata", f"'{param_key}' için değer girilmemiş.")
                    return
                try:
                    # 'Şekil' (Shape) is a string from combobox
                    if param_key != 'Şekil':
                        input_values[param_key] = float(value_str)
                    else:
                        # Shape name is a string
                        input_values[param_key] = value_str
                except ValueError:
                    # Error message if conversion to float fails for numerical inputs
                    # Turkish: "Error", "Invalid numerical value for '{param_key}': {value_str}"
                    messagebox.showerror(
                        "Hata", f"'{param_key}' için geçersiz sayısal değer: {value_str}")
                    return

            # Perform the calculation using the collected data
            calculation_result = self.perform_calculation(
                calc_type, calculation_name, input_values)

            # Update the display with the results
            self.update_result_display({
                'calculation': calculation_name,
                'parameters': input_values,  # Pass collected values for display
                'result': calculation_result
            })

        except ValueError as ve:  # Catch specific ValueErrors raised by our logic or calculator
            # Turkish: "Input Error"
            messagebox.showerror("Giriş Hatası", str(ve))
        except Exception as e:  # Catch any other unexpected errors during calculation
            # Turkish: "Calculation Error", "An unexpected error occurred: {str(e)}"
            messagebox.showerror("Hesaplama Hatası",
                                 f"Beklenmedik bir hata oluştu: {str(e)}")

    def calculate_material_mass(self, calculation_name: str, input_params: dict) -> str:
        """
        Calculates material mass using `EngineeringCalculator.calculate_material_mass`.

        Args:
            calculation_name (str): The name of the calculation (e.g., "Kütle Hesabı"). Not directly used here
                                   as this method is specific to mass calculation.
            input_params (dict): Dictionary of input parameters from the GUI, keyed by Turkish names.
                                 Expected keys: 'Şekil', 'Yoğunluk', and shape-specific dimension keys.

        Returns:
            str: A formatted string representing the calculated mass and its unit (grams).

        Raises:
            ValueError: If required parameters are missing or if `EngineeringCalculator` raises an error.
        """
        shape_turkish_name = input_params['Şekil']  # Turkish name from Combobox

        # Ensure reverse_shape_names is populated (should be by update_input_fields)
        if not hasattr(self, 'reverse_shape_names') or not self.reverse_shape_names:
            # This is a fallback, ideally self.reverse_shape_names is always up-to-date.
            self.reverse_shape_names = {v: k for k,
                                        v in ec.get_available_shapes().items()}

        # Convert Turkish name to internal key
        shape_key = self.reverse_shape_names.get(shape_turkish_name)
        if not shape_key:
            # Turkish: "Invalid shape name"
            raise ValueError(f"Geçersiz şekil adı: {shape_turkish_name}")

        density = float(input_params['Yoğunluk'])  # Turkish: "Density"

        # Dynamically get the list of required dimension parameters for the selected shape_key
        # from EngineeringCalculator (e.g., ['width', 'height'] or ['radius'])
        param_names_from_calc = ec.get_shape_parameters(shape_key)

        # Map these English parameter names to the Turkish keys used in `input_params`
        # This mapping is crucial for fetching correct values from the GUI's input_params dictionary.
        param_to_gui_key_map = {  # English (from calculator) to Turkish (GUI key)
            'radius': 'Yarıçap',      # Radius
            'width': 'Genişlik',       # Width
            'height': 'Yükseklik',     # Height
            'length1': 'Uzunluk 1',    # Length 1
            'height1': 'Yükseklik 1',  # Height 1
            'length2': 'Uzunluk 2',    # Length 2
            'height2': 'Yükseklik 2',  # Height 2
            'diagonal1': 'Köşegen 1',  # Diagonal 1
            'diagonal2': 'Köşegen 2',  # Diagonal 2
        }

        # List to hold dimension values in the order expected by EngineeringCalculator
        args_for_calculator = []
        for p_name_english in param_names_from_calc:
            # Find the Turkish GUI key for the current English parameter name
            # Fallback to capitalized English name if no direct map
            gui_key_turkish = param_to_gui_key_map.get(
                p_name_english, p_name_english.capitalize())
            if gui_key_turkish not in input_params:
                # Turkish: "Missing value for parameter '{gui_key_turkish}'."
                raise ValueError(
                    f"\'{gui_key_turkish}\' parametresi için değer eksik.")
            args_for_calculator.append(float(input_params[gui_key_turkish]))

        # Append the common 'Uzunluk' (Length) parameter, which is always present for extrusion
        if 'Uzunluk' not in input_params:
            # Turkish: "Missing value for parameter 'Uzunluk'."
            raise ValueError("'Uzunluk' parametresi için değer eksik.")
        args_for_calculator.append(float(input_params['Uzunluk']))

        # Call the core calculation method from EngineeringCalculator
        # Note: EngineeringCalculator.calculate_material_mass now handles mm³ to cm³ conversion.
        mass_value = ec.calculate_material_mass(
            shape_key, density, *args_for_calculator)
        # Result formatted to two decimal places
        return f"{mass_value:.2f} gram"

    def calculate_turning(self, calculation_name: str, input_params: dict) -> str:
        """
        Calculates turning parameters using `EngineeringCalculator.calculate_turning`.

        Args:
            calculation_name (str): The Turkish name of the specific turning calculation.
            input_params (dict): Dictionary of input parameters from the GUI, keyed by parameter names
                                 (which match `TURNING_CALCS[calculation_name]['params']`).

        Returns:
            str: A formatted string representing the calculated value and its unit.
        """
        # `calculation_name` is the Turkish display name, which is also the method key in ec.definitions
        # `input_params` are now keyed by internal English names (e.g., 'Dm', 'n')

        # Fetch parameter definitions to know the order and internal names
        param_info_list = ec.get_calculation_params(
            'turning', calculation_name)

        args_for_calculator = []
        for param_info in param_info_list:
            internal_name = param_info['name']
            if internal_name not in input_params:
                raise ValueError(
                    f"'{param_info['display_text_turkish']}' parametresi için değer eksik.")
            args_for_calculator.append(float(input_params[internal_name]))

        # The `calculation_name` (e.g., "Kesme Hızı") is directly used as the method_key
        result_dict = ec.calculate_turning(
            calculation_name, *args_for_calculator)
        return f"{result_dict['value']:.2f} {result_dict['units']}"

    def calculate_milling(self, calculation_name: str, input_params: dict) -> str:
        """
        Calculates milling parameters using `EngineeringCalculator.calculate_milling`.
        The `input_params` dictionary is now keyed by internal English parameter names.

        Args:
            calculation_name (str): The Turkish name (which is also the method key) of the specific milling calculation.
            input_params (dict): Dictionary of input parameters from the GUI, keyed by internal English parameter names.

        Returns:
            str: A formatted string representing the calculated value and its unit.
        """
        # `calculation_name` is the Turkish display name / method key.
        # `input_params` are keyed by internal English names.

        param_info_list = ec.get_calculation_params(
            'milling', calculation_name)

        args_for_calculator = []
        for param_info in param_info_list:
            internal_name = param_info['name']
            if internal_name not in input_params:
                raise ValueError(
                    f"'{param_info['display_text_turkish']}' parametresi için değer eksik.")
            args_for_calculator.append(float(input_params[internal_name]))

        result_dict = ec.calculate_milling(
            calculation_name, *args_for_calculator)
        return f"{result_dict['value']:.2f} {result_dict['units']}"

    def perform_calculation(self, calc_category: str, calc_name: str, params_values: dict) -> str:
        """
        Delegates to the appropriate calculation method based on the selected category.

        This acts as a dispatcher to specific `calculate_...` methods.

        Args:
            calc_category (str): The category of calculation (e.g., "Malzeme Hesaplamaları").
            calc_name (str): The specific name of the calculation (e.g., "Kütle Hesabı").
            params_values (dict): A dictionary of parameter values collected from the GUI.

        Returns:
            str: The formatted result string from the specific calculation method.

        Raises:
            ValueError: If the `calc_category` is unknown.
        """
        if calc_category == 'Malzeme Hesaplamaları':  # Turkish: "Material Calculations"
            return self.calculate_material_mass(calc_name, params_values)
        elif calc_category == 'Tornalama Hesaplamaları':  # Turkish: "Turning Calculations"
            return self.calculate_turning(calc_name, params_values)
        elif calc_category == 'Frezeleme Hesaplamaları':  # Turkish: "Milling Calculations"
            return self.calculate_milling(calc_name, params_values)
        else:
            # This case should ideally not be reached if GUI is set up correctly with calc_types
            # Turkish: "Unknown calculation category"
            raise ValueError(
                f"Bilinmeyen hesaplama kategorisi: {calc_category}")

    def update_input_fields(self, event: tk.Event | None = None):
        """
        Dinamik olarak GUI'deki parametre alanlarını günceller. Her hesaplama türü ve seçimi için gerekli alanlar gösterilir.
        """
        # Tüm mevcut widget'ları temizle
        for widget in self.params_container.winfo_children():
            widget.destroy()
        self.input_fields = {}
        self.shape_combo = None

        calc_category = self.calc_type.get()
        selected_calculation = self.calculation.get()
        if not calc_category or not selected_calculation:
            return

        if calc_category == 'Malzeme Hesaplamaları' and selected_calculation == 'Kütle Hesabı':
            available_shapes_map = ec.get_available_shapes()
            self.reverse_shape_names = {v: k for k,
                                        v in available_shapes_map.items()}
            shape_display_names = list(available_shapes_map.values())

            shape_frame = ttk.Frame(self.params_container, style='Calc.TFrame')
            shape_frame.pack(fill='x', pady=2, padx=5)
            ttk.Label(shape_frame, text="Şekil:", style='Calc.TLabel').pack(
                side='left', padx=(0, 5))
            self.shape_combo = ttk.Combobox(
                shape_frame, values=shape_display_names, state="readonly")
            self.shape_combo.pack(side='left', fill='x', expand=True)
            if shape_display_names:
                self.shape_combo.set(shape_display_names[0])
            self.shape_combo.bind('<<ComboboxSelected>>',
                                  self._update_material_params)
            self.input_fields['Şekil'] = self.shape_combo
            # Tooltip for shape selection
            AdvancedToolTip(self.shape_combo, self.tooltips.get(
                "Şekil", "Şekil seçin."))
            self._update_material_params()
        else:
            category_to_internal_key = {
                'Tornalama Hesaplamaları': 'turning',
                'Frezeleme Hesaplamaları': 'milling'
            }
            calc_category_internal = category_to_internal_key.get(
                calc_category)
            if calc_category_internal:
                try:
                    param_info_list = ec.get_calculation_params(
                        calc_category_internal, selected_calculation)
                    for param_info in param_info_list:
                        param_input_frame = ttk.Frame(
                            self.params_container, style='Calc.TFrame')
                        param_input_frame.pack(fill='x', pady=2, padx=5)
                        label_text = f"{param_info['display_text_turkish']} [{param_info['unit']}]:"
                        label_widget = ttk.Label(
                            param_input_frame, text=label_text, style='Calc.TLabel')
                        label_widget.pack(side='left', padx=(0, 5))
                        entry = ttk.Entry(param_input_frame)
                        entry.pack(side='left', fill='x', expand=True)
                        self.input_fields[param_info['name']] = entry
                        # Tooltip for each parameter
                        tooltip_key = param_info['name']
                        tooltip_text = self.tooltips.get(tooltip_key, self.tooltips.get(
                            param_info['display_text_turkish'], f"{param_info['display_text_turkish']} girin."))
                        AdvancedToolTip(entry, tooltip_text)
                except ValueError as e:
                    ttk.Label(
                        self.params_container, text="Bu hesaplama için parametre tanımlanmamış.", style='Calc.TLabel').pack()

    def _update_material_params(self, event: tk.Event | None = None):
        """
        Kütle hesabı için şekil seçildiğinde yoğunluk ve şekil parametrelerini günceller.
        """
        # Şekil combobox'u hariç tüm widget'ları temizle
        widgets = list(self.params_container.winfo_children())
        if len(widgets) > 1:
            for widget in widgets[1:]:
                widget.destroy()
        if 'Şekil' not in self.input_fields or self.input_fields['Şekil'] is None:
            return
        current_shape_selection = self.input_fields['Şekil'].get()
        self.input_fields = {'Şekil': self.input_fields['Şekil']}
        self.input_fields['Şekil'].set(current_shape_selection)

        density_frame = ttk.Frame(self.params_container, style='Calc.TFrame')
        density_frame.pack(fill='x', pady=2, padx=5)
        ttk.Label(density_frame, text="Yoğunluk [g/cm³]:",
                  style='Calc.TLabel').pack(side='left', padx=(0, 5))
        density_entry = ttk.Entry(density_frame, width=10)
        density_entry.pack(side='left', fill='x', expand=True)
        self.input_fields['Yoğunluk'] = density_entry
        # Tooltip for density
        AdvancedToolTip(density_entry, self.tooltips.get(
            "Yoğunluk", "Malzemenin yoğunluğunu girin."))

        material_names = list(ec.material_density.keys())
        material_combo = ttk.Combobox(
            density_frame, values=material_names, state="readonly", width=15)
        material_combo.pack(side='left', padx=(10, 0))

        def _on_material_select(event=None):
            mat = material_combo.get()
            if mat in ec.material_density:
                density_entry.delete(0, 'end')
                density_entry.insert(0, str(ec.material_density[mat]))
        material_combo.bind('<<ComboboxSelected>>', _on_material_select)
        if material_names:
            material_combo.set(material_names[0])
            _on_material_select()
        # Tooltip for material selection
        AdvancedToolTip(material_combo, self.tooltips.get(
            "MalzemeSec", "Bir malzeme seçerek yoğunluğu otomatik doldurun."))

        selected_shape_turkish = self.shape_combo.get() if self.shape_combo else None
        shape_key = self.reverse_shape_names.get(
            selected_shape_turkish) if selected_shape_turkish else None
        if shape_key:
            param_to_gui_key_map = {
                'radius': 'Yarıçap', 'width': 'Genişlik', 'height': 'Yükseklik',
                'length1': 'Uzunluk 1', 'height1': 'Yükseklik 1',
                'length2': 'Uzunluk 2', 'height2': 'Yükseklik 2',
                'diagonal1': 'Köşegen 1', 'diagonal2': 'Köşegen 2',
            }
            shape_specific_params_english = ec.get_shape_parameters(shape_key)
            gui_params_to_create = []
            for p_name_english in shape_specific_params_english:
                turkish_label = param_to_gui_key_map.get(
                    p_name_english, p_name_english.capitalize())
                gui_params_to_create.append(
                    (turkish_label, 'mm', p_name_english))
            gui_params_to_create.append(('Uzunluk', 'mm', 'Uzunluk'))
            for param_label_turkish, unit_str, tooltip_key in gui_params_to_create:
                param_input_frame = ttk.Frame(
                    self.params_container, style='Calc.TFrame')
                param_input_frame.pack(fill='x', pady=2, padx=5)
                label_full_text = f"{param_label_turkish} [{unit_str}]:"
                ttk.Label(param_input_frame, text=label_full_text,
                          style='Calc.TLabel').pack(side='left', padx=(0, 5))
                entry = ttk.Entry(param_input_frame)
                entry.pack(side='left', fill='x', expand=True)
                self.input_fields[param_label_turkish] = entry
                # Tooltip for each shape parameter
                tooltip_text = self.tooltips.get(tooltip_key, self.tooltips.get(
                    param_label_turkish, f"{param_label_turkish} girin."))
                AdvancedToolTip(entry, tooltip_text)
        self.params_container.update_idletasks()

    def update_result_display(self, result_data: dict):
        """
        Updates the shared workspace (result_text) with formatted calculation inputs and results
        using the add_to_workspace method.

        Args:
            result_data (dict): A dictionary containing:
                - 'calculation': Name of the calculation performed.
                - 'parameters': Dictionary of input parameters used.
                - 'result': The calculated result string.
        """
        calc_name = result_data.get('calculation', 'Bilinmeyen Hesaplama')
        params = result_data.get('parameters', {})
        result_str = result_data.get('result', 'Sonuç bulunamadı.')

        self.add_to_workspace("Sistem", f"Hesaplama: {calc_name}")

        param_details = "\n".join(
            [f"  - {key.replace('_', ' ').capitalize()}: {value}" for key, value in params.items()])
        if param_details:
            self.add_to_workspace("Giriş Parametreleri", param_details)

        self.add_to_workspace("Hesaplama Sonucu", result_str)


if __name__ == "__main__":
    tooltips = load_tooltips('tooltips.json')
    root = tk.Tk()
    app = AdvancedCalculator(root, tooltips)
    root.mainloop()
