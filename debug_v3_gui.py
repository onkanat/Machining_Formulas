#!/usr/bin/env python3
"""
V3 GUI Debug Version - Enhanced with detailed logging and widget inspection
This version helps identify why form fields appear empty.
"""

import json
import logging
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from typing import Dict, List

# Core calculation logic (PRESERVED FROM V1)
from engineering_calculator import EngineeringCalculator
from material_utils import MaterialMassParameters, prepare_material_mass_arguments

# V3 Components - with error handling
try:
    from workspace_buffer import WorkspaceBuffer
    from workspace_editor import WorkspaceEditor
    from ollama_utils_v2 import (
        single_chat_request,
        get_available_models,
        test_connection,
    )

    WORKSPACE_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Workspace components not available: {e}")
    WORKSPACE_AVAILABLE = False

# V1 Components (PRESERVED)
try:
    from execute_mode import ExecuteModeMixin

    EXECUTE_MODE_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Execute mode not available: {e}")
    EXECUTE_MODE_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("v3_gui_debug.log"), logging.StreamHandler()],
)

logger = logging.getLogger(__name__)

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


class DebugV3Calculator:
    """Debug version of V3 Calculator with enhanced logging."""

    def __init__(self, root: tk.Tk, tooltips: Dict[str, str]):
        logger.info("Initializing DebugV3Calculator")

        self.root = root
        self.tooltips = tooltips

        # Initialize workspace buffer if available
        if WORKSPACE_AVAILABLE:
            self.workspace_buffer = WorkspaceBuffer()
        else:
            self.workspace_buffer = None

        # Model configuration
        self.current_model_url = ""
        self.current_model_name = ""
        self.ollama_models: List[str] = []

        # Setup UI
        self.setup_ui()
        self._apply_default_geometry()

        # Initialize model connection
        self.refresh_model_list()

        # Debug: Log widget hierarchy after setup
        self.debug_widget_hierarchy()

    def setup_ui(self):
        """Setup the main V3 interface with debug logging."""
        logger.info("Setting up UI")

        # Configure root window
        self.root.title("🔧 DEBUG Mühendislik Hesaplayıcı V3")
        self.root.geometry(f"{DEFAULT_WINDOW_SIZE[0]}x{DEFAULT_WINDOW_SIZE[1]}")

        # Configure styles
        self._setup_styles()

        # Create main layout
        self._create_main_layout()

        # Create menu bar
        self._create_menu_bar()

        # Create status bar
        self._create_status_bar()

        logger.info("UI setup completed")

    def _setup_styles(self):
        """Setup ttk styles with debug info."""
        logger.debug("Setting up styles")

        style = ttk.Style()
        style.theme_use("clam")

        # Configure custom styles with debug colors
        style.configure("Calc.TFrame", background="#f0f0f0")
        style.configure("Calc.TLabel", background="#f0f0f0", font=("Arial", 10))
        style.configure(
            "Header.TLabel", background="#f0f0f0", font=("Arial", 12, "bold")
        )
        style.configure("Calc.TButton", font=("Arial", 9))
        style.configure("Calc.TCombobox", fieldbackground="white", font=("Arial", 9))

        # Debug style for highlighting
        style.configure("Debug.TFrame", background="#ffcccc")  # Light red
        style.configure(
            "Debug.TLabel", background="#ffcccc", font=("Arial", 10, "bold")
        )

    def _create_main_layout(self):
        """Create main layout with paned windows."""
        logger.debug("Creating main layout")

        # Main container
        main_container = ttk.Frame(self.root, style="Calc.TFrame")
        main_container.pack(fill="both", expand=True)

        # Create horizontal paned window
        self.paned_window = ttk.PanedWindow(main_container, orient="horizontal")
        self.paned_window.pack(fill="both", expand=True, padx=5, pady=5)

        # Left panel - Calculation tools
        self._create_calculation_panel()

        # Right panel - Workspace editor
        if WORKSPACE_AVAILABLE:
            self._create_workspace_panel()
        else:
            # Create placeholder panel
            placeholder_frame = ttk.Frame(self.paned_window, style="Debug.TFrame")
            self.paned_window.add(placeholder_frame, weight=3)

            ttk.Label(
                placeholder_frame,
                text="Workspace components not available\n(Import error)",
                style="Debug.TLabel",
            ).pack(expand=True)

    def _create_calculation_panel(self):
        """Create calculation tools panel with debug logging."""
        logger.debug("Creating calculation panel")

        calc_frame = ttk.Frame(self.paned_window, style="Calc.TFrame")
        self.paned_window.add(calc_frame, weight=1)

        # Calculation tools header
        header_frame = ttk.Frame(calc_frame, style="Calc.TFrame")
        header_frame.pack(fill="x", padx=5, pady=5)

        ttk.Label(
            header_frame,
            text="🧮 HESAPLAMA ARAÇLARI (DEBUG)",
            font=("Arial", 11, "bold"),
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
        """Create calculation categories and tools with debug logging."""
        logger.debug("Creating calculation categories")

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

    def _create_material_tab(self):
        """Create material calculations tab with enhanced debugging."""
        logger.debug("Creating material tab")

        material_frame = ttk.Frame(self.calc_notebook, style="Calc.TFrame")
        self.calc_notebook.add(material_frame, text="Malzeme")

        # Mass calculation
        self._create_mass_calc(material_frame)

    def _create_mass_calc(self, parent):
        """Create mass calculation with detailed debugging."""
        logger.info("Creating mass calculation form")

        frame = ttk.LabelFrame(parent, text="Kütle Hesabı (DEBUG)", style="Calc.TFrame")
        frame.pack(fill="x", padx=5, pady=5)

        # Shape selection
        shape_frame = ttk.Frame(frame, style="Calc.TFrame")
        shape_frame.pack(fill="x", padx=5, pady=2)
        ttk.Label(shape_frame, text="Şekil:", width=15).pack(side="left")

        logger.debug("Creating shape selection combobox")
        self.mass_shape = ttk.Combobox(shape_frame, width=15, style="Calc.TCombobox")
        self.mass_shape.pack(side="left", padx=(5, 0))

        # Populate shapes
        shapes = (
            "circle",
            "rectangle",
            "triangle",
            "square",
            "semi-circle",
            "tube",
            "sphere",
        )
        self.mass_shape["values"] = shapes
        self.mass_shape.set("circle")

        logger.info(f"Shape combobox created with values: {shapes}")
        logger.info(f"Current shape selection: {self.mass_shape.get()}")

        # Bind event with debug logging
        self.mass_shape.bind("<<ComboboxSelected>>", self._debug_update_mass_params)

        # Dynamic parameters frame
        logger.debug("Creating mass parameters frame")
        self.mass_params_frame = ttk.Frame(frame, style="Calc.TFrame")
        self.mass_params_frame.pack(fill="x", padx=5, pady=5)

        # Highlight parameters frame for debugging
        self.mass_params_frame.configure(style="Debug.TFrame")

        # Density input
        density_frame = ttk.Frame(frame, style="Calc.TFrame")
        density_frame.pack(fill="x", padx=5, pady=2)
        ttk.Label(density_frame, text="Yoğunluk:", width=15).pack(side="left")
        self.mass_density = ttk.Entry(density_frame, width=15)
        self.mass_density.pack(side="left", padx=(5, 0))
        ttk.Label(density_frame, text="g/cm³").pack(side="left", padx=(2, 0))

        # Initialize with circle parameters
        logger.info("Initializing with circle parameters")
        self._debug_update_mass_params()

        # Calculate button
        ttk.Button(frame, text="Hesapla", command=self._calculate_mass).pack(pady=5)

        # Result display
        self.mass_result = ttk.Label(
            frame, text="", font=("Arial", 10, "bold"), foreground="blue"
        )
        self.mass_result.pack(pady=2)

        # Inject to workspace button
        if WORKSPACE_AVAILABLE:
            ttk.Button(
                frame, text="📝 Çalışma Alanına Ekle", command=self._inject_mass
            ).pack(pady=2)

        # Debug info button
        ttk.Button(frame, text="🔍 Debug Info", command=self._show_debug_info).pack(
            pady=2
        )

    def _debug_update_mass_params(self, event=None):
        """Debug version of _update_mass_params with detailed logging."""
        logger.info("=== DEBUG _update_mass_params ===")

        try:
            shape = self.mass_shape.get()
            logger.info(f"Selected shape: '{shape}'")

            # Clear existing parameter widgets
            existing_widgets = self.mass_params_frame.winfo_children()
            logger.info(f"Clearing {len(existing_widgets)} existing widgets")

            for widget in existing_widgets:
                logger.debug(f"Destroying widget: {widget.__class__.__name__}")
                widget.destroy()

            # Get parameters from calculator
            logger.info(f"Getting parameters for shape: {shape}")
            param_names = ec.get_shape_parameters(shape)
            logger.info(f"Parameters from calculator: {param_names}")

            self.mass_param_widgets = {}

            for i, param_name in enumerate(param_names):
                logger.debug(f"Creating widget for parameter: {param_name}")

                frame = ttk.Frame(self.mass_params_frame, style="Calc.TFrame")
                frame.pack(fill="x", pady=1)

                # Use Turkish display names if available
                display_name = ec.PARAM_TURKISH_NAMES.get(
                    param_name, param_name.capitalize()
                )
                label_text = f"{display_name}:"

                logger.debug(f"Creating label: '{label_text}' for {param_name}")
                ttk.Label(frame, text=label_text, width=15).pack(side="left")

                logger.debug(f"Creating entry widget for {param_name}")
                entry = ttk.Entry(frame, width=15)
                entry.pack(side="left", padx=(5, 0))

                # Store widget
                self.mass_param_widgets[param_name] = entry
                logger.info(f"Created widget for {param_name}: {display_name}")

            logger.info(
                f"Total parameter widgets created: {len(self.mass_param_widgets)}"
            )

            # Debug: Check frame visibility
            self.debug_frame_visibility()

        except ValueError as e:
            logger.error(f"ValueError in _update_mass_params: {e}")
            # Show error message in the parameters frame
            error_frame = ttk.Frame(self.mass_params_frame, style="Debug.TFrame")
            error_frame.pack(fill="x", pady=1)

            error_label = ttk.Label(
                error_frame,
                text=f"Hata: {shape} şekli desteklenmiyor",
                foreground="red",
                font=("Arial", 9),
            )
            error_label.pack(side="left")
            self.mass_param_widgets = {}

        except Exception as e:
            logger.error(f"Unexpected error in _update_mass_params: {e}")
            import traceback

            logger.error(traceback.format_exc())

    def debug_frame_visibility(self):
        """Debug method to check frame visibility."""
        logger.debug("=== Frame Visibility Debug ===")

        try:
            # Check mass_params_frame
            frame = self.mass_params_frame
            logger.debug(f"Frame class: {frame.__class__.__name__}")
            logger.debug(f"Frame visible: {frame.winfo_ismapped()}")
            logger.debug(f"Frame geometry: {frame.winfo_geometry()}")
            logger.debug(f"Frame width: {frame.winfo_width()}")
            logger.debug(f"Frame height: {frame.winfo_height()}")
            logger.debug(f"Frame children: {len(frame.winfo_children())}")

            # Check each child widget
            for i, child in enumerate(frame.winfo_children()):
                logger.debug(f"  Child {i}: {child.__class__.__name__}")
                logger.debug(f"    Visible: {child.winfo_ismapped()}")
                logger.debug(f"    Geometry: {child.winfo_geometry()}")

        except Exception as e:
            logger.error(f"Error in debug_frame_visibility: {e}")

    def debug_widget_hierarchy(self):
        """Debug method to inspect widget hierarchy."""
        logger.info("=== Widget Hierarchy Debug ===")

        def inspect_widget(widget, level=0):
            indent = "  " * level
            logger.debug(f"{indent}{widget.__class__.__name__}: {widget.winfo_name()}")
            logger.debug(f"{indent}  Visible: {widget.winfo_ismapped()}")
            logger.debug(f"{indent}  Geometry: {widget.winfo_geometry()}")

            for child in widget.winfo_children():
                inspect_widget(child, level + 1)

        try:
            inspect_widget(self.root)
        except Exception as e:
            logger.error(f"Error in debug_widget_hierarchy: {e}")

        logger.info("=== End Widget Hierarchy Debug ===")

    def _show_debug_info(self):
        """Show debug information dialog."""
        debug_info = f"""
Debug Information:
================
Shape: {self.mass_shape.get()}
Parameter widgets: {len(self.mass_param_widgets)}
Parameters: {list(self.mass_param_widgets.keys())}

Frame Info:
- Visible: {self.mass_params_frame.winfo_ismapped()}
- Width: {self.mass_params_frame.winfo_width()}
- Height: {self.mass_params_frame.winfo_height()}
- Children: {len(self.mass_params_frame.winfo_children())}

Calculator Info:
- Available shapes: {list(ec.get_available_shapes()["shapes"])}
- Turkish labels: {len(ec.PARAM_TURKISH_NAMES)}
"""

        # Create debug window
        debug_window = tk.Toplevel(self.root)
        debug_window.title("Debug Information")
        debug_window.geometry("500x400")

        text_widget = tk.Text(debug_window, wrap=tk.WORD, font=("Consolas", 10))
        text_widget.pack(fill="both", expand=True, padx=10, pady=10)
        text_widget.insert("1.0", debug_info)
        text_widget.config(state="disabled")

        ttk.Button(debug_window, text="Close", command=debug_window.destroy).pack(
            pady=10
        )

    def _calculate_mass(self):
        """Calculate mass with debug logging."""
        logger.info("=== Mass Calculation ===")

        try:
            shape = self.mass_shape.get()
            density = float(self.mass_density.get())

            logger.info(f"Shape: {shape}, Density: {density}")

            # Get shape parameters
            params = {}
            for param_name, entry in self.mass_param_widgets.items():
                value = float(entry.get())
                params[param_name] = value
                logger.info(f"Parameter {param_name}: {value}")

            # Calculate mass using correct API
            param_values = list(params.values())
            result = ec.calculate_material_mass(shape, density, *param_values)

            logger.info(f"Calculation result: {result}")
            self.mass_result.config(text=f"Sonuç: {result:.2f} g")

        except ValueError as e:
            logger.error(f"ValueError in mass calculation: {e}")
            messagebox.showerror("Hata", "Lütfen geçerli sayısal değerler girin.")
        except Exception as e:
            logger.error(f"Error in mass calculation: {e}")
            messagebox.showerror("Hata", f"Hesaplama hatası: {str(e)}")

    def _inject_mass(self):
        """Inject mass calculation into workspace."""
        logger.info("Injecting mass calculation to workspace")
        # Implementation similar to original but with logging
        pass

    # Simplified implementations for other methods
    def _create_turning_tab(self):
        """Create turning calculations tab."""
        turning_frame = ttk.Frame(self.calc_notebook, style="Calc.TFrame")
        self.calc_notebook.add(turning_frame, text="Tornalama")

        ttk.Label(
            turning_frame,
            text="Tornalama hesaplamaları (debug mode)",
            font=("Arial", 10),
        ).pack(pady=20)

    def _create_milling_tab(self):
        """Create milling calculations tab."""
        milling_frame = ttk.Frame(self.calc_notebook, style="Calc.TFrame")
        self.calc_notebook.add(milling_frame, text="Frezeleme")

        ttk.Label(
            milling_frame,
            text="Frezeleme hesaplamaları (debug mode)",
            font=("Arial", 10),
        ).pack(pady=20)

    def _create_drilling_tab(self):
        """Create drilling calculations tab."""
        drilling_frame = ttk.Frame(self.calc_notebook, style="Calc.TFrame")
        self.calc_notebook.add(drilling_frame, text="Delme")

        ttk.Label(
            drilling_frame,
            text="Delme hesaplamaları (debug mode)",
            font=("Arial", 10),
        ).pack(pady=20)

    def _create_workspace_panel(self):
        """Create workspace editor panel."""
        if not WORKSPACE_AVAILABLE:
            return

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
        file_menu.add_command(label="Debug Info", command=self._show_debug_info)
        file_menu.add_separator()
        file_menu.add_command(label="Çıkış", command=self.root.quit)

    def _create_status_bar(self):
        """Create status bar."""
        self.status_frame = ttk.Frame(self.root, style="Calc.TFrame")
        self.status_frame.pack(fill="x", side="bottom")

        self.status_var = tk.StringVar()
        self.status_var.set("Debug mode - Hazır")

        status_label = ttk.Label(
            self.status_frame, textvariable=self.status_var, relief="sunken"
        )
        status_label.pack(fill="x", padx=2, pady=2)

    def refresh_model_list(self):
        """Refresh available models."""
        logger.info("Refreshing model list")
        # Simplified implementation
        pass

    def test_model_connection(self):
        """Test connection to model."""
        logger.info("Testing model connection")
        # Simplified implementation
        pass

    def _handle_model_suggestion(self, context: str):
        """Handle model suggestion request."""
        logger.info(f"Model suggestion requested: {context}")
        # Simplified implementation
        pass

    def _on_workspace_change(self, content: str):
        """Handle workspace content change."""
        logger.debug(f"Workspace content changed: {len(content)} characters")

    def _apply_default_geometry(self):
        """Apply default window geometry."""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")


def main():
    """Main entry point for Debug V3 GUI."""
    logger.info("Starting Debug V3 GUI")

    root = tk.Tk()

    # Load tooltips
    try:
        with open("tooltips.json", "r", encoding="utf-8") as f:
            tooltips = json.load(f)
    except FileNotFoundError:
        tooltips = {}

    # Create Debug V3 GUI
    app = DebugV3Calculator(root, tooltips)

    # Start GUI
    logger.info("Starting main loop")
    root.mainloop()


if __name__ == "__main__":
    main()
