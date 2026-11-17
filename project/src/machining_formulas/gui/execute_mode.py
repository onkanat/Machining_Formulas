"""Mixin to encapsulate the experimental execute-mode behaviour."""

from __future__ import annotations

import ast
import math
import operator
import tkinter as tk
from tkinter import messagebox
from typing import Any


_BIN_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}


def _evaluate_safe_expression(code: str, calculator: Any) -> Any:
    """Evaluate a numeric expression restricted to ``calc.<method>(...)`` calls."""
    try:
        parsed = ast.parse(code.strip(), mode="eval")
    except SyntaxError as exc:
        raise ValueError(f"Geçersiz ifade: {exc.msg}") from exc
    return _eval_node(parsed.body, calculator)


def _eval_node(node: ast.AST, calculator: Any) -> Any:
    if isinstance(node, ast.Constant):
        if isinstance(node.value, bool) or not isinstance(
            node.value, (int, float, str)
        ):
            raise ValueError("Yalnızca sayı ve metin sabitlerine izin verilir.")
        return node.value

    if isinstance(node, ast.Name):
        if node.id == "pi":
            return math.pi
        raise ValueError(f"İzin verilmeyen ad: {node.id}")

    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        operand = _eval_node(node.operand, calculator)
        return +operand if isinstance(node.op, ast.UAdd) else -operand

    if isinstance(node, ast.BinOp) and type(node.op) in _BIN_OPS:
        left = _eval_node(node.left, calculator)
        right = _eval_node(node.right, calculator)
        return _BIN_OPS[type(node.op)](left, right)

    if isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Attribute):
            raise ValueError("Yalnızca 'calc.<hesap>(...)' biçimi çalıştırılabilir.")
        if not isinstance(node.func.value, ast.Name) or node.func.value.id not in {
            "calc",
            "ec",
        }:
            raise ValueError("Yalnızca 'calc' veya 'ec' nesnesi üzerinden çağrı yapılabilir.")
        if node.keywords or any(isinstance(arg, ast.Starred) for arg in node.args):
            raise ValueError("Anahtar kelime ve yıldızlı argümanlar desteklenmez.")
        method_name = node.func.attr
        if method_name.startswith("_"):
            raise ValueError("Özel metotlar çalıştırılamaz.")
        method = getattr(calculator, method_name, None)
        if not callable(method):
            raise ValueError(f"Bilinmeyen hesap metodu: {method_name}")
        return method(*(_eval_node(arg, calculator) for arg in node.args))

    raise ValueError(f"İzin verilmeyen ifade türü: {type(node).__name__}")


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
            "\n\n--- HESAPLAMA ÇALIŞTIRMA (EXECUTE) MODU AKTİF ---\n"
            "Kısa Rehber:\n"
            "1. Çalıştırmak istediğiniz ifadeyi (örn: 'calc.calculate_turning(\"Cutting speed\", 100, 500)') seçin.\n"
            "2. Seçilen kodu execute komutuyla çalıştırın.\n"
            "3. Güvenlik Sınırı: Kod seçimi maksimum 2 kB (2048 karakter) ile sınırlıdır.\n"
            "4. Güvenli Kapsam: Yalnızca 'calc.<hesap>(...)' çağrıları ve aritmetik ifadeler desteklenir.\n"
            "--------------------------------------------------\n",
        )

    def execute_calculation(self, event: tk.Event | None = None) -> None:
        if not getattr(self, "execute_mode", False):
            return

        try:
            selected_code = self.result_text.get("sel.first", "sel.last")
            if not selected_code:
                self.result_text.insert(tk.END, "\nSeçili kod yok.\n")
                return

            # Güvenlik Sınırı Kontrolü: 2 kB (2048 bytes) sınırı
            if len(selected_code.encode("utf-8")) > 2048:
                warning_msg = "Seçilen kod boyutu 2 kB sınırını aşmaktadır. Güvenlik nedeniyle işlem iptal edildi."
                messagebox.showwarning("Güvenlik Sınırı Uyarısı", warning_msg)
                self.result_text.insert(tk.END, f"\n[İPTAL] {warning_msg}\n")
                return

            calculator = self._get_exec_mode_calculator()
            result = _evaluate_safe_expression(selected_code, calculator)
            self.result_text.insert(
                "insert",
                f"\n>>> {selected_code}\nSonuç: {result}\n",
            )
        except Exception as exc:  # pragma: no cover
            error_message = f"Kod çalıştırma hatası: {exc}"
            messagebox.showerror("Hata", error_message)
            self.result_text.insert("insert", f"\nHata: {error_message}\n")
        finally:
            self.disable_execute_mode()

    def disable_execute_mode(self) -> None:
        if hasattr(self, "result_text"):
            self.result_text.config(bg="white")
            self.result_text.insert(tk.END, "\n--- Execute Modu Devre Dışı ---\n")
        self.execute_mode = False

    def _get_exec_mode_calculator(self):  # type: ignore[override]
        raise NotImplementedError("ExecuteModeMixin requires a calculator provider")
