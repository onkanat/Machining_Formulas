#! /opt/miniconda3/bin/python
# -*- coding : utf-8 -*-# # Standard Python encoding declaration.
# Autor:Hakan KILIÇASLAN 2025 # Author and year.

# --- Constants for Calculation Definitions ---
# MATERIAL_CALCS is kept for 'Kütle Hesabı' (Mass Calculation) which has unique handling for shapes.
# TURNING_CALCS and MILLING_CALCS are removed as their parameter definitions
# will now be sourced directly from EngineeringCalculator.

MATERIAL_CALCS = {
    'Kütle Hesabı': { # Turkish: "Mass Calculation"
        # 'params' and 'units' for Kütle Hesabı are handled dynamically by _update_material_params
        # based on shape selection and EngineeringCalculator.get_shape_parameters().
        # This entry mainly serves to list "Kütle Hesabı" under "Malzeme Hesaplamaları".
    }
}

# TURNING_CALCS and MILLING_CALCS are now removed.
# The UI will populate calculation names (keys) for Turning and Milling
# directly from ec.turning_definitions.keys() and ec.milling_definitions.keys().
# Parameter details (name, unit, display_text_turkish) for each calculation
# will be fetched using ec.get_calculation_params().

# --- Standard Library and Third-Party Imports ---
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from engineering_calculator import EngineeringCalculator # Core calculation logic.
import json # For loading tooltips from a JSON file.
import os # Potentially for path operations (though not explicitly used here).
import markdown # For rendering markdown text (if used, e.g. in results display).
import re # Regular expressions, possibly for text processing or input validation.
import math # For mathematical constants like pi.
from tkinter import font # For font manipulation if needed.
import requests # For making HTTP requests to the Ollama API.

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
        self.widget.bind('<Button>', self.leave) # Hide tooltip on button click as well.

    def enter(self, event=None):
        """Schedules the tooltip to appear when the mouse enters the widget."""
        self.schedule()

    def leave(self, event=None):
        """Unschedules and hides the tooltip when the mouse leaves the widget."""
        self.unschedule()
        self.hide()

    def schedule(self):
        """Schedules the `show` method to be called after `self.delay` milliseconds."""
        self.unschedule() # Cancel any existing schedules.
        self.id = self.widget.after(int(self.delay * 1000), self.show)

    def unschedule(self):
        """Unschedules the näyttäminen of the tooltip if it's currently scheduled."""
        if self.id:
            self.widget.after_cancel(self.id)
            self.id = None

    def show(self):
        """Displays the tooltip window near the widget."""
        if self.tooltip: # If tooltip is already shown, do nothing.
            return

        # Calculate tooltip position safely without relying on bbox (not supported by all widgets)
        try:
            x = self.widget.winfo_rootx() + 20
            y = self.widget.winfo_rooty() + self.widget.winfo_height() + 10
        except Exception:
            x, y = 100, 100

        # Create a Toplevel window for the tooltip.
        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True) # Remove window decorations (border, title bar).

        # Create a label within the Toplevel to display the tooltip text.
        label = tk.Label(self.tooltip, text=self.text,
                      justify='left',
                      background=self.background,
                      foreground=self.foreground,
                      font=self.font,
                      relief='solid', # Add a border to the tooltip.
                      borderwidth=1)
        label.pack()

        self.tooltip.wm_geometry(f"+{x}+{y}") # Position the tooltip window.

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

class AdvancedCalculator:
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
        super().__init__() # Though not inheriting from a specific base class here, good practice if refactored.

        self.root = root
        self.tooltips = tooltips
        self.root.title("Mühendislik Hesaplamaları ve Analiz Uygulaması") # Turkish: Engineering Calculations and Analysis Application
        self.root.geometry("1200x800") # Set initial window size.

        # --- Styling ---
        style = ttk.Style()
        style.configure('Calc.TFrame', background='#f0f0f0') # Custom style for frames.
        style.configure('Calc.TLabel', background='#f0f0f0', font=('Arial', 10)) # Custom style for labels.
        style.configure('Calc.TButton', font=('Arial', 10)) # Custom style for buttons.

        # --- Main Layout Frames ---
        self.main_frame = ttk.Frame(root, style='Calc.TFrame')
        self.main_frame.pack(fill='both', expand=True, padx=10, pady=10)

        # Left frame for input controls
        self.left_frame = ttk.Frame(self.main_frame, style='Calc.TFrame')
        self.left_frame.pack(side='left', fill='y', padx=5)

        # Right frame for results
        self.right_frame = ttk.Frame(self.main_frame) # Default style
        self.right_frame.pack(side='right', fill='both', expand=True, padx=5)

        # --- Static UI Elements in Left Frame ---
        # Populate calculation types. Turning and Milling calculation names (keys)
        # are fetched directly from the EngineeringCalculator instance.
        # The empty dictionaries {} as values are placeholders; actual parameter details
        # will be fetched on demand by `update_input_fields` using `ec.get_calculation_params`.
        self.calc_types = {
            'Malzeme Hesaplamaları': MATERIAL_CALCS, # Turkish: "Material Calculations"
            'Tornalama Hesaplamaları': {key: {} for key in ec.turning_definitions.keys()}, # Turkish: "Turning Calculations"
            'Frezeleme Hesaplamaları': {key: {} for key in ec.milling_definitions.keys()}  # Turkish: "Milling Calculations"
        }

        ttk.Label(self.left_frame, text="Hesaplama Türü:", style='Calc.TLabel').pack(pady=(5,0), anchor='w') # Turkish: "Calculation Type:"
        self.calc_type = ttk.Combobox(self.left_frame, values=list(self.calc_types.keys()), state="readonly")
        self.calc_type.pack(fill='x', pady=(0,10))
        AdvancedToolTip(self.calc_type, self.tooltips.get("HesaplamaTuru", "Bir hesaplama türü seçin.")) # Turkish: "Select a calculation type."
        self.calc_type.bind('<<ComboboxSelected>>', self.update_calculations) # Event binding

        ttk.Label(self.left_frame, text="Hesaplama Seçimi:", style='Calc.TLabel').pack(pady=(5,0), anchor='w') # Turkish: "Calculation Selection:"
        self.calculation = ttk.Combobox(self.left_frame, state="readonly")
        self.calculation.pack(fill='x', pady=(0,10))
        AdvancedToolTip(self.calculation, self.tooltips.get("HesaplamaSecimi", "Bir hesaplama seçin.")) # Turkish: "Select a calculation."
        # Note: self.calculation.bind is set in update_calculations

        # Frame to hold dynamically generated parameter input fields
        self.params_frame = ttk.Frame(self.left_frame, style='Calc.TFrame')
        self.params_frame.pack(fill='x', pady=5)
        self.params_container = ttk.Frame(self.params_frame, style='Calc.TFrame') # Inner container for parameters
        self.params_container.pack(fill='x', expand=True)


        # --- Result Display Area in Right Frame ---
        self.result_text = scrolledtext.ScrolledText(self.right_frame, wrap=tk.WORD,
                                                   width=80, height=35, # Adjusted size
                                                   font=('Courier New', 11)) # Using Courier for code-like display
        self.result_text.pack(fill='both', expand=True)
        # Initial content or placeholder for the results area
        self.result_text.insert(tk.END, "# Hesaplama Sonuçları ve Detayları\n\nBurada hesaplama sonuçlarınız gösterilecektir.\n") # Turkish: Calculation Results and Details. Your calculation results will be displayed here.

        # --- Global Key Bindings ---
        self.root.bind('<Control-e>', self.enable_execute_mode)  # Enable code execution mode
        self.root.bind('<Control-c>', self.execute_calculation) # Execute selected code

        # --- Calculate Button ---
        self.calculate_button = ttk.Button(self.left_frame, text="HESAPLA",
                                           command=self.calculate, style='Calc.TButton') # Turkish: "CALCULATE"
        self.calculate_button.pack(pady=10, fill='x', ipady=5) # Adjusted padding
        AdvancedToolTip(self.calculate_button, self.tooltips.get("HesaplaButonu", "Seçili hesaplamayı gerçekleştir.")) # Turkish: "Perform the selected calculation."

        # --- Separator ---
        ttk.Separator(self.left_frame, orient='horizontal').pack(fill='x', pady=10)

        # --- LLM Interaction UI Elements ---
        llm_frame = ttk.Frame(self.left_frame, style='Calc.TFrame')
        llm_frame.pack(fill='x', pady=5)

        # Model URL
        ttk.Label(llm_frame, text="Model URL:", style='Calc.TLabel').pack(pady=(5,0), anchor='w')
        self.model_url_entry = ttk.Entry(llm_frame)
        self.model_url_entry.pack(fill='x', pady=(0,5))
        # Unified default: Ollama chat endpoint on localhost
        self.model_url_entry.insert(0, "http://localhost:11434/api/chat")
        AdvancedToolTip(self.model_url_entry, self.tooltips.get("ModelURL", "Kullanılacak Ollama modelinin URL'si."))

        # Model Selection
        ttk.Label(llm_frame, text="Model Seçin:", style='Calc.TLabel').pack(pady=(5,0), anchor='w')
        self.model_selection_combo = ttk.Combobox(llm_frame, state="readonly")
        self.model_selection_combo.pack(fill='x', pady=(0,5))
        # Model list is populated dynamically from Ollama /api/tags with graceful fallback
        self.model_selection_combo['values'] = []
        # We'll attempt to fetch models after widgets are set
        AdvancedToolTip(self.model_selection_combo, self.tooltips.get("ModelSecimi", "Kullanılacak LLM modelini seçin."))
        # Reset conversation when model changes
        self.model_selection_combo.bind('<<ComboboxSelected>>', self.on_model_change)

        # Chat Prompt Input
        ttk.Label(llm_frame, text="Soru / Prompt:", style='Calc.TLabel').pack(pady=(5,0), anchor='w')
        self.chat_prompt_text = scrolledtext.ScrolledText(llm_frame, wrap=tk.WORD, height=5, font=('Arial', 10))
        self.chat_prompt_text.pack(fill='x', pady=(0,5))
        AdvancedToolTip(self.chat_prompt_text, self.tooltips.get("ChatPrompt", "Modele göndermek istediğiniz soru veya komut."))

        # Send Prompt Button
        self.send_prompt_button = ttk.Button(llm_frame, text="Gönder", command=self.send_prompt_to_model, style='Calc.TButton')
        self.send_prompt_button.pack(pady=10, fill='x', ipady=5)
        AdvancedToolTip(self.send_prompt_button, self.tooltips.get("GonderButonu", "Soruyu modele gönder."))

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

        # --- Initialize dynamic fields ---
        self.input_fields = {}
        self.reverse_shape_names = {}
        self.shape_combo = None # Will be created in update_input_fields if needed
        self.execute_mode = False # Flag for the experimental code execution mode

        # Initialize first calculation type
        if list(self.calc_types.keys()):
            self.calc_type.set(list(self.calc_types.keys())[0])
            self.update_calculations()

        # Try to fetch available models now
        try:
            self.refresh_model_list()
        except Exception:
            # Fallback to a small static list if fetch fails
            self.ollama_models = ["llama3.1", "qwen2.5", "gemma2"]
            self.model_selection_combo['values'] = self.ollama_models
            if self.ollama_models:
                self.model_selection_combo.set(self.ollama_models[0])


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
            messagebox.showwarning("Eksik Bilgi", "Lütfen Model URL, Model ve Prompt girdiğinizden emin olun.")
            return

        # Add user's prompt to the shared workspace (result_text)
        self.add_to_workspace("Kullanıcı", user_prompt)

        # Actual backend call
        self.call_ollama_api(model_url, selected_model, user_prompt)

        self.chat_prompt_text.delete("1.0", tk.END) # Clear the prompt input area

    def get_conversation_history(self) -> list[dict]:
        """
        Yapılandırılmış konuşma geçmişini döndürür.
        Not: Sistem mesajı bu listede tutulmaz; her istekte başa ayrıca eklenir.
        """
        return list(self.history)

    def _get_calculator_tools_definition(self) -> list[dict]:
        """
        Generates the tool definitions for EngineeringCalculator methods
        in the format expected by Ollama.
        """
        tools = []
        # Turning calculations
        for calc_name in ec.turning_definitions.keys():
            params_info = ec.get_calculation_params('turning', calc_name)
            properties = {
                param['name']: {"type": "number", "description": f"{param['display_text_turkish']} ({param['unit']})"}
                for param in params_info
            }
            required = [param['name'] for param in params_info]

            tools.append({
                "type": "function",
                "function": {
                    "name": f"calculate_turning_{calc_name.replace(' ', '_').lower()}", #e.g. calculate_turning_cutting_speed
                    "description": f"Tornalama için '{calc_name}' hesaplaması yapar. Örn: {calc_name}",
                    "parameters": {
                        "type": "object",
                        "properties": properties,
                        "required": required
                    }
                }
            })

        # Milling calculations
        for calc_name in ec.milling_definitions.keys():
            params_info = ec.get_calculation_params('milling', calc_name)
            properties = {
                param['name']: {"type": "number", "description": f"{param['display_text_turkish']} ({param['unit']})"}
                for param in params_info
            }
            required = [param['name'] for param in params_info]
            tools.append({
                "type": "function",
                "function": {
                    "name": f"calculate_milling_{calc_name.replace(' ', '_').lower()}",
                    "description": f"Frezeleme için '{calc_name}' hesaplaması yapar. Örn: {calc_name}",
                    "parameters": {
                        "type": "object",
                        "properties": properties,
                        "required": required
                    }
                }
            })

        # Material mass calculation (a bit more complex due to shapes)
        # For simplicity, we'll define a generic material mass tool.
        # Model will need to specify shape and its dimensions.
        # This requires careful prompting or the model knowing shape parameter names.
        # Let's define it with common params and expect the model to learn/be prompted for shape specific ones.
        # A better approach might be separate tools for each shape, or a more structured input.
        # For now, one tool for mass calculation.

        # General parameters for mass calculation (density, length are common)
        mass_params = {
            "shape_key": {"type": "string", "description": "Malzemenin şekli (örn: 'triangle', 'circle', 'square')."},
            "density": {"type": "number", "description": "Malzeme yoğunluğu (g/cm³)."},
            "length": {"type": "number", "description": "Ekstrüzyon uzunluğu (mm)."}
            # Shape specific params like 'radius', 'width', 'height' need to be dynamically asked or known by model.
            # Ollama's tool definition doesn't easily support "anyOf" for parameters based on another param (shape_key).
            # We'll make them optional here and handle in the execution logic.
        }
        # Add shape parameters dynamically to the description or as optional params
        # This is a simplification. A robust solution would require more complex tool definition or interaction.
        # For now, we'll rely on the model to provide necessary args based on the shape_key.
        # The function call will need to parse these.

        # We can list all possible shape parameters as optional to guide the model.
        all_shape_params = set()
        available_shapes = ec.get_available_shapes() # Get available shapes {key: turkish_name}
        for shape_k in available_shapes.keys():
            for p_name in ec.get_shape_parameters(shape_k):
                all_shape_params.add(p_name)

        for p_name in sorted(list(all_shape_params)):
             mass_params[p_name] = {"type": "number", "description": f"Şekle özel parametre: {p_name} (mm), eğer şekil için gerekliyse."}

        # Update shape_key description to list available shapes
        shape_keys_str = ", ".join(available_shapes.keys())
        mass_params["shape_key"] = {"type": "string", "description": f"Malzemenin şekli. Geçerli değerler: {shape_keys_str}."}


        tools.append({
            "type": "function",
            "function": {
                "name": "calculate_material_mass",
                "description": "Belirli bir şekil ve yoğunluk için malzeme kütlesini hesaplar. 'shape_key' ve gerekli boyutları belirtin.",
                "parameters": {
                    "type": "object",
                    "properties": mass_params,
                    "required": ["shape_key", "density", "length"] # Core requirements
                }
            }
        })
        return tools

    def _normalize_chat_url(self, url: str) -> str:
        """
        Ensures the provided URL points to Ollama chat endpoint (/api/chat).
        Accepts base URLs like http://host:11434 or http://host:11434/api and normalizes to /api/chat.
        """
        if not url:
            return "http://localhost:11434/api/chat"
        u = url.strip()
        # If already /api/chat
        if "/api/chat" in u:
            # ensure no trailing spaces
            return u
        # Convert /api/tags or any /api/* to /api/chat
        if "/api/" in u:
            base = u.split("/api/")[0]
            return base + "/api/chat"
        # Ends with /api
        if u.endswith("/api"):
            return u + "/chat"
        # Base host: append /api/chat
        if u.endswith('/'):
            u = u[:-1]
        return u + "/api/chat"

    def _build_tags_url(self, url: str) -> str:
        """Builds the Ollama tags endpoint URL from a given chat/base URL."""
        if not url:
            return "http://localhost:11434/api/tags"
        u = url.strip()
        if "/api/tags" in u:
            return u
        if "/api/chat" in u:
            return u.replace("/api/chat", "/api/tags")
        if "/api/" in u:
            base = u.split("/api/")[0]
            return base + "/api/tags"
        if u.endswith("/api"):
            return u + "/tags"
        if u.endswith('/'):
            u = u[:-1]
        return u + "/api/tags"

    def refresh_model_list(self):
        """Fetch available Ollama models via /api/tags and populate the combobox with fallback."""
        tags_url = self._build_tags_url(self.model_url_entry.get())
        try:
            resp = requests.get(tags_url, timeout=60)
            resp.raise_for_status()
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
                self.add_to_workspace("Sistem Uyarısı", "Model listesi alınamadı, varsayılan liste kullanılacak.")
            self.ollama_models = models
            self.model_selection_combo['values'] = self.ollama_models
            if self.ollama_models and self.model_selection_combo.get() not in self.ollama_models:
                self.model_selection_combo.set(self.ollama_models[0])
        except requests.exceptions.RequestException as e:
            # Network or server error: fallback
            self.ollama_models = ["llama3.1", "qwen2.5", "gemma2"]
            self.model_selection_combo['values'] = self.ollama_models
            if self.ollama_models and self.model_selection_combo.get() not in self.ollama_models:
                self.model_selection_combo.set(self.ollama_models[0])
            self.add_to_workspace("Sistem Uyarısı", f"Model listesi alınamadı ({e}). Varsayılan liste kullanılıyor.")

    def call_ollama_api(self, model_url: str, model_name: str, user_prompt: str):
        """
        Calls the Ollama API with the given prompt, model, and conversation history.
        Handles tool calls if the model requests them.
        """
        headers = {"Content-Type": "application/json"}

        # Build dynamic guidance: shapes and material densities
        try:
            shapes_map = ec.get_available_shapes()
        except Exception:
            shapes_map = {}
        shapes_list = ", ".join([f"{k} (TR: {v})" for k, v in shapes_map.items()])

        try:
            densities = ec.material_density
        except Exception:
            densities = {}
        dens_list = ", ".join([f"{name}: {val} g/cm³" for name, val in densities.items()])

        system_instructions = f"""
Sen bir mühendislik hesaplama asistanısın. Kullanıcı isteklerini yanıtlamak için sana verilen araçları (tool) kullan.

Kritik kurallar (uygulamak ZORUNLU):
- Bir hesaplama istendiğinde, uygun aracı çağır ve ilk mesajında SADECE tool_calls döndür. Serbest metin yazma.
- Araç fonksiyon adlarını ve parametre isimlerini, araç tanımında (tools) verildiği şekilde birebir aynı kullan.
- Gerekli parametrelerin hepsini sağla, fazladan parametre yollama.
- Birimlere dikkat et: uzunluklar mm, yoğunluk g/cm³. Kütle aracı gram döndürür; nihai mesajında gr ve kg olarak sun.

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

        system_message = {
            "role": "system",
            "content": system_instructions
        }

        # Normalize URL and decide whether to reset history on model/URL change
        chat_url = self._normalize_chat_url(model_url)
        should_reset = (
            self.reset_history_next_prompt or
            (self.current_model_name is not None and self.current_model_name != model_name) or
            (self.current_chat_url is not None and self.current_chat_url != chat_url)
        )

        if should_reset:
            self.history = []
            self.add_to_workspace("Sistem", f"Yeni modele/URL'ye geçildi. Konuşma geçmişi bu istek için sıfırlandı.")
        
        # Append current user prompt to structured history
        self.history.append({"role": "user", "content": user_prompt})

        # Prepend system message to guide the model.
        current_messages = [system_message] + self.get_conversation_history()

        tools = self._get_calculator_tools_definition()

        payload = {
            "model": model_name,
            "messages": current_messages,
            "stream": False, # Important for tool use, stream=True might behave differently
            "tools": tools,
            "options": {
                # Lower temperature and reasonable top_p improve tool_call adherence
                "temperature": 0.2,
                "top_p": 0.9
            }
        }

        self.add_to_workspace("Sistem", f"""'{model_name}' modeline gönderiliyor...
Prompt: {user_prompt}
Tools: {[t['function']['name'] for t in tools]}""")

        try:
            # Call with timeout
            response = requests.post(chat_url, json=payload, headers=headers, timeout=60)
            response.raise_for_status()  # Raise an exception for HTTP errors
            response_data = response.json()

            self.add_to_workspace("Model Ham Cevap", json.dumps(response_data, indent=2, ensure_ascii=False)) # Log raw response

            # The response itself is the assistant's message
            assistant_message = response_data.get("message", {})

            tool_calls_payload = assistant_message.get("tool_calls")
            if tool_calls_payload:
                self.add_to_workspace("Model", "Bir araç kullanmak istiyor...")
                # Add assistant with tool_calls to history
                self.history.append({"role": "assistant", "content": "", "tool_calls": tool_calls_payload})
                self.handle_tool_calls(model_url, model_name, current_messages, tool_calls_payload, tools)
            else:
                # Fallback: try to parse tool_calls JSON embedded in content
                content = assistant_message.get("content", "")
                parsed_tool_calls = None
                if isinstance(content, str) and content:
                    try:
                        # Capture first JSON array that looks like tool_calls
                        m = re.search(r"\[(?:\s|\S)*?\{\s*\"type\"\s*:\s*\"function\"(?:.|\n)*?\]\s*", content)
                        if m:
                            parsed_tool_calls = json.loads(m.group(0))
                    except Exception:
                        parsed_tool_calls = None

                if parsed_tool_calls:
                    self.add_to_workspace("Model", "İçerikte gömülü tool çağrıları bulundu, işleniyor...")
                    # Record assistant tool_calls in history
                    self.history.append({"role": "assistant", "content": "", "tool_calls": parsed_tool_calls})
                    self.handle_tool_calls(model_url, model_name, current_messages, parsed_tool_calls, tools)
                else:
                    content_final = content or "Modelden içerik alınamadı."
                    self.add_to_workspace("Model", content_final)
                    # Append assistant free-form content to history
                    self.history.append({"role": "assistant", "content": content_final})

        except requests.exceptions.ReadTimeout as e:
            # One-shot retry with simplified history (fresh turn)
            self.add_to_workspace("Sistem Uyarısı", f"İstek zaman aşımına uğradı, sadeleştirilmiş geçmişle yeniden denenecek...")
            retry_payload = {
                "model": model_name,
                "messages": [system_message, {"role": "user", "content": user_prompt}],
                "stream": False,
                "tools": tools,
                "options": payload.get("options", {})
            }
            try:
                response = requests.post(chat_url, json=retry_payload, headers=headers, timeout=60)
                response.raise_for_status()
                response_data = response.json()

                self.add_to_workspace("Model Ham Cevap", json.dumps(response_data, indent=2, ensure_ascii=False))

                assistant_message = response_data.get("message", {})
                tool_calls_payload = assistant_message.get("tool_calls")
                if tool_calls_payload:
                    self.add_to_workspace("Model", "Bir araç kullanmak istiyor...")
                    self.history.append({"role": "assistant", "content": "", "tool_calls": tool_calls_payload})
                    self.handle_tool_calls(model_url, model_name, [system_message, {"role": "user", "content": user_prompt}], tool_calls_payload, tools)
                else:
                    content = assistant_message.get("content", "")
                    parsed_tool_calls = None
                    if isinstance(content, str) and content:
                        try:
                            m = re.search(r"\[(?:\s|\S)*?\{\s*\"type\"\s*:\s*\"function\"(?:.|\n)*?\]\s*", content)
                            if m:
                                parsed_tool_calls = json.loads(m.group(0))
                        except Exception:
                            parsed_tool_calls = None
                    if parsed_tool_calls:
                        self.add_to_workspace("Model", "İçerikte gömülü tool çağrıları bulundu, işleniyor...")
                        self.history.append({"role": "assistant", "content": "", "tool_calls": parsed_tool_calls})
                        self.handle_tool_calls(model_url, model_name, [system_message, {"role": "user", "content": user_prompt}], parsed_tool_calls, tools)
                    else:
                        content_final = content or "Modelden içerik alınamadı."
                        self.add_to_workspace("Model", content_final)
                        self.history.append({"role": "assistant", "content": content_final})
            except Exception as e2:
                error_msg = f"Yeniden deneme de başarısız: {e2}"
                self.add_to_workspace("Sistem Hatası", error_msg)
                messagebox.showerror("API Hatası", error_msg)
        except requests.exceptions.RequestException as e:
            error_msg = f"API isteği başarısız: {e}"
            self.add_to_workspace("Sistem Hatası", error_msg)
            messagebox.showerror("API Hatası", error_msg)
        except json.JSONDecodeError:
            error_msg = "API'den gelen cevap JSON formatında değil."
            self.add_to_workspace("Sistem Hatası", error_msg)
            messagebox.showerror("API Cevap Hatası", error_msg)
        except Exception as e:
            error_msg = f"Beklenmedik bir hata oluştu: {e}"
            self.add_to_workspace("Sistem Hatası", error_msg)
            messagebox.showerror("Genel Hata", error_msg)
        else:
            # Update session tracking after a successful call
            self.current_model_name = model_name
            self.current_chat_url = chat_url
            self.reset_history_next_prompt = False

    def handle_tool_calls(self, model_url: str, model_name: str, messages_history: list, tool_calls: list, tools_definition: list):
        """
        Executes tool calls requested by the model and sends results back to Ollama.
        """
        # Add the assistant's message with tool_calls to history for the next API call
        messages_for_next_turn = messages_history + [{"role": "assistant", "content": "", "tool_calls": tool_calls}]

        tool_results = []

        for tool_call in tool_calls:
            function_name_from_model = tool_call["function"]["name"]
            # Arguments are already a dict because response.json() parsed the whole body.
            arguments = tool_call["function"]["arguments"]
            # The model might not return an ID for the tool call, handle this safely.
            tool_call_id = tool_call.get("id")

            # Although the official spec implies an ID, some models might omit it.
            # If no ID, we create a temporary one to proceed.
            if not tool_call_id:
                import uuid
                tool_call_id = f"call_{uuid.uuid4()}"
                self.add_to_workspace("Sistem Uyarısı", f"Tool çağrısı '{function_name_from_model}' için model tarafından bir 'id' sağlanmadı. Geçici ID oluşturuldu: {tool_call_id}")

            self.add_to_workspace("Sistem", f"Tool Çağrısı: {function_name_from_model} ID: {tool_call_id} Argümanlar: {arguments}")

            result_content = ""
            try:
                if function_name_from_model.startswith("calculate_turning_"):
                    # Find the original calculation name (key) by matching the generated function name
                    actual_calc_name = None
                    model_func_name_part = function_name_from_model.replace("calculate_turning_", "")
                    for key in ec.turning_definitions.keys():
                        key_func_part = key.replace(' ', '_').lower()
                        if model_func_name_part == key_func_part:
                            actual_calc_name = key
                            break
                    if not actual_calc_name:
                        raise ValueError(f"Geçersiz fonksiyon adı, bilinen bir tornalama hesabıyla eşleştirilemedi: {function_name_from_model}")

                    params_info = ec.get_calculation_params('turning', actual_calc_name)
                    ordered_args = [arguments[p['name']] for p in params_info]
                    calc_result = ec.calculate_turning(actual_calc_name, *ordered_args)
                    result_content = f"{calc_result['value']:.2f} {calc_result['units']}"

                elif function_name_from_model.startswith("calculate_milling_"):
                    # Find the original calculation name (key)
                    actual_calc_name = None
                    model_func_name_part = function_name_from_model.replace("calculate_milling_", "")
                    for key in ec.milling_definitions.keys():
                        key_func_part = key.replace(' ', '_').lower()
                        if model_func_name_part == key_func_part:
                            actual_calc_name = key
                            break
                    if not actual_calc_name:
                        raise ValueError(f"Geçersiz fonksiyon adı, bilinen bir frezeleme hesabıyla eşleştirilemedi: {function_name_from_model}")

                    params_info = ec.get_calculation_params('milling', actual_calc_name)
                    ordered_args = [arguments[p['name']] for p in params_info]
                    calc_result = ec.calculate_milling(actual_calc_name, *ordered_args)
                    result_content = f"{calc_result['value']:.2f} {calc_result['units']}"

                elif function_name_from_model == "calculate_material_mass":
                    # Normalize and validate inputs from the model
                    try:
                        raw_shape_key = arguments.pop("shape_key")
                    except KeyError:
                        raise ValueError("'shape_key' parametresi eksik")

                    # Canonicalize common shape aliases (TR/EN)
                    shape_aliases = {
                        'cylinder': 'circle',
                        'silindir': 'circle',
                        'yuvarlak': 'circle',
                        'daire': 'circle',
                        'yarım daire': 'semi-circle',
                        'semi_circle': 'semi-circle',
                        'semi-circle': 'semi-circle',
                        'dikdörtgen': 'rectangle',
                        'kare': 'square',
                        'üçgen': 'triangle',
                        'paralelkenar': 'parallelogram',
                        'eşkenar dörtgen': 'rhombus',
                        'yamuk': 'trapezium',
                    }
                    # Ensure normalized, non-empty string key
                    shape_key = shape_aliases.get(str(raw_shape_key).lower(), str(raw_shape_key).lower())

                    # Density or material name
                    try:
                        density = float(arguments.pop("density"))
                    except KeyError:
                        # Try to infer from material name (TR/EN aliases) or user text
                        material_key = None
                        for mk in ("material", "malzeme", "material_name"):
                            if mk in arguments:
                                material_key = mk
                                break
                        mat_aliases = {
                            'çelik': 'Çelik', 'steel': 'Çelik',
                            'alüminyum': 'Alüminyum', 'aluminum': 'Alüminyum', 'aluminium': 'Alüminyum',
                            'bakır': 'Bakır', 'copper': 'Bakır',
                            'pirinç': 'Pirinç', 'brass': 'Pirinç',
                            'dökme demir': 'Dökme Demir', 'cast iron': 'Dökme Demir',
                            'plastik': 'Plastik', 'plastic': 'Plastik',
                            'titanyum': 'Titanyum', 'titanium': 'Titanyum',
                            'kurşun': 'Kurşun', 'lead': 'Kurşun',
                            'çinko': 'Çinko', 'zinc': 'Çinko',
                            'nikel': 'Nikel', 'nickel': 'Nikel',
                        }
                        canonical_mat = None
                        if material_key:
                            raw_mat = str(arguments.pop(material_key)).strip()
                            canonical_mat = mat_aliases.get(raw_mat.lower(), raw_mat)
                        else:
                            # Scan recent user message for a known material keyword
                            user_text = None
                            for msg in reversed(messages_history):
                                if msg.get("role") == "user" and isinstance(msg.get("content"), str):
                                    user_text = msg["content"]
                                    break
                            if user_text:
                                lower_text = user_text.lower()
                                for alias, canonical in mat_aliases.items():
                                    if alias in lower_text:
                                        canonical_mat = canonical
                                        break
                        if canonical_mat:
                            try:
                                density = float(ec.get_material_density(canonical_mat))
                            except ValueError:
                                density = float(ec.get_material_density(canonical_mat.title()))
                        else:
                            raise ValueError("'density' (g/cm³) veya malzeme adı saptanamadı")

                    # Accept length synonyms if model omits the exact key
                    length = arguments.pop("length", None)  # Extrusion length in mm
                    if length is None:
                        for len_key in ("L", "uzunluk", "boy", "length_mm"):
                            if len_key in arguments:
                                length = arguments.pop(len_key)
                                break
                    if length is None:
                        # Try to infer from latest user text (e.g., "boy 100 mm", "uzunluk 120")
                        try:
                            user_text = None
                            for msg in reversed(messages_history):
                                if msg.get("role") == "user" and isinstance(msg.get("content"), str):
                                    user_text = msg["content"].lower()
                                    break
                            if user_text:
                                import re as _re
                                m = _re.search(r"(boy|uzunluk|length)\D*(\d+(?:[\.,]\d+)?)", user_text)
                                if m:
                                    length = m.group(2).replace(',', '.')
                        except Exception:
                            pass
                    if length is None:
                        raise ValueError("'length' (mm) parametresi eksik")
                    try:
                        length = float(length)
                    except Exception:
                        raise ValueError("'length' (mm) sayısal olmalıdır")

                    # Handle dimension synonyms, e.g., diameter -> radius for circle-like shapes
                    if shape_key in ("circle", "semi-circle"):
                        if "radius" not in arguments:
                            # Common alternates that might be supplied
                            for dkey in ("diameter", "cap", "çap", "D"):
                                if dkey in arguments:
                                    try:
                                        arguments["radius"] = float(arguments.pop(dkey)) / 2.0
                                    except Exception:
                                        # If conversion fails, let it fall through to missing param error below
                                        pass
                                    break
                        else:
                            # If user specified diameter in text but model wrongly set radius=diameter, fix it
                            try:
                                user_text = None
                                for msg in reversed(messages_history):
                                    if msg.get("role") == "user" and isinstance(msg.get("content"), str):
                                        user_text = msg["content"].lower()
                                        break
                                if user_text and ("çap" in user_text or "diameter" in user_text or "cap" in user_text):
                                    import re as _re
                                    m = _re.search(r"(çap|diameter|cap)\D*(\d+(?:[\.,]\d+)?)", user_text)
                                    if m:
                                        dia_val = float(m.group(2).replace(',', '.'))
                                        rad_val = float(arguments.get("radius"))
                                        # If radius equals diameter (within tolerance), correct it
                                        if abs(rad_val - dia_val) < 1e-6:
                                            arguments["radius"] = dia_val / 2.0
                            except Exception:
                                pass

                    # Build ordered args expected by EngineeringCalculator
                    shape_dim_names = ec.get_shape_parameters(shape_key)
                    try:
                        shape_dims_values = [float(arguments[dim_name]) for dim_name in shape_dim_names]
                    except KeyError as e:
                        missing = str(e).strip("'")
                        raise ValueError(f"'{missing}' parametresi eksik")

                    all_args_for_mass = shape_dims_values + [length]
                    mass_val = ec.calculate_material_mass(shape_key, density, *all_args_for_mass)
                    result_content = f"{mass_val:.2f} gram"

                else:
                    # Unknown function: try a smart fallback for cylinder/circle volume-like calls
                    fname = str(function_name_from_model).lower()
                    fallback_done = False
                    try:
                        if any(k in fname for k in ("cylinder", "circle", "volume")):
                            # Attempt to compute circle-based mass using provided arguments
                            shape_key = "circle"
                            # length/height mapping
                            length_val = arguments.get("length") or arguments.get("height")
                            if length_val is None:
                                for len_key in ("L", "uzunluk", "boy", "length_mm"):
                                    if len_key in arguments:
                                        length_val = arguments.get(len_key)
                                        break
                            if length_val is None:
                                # Infer from user text
                                try:
                                    user_text = None
                                    for msg in reversed(messages_history):
                                        if msg.get("role") == "user" and isinstance(msg.get("content"), str):
                                            user_text = msg["content"].lower()
                                            break
                                    if user_text:
                                        import re as _re
                                        m = _re.search(r"(boy|uzunluk|length)\D*(\d+(?:[\.,]\d+)?)", user_text)
                                        if m:
                                            length_val = float(m.group(2).replace(',', '.'))
                                except Exception:
                                    pass
                            # radius/diameter mapping
                            radius_val = arguments.get("radius")
                            if radius_val is None:
                                for dkey in ("diameter", "cap", "çap", "D"):
                                    if dkey in arguments:
                                        try:
                                            radius_val = float(arguments.get(dkey)) / 2.0
                                        except Exception:
                                            pass
                                        break
                            else:
                                # If user text mentions diameter and model used radius=diameter, correct it
                                try:
                                    user_text = None
                                    for msg in reversed(messages_history):
                                        if msg.get("role") == "user" and isinstance(msg.get("content"), str):
                                            user_text = msg["content"].lower()
                                            break
                                    if user_text and ("çap" in user_text or "diameter" in user_text or "cap" in user_text):
                                        import re as _re
                                        m = _re.search(r"(çap|diameter|cap)\D*(\d+(?:[\.,]\d+)?)", user_text)
                                        if m:
                                            dia_val = float(m.group(2).replace(',', '.'))
                                            r_val = float(radius_val)
                                            if abs(r_val - dia_val) < 1e-6:
                                                radius_val = dia_val / 2.0
                                except Exception:
                                    pass
                            # density: direct or by guessing from user text
                            density_val = arguments.get("density")
                            if density_val is None:
                                mat_aliases2 = {
                                    'çelik': 'Çelik', 'steel': 'Çelik',
                                    'alüminyum': 'Alüminyum', 'aluminum': 'Alüminyum', 'aluminium': 'Alüminyum',
                                    'bakır': 'Bakır', 'copper': 'Bakır',
                                    'pirinç': 'Pirinç', 'brass': 'Pirinç',
                                    'dökme demir': 'Dökme Demir', 'cast iron': 'Dökme Demir',
                                    'plastik': 'Plastik', 'plastic': 'Plastik',
                                    'titanyum': 'Titanyum', 'titanium': 'Titanyum',
                                    'kurşun': 'Kurşun', 'lead': 'Kurşun',
                                    'çinko': 'Çinko', 'zinc': 'Çinko',
                                    'nikel': 'Nikel', 'nickel': 'Nikel',
                                }
                                user_text = None
                                for msg in reversed(messages_history):
                                    if msg.get("role") == "user" and isinstance(msg.get("content"), str):
                                        user_text = msg["content"]
                                        break
                                if user_text:
                                    lower_text = user_text.lower()
                                    guessed_mat = None
                                    for alias, canonical in mat_aliases2.items():
                                        if alias in lower_text:
                                            guessed_mat = canonical
                                            break
                                    if guessed_mat:
                                        density_val = ec.get_material_density(guessed_mat)
                            if radius_val is not None and length_val is not None and density_val is not None:
                                mass_val = ec.calculate_material_mass(shape_key, float(density_val), float(radius_val), float(length_val))
                                result_content = f"{mass_val:.2f} gram"
                                fallback_done = True
                    except Exception:
                        fallback_done = False
                    if not fallback_done:
                        result_content = f"Bilinmeyen fonksiyon: {function_name_from_model}"

                self.add_to_workspace("Tool Sonucu", f"Fonksiyon: {function_name_from_model}, Sonuç: {result_content}")
                tool_results.append({
                    "tool_call_id": tool_call_id,
                    "role": "tool",
                    "content": result_content
                })
                # Append to structured history as well
                self.history.append({
                    "tool_call_id": tool_call_id,
                    "role": "tool",
                    "content": result_content
                })

            except Exception as e:
                error_str = f"Tool çalıştırma hatası ({function_name_from_model}): {e}"
                self.add_to_workspace("Sistem Hatası", error_str)
                tool_results.append({
                    "tool_call_id": tool_call_id,
                    "role": "tool",
                    "content": error_str
                })

        # Send the tool results back to Ollama
        messages_for_next_turn += tool_results

        payload_after_tool_call = {
            "model": model_name,
            "messages": messages_for_next_turn,
            "stream": False,
            "tools": tools_definition,
            "options": {
                "temperature": 0.2,
                "top_p": 0.9
            }
        }

        self.add_to_workspace("Sistem", "Tool sonuçları modele gönderiliyor...")
        try:
            chat_url = self._normalize_chat_url(model_url)
            response = requests.post(chat_url, json=payload_after_tool_call, headers={"Content-Type": "application/json"}, timeout=60)
            response.raise_for_status()
            final_response_data = response.json()

            self.add_to_workspace("Model Ham Cevap (Tool Sonrası)", json.dumps(final_response_data, indent=2, ensure_ascii=False))

            final_content = final_response_data.get("message", {}).get("content", "Modelden nihai cevap alınamadı.")
            self.add_to_workspace("Model", final_content)
            # Append final assistant content to history
            self.history.append({"role": "assistant", "content": final_content})

        except requests.exceptions.ReadTimeout as e:
            # Retry once with same payload (tool results are deterministic)
            self.add_to_workspace("Sistem Uyarısı", "Tool sonrası istek zaman aşımı; tek seferlik yeniden deneme yapılıyor...")
            try:
                chat_url = self._normalize_chat_url(model_url)
                response = requests.post(chat_url, json=payload_after_tool_call, headers={"Content-Type": "application/json"}, timeout=60)
                response.raise_for_status()
                final_response_data = response.json()

                self.add_to_workspace("Model Ham Cevap (Tool Sonrası)", json.dumps(final_response_data, indent=2, ensure_ascii=False))

                final_content = final_response_data.get("message", {}).get("content", "Modelden nihai cevap alınamadı.")
                self.add_to_workspace("Model", final_content)
                self.history.append({"role": "assistant", "content": final_content})
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

    def on_model_change(self, event=None):
        """Called when the user selects a different model. Flags history reset for next prompt."""
        try:
            new_model = self.model_selection_combo.get()
        except Exception:
            new_model = None
        self.reset_history_next_prompt = True
        if new_model:
            self.add_to_workspace("Sistem", f"Model değiştirildi: {new_model}. Bir sonraki istek yeni oturum olarak gönderilecek.")

    def on_model_url_change(self, event=None):
        """Called when the model URL field changes. Flags history reset for next prompt if URL differs."""
        try:
            new_url = self._normalize_chat_url(self.model_url_entry.get())
        except Exception:
            new_url = None
        if new_url and new_url != self.current_chat_url:
            self.reset_history_next_prompt = True
            self.add_to_workspace("Sistem", f"Model URL değişti: {new_url}. Bir sonraki istek yeni oturum olarak gönderilecek.")


    def add_to_workspace(self, source: str, message: str):
        """
        Adds a message to the result_text (shared workspace) with a source prefix.

        Args:
            source (str): "Kullanıcı", "Model", "Sistem", "Hesaplama Sonucu", etc.
            message (str): The message content.
        """
        formatted_message = f"\n\n{source}: {message}\n"
        self.result_text.insert(tk.END, formatted_message)
        self.result_text.see(tk.END) # Scroll to the end


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
            self.calculation['values'] = list(available_calcs.keys()) # Update values of the second combobox
            
            if list(available_calcs.keys()): # If there are calculations available
                self.calculation.set(list(available_calcs.keys())[0]) # Set to the first one
                self.calculation.config(state="readonly")
            else: # No calculations for this type
                self.calculation.set("")
                self.calculation.config(state="disabled")

            # Bind event for updating input fields when a specific calculation is chosen
            self.calculation.bind('<<ComboboxSelected>>', self.update_input_fields)
            self.update_input_fields() # Trigger update for the currently selected calculation
        else: # Should not happen if combobox is properly populated
            self.calculation['values'] = []
            self.calculation.set("")
            self.calculation.config(state="disabled")
            self.update_input_fields() # Clear input fields

    def calculate(self):
        """
        Handles the main calculation logic when the "HESAPLA" button is clicked.
        
        It retrieves selected calculation type, specific calculation, and input values,
        then calls `perform_calculation` and updates the result display.
        Includes error handling for invalid inputs or calculation issues.
        """
        try:
            calc_type = self.calc_type.get() # Selected calculation category (e.g., "Malzeme Hesaplamaları")
            calculation_name = self.calculation.get() # Specific calculation selected (e.g., "Kütle Hesabı")

            # Validate that a calculation is actually selected
            if not calc_type or not calculation_name:
                messagebox.showwarning("Uyarı", "Lütfen bir hesaplama türü ve hesaplama seçin.") # Turkish: "Warning", "Please select a calculation type and a calculation."
                return

            # Collect input values from dynamically generated fields
            input_values = {}
            for param_key, field_widget in self.input_fields.items():
                value_str = field_widget.get()
                if not value_str: # Check for empty field
                    messagebox.showerror("Hata", f"'{param_key}' için değer girilmemiş.") # Turkish: "Error", "Value not entered for '{param_key}'."
                    return
                try:
                    if param_key != 'Şekil': # 'Şekil' (Shape) is a string from combobox
                        input_values[param_key] = float(value_str)
                    else:
                        input_values[param_key] = value_str # Shape name is a string
                except ValueError:
                    # Error message if conversion to float fails for numerical inputs
                    messagebox.showerror("Hata", f"'{param_key}' için geçersiz sayısal değer: {value_str}") # Turkish: "Error", "Invalid numerical value for '{param_key}': {value_str}"
                    return
            
            # Perform the calculation using the collected data
            calculation_result = self.perform_calculation(calc_type, calculation_name, input_values)
            
            # Update the display with the results
            self.update_result_display({
                'calculation': calculation_name,
                'parameters': input_values, # Pass collected values for display
                'result': calculation_result
            })

        except ValueError as ve: # Catch specific ValueErrors raised by our logic or calculator
            messagebox.showerror("Giriş Hatası", str(ve)) # Turkish: "Input Error"
        except Exception as e: # Catch any other unexpected errors during calculation
            messagebox.showerror("Hesaplama Hatası", f"Beklenmedik bir hata oluştu: {str(e)}") # Turkish: "Calculation Error", "An unexpected error occurred: {str(e)}"


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
        shape_turkish_name = input_params['Şekil'] # Turkish name from Combobox
        
        # Ensure reverse_shape_names is populated (should be by update_input_fields)
        if not hasattr(self, 'reverse_shape_names') or not self.reverse_shape_names:
            # This is a fallback, ideally self.reverse_shape_names is always up-to-date.
            self.reverse_shape_names = {v: k for k, v in ec.get_available_shapes().items()}

        shape_key = self.reverse_shape_names.get(shape_turkish_name) # Convert Turkish name to internal key
        if not shape_key:
            raise ValueError(f"Geçersiz şekil adı: {shape_turkish_name}") # Turkish: "Invalid shape name"
        
        density = float(input_params['Yoğunluk']) # Turkish: "Density"
        
        # Dynamically get the list of required dimension parameters for the selected shape_key
        # from EngineeringCalculator (e.g., ['width', 'height'] or ['radius'])
        param_names_from_calc = ec.get_shape_parameters(shape_key)
        
        # Map these English parameter names to the Turkish keys used in `input_params`
        # This mapping is crucial for fetching correct values from the GUI's input_params dictionary.
        param_to_gui_key_map = { # English (from calculator) to Turkish (GUI key)
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

        args_for_calculator = [] # List to hold dimension values in the order expected by EngineeringCalculator
        for p_name_english in param_names_from_calc:
            # Find the Turkish GUI key for the current English parameter name
            gui_key_turkish = param_to_gui_key_map.get(p_name_english, p_name_english.capitalize()) # Fallback to capitalized English name if no direct map
            if gui_key_turkish not in input_params:
                raise ValueError(f"\'{gui_key_turkish}\' parametresi için değer eksik.") # Turkish: "Missing value for parameter '{gui_key_turkish}'."
            args_for_calculator.append(float(input_params[gui_key_turkish]))
        
        # Append the common 'Uzunluk' (Length) parameter, which is always present for extrusion
        if 'Uzunluk' not in input_params:
             raise ValueError("'Uzunluk' parametresi için değer eksik.") # Turkish: "Missing value for parameter 'Uzunluk'."
        args_for_calculator.append(float(input_params['Uzunluk']))

        # Call the core calculation method from EngineeringCalculator
        # Note: EngineeringCalculator.calculate_material_mass now handles mm³ to cm³ conversion.
        mass_value = ec.calculate_material_mass(shape_key, density, *args_for_calculator)
        return f"{mass_value:.2f} gram" # Result formatted to two decimal places


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
        param_info_list = ec.get_calculation_params('turning', calculation_name)
        
        args_for_calculator = []
        for param_info in param_info_list:
            internal_name = param_info['name']
            if internal_name not in input_params:
                raise ValueError(f"'{param_info['display_text_turkish']}' parametresi için değer eksik.")
            args_for_calculator.append(float(input_params[internal_name]))
        
        # The `calculation_name` (e.g., "Kesme Hızı") is directly used as the method_key
        result_dict = ec.calculate_turning(calculation_name, *args_for_calculator)
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

        param_info_list = ec.get_calculation_params('milling', calculation_name)
        
        args_for_calculator = []
        for param_info in param_info_list:
            internal_name = param_info['name']
            if internal_name not in input_params:
                raise ValueError(f"'{param_info['display_text_turkish']}' parametresi için değer eksik.")
            args_for_calculator.append(float(input_params[internal_name]))

        result_dict = ec.calculate_milling(calculation_name, *args_for_calculator)
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
        if calc_category == 'Malzeme Hesaplamaları': # Turkish: "Material Calculations"
            return self.calculate_material_mass(calc_name, params_values)
        elif calc_category == 'Tornalama Hesaplamaları': # Turkish: "Turning Calculations"
            return self.calculate_turning(calc_name, params_values)
        elif calc_category == 'Frezeleme Hesaplamaları': # Turkish: "Milling Calculations"
            return self.calculate_milling(calc_name, params_values)
        else:
            # This case should ideally not be reached if GUI is set up correctly with calc_types
            raise ValueError(f"Bilinmeyen hesaplama kategorisi: {calc_category}") # Turkish: "Unknown calculation category"

    def enable_execute_mode(self, event: tk.Event | None = None):
        """
        Enables an experimental 'execute mode' for the result text area.
        
        This mode allows selected text in the results area to be evaluated as Python code.
        Changes the background color of the result text area to indicate the mode.

        Args:
            event: The Tkinter event that triggered this method (e.g., a key press). Default is None.
        """
        self.result_text.config(bg='#ffffd0') # Light yellow background to indicate execute mode.
        self.execute_mode = True
        self.result_text.insert(tk.END, "\n\n--- Execute Modu Aktif --- \nKod seçip Ctrl+C ile çalıştırın.\n") # Turkish: Execute Mode Active. Select code and run with Ctrl+C

    def execute_calculation(self, event: tk.Event | None = None):
        """
        Executes Python code selected in the result text area if 'execute mode' is active.

        The code is evaluated in a limited scope with `EngineeringCalculator` instance (`ec` or `calc`)
        and `math.pi` available. The result of the evaluation is appended to the text area.

        Args:
            event: The Tkinter event (e.g., a key press like Ctrl+C). Default is None.
        """
        if not hasattr(self, 'execute_mode') or not self.execute_mode:
            return # Do nothing if execute mode is not enabled.

        try:
            # Get the selected text from the result display area.
            selected_code = self.result_text.get('sel.first', 'sel.last')
            if selected_code:
                # Define a limited local scope for eval().
                # Provides access to the calculator instance and math.pi.
                local_scope = {'calc': ec, 'ec': ec, 'pi': math.pi}
                
                # Evaluate the selected code.
                # WARNING: eval() can be dangerous if the input string is not controlled.
                # Here it's assumed the user is intentionally running code they might have pasted or typed.
                evaluation_result = eval(selected_code, {'__builtins__': {}}, local_scope) # Restricted builtins for safety.
                
                self.result_text.insert('insert', f'\n>>> {selected_code}\nSonuç: {evaluation_result}\n') # Turkish: Result
            else:
                self.result_text.insert(tk.END, "\nSeçili kod yok.\n") # Turkish: No code selected.
        except Exception as e:
            # Display any error during code execution in a messagebox and in the text area.
            error_message = f"Kod çalıştırma hatası: {str(e)}" # Turkish: Code execution error
            messagebox.showerror("Hata", error_message)
            self.result_text.insert('insert', f'\nHata: {error_message}\n')
        finally:
            # Always disable execute mode and reset background after an attempt.
            self.execute_mode = False
            self.result_text.config(bg='white') # Reset background to normal.
            self.result_text.insert(tk.END, "\n--- Execute Modu Devre Dışı ---\n") # Turkish: Execute Mode Deactivated


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
            self.reverse_shape_names = {v: k for k, v in available_shapes_map.items()}
            shape_display_names = list(available_shapes_map.values())

            shape_frame = ttk.Frame(self.params_container, style='Calc.TFrame')
            shape_frame.pack(fill='x', pady=2, padx=5)
            ttk.Label(shape_frame, text="Şekil:", style='Calc.TLabel').pack(side='left', padx=(0,5))
            self.shape_combo = ttk.Combobox(shape_frame, values=shape_display_names, state="readonly")
            self.shape_combo.pack(side='left', fill='x', expand=True)
            if shape_display_names:
                self.shape_combo.set(shape_display_names[0])
            self.shape_combo.bind('<<ComboboxSelected>>', self._update_material_params)
            self.input_fields['Şekil'] = self.shape_combo
            # Tooltip for shape selection
            AdvancedToolTip(self.shape_combo, self.tooltips.get("Şekil", "Şekil seçin."))
            self._update_material_params()
        else:
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
                        label_widget.pack(side='left', padx=(0,5))
                        entry = ttk.Entry(param_input_frame)
                        entry.pack(side='left', fill='x', expand=True)
                        self.input_fields[param_info['name']] = entry
                        # Tooltip for each parameter
                        tooltip_key = param_info['name']
                        tooltip_text = self.tooltips.get(tooltip_key, self.tooltips.get(param_info['display_text_turkish'], f"{param_info['display_text_turkish']} girin."))
                        AdvancedToolTip(entry, tooltip_text)
                except ValueError as e:
                    ttk.Label(self.params_container, text="Bu hesaplama için parametre tanımlanmamış.", style='Calc.TLabel').pack()

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
        ttk.Label(density_frame, text="Yoğunluk [g/cm³]:", style='Calc.TLabel').pack(side='left', padx=(0,5))
        density_entry = ttk.Entry(density_frame, width=10)
        density_entry.pack(side='left', fill='x', expand=True)
        self.input_fields['Yoğunluk'] = density_entry
        # Tooltip for density
        AdvancedToolTip(density_entry, self.tooltips.get("Yoğunluk", "Malzemenin yoğunluğunu girin."))

        material_names = list(ec.material_density.keys())
        material_combo = ttk.Combobox(density_frame, values=material_names, state="readonly", width=15)
        material_combo.pack(side='left', padx=(10,0))
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
        AdvancedToolTip(material_combo, self.tooltips.get("MalzemeSec", "Bir malzeme seçerek yoğunluğu otomatik doldurun."))

        selected_shape_turkish = self.shape_combo.get() if self.shape_combo else None
        shape_key = self.reverse_shape_names.get(selected_shape_turkish) if selected_shape_turkish else None
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
                turkish_label = param_to_gui_key_map.get(p_name_english, p_name_english.capitalize())
                gui_params_to_create.append((turkish_label, 'mm', p_name_english))
            gui_params_to_create.append(('Uzunluk', 'mm', 'Uzunluk'))
            for param_label_turkish, unit_str, tooltip_key in gui_params_to_create:
                param_input_frame = ttk.Frame(self.params_container, style='Calc.TFrame')
                param_input_frame.pack(fill='x', pady=2, padx=5)
                label_full_text = f"{param_label_turkish} [{unit_str}]:"
                ttk.Label(param_input_frame, text=label_full_text, style='Calc.TLabel').pack(side='left', padx=(0,5))
                entry = ttk.Entry(param_input_frame)
                entry.pack(side='left', fill='x', expand=True)
                self.input_fields[param_label_turkish] = entry
                # Tooltip for each shape parameter
                tooltip_text = self.tooltips.get(tooltip_key, self.tooltips.get(param_label_turkish, f"{param_label_turkish} girin."))
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

        param_details = "\n".join([f"  - {key.replace('_', ' ').capitalize()}: {value}" for key, value in params.items()])
        if param_details:
            self.add_to_workspace("Giriş Parametreleri", param_details)

        self.add_to_workspace("Hesaplama Sonucu", result_str)


if __name__ == "__main__":
    tooltips = load_tooltips('tooltips.json')
    root = tk.Tk()
    app = AdvancedCalculator(root,tooltips)
    root.mainloop()
