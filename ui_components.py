"""V2 UI components for single-page workspace interface.

This module provides the UI components for V2 system including
workspace display, calculation cards, and interaction elements.
"""

from __future__ import annotations

import tkinter as tk
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from tkinter import ttk, scrolledtext, messagebox
from workspace_manager import CalculationEntry


class AdvancedToolTip:
    """Enhanced tooltip for V2 components."""

    def __init__(
        self,
        widget: tk.Widget,
        text: str = "",
        delay: float = 0.5,
        background: str = "#ffffe0",
        foreground: str = "black",
        font: tuple = ("tahoma", 8, "normal"),
    ):
        self.widget = widget
        self.text = text
        self.delay = delay
        self.background = background
        self.foreground = foreground
        self.font = font
        self.tooltip = None
        self.id = None

        widget.bind("<Enter>", self.on_enter)
        widget.bind("<Leave>", self.on_leave)
        widget.bind("<Motion>", self.on_motion)

    def on_enter(self, event=None):
        self.schedule_tooltip()

    def on_leave(self, event=None):
        self.hide_tooltip()

    def on_motion(self, event=None):
        self.hide_tooltip()
        self.schedule_tooltip()

    def schedule_tooltip(self):
        if self.id:
            self.widget.after_cancel(self.id)
        self.id = self.widget.after(int(self.delay * 1000), self.show_tooltip)

    def show_tooltip(self):
        if self.tooltip or not self.text:
            return

        x, y, _, _ = (
            self.widget.bbox("insert") if hasattr(self.widget, "bbox") else (0, 0, 0, 0)
        )
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 25

        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")

        label = tk.Label(
            self.tooltip,
            text=self.text,
            background=self.background,
            foreground=self.foreground,
            font=self.font,
            relief="solid",
            borderwidth=1,
        )
        label.pack()

    def hide_tooltip(self):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None
        if self.id:
            self.widget.after_cancel(self.id)
            self.id = None


class CalculationCard(ttk.Frame):
    """A single calculation card component for workspace display."""

    def __init__(
        self,
        parent: ttk.Widget,
        calculation: CalculationEntry,
        on_add_note: Optional[Callable[[str], None]] = None,
        on_request_analysis: Optional[Callable[[], None]] = None,
        on_remove: Optional[Callable[[], None]] = None,
        tooltips: Optional[Dict[str, str]] = None,
    ):
        super().__init__(parent, style="Calc.TFrame")

        self.calculation = calculation
        self.on_add_note = on_add_note
        self.on_request_analysis = on_request_analysis
        self.on_remove = on_remove
        self.tooltips = tooltips or {}

        self.setup_ui()
        self.update_display()

    def setup_ui(self):
        """Setup the card UI structure."""
        # Header with calculation info
        header_frame = ttk.Frame(self, style="Calc.TFrame")
        header_frame.pack(fill="x", padx=5, pady=(5, 0))

        # Calculation type and name
        title_text = (
            f"🔷 {self.calculation.calc_type} - {self.calculation.calculation_name}"
        )
        title_label = ttk.Label(
            header_frame, text=title_text, font=("Arial", 10, "bold")
        )
        title_label.pack(side="left")

        # Remove button
        if self.on_remove:
            remove_btn = ttk.Button(
                header_frame, text="✕", width=3, command=self.on_remove
            )
            remove_btn.pack(side="right", padx=(5, 0))
            AdvancedToolTip(remove_btn, "Bu hesaplamayı kaldır")

        # Timestamp
        timestamp_text = self.calculation.timestamp.strftime("%d.%m.%Y %H:%M")
        timestamp_label = ttk.Label(
            header_frame, text=timestamp_text, font=("Arial", 8), foreground="gray"
        )
        timestamp_label.pack(side="right", padx=10)

        # Parameters and result frame
        params_frame = ttk.Frame(self, style="Calc.TFrame")
        params_frame.pack(fill="x", padx=5, pady=2)

        # Parameters
        params_text = "Parametreler: " + ", ".join(
            [f"{k}: {v}" for k, v in self.calculation.parameters.items()]
        )
        params_label = ttk.Label(params_frame, text=params_text, font=("Arial", 9))
        params_label.pack(anchor="w")

        # Result
        result_text = f"Sonuç: {self.calculation.result} {self.calculation.unit}"
        result_label = ttk.Label(
            params_frame, text=result_text, font=("Arial", 9, "bold"), foreground="blue"
        )
        result_label.pack(anchor="w")

        # Notes section
        self.notes_frame = ttk.Frame(self, style="Calc.TFrame")
        self.notes_frame.pack(fill="x", padx=5, pady=2)

        # User notes
        if self.calculation.user_notes:
            user_notes_label = ttk.Label(
                self.notes_frame,
                text="👤 Kullanıcı Notları:",
                font=("Arial", 9, "bold"),
            )
            user_notes_label.pack(anchor="w")

            for note in self.calculation.user_notes:
                note_label = ttk.Label(
                    self.notes_frame,
                    text=f"  • {note}",
                    font=("Arial", 8),
                    wraplength=600,
                )
                note_label.pack(anchor="w", padx=(10, 0))

        # Model comments
        if self.calculation.model_comments:
            model_comments_label = ttk.Label(
                self.notes_frame, text="🤖 Model Yorumları:", font=("Arial", 9, "bold")
            )
            model_comments_label.pack(anchor="w", pady=(5, 0))

            for comment in self.calculation.model_comments:
                comment_label = ttk.Label(
                    self.notes_frame,
                    text=f"  • {comment}",
                    font=("Arial", 8),
                    wraplength=600,
                    foreground="darkgreen",
                )
                comment_label.pack(anchor="w", padx=(10, 0))

        # Action buttons
        actions_frame = ttk.Frame(self, style="Calc.TFrame")
        actions_frame.pack(fill="x", padx=5, pady=(5, 5))

        # Add note button
        if self.on_add_note:
            add_note_btn = ttk.Button(
                actions_frame, text="📝 Not Ekle", command=self.show_add_note_dialog
            )
            add_note_btn.pack(side="left", padx=(0, 5))
            AdvancedToolTip(add_note_btn, "Bu hesaplamaya not ekle")

        # Request analysis button
        if self.on_request_analysis:
            analysis_btn = ttk.Button(
                actions_frame, text="🔍 Analiz İste", command=self.on_request_analysis
            )
            analysis_btn.pack(side="left")
            AdvancedToolTip(analysis_btn, "Modelden bu hesaplama için analiz iste")

        # Separator
        separator = ttk.Separator(self, orient="horizontal")
        separator.pack(fill="x", padx=5, pady=5)

    def update_display(self):
        """Update the card display with current calculation data."""
        # Clear and recreate the display
        for widget in self.winfo_children():
            widget.destroy()
        self.setup_ui()

    def show_add_note_dialog(self):
        """Show dialog to add a user note."""
        dialog = tk.Toplevel(self)
        dialog.title("Not Ekle")
        dialog.geometry("400x200")
        dialog.transient(self)
        dialog.grab_set()

        # Label
        label = ttk.Label(dialog, text="Notunuzu girin:")
        label.pack(pady=10)

        # Text widget
        text_widget = scrolledtext.ScrolledText(dialog, width=50, height=8)
        text_widget.pack(padx=10, pady=5, fill="both", expand=True)
        text_widget.focus_set()

        # Buttons
        button_frame = ttk.Frame(dialog)
        button_frame.pack(pady=10)

        def save_note():
            note_text = text_widget.get("1.0", tk.END).strip()
            if note_text and self.on_add_note:
                self.on_add_note(note_text)
                dialog.destroy()

        save_btn = ttk.Button(button_frame, text="Kaydet", command=save_note)
        save_btn.pack(side="left", padx=5)

        cancel_btn = ttk.Button(button_frame, text="İptal", command=dialog.destroy)
        cancel_btn.pack(side="left", padx=5)

        # Bind Enter key to save
        dialog.bind("<Return>", lambda e: save_note())
        dialog.bind("<Escape>", lambda e: dialog.destroy())


class WorkspaceDisplay(ttk.Frame):
    """Main workspace display component."""

    def __init__(
        self,
        parent: ttk.Widget,
        on_add_note: Optional[Callable[[str, str], None]] = None,
        on_request_analysis: Optional[Callable[[Optional[str]], None]] = None,
        on_remove_calculation: Optional[Callable[[str], None]] = None,
        tooltips: Optional[Dict[str, str]] = None,
    ):
        super().__init__(parent, style="Calc.TFrame")

        self.on_add_note = on_add_note
        self.on_request_analysis = on_request_analysis
        self.on_remove_calculation = on_remove_calculation
        self.tooltips = tooltips or {}

        self.calculation_cards: Dict[str, CalculationCard] = {}

        self.setup_ui()

    def setup_ui(self):
        """Setup the workspace display UI."""
        # Header
        header_frame = ttk.Frame(self, style="Calc.TFrame")
        header_frame.pack(fill="x", padx=5, pady=5)

        title_label = ttk.Label(
            header_frame, text="🔧 ÇALIŞMA ALANI", font=("Arial", 12, "bold")
        )
        title_label.pack(side="left")

        # Clear all button
        clear_btn = ttk.Button(
            header_frame, text="🗑️ Temizle", command=self.show_clear_confirmation
        )
        clear_btn.pack(side="right", padx=(5, 0))
        AdvancedToolTip(clear_btn, "Tüm hesaplamaları temizle")

        # Export button
        export_btn = ttk.Button(
            header_frame, text="💾 Dışa Aktar", command=self.request_export
        )
        export_btn.pack(side="right", padx=(5, 0))
        AdvancedToolTip(export_btn, "Oturumu dışa aktar")

        # Separator
        separator = ttk.Separator(self, orient="horizontal")
        separator.pack(fill="x", padx=5, pady=5)

        # Scrollable area for calculation cards
        self.canvas = tk.Canvas(self, bg="white")
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas, style="Calc.TFrame")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")),
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True, padx=5)
        scrollbar.pack(side="right", fill="y")

        # Empty state message
        self.empty_label = ttk.Label(
            self.scrollable_frame,
            text="📋 Henüz hesaplama bulunmuyor.\n\nSol panelden hesaplama yaparak başlayın.",
            font=("Arial", 10),
            foreground="gray",
            justify="center",
        )
        self.empty_label.pack(expand=True, pady=50)

    def add_calculation_card(self, calculation: CalculationEntry):
        """Add a new calculation card to the workspace."""
        # Hide empty state message
        if self.empty_label:
            self.empty_label.destroy()
            self.empty_label = None

        # Create card
        card = CalculationCard(
            self.scrollable_frame,
            calculation,
            on_add_note=lambda note: self.handle_add_note(calculation.id, note),
            on_request_analysis=lambda: self.handle_request_analysis(calculation.id),
            on_remove=lambda: self.handle_remove_calculation(calculation.id),
            tooltips=self.tooltips,
        )

        card.pack(fill="x", pady=5)
        self.calculation_cards[calculation.id] = card

        # Scroll to bottom
        self.canvas.update_idletasks()
        self.canvas.yview_moveto(1.0)

    def update_calculation_card(self, calc_id: str):
        """Update an existing calculation card."""
        if calc_id in self.calculation_cards:
            card = self.calculation_cards[calc_id]
            card.update_display()

    def remove_calculation_card(self, calc_id: str):
        """Remove a calculation card from the workspace."""
        if calc_id in self.calculation_cards:
            card = self.calculation_cards[calc_id]
            card.destroy()
            del self.calculation_cards[calc_id]

            # Show empty state if no cards left
            if not self.calculation_cards and not self.empty_label:
                self.empty_label = ttk.Label(
                    self.scrollable_frame,
                    text="📋 Henüz hesaplama bulunmuyor.\n\nSol panelden hesaplama yaparak başlayın.",
                    font=("Arial", 10),
                    foreground="gray",
                    justify="center",
                )
                self.empty_label.pack(expand=True, pady=50)

    def clear_all_cards(self):
        """Clear all calculation cards."""
        for card in self.calculation_cards.values():
            card.destroy()
        self.calculation_cards.clear()

        # Show empty state
        if not self.empty_label:
            self.empty_label = ttk.Label(
                self.scrollable_frame,
                text="📋 Henüz hesaplama bulunmuyor.\n\nSol panelden hesaplama yaparak başlayın.",
                font=("Arial", 10),
                foreground="gray",
                justify="center",
            )
            self.empty_label.pack(expand=True, pady=50)

    def handle_add_note(self, calc_id: str, note: str):
        """Handle add note action."""
        if self.on_add_note:
            self.on_add_note(calc_id, note)

    def handle_request_analysis(self, calc_id: str):
        """Handle request analysis action."""
        if self.on_request_analysis:
            self.on_request_analysis(calc_id)

    def handle_remove_calculation(self, calc_id: str):
        """Handle remove calculation action."""
        if self.on_remove_calculation:
            self.on_remove_calculation(calc_id)

    def show_clear_confirmation(self):
        """Show confirmation dialog for clearing workspace."""
        result = messagebox.askyesno(
            "Çalışma Alanını Temizle",
            "Tüm hesaplamaları ve notları silmek istediğinizden emin misiniz?\n\nBu işlem geri alınamaz.",
            icon="warning",
        )
        if result:
            self.clear_all_cards()
            if self.on_remove_calculation:
                self.on_remove_calculation(None)  # None means clear all

    def request_export(self):
        """Request workspace export."""
        # This will be handled by the main GUI
        if hasattr(self.master, "export_workspace"):
            self.master.export_workspace()


class V2ControlPanel(ttk.Frame):
    """V2 control panel with analysis and action buttons."""

    def __init__(
        self,
        parent: ttk.Widget,
        on_general_analysis: Optional[Callable[[], None]] = None,
        on_compare_calculations: Optional[Callable[[], None]] = None,
        tooltips: Optional[Dict[str, str]] = None,
    ):
        super().__init__(parent, style="Calc.TFrame")

        self.on_general_analysis = on_general_analysis
        self.on_compare_calculations = on_compare_calculations
        self.tooltips = tooltips or {}

        self.setup_ui()

    def setup_ui(self):
        """Setup the control panel UI."""
        # Header
        header_label = ttk.Label(
            self, text="🎛️ KONTROL PANELİ", font=("Arial", 11, "bold")
        )
        header_label.pack(pady=5)

        # General analysis button
        general_btn = ttk.Button(
            self, text="🔍 Genel Analiz İste", command=self.on_general_analysis
        )
        general_btn.pack(fill="x", padx=10, pady=2)
        AdvancedToolTip(
            general_btn, "Modelden tüm çalışma alanı için genel analiz iste"
        )

        # Compare calculations button
        compare_btn = ttk.Button(
            self,
            text="⚖️ Hesaplamaları Karşılaştır",
            command=self.on_compare_calculations,
        )
        compare_btn.pack(fill="x", padx=10, pady=2)
        AdvancedToolTip(compare_btn, "Birden fazla hesaplamayı karşılaştır")

        # Separator
        separator = ttk.Separator(self, orient="horizontal")
        separator.pack(fill="x", padx=10, pady=10)

        # Model settings
        settings_label = ttk.Label(
            self, text="⚙️ MODEL AYARLARI", font=("Arial", 10, "bold")
        )
        settings_label.pack(pady=5)

        # These will be connected to the main GUI's model controls
        # The actual implementation will be in the main GUI class
