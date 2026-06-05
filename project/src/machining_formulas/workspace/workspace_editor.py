"""Workspace Buffer UI - Collaborative text editor interface.

This module provides the UI components for the workspace buffer
where users and models can collaboratively edit content.
"""

from __future__ import annotations

import tkinter as tk
from datetime import datetime
from typing import Any, Callable, Dict, Optional

from tkinter import ttk, scrolledtext, messagebox

from .workspace_buffer import WorkspaceBuffer


class WorkspaceEditor(ttk.Frame):
    """Main workspace editor component with collaborative editing support."""

    def __init__(
        self,
        parent: ttk.Widget,
        workspace_buffer: WorkspaceBuffer,
        on_model_suggestion: Optional[Callable[[str], None]] = None,
        on_content_change: Optional[Callable[[str], None]] = None,
        tooltips: Optional[Dict[str, str]] = None,
    ):
        super().__init__(parent, style="Calc.TFrame")

        self.workspace_buffer = workspace_buffer
        self.on_model_suggestion = on_model_suggestion
        self.on_content_change = on_content_change
        self.tooltips = tooltips or {}

        # Track user edits vs programmatic updates
        self._user_editing = False
        self._last_known_content = ""

        self._setup_ui()
        self._load_content()

        # Start tracking after initial content is loaded
        self._user_editing = True

    def _setup_ui(self):
        """Setup the workspace editor UI."""
        # Header with toolbar
        self._setup_toolbar()

        # Main editor area
        self._setup_editor()

        # Status bar
        self._setup_status_bar()

        # Suggestions panel (initially hidden)
        self._setup_suggestions_panel()

    def _setup_toolbar(self):
        """Setup editor toolbar."""
        toolbar_frame = ttk.Frame(self, style="Calc.TFrame")
        toolbar_frame.pack(fill="x", padx=5, pady=5)

        title_label = ttk.Label(
            toolbar_frame, text="📝 ÇALIŞMA ALANI EDITÖRÜ", font=("Arial", 12, "bold")
        )
        title_label.pack(side="left")

        ttk.Separator(toolbar_frame, orient="vertical").pack(side="left", padx=10, fill="y")

        undo_btn = ttk.Button(toolbar_frame, text="↶ Geri", command=self._undo)
        undo_btn.pack(side="left", padx=2)

        redo_btn = ttk.Button(toolbar_frame, text="↷ İleri", command=self._redo)
        redo_btn.pack(side="left", padx=2)

        ttk.Separator(toolbar_frame, orient="vertical").pack(side="left", padx=5, fill="y")

        model_btn = ttk.Button(
            toolbar_frame,
            text="🤖 Model Düzenleme Öner",
            command=self._request_model_suggestion,
        )
        model_btn.pack(side="left", padx=2)

        suggestions_btn = ttk.Button(
            toolbar_frame,
            text="💡 Önerileri Göster",
            command=self._toggle_suggestions,
        )
        suggestions_btn.pack(side="left", padx=2)

        ttk.Separator(toolbar_frame, orient="vertical").pack(side="left", padx=5, fill="y")

        history_btn = ttk.Button(toolbar_frame, text="📜 Geçmiş", command=self._show_version_history)
        history_btn.pack(side="left", padx=2)

        clear_btn = ttk.Button(toolbar_frame, text="🗑️ Temizle", command=self._clear_workspace)
        clear_btn.pack(side="right", padx=2)

    def _setup_editor(self):
        """Setup the main text editor."""
        editor_frame = ttk.Frame(self, style="Calc.TFrame")
        editor_frame.pack(fill="both", expand=True, padx=5, pady=5)

        self.line_numbers = tk.Text(
            editor_frame,
            width=4,
            padx=3,
            takefocus=0,
            border=0,
            state="disabled",
            wrap="none",
            background="#f0f0f0",
            foreground="#666666",
            font=("Consolas", 10),
        )
        self.line_numbers.pack(side="left", fill="y")

        self.text_editor = scrolledtext.ScrolledText(
            editor_frame,
            wrap=tk.WORD,
            font=("Consolas", 11),
            undo=True,
            maxundo=-1,
            padx=5,
            pady=5,
        )
        self.text_editor.pack(side="left", fill="both", expand=True)

        self.text_editor.bind("<KeyRelease>", self._on_key_release)
        self.text_editor.bind("<Button-1>", self._on_mouse_click)
        self.text_editor.bind("<<Modified>>", self._on_text_modified)

        self.text_editor.tag_configure("user_insert", background="#e8f5e8")
        self.text_editor.tag_configure("user_delete", background="#ffe8e8")
        self.text_editor.tag_configure("model_suggestion", background="#fff3cd")
        self.text_editor.tag_configure("model_accepted", background="#d1ecf1")

    def _setup_status_bar(self):
        """Setup status bar."""
        self.status_frame = ttk.Frame(self, style="Calc.TFrame")
        self.status_frame.pack(fill="x", padx=5, pady=2)

        self.status_label = ttk.Label(self.status_frame, text="Hazır", font=("Arial", 9))
        self.status_label.pack(side="left")

        self.edit_counter = ttk.Label(self.status_frame, text="", font=("Arial", 9))
        self.edit_counter.pack(side="right")

        self._update_status()

    def _setup_suggestions_panel(self):
        """Setup model suggestions panel."""
        self.suggestions_frame = ttk.Frame(self, style="Calc.TFrame")

        header_frame = ttk.Frame(self.suggestions_frame, style="Calc.TFrame")
        header_frame.pack(fill="x", padx=5, pady=5)

        ttk.Label(
            header_frame,
            text="🤖 Model Önerileri",
            font=("Arial", 10, "bold"),
        ).pack(side="left")

        close_btn = ttk.Button(header_frame, text="✕", command=self._hide_suggestions, width=3)
        close_btn.pack(side="right")

        self.suggestions_listbox = tk.Listbox(
            self.suggestions_frame,
            height=6,
            font=("Consolas", 9),
            selectmode=tk.SINGLE,
        )
        self.suggestions_listbox.pack(fill="both", expand=True, padx=5, pady=5)

        button_frame = ttk.Frame(self.suggestions_frame, style="Calc.TFrame")
        button_frame.pack(fill="x", padx=5, pady=5)

        ttk.Button(button_frame, text="✅ Kabul Et", command=self._accept_suggestion).pack(side="left", padx=2)
        ttk.Button(button_frame, text="❌ Reddet", command=self._reject_suggestion).pack(side="left", padx=2)
        ttk.Button(button_frame, text="👁️ Önizle", command=self._preview_suggestion).pack(side="left", padx=2)

    def _load_content(self):
        """Load content from workspace buffer."""
        content = self.workspace_buffer.get_content()
        self.text_editor.delete("1.0", tk.END)
        self.text_editor.insert("1.0", content)
        self._last_known_content = content
        self._update_line_numbers()

    def _on_key_release(self, event=None):
        """Handle key release events."""
        self._update_line_numbers()
        self._update_status()

    def _on_mouse_click(self, event=None):
        """Handle mouse click events."""
        self._update_status()

    def _on_text_modified(self, event=None):
        """Handle text modification events."""
        # Reset modified flag early to avoid recursive triggers
        try:
            self.text_editor.edit_modified(False)
        except Exception:
            pass

        if not self._user_editing:
            return

        try:
            current_content = self.text_editor.get("1.0", tk.END).rstrip("\n")

            if current_content != self._last_known_content:
                self._record_text_change(self._last_known_content, current_content)
                self._last_known_content = current_content

                if self.on_content_change:
                    self.on_content_change(current_content)

        except Exception:
            # Ignore errors during modification tracking
            pass

    def _record_text_change(self, old_content: str, new_content: str):
        """Record text change in workspace buffer."""
        min_len = min(len(old_content), len(new_content))

        first_diff = 0
        for i in range(min_len):
            if old_content[i] != new_content[i]:
                first_diff = i
                break
        else:
            first_diff = min_len

        old_rev = old_content[::-1]
        new_rev = new_content[::-1]

        min_suffix = min(len(old_rev), len(new_rev))
        for i in range(min_suffix):
            if old_rev[i] != new_rev[i]:
                min_suffix = i
                break
        else:
            # identical or one is prefix of the other
            pass

        old_suffix = old_rev[:min_suffix][::-1] if min_suffix > 0 else ""
        new_suffix = new_rev[:min_suffix][::-1] if min_suffix > 0 else ""

        old_changed = (
            old_content[first_diff: len(old_content) - len(old_suffix)]
            if old_suffix
            else old_content[first_diff:]
        )
        new_changed = (
            new_content[first_diff: len(new_content) - len(new_suffix)]
            if new_suffix
            else new_content[first_diff:]
        )

        if old_changed and not new_changed:
            self.workspace_buffer.delete_text(first_diff, first_diff + len(old_changed), "user")
        elif new_changed and not old_changed:
            self.workspace_buffer.insert_text(first_diff, new_changed, "user")
        elif old_changed != new_changed:
            self.workspace_buffer.replace_text(first_diff, first_diff + len(old_changed), new_changed, "user")

    def _update_line_numbers(self):
        """Update line numbers."""
        self.line_numbers.config(state="normal")
        self.line_numbers.delete("1.0", tk.END)

        line_count = int(self.text_editor.index("end-1c").split(".")[0])
        self.line_numbers.insert("1.0", "\n".join(str(i) for i in range(1, line_count + 1)))
        self.line_numbers.config(state="disabled")

    def _update_status(self):
        """Update status bar."""
        try:
            cursor_pos = self.text_editor.index(tk.INSERT)
            line, col = cursor_pos.split(".")

            content = self.text_editor.get("1.0", tk.END)
            char_count = len(content) - 1
            word_count = len(content.split())

            stats = self.workspace_buffer.get_stats()

            status_text = f"Satır: {line}, Sütun: {col} | Karakter: {char_count}, Kelime: {word_count}"
            self.status_label.config(text=status_text)

            edit_text = f"Düzenlemeler: {stats['user_edits']} kullanıcı, {stats['model_edits']} model"
            if stats["pending_suggestions"] > 0:
                edit_text += f" | Bekleyen öneriler: {stats['pending_suggestions']}"
            self.edit_counter.config(text=edit_text)

        except Exception:
            pass

    def _request_model_suggestion(self):
        """Request model suggestion for current selection or content."""
        if not self.on_model_suggestion:
            return

        try:
            selection = self.text_editor.get(tk.SEL_FIRST, tk.SEL_LAST)
            context = f"Seçili metin: {selection}"
        except tk.TclError:
            context = self.text_editor.get("1.0", tk.END)
            context = f"Tüm içerik: {context}"

        self.on_model_suggestion(context)

    def _toggle_suggestions(self):
        """Toggle suggestions panel visibility."""
        if self.suggestions_frame.winfo_ismapped():
            self._hide_suggestions()
        else:
            self._show_suggestions()

    def _show_suggestions(self):
        """Show suggestions panel."""
        self._refresh_suggestions()
        self.suggestions_frame.pack(fill="x", padx=5, pady=5)

    def _hide_suggestions(self):
        """Hide suggestions panel."""
        self.suggestions_frame.pack_forget()

    def _refresh_suggestions(self):
        """Refresh suggestions list."""
        self.suggestions_listbox.delete(0, tk.END)

        suggestions = self.workspace_buffer.get_pending_suggestions()
        for i, suggestion in enumerate(suggestions):
            preview = (
                suggestion.new_text[:50] + "..."
                if len(suggestion.new_text) > 50
                else suggestion.new_text
            )
            self.suggestions_listbox.insert(tk.END, f"{i + 1}. {preview}")

    def _accept_suggestion(self):
        """Accept selected suggestion."""
        selection = self.suggestions_listbox.curselection()
        if not selection:
            messagebox.showwarning("Uyarı", "Lütfen bir öneri seçin.")
            return

        suggestions = self.workspace_buffer.get_pending_suggestions()
        index = selection[0]

        if index < len(suggestions):
            suggestion = suggestions[index]
            if self.workspace_buffer.accept_suggestion(suggestion.id):
                self._load_content()
                self._refresh_suggestions()
                self._update_status()
                messagebox.showinfo("Başarılı", "Öneri kabul edildi.")
            else:
                messagebox.showerror("Hata", "Öneri kabul edilemedi.")

    def _reject_suggestion(self):
        """Reject selected suggestion."""
        selection = self.suggestions_listbox.curselection()
        if not selection:
            messagebox.showwarning("Uyarı", "Lütfen bir öneri seçin.")
            return

        suggestions = self.workspace_buffer.get_pending_suggestions()
        index = selection[0]

        if index < len(suggestions):
            suggestion = suggestions[index]
            if self.workspace_buffer.reject_suggestion(suggestion.id):
                self._refresh_suggestions()
                self._update_status()
                messagebox.showinfo("Başarılı", "Öneri reddedildi.")
            else:
                messagebox.showerror("Hata", "Öneri reddedilemedi.")

    def _preview_suggestion(self):
        """Preview selected suggestion."""
        selection = self.suggestions_listbox.curselection()
        if not selection:
            messagebox.showwarning("Uyarı", "Lütfen bir öneri seçin.")
            return

        suggestions = self.workspace_buffer.get_pending_suggestions()
        index = selection[0]

        if index >= len(suggestions):
            return

        suggestion = suggestions[index]

        preview_window = tk.Toplevel(self)
        preview_window.title("Öneri Önizlemesi")
        preview_window.geometry("600x400")

        ttk.Label(preview_window, text="Mevcut Metin:", font=("Arial", 10, "bold")).pack(
            anchor="w", padx=10, pady=(10, 5)
        )
        original_text = tk.Text(preview_window, height=8, wrap=tk.WORD, font=("Consolas", 10))
        original_text.pack(fill="x", padx=10, pady=5)
        original_text.insert("1.0", suggestion.old_text)
        original_text.config(state="disabled")

        ttk.Label(preview_window, text="Önerilen Metin:", font=("Arial", 10, "bold")).pack(
            anchor="w", padx=10, pady=(10, 5)
        )
        suggested_text = tk.Text(preview_window, height=8, wrap=tk.WORD, font=("Consolas", 10))
        suggested_text.pack(fill="both", expand=True, padx=10, pady=5)
        suggested_text.insert("1.0", suggestion.new_text)

        button_frame = ttk.Frame(preview_window)
        button_frame.pack(fill="x", padx=10, pady=10)

        ttk.Button(button_frame, text="Kapat", command=preview_window.destroy).pack(side="right")

    def _show_version_history(self):
        """Show version history dialog."""
        history_window = tk.Toplevel(self)
        history_window.title("Versiyon Geçmişi")
        history_window.geometry("800x500")

        list_frame = ttk.Frame(history_window)
        list_frame.pack(fill="both", expand=True, padx=10, pady=10)

        columns = ("Tarih", "Açıklama", "Düzenlemeler")
        version_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)

        for col in columns:
            version_tree.heading(col, text=col)
            version_tree.column(col, width=250)

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=version_tree.yview)
        version_tree.configure(yscrollcommand=scrollbar.set)

        version_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        versions = self.workspace_buffer.get_version_history()
        for version in reversed(versions[-20:]):
            timestamp = version.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            description = (
                version.description[:50] + "..."
                if len(version.description) > 50
                else version.description
            )
            edit_count = len(version.edit_ids)

            version_tree.insert(
                "",
                "end",
                values=(timestamp, description, edit_count),
                tags=(version.id,),
            )

        button_frame = ttk.Frame(history_window)
        button_frame.pack(fill="x", padx=10, pady=10)

        def restore_version():
            selection = version_tree.selection()
            if not selection:
                messagebox.showwarning("Uyarı", "Lütfen bir versiyon seçin.")
                return

            version_id = version_tree.item(selection[0])["tags"][0]
            if self.workspace_buffer.restore_version(version_id):
                self._load_content()
                self._update_status()
                messagebox.showinfo("Başarılı", "Versiyon geri yüklendi.")
                history_window.destroy()
            else:
                messagebox.showerror("Hata", "Versiyon geri yüklenemedi.")

        ttk.Button(button_frame, text="Geri Yükle", command=restore_version).pack(side="left")
        ttk.Button(button_frame, text="Kapat", command=history_window.destroy).pack(side="right")

    def _clear_workspace(self):
        """Clear workspace content."""
        if messagebox.askyesno("Onay", "Çalışma alanını temizlemek istediğinizden emin misiniz?"):
            self.workspace_buffer.clear_all()
            self._load_content()
            self._update_status()

    def _undo(self):
        """Undo last edit."""
        self.text_editor.edit_undo()

    def _redo(self):
        """Redo last undone edit."""
        self.text_editor.edit_redo()

    def insert_calculation_result(
        self,
        calc_type: str,
        calc_name: str,
        params: Dict[str, Any],
        result: float,
        unit: str,
    ):
        """Insert calculation result into workspace."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        formatted_result = f"""
🔧 HESAPLAMA SONUCU
Tarih: {timestamp}
Tür: {calc_type}
İşlem: {calc_name}
Parametreler: {params}
Sonuç: {result} {unit}
{"=" * 50}

"""

        cursor_pos = self.text_editor.index(tk.INSERT)
        self.text_editor.insert(cursor_pos, formatted_result)

        self._user_editing = False
        current_content = self.text_editor.get("1.0", tk.END).rstrip("\n")
        self.workspace_buffer.set_content(current_content, "user", f"Calculation result inserted: {calc_name}")
        self._last_known_content = current_content
        self._user_editing = True

        self._update_line_numbers()
        self._update_status()

    def get_current_content(self) -> str:
        """Get current editor content."""
        return self.text_editor.get("1.0", tk.END).rstrip("\n")

    def set_content(self, content: str):
        """Set editor content."""
        self._user_editing = False
        self.text_editor.delete("1.0", tk.END)
        self.text_editor.insert("1.0", content)
        self.workspace_buffer.set_content(content, "system", "Content loaded")
        self._last_known_content = content
        self._user_editing = True

        self._update_line_numbers()
        self._update_status()
