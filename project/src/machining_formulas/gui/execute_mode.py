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

# Değerlendirme sınırları: 2 kB seçim sınırına ek olarak ifade karmaşıklığını
# ve üretilebilecek sayı büyüklüğünü sınırlar (bellek/CPU tüketimini engeller).
_MAX_NODES = 200
_MAX_DEPTH = 40
_MAX_POW_EXPONENT = 64
_MAX_INT_BITS = 1024


def _evaluate_safe_expression(code: str, calculator: Any) -> Any:
    """Evaluate a numeric expression restricted to ``calc.<method>(...)`` calls."""
    try:
        parsed = ast.parse(code.strip(), mode="eval")
    except SyntaxError as exc:
        raise ValueError(f"Geçersiz ifade: {exc.msg}") from exc

    node_count = sum(1 for _ in ast.walk(parsed))
    if node_count > _MAX_NODES:
        raise ValueError(
            f"İfade çok karmaşık ({node_count} düğüm); en fazla {_MAX_NODES} düğüm desteklenir."
        )
    return _eval_node(parsed.body, calculator, depth=0)


def _check_int_size(value: int) -> int:
    if value.bit_length() > _MAX_INT_BITS:
        raise ValueError("Sayı değeri güvenlik sınırını aşıyor.")
    return value


def _numeric(value: Any, node_label: str) -> Any:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{node_label} için sayısal değer gerekir.")
    return value


def _eval_node(node: ast.AST, calculator: Any, depth: int = 0) -> Any:
    if depth > _MAX_DEPTH:
        raise ValueError("İfade iç içe çok derin; sadeleştirin.")

    if isinstance(node, ast.Constant):
        if isinstance(node.value, bool) or not isinstance(
            node.value, (int, float, str)
        ):
            raise ValueError("Yalnızca sayı ve metin sabitlerine izin verilir.")
        if isinstance(node.value, int):
            return _check_int_size(node.value)
        return node.value

    if isinstance(node, ast.Name):
        if node.id == "pi":
            return math.pi
        raise ValueError(f"İzin verilmeyen ad: {node.id}")

    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        operand = _numeric(_eval_node(node.operand, calculator, depth + 1), "İşaret işlemi")
        return +operand if isinstance(node.op, ast.UAdd) else -operand

    if isinstance(node, ast.BinOp) and type(node.op) in _BIN_OPS:
        left = _numeric(_eval_node(node.left, calculator, depth + 1), "Aritmetik işlem")
        right = _numeric(_eval_node(node.right, calculator, depth + 1), "Aritmetik işlem")
        if isinstance(node.op, ast.Pow):
            if abs(right) > _MAX_POW_EXPONENT:
                raise ValueError(
                    f"Üs en fazla {_MAX_POW_EXPONENT} olabilir (verilen: {right})."
                )
        result = _BIN_OPS[type(node.op)](left, right)
        if isinstance(result, int):
            return _check_int_size(result)
        return result

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
        return method(*(_eval_node(arg, calculator, depth + 1) for arg in node.args))

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
        if getattr(self, "execute_mode", False):
            return
        self.result_text.config(bg="#ffffd0")
        self.execute_mode = True
        self.result_text.insert(
            tk.END,
            "\n\n--- HESAPLAMA ÇALIŞTIRMA (EXECUTE) MODU AKTİF ---\n"
            "Kısa Rehber:\n"
            "1. Çalıştırmak istediğiniz ifadeyi (örn: 'calc.calculate_turning(\"Cutting speed\", 100, 500)') seçin.\n"
            "2. Seçilen kodu çalıştırma komutuyla (Cmd/Ctrl+Enter) değerlendirin.\n"
            "3. Güvenlik Sınırı: Kod seçimi en fazla 2 kB (2048 bayt) olabilir.\n"
            "4. Güvenli Kapsam: Yalnızca 'calc.<hesap>(...)' çağrıları ve sayısal aritmetik desteklenir.\n"
            "5. Ek sınırlar: en fazla 200 ifade düğümü, üs en fazla 64, derinlik en fazla 40.\n"
            "--------------------------------------------------\n",
        )

    def execute_calculation(self, event: tk.Event | None = None) -> None:
        if not getattr(self, "execute_mode", False):
            return

        try:
            try:
                selected_code = self.result_text.get("sel.first", "sel.last")
            except tk.TclError:
                selected_code = ""
            if not selected_code.strip():
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
                tk.END,
                f"\n>>> {selected_code}\nSonuç: {result}\n",
            )
        except ValueError as exc:
            self.result_text.insert(tk.END, f"\nHata: {exc}\n")
        except Exception as exc:  # pragma: no cover - beklenmeyen Tk/hesap hataları
            error_message = f"Kod çalıştırma hatası: {exc}"
            messagebox.showerror("Hata", error_message)
            self.result_text.insert(tk.END, f"\nHata: {error_message}\n")

    def disable_execute_mode(self) -> None:
        if hasattr(self, "result_text"):
            self.result_text.config(bg="white")
            self.result_text.insert(tk.END, "\n--- Execute Modu Devre Dışı ---\n")
        self.execute_mode = False

    def _get_exec_mode_calculator(self):  # type: ignore[override]
        raise NotImplementedError("ExecuteModeMixin requires a calculator provider")
