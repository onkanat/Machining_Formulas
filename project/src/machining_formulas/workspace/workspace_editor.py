"""Workspace Buffer UI - Collaborative text editor interface.

This module provides the UI components for the workspace buffer
where users and models can collaboratively edit content.
"""

from __future__ import annotations

import tkinter as tk
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from tkinter import ttk, scrolledtext, messagebox

from .workspace_buffer import EditType, WorkspaceBuffer, WorkspaceEdit, line_diff

MODE_APPEND = "append"
MODE_INSERT = "insert"
MODE_REPLACE = "replace"

_INSERT_MODE_LABELS = {
    "Sona ekle": MODE_APPEND,
    "İmlece ekle": MODE_INSERT,
}

_DIFF_TAGS = {
    " ": "diff_ctx",
    "-": "diff_del",
    "+": "diff_add",
    "@": "diff_hunk",
}


@dataclass(frozen=True)
class ModelRequest:
    """A structured request from the workspace editor to the model layer."""

    question: str = ""
    source_text: str = ""
    mode: str = MODE_APPEND
    offset: int = 0


def format_answer_block(question: str, answer: str, *, max_question_chars: int = 500) -> str:
    """Format a model answer for insertion into the workspace.

    Belgenin tümü asla "Soru" başlığına yazılmaz; yalnızca soru çubuğuna yazılan
    kısa soru korunur. Böylece her turda belge kendi kopyasını taşımaz.
    """
    answer = (answer or "").strip()
    question = (question or "").strip()
    if not answer:
        return ""
    if question and len(question) <= max_question_chars:
        return f"Soru: {question}\n\nYanıt:\n{answer}"
    return answer


class WorkspaceEditor(ttk.Frame):
    """Main workspace editor component with collaborative editing support."""

    def __init__(
        self,
        parent: ttk.Widget,
        workspace_buffer: WorkspaceBuffer,
        on_model_request: Optional[Callable[[ModelRequest], None]] = None,
        on_content_change: Optional[Callable[[str], None]] = None,
        tooltips: Optional[Dict[str, str]] = None,
    ):
        super().__init__(parent, style="Calc.TFrame")

        self.workspace_buffer = workspace_buffer
        self.on_model_request = on_model_request
        self.on_content_change = on_content_change
        self.tooltips = tooltips or {}

        # Track user edits vs programmatic updates
        self._user_editing = False
        self._last_known_content = ""

        self._review_pane_visible = False
        self._selector_suggestions: List[WorkspaceEdit] = []
        self._hint_serial = 0

        self._setup_ui()
        self._load_content()

        # Start tracking after initial content is loaded
        self._user_editing = True

    # ------------------------------------------------------------------ UI

    def _setup_ui(self):
        """Setup the workspace editor UI."""
        self._setup_toolbar()
        # Alttan yukarı: durum çubuğu en altta, soru çubuğu onun üstünde.
        self._setup_status_bar()
        self._setup_question_bar()
        self._setup_paned_area()
        self._setup_review_panel()

    def _setup_toolbar(self):
        """Setup editor toolbar."""
        toolbar_frame = ttk.Frame(self, style="Calc.TFrame")
        toolbar_frame.pack(fill="x", padx=5, pady=5)

        title_label = ttk.Label(
            toolbar_frame, text="📝 ÇALIŞMA ALANI", font=("Arial", 12, "bold")
        )
        title_label.pack(side="left")

        ttk.Separator(toolbar_frame, orient="vertical").pack(side="left", padx=10, fill="y")

        ttk.Button(toolbar_frame, text="↶ Geri", command=self._undo).pack(side="left", padx=2)
        ttk.Button(toolbar_frame, text="↷ İleri", command=self._redo).pack(side="left", padx=2)

        ttk.Separator(toolbar_frame, orient="vertical").pack(side="left", padx=5, fill="y")

        ttk.Button(
            toolbar_frame,
            text="🤖 Sor / Düzenle",
            command=self._send_question,
        ).pack(side="left", padx=2)

        ttk.Button(
            toolbar_frame,
            text="🔍 İnceleme",
            command=self._toggle_review_panel,
        ).pack(side="left", padx=2)

        ttk.Separator(toolbar_frame, orient="vertical").pack(side="left", padx=5, fill="y")

        ttk.Button(
            toolbar_frame, text="📜 Geçmiş", command=self._show_version_history
        ).pack(side="left", padx=2)

        ttk.Button(
            toolbar_frame, text="🗑️ Temizle", command=self._clear_workspace
        ).pack(side="right", padx=2)

    def _setup_paned_area(self):
        """Create the vertical pane holding the editor and the review panel."""
        self.workspace_paned = ttk.PanedWindow(self, orient="vertical")
        self.workspace_paned.pack(fill="both", expand=True, padx=5, pady=5)

        editor_pane = ttk.Frame(self.workspace_paned, style="Calc.TFrame")
        self._setup_editor(editor_pane)
        self.workspace_paned.add(editor_pane, weight=4)

    def _setup_editor(self, parent: ttk.Frame):
        """Setup the main text editor inside its pane."""
        self.line_numbers = tk.Text(
            parent,
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
            parent,
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
        self.text_editor.bind("<Control-Return>", lambda event: self._send_question())
        self.text_editor.bind("<Command-Return>", lambda event: self._send_question())

        self.text_editor.tag_configure("user_insert", background="#e8f5e8")
        self.text_editor.tag_configure("user_delete", background="#ffe8e8")
        self.text_editor.tag_configure("model_suggestion", background="#fff3cd")
        self.text_editor.tag_configure("model_accepted", background="#d1ecf1")

    def _setup_status_bar(self):
        """Setup status bar."""
        self.status_frame = ttk.Frame(self, style="Calc.TFrame")
        self.status_frame.pack(side="bottom", fill="x", padx=5, pady=2)

        self.status_label = ttk.Label(self.status_frame, text="Hazır", font=("Arial", 9))
        self.status_label.pack(side="left")

        self.hint_label = ttk.Label(self.status_frame, text="", font=("Arial", 9))
        self.hint_label.pack(side="left", padx=(12, 0))

        self.edit_counter = ttk.Label(self.status_frame, text="", font=("Arial", 9))
        self.edit_counter.pack(side="right")

    def _setup_question_bar(self):
        """Setup the question / command bar under the editor."""
        bar = ttk.Frame(self, style="Calc.TFrame")
        bar.pack(side="bottom", fill="x", padx=5, pady=(2, 4))

        ttk.Label(bar, text="Soru:", font=("Arial", 9)).pack(side="left")

        self.question_entry = ttk.Entry(bar)
        self.question_entry.pack(side="left", fill="x", expand=True, padx=(5, 8))
        self.question_entry.bind("<Return>", lambda event: self._send_question())

        ttk.Label(bar, text="Ekleme:", font=("Arial", 9)).pack(side="left")

        self.insert_mode = ttk.Combobox(
            bar,
            state="readonly",
            width=12,
            values=tuple(_INSERT_MODE_LABELS.keys()),
        )
        self.insert_mode.current(0)
        self.insert_mode.pack(side="left", padx=(5, 8))

        self.send_button = ttk.Button(bar, text="Gönder", command=self._send_question)
        self.send_button.pack(side="left")

    def _setup_review_panel(self):
        """Setup the diff review panel (added to the pane only when needed)."""
        self.review_frame = ttk.Frame(self.workspace_paned, style="Calc.TFrame")

        header = ttk.Frame(self.review_frame, style="Calc.TFrame")
        header.pack(fill="x", padx=5, pady=(5, 2))

        ttk.Label(
            header, text="🔍 DEĞİŞİKLİK İNCELEME", font=("Arial", 10, "bold")
        ).pack(side="left")

        self.review_summary = ttk.Label(header, text="", font=("Arial", 9))
        self.review_summary.pack(side="left", padx=8)

        ttk.Button(header, text="✕", width=3, command=self._hide_review_panel).pack(side="right")
        self.reject_button = ttk.Button(
            header, text="❌ Reddet", command=self._reject_current_suggestion
        )
        self.reject_button.pack(side="right", padx=2)
        self.accept_button = ttk.Button(
            header, text="✅ Kabul Et", command=self._accept_current_suggestion
        )
        self.accept_button.pack(side="right", padx=2)
        ttk.Button(header, text="🔄", width=3, command=self._refresh_suggestion_selector).pack(
            side="right", padx=2
        )

        selector_row = ttk.Frame(self.review_frame, style="Calc.TFrame")
        selector_row.pack(fill="x", padx=5, pady=2)

        ttk.Label(selector_row, text="Öneri:", font=("Arial", 9)).pack(side="left")
        self.suggestion_selector = ttk.Combobox(selector_row, state="readonly", values=[])
        self.suggestion_selector.pack(side="left", fill="x", expand=True, padx=(5, 0))
        self.suggestion_selector.bind(
            "<<ComboboxSelected>>", lambda event: self._refresh_review()
        )

        diff_container = ttk.Frame(self.review_frame, style="Calc.TFrame")
        diff_container.pack(fill="both", expand=True, padx=5, pady=(2, 5))

        diff_scroll = ttk.Scrollbar(diff_container, orient="vertical")
        self.diff_text = tk.Text(
            diff_container,
            wrap="word",
            font=("Consolas", 9),
            height=8,
            state="disabled",
            background="#fbfbfb",
            padx=6,
            pady=4,
        )
        self.diff_text.configure(yscrollcommand=diff_scroll.set)
        diff_scroll.configure(command=self.diff_text.yview)

        self.diff_text.pack(side="left", fill="both", expand=True)
        diff_scroll.pack(side="right", fill="y")

        self.diff_text.tag_configure("diff_add", background="#d4f5d4", foreground="#14532d")
        self.diff_text.tag_configure("diff_del", background="#fbd5d5", foreground="#7f1d1d")
        self.diff_text.tag_configure("diff_ctx", foreground="#4b5563")
        self.diff_text.tag_configure("diff_hunk", foreground="#1d4ed8", font=("Consolas", 9, "bold"))
        self.diff_text.tag_configure("diff_note", foreground="#92400e", font=("Arial", 9, "italic"))

        self._set_review_buttons_state("disabled")

    # -------------------------------------------------------------- content

    def _load_content(self):
        """Load content from workspace buffer."""
        previous_editing = self._user_editing
        self._user_editing = False
        try:
            content = self.workspace_buffer.get_content()
            self.text_editor.delete("1.0", tk.END)
            self.text_editor.insert("1.0", content)
            self.text_editor.edit_modified(False)
            self._last_known_content = self.text_editor.get("1.0", tk.END).rstrip("\n")
        finally:
            self._user_editing = previous_editing

        self._update_line_numbers()
        self._update_status()

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

    def _set_hint(self, text: str, duration_ms: int = 6000):
        """Show a short-lived message in the status bar."""
        self.hint_label.config(text=text)
        self._hint_serial += 1
        serial = self._hint_serial
        if duration_ms > 0:
            self.after(
                duration_ms,
                lambda: self.hint_label.config(text="") if self._hint_serial == serial else None,
            )

    # ------------------------------------------------------------- requests

    def _cursor_offset(self) -> int:
        return len(self.text_editor.get("1.0", tk.INSERT))

    def _selected_source(self) -> tuple[str, int]:
        """Return the selected text and its character offset, else ("", cursor)."""
        try:
            selection = self.text_editor.get(tk.SEL_FIRST, tk.SEL_LAST)
        except tk.TclError:
            selection = ""

        if selection:
            return selection, len(self.text_editor.get("1.0", tk.SEL_FIRST))
        return "", self._cursor_offset()

    def _build_request(self) -> Optional[ModelRequest]:
        question = self.question_entry.get().strip()
        selection, offset = self._selected_source()

        if question:
            mode = _INSERT_MODE_LABELS.get(self.insert_mode.get(), MODE_APPEND)
            # Seçim varsa yalnızca bağlam olarak gönderilir; yanıt seçilen yere eklenir.
            return ModelRequest(
                question=question,
                source_text=selection,
                mode=mode,
                offset=offset,
            )

        if selection:
            return ModelRequest(source_text=selection, mode=MODE_REPLACE, offset=offset)

        content = self.get_current_content()
        if not content.strip():
            self._set_hint("Önce metin yazın veya yukarıdaki soru alanına bir soru girin.")
            return None
        return ModelRequest(source_text=content, mode=MODE_REPLACE, offset=0)

    def _send_question(self):
        """Send the question bar content (or the current selection) to the model."""
        if not self.on_model_request:
            self._set_hint("Model bağlı değil.")
            return

        request = self._build_request()
        if request is None:
            return

        self.send_button.state(["disabled"])
        self._set_hint("Model yanıtı hazırlanıyor...", duration_ms=0)
        self.on_model_request(request)

    def finish_request(self, message: str = ""):
        """Re-enable the question bar after a model request completes."""
        try:
            self.send_button.state(["!disabled"])
        except Exception:
            pass
        if message:
            self._set_hint(message)

    # --------------------------------------------------------------- review

    def _pending_suggestions(self) -> List[WorkspaceEdit]:
        return self.workspace_buffer.get_pending_suggestions()

    def _line_for_offset(self, offset: int) -> int:
        content = self.workspace_buffer.get_content()
        bounded = max(0, min(offset, len(content)))
        return content.count("\n", 0, bounded) + 1

    def _description_for(self, edit: WorkspaceEdit) -> str:
        kind = "Ekleme" if edit.edit_type == EditType.MODEL_INSERT else "Değiştirme"
        line = self._line_for_offset(edit.position)
        delta = len(edit.new_text) - len(edit.old_text)
        sign = "+" if delta >= 0 else ""
        return f"Satır {line} · {kind} ({sign}{delta} karakter)"

    def open_review(self, edit_id: Optional[str] = None):
        """Show the review panel, selecting ``edit_id`` (else the newest pending)."""
        self._show_review_panel()
        self._refresh_suggestion_selector(edit_id)

    def _toggle_review_panel(self):
        if self._review_pane_visible:
            self._hide_review_panel()
        else:
            self.open_review()

    def _show_review_panel(self):
        if self._review_pane_visible:
            return
        self.workspace_paned.add(self.review_frame, weight=2)
        self._review_pane_visible = True

    def _hide_review_panel(self):
        if not self._review_pane_visible:
            return
        self.workspace_paned.forget(self.review_frame)
        self._review_pane_visible = False

    def _refresh_suggestion_selector(self, select_id: Optional[str] = None):
        """Rebuild the suggestion list and render the selected diff."""
        suggestions = self._pending_suggestions()
        self._selector_suggestions = suggestions

        labels = [
            f"{index + 1}/{len(suggestions)} · {self._description_for(edit)}"
            for index, edit in enumerate(suggestions)
        ]
        self.suggestion_selector.configure(values=labels)

        if not labels:
            self.suggestion_selector.set("")
            self._refresh_review()
            return

        target_index = len(suggestions) - 1
        if select_id:
            for index, edit in enumerate(suggestions):
                if edit.id == select_id:
                    target_index = index
                    break
        self.suggestion_selector.current(target_index)
        self._refresh_review()

    def _current_review_edit(self) -> Optional[WorkspaceEdit]:
        index = self.suggestion_selector.current()
        if 0 <= index < len(self._selector_suggestions):
            return self._selector_suggestions[index]
        return None

    def _refresh_review(self):
        """Render the diff of the selected suggestion."""
        edit = self._current_review_edit()

        self.diff_text.configure(state="normal")
        self.diff_text.delete("1.0", tk.END)

        if edit is None:
            self.review_summary.config(text="")
            self._set_review_buttons_state("disabled")
            self._insert_diff_line("Bekleyen öneri yok.", "diff_note")
            self.diff_text.configure(state="disabled")
            return

        self._set_review_buttons_state("normal")
        kind = "Ekleme" if edit.edit_type == EditType.MODEL_INSERT else "Değiştirme"
        self.review_summary.config(
            text=f"{kind} · −{len(edit.old_text.splitlines())} / +{len(edit.new_text.splitlines())} satır"
        )

        diff_lines = line_diff(edit.old_text, edit.new_text)
        if not diff_lines:
            self._insert_diff_line("Öneri mevcut metinle aynı; uygulanacak değişiklik yok.", "diff_note")
        for tag, text in diff_lines:
            if tag == "@":
                self._insert_diff_line(text, _DIFF_TAGS[tag])
            else:
                self._insert_diff_line(f"{tag} {text}", _DIFF_TAGS[tag])

        self.diff_text.see("1.0")
        self.diff_text.configure(state="disabled")

    def _insert_diff_line(self, text: str, tag: str):
        self.diff_text.insert(tk.END, text + "\n", (tag,))

    def _set_review_buttons_state(self, state: str):
        for button in (self.accept_button, self.reject_button):
            try:
                if state == "normal":
                    button.state(["!disabled"])
                else:
                    button.state(["disabled"])
            except Exception:
                pass

    def _accept_current_suggestion(self):
        edit = self._current_review_edit()
        if edit is None:
            messagebox.showwarning("Uyarı", "Uygulanacak öneri yok.")
            return

        if self.workspace_buffer.accept_suggestion(edit.id):
            self._load_content()
            self._refresh_suggestion_selector()
            self._update_status()
            self._set_hint("Öneri kabul edildi.")
            return

        if edit.stale:
            messagebox.showwarning(
                "Öneri Geçersiz",
                "Çalışma alanı bu öneri hazırlandıktan sonra değişti; "
                "öneri uygulanmadı. Lütfen yeni bir öneri isteyin.",
            )
            self._refresh_suggestion_selector()
            return

        messagebox.showerror("Hata", "Öneri kabul edilemedi.")

    def _reject_current_suggestion(self):
        edit = self._current_review_edit()
        if edit is None:
            messagebox.showwarning("Uyarı", "Reddedilecek öneri yok.")
            return

        if self.workspace_buffer.reject_suggestion(edit.id):
            self._refresh_suggestion_selector()
            self._update_status()
            self._set_hint("Öneri reddedildi.")
        else:
            messagebox.showerror("Hata", "Öneri reddedilemedi.")

    # ------------------------------------------------------------- history

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
                self._refresh_suggestion_selector()
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
            self._refresh_suggestion_selector()
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
        """Insert calculation result into workspace at the cursor."""
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

        previous_editing = self._user_editing
        self._user_editing = False
        try:
            cursor_pos = self.text_editor.index(tk.INSERT)
            self.text_editor.insert(cursor_pos, formatted_result)
            # İmleç eklenen bloğun sonuna taşınır; sonraki eklemeler üst üste binmez.
            self.text_editor.mark_set(
                tk.INSERT, f"{cursor_pos} + {len(formatted_result)}c"
            )
            self.text_editor.see(tk.INSERT)
            self.text_editor.edit_modified(False)

            current_content = self.text_editor.get("1.0", tk.END).rstrip("\n")
            self.workspace_buffer.set_content(
                current_content, "user", f"Calculation result inserted: {calc_name}"
            )
            self._last_known_content = current_content
        finally:
            self._user_editing = previous_editing

        self._update_line_numbers()
        self._update_status()
        if self._review_pane_visible:
            self._refresh_suggestion_selector()

    def get_current_content(self) -> str:
        """Get current editor content."""
        return self.text_editor.get("1.0", tk.END).rstrip("\n")

    def set_content(self, content: str):
        """Set editor content."""
        previous_editing = self._user_editing
        self._user_editing = False
        try:
            self.text_editor.delete("1.0", tk.END)
            self.text_editor.insert("1.0", content)
            self.text_editor.edit_modified(False)
            self.workspace_buffer.set_content(content, "system", "Content loaded")
            self._last_known_content = self.text_editor.get("1.0", tk.END).rstrip("\n")
        finally:
            self._user_editing = previous_editing

        self._update_line_numbers()
        self._update_status()
