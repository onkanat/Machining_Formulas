"""Mixin to encapsulate the experimental execute-mode behaviour."""
from __future__ import annotations

import math
import tkinter as tk
from tkinter import messagebox
from typing import Any


class ExecuteModeMixin:
    """Provide enable/disable helpers for the execute-mode feature."""

    execute_mode: bool
    result_text: tk.Text

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self.execute_mode = False

    def enable_execute_mode(self, event: tk.Event | None = None) -> None:
        if not hasattr(self, "result_text"):
            return
        self.result_text.config(bg="#ffffd0")
        self.execute_mode = True
        self.result_text.insert(
            tk.END,
            (
                "\n\n--- Execute Modu Aktif --- \n"
                "Kod seçip Ctrl+C ile çalıştırın.\n"
            ),
        )

    def execute_calculation(self, event: tk.Event | None = None) -> None:
        if not getattr(self, "execute_mode", False):
            return

        try:
            selected_code = self.result_text.get("sel.first", "sel.last")
            if not selected_code:
                self.result_text.insert(tk.END, "\nSeçili kod yok.\n")
                return

            calculator = self._get_exec_mode_calculator()
            local_scope = {"calc": calculator, "ec": calculator, "pi": math.pi}
            result = eval(  # noqa: S307
                selected_code,
                {"__builtins__": {}},
                local_scope,
            )
            self.result_text.insert(
                "insert",
                f"\n>>> {selected_code}\nSonuç: {result}\n",
            )
        except Exception as exc:  # pylint: disable=broad-exception-caught
            error_message = f"Kod çalıştırma hatası: {exc}"
            messagebox.showerror("Hata", error_message)
            self.result_text.insert("insert", f"\nHata: {error_message}\n")
        finally:
            self.disable_execute_mode()

    def disable_execute_mode(self) -> None:
        if hasattr(self, "result_text"):
            self.result_text.config(bg="white")
            self.result_text.insert(
                tk.END,
                "\n--- Execute Modu Devre Dışı ---\n",
            )
        self.execute_mode = False

    def _get_exec_mode_calculator(self):  # type: ignore[override]
        raise NotImplementedError(
            "ExecuteModeMixin requires a calculator provider"
        )
