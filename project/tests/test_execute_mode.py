import tkinter as tk
from unittest.mock import MagicMock

import pytest

from machining_formulas.core.engineering_calculator import EngineeringCalculator
from machining_formulas.gui.execute_mode import (
    ExecuteModeMixin,
    _evaluate_safe_expression,
)


class DummyCalculator(ExecuteModeMixin):
    def __init__(self):
        super().__init__()
        self.result_text = MagicMock()

    def _get_exec_mode_calculator(self):
        return MagicMock()


def _inserted_text(widget: MagicMock) -> str:
    return "".join(call.args[1] for call in widget.insert.call_args_list if len(call.args) > 1)


def test_execute_mode_under_limit(monkeypatch):
    """Test execute_calculation executes normally when selection is under 2kB."""
    calc = DummyCalculator()
    calc.execute_mode = True

    # Selection of code under limit
    calc.result_text.get.return_value = "2 + 2"

    # Mock messagebox
    mock_showwarning = MagicMock()
    monkeypatch.setattr("tkinter.messagebox.showwarning", mock_showwarning)

    calc.execute_calculation()

    # showwarning should NOT be called
    mock_showwarning.assert_not_called()
    assert "Sonuç: 4" in _inserted_text(calc.result_text)
    assert calc.execute_mode is True


def test_execute_mode_over_limit(monkeypatch):
    """Test execute_calculation blocks and shows a warning when selection is over 2kB."""
    calc = DummyCalculator()
    calc.execute_mode = True

    # Selection of extremely long code over 2048 bytes
    calc.result_text.get.return_value = "a" * 2050

    # Mock messagebox
    mock_showwarning = MagicMock()
    monkeypatch.setattr("tkinter.messagebox.showwarning", mock_showwarning)

    calc.execute_calculation()

    # showwarning SHOULD be called
    mock_showwarning.assert_called_once()
    assert calc.execute_mode is True


def test_execute_mode_without_selection_reports_turkish_message(monkeypatch):
    """Seçim yokken TclError yutulmalı ve kullanıcıya açık mesaj gösterilmeli."""
    calc = DummyCalculator()
    calc.execute_mode = True
    calc.result_text.get.side_effect = tk.TclError("text doesn't contain any characters tagged with sel")

    mock_showerror = MagicMock()
    monkeypatch.setattr("tkinter.messagebox.showerror", mock_showerror)

    calc.execute_calculation()

    assert "Seçili kod yok." in _inserted_text(calc.result_text)
    mock_showerror.assert_not_called()
    assert calc.execute_mode is True


def test_execute_mode_blocks_dunder_escape(monkeypatch):
    """Özel (dunder) attribute erişimi sandbox kaçışına izin vermemeli."""
    calc = DummyCalculator()
    calc.execute_mode = True
    calc.result_text.get.return_value = "(1).__class__.__base__.__subclasses__()"

    mock_showerror = MagicMock()
    monkeypatch.setattr("tkinter.messagebox.showerror", mock_showerror)

    calc.execute_calculation()

    assert "Hata:" in _inserted_text(calc.result_text)
    mock_showerror.assert_not_called()
    assert calc.execute_mode is True


def test_calculator_method_call_is_evaluated():
    """calc.<hesap>(...) çağrısı gerçek hesaplayıcı üzerinde çalışmalı."""
    result = _evaluate_safe_expression(
        'ec.calculate_turning("Cutting speed", 100, 500)', EngineeringCalculator()
    )

    assert pytest.approx(result["value"], rel=1e-4) == 157.08
    assert result["units"] == "m/min"


@pytest.mark.parametrize(
    ("code", "message"),
    [
        ("(1).__class__", "İzin verilmeyen ifade türü"),
        ("os.system('ls')", "Yalnızca 'calc' veya 'ec'"),
        ("calc._private()", "Özel metotlar"),
        ("calc.yok_boyle_metot()", "Bilinmeyen hesap metodu"),
        ("calc.calculate_turning(name='x')", "Anahtar kelime"),
        ("2 ** 65", "Üs en fazla"),
        ('"a" * 5', "sayısal değer gerekir"),
        ("-" * 50 + "1", "iç içe çok derin"),
        ("1" * 2000, "güvenlik sınırını aşıyor"),
    ],
)
def test_evaluator_rejects_unsafe_expressions(code, message):
    with pytest.raises(ValueError, match=message):
        _evaluate_safe_expression(code, EngineeringCalculator())


def test_evaluator_rejects_too_many_nodes():
    expression = " + ".join(["1"] * 150)

    with pytest.raises(ValueError, match="çok karmaşık"):
        _evaluate_safe_expression(expression, EngineeringCalculator())


def test_evaluator_allows_pi_and_basic_arithmetic():
    result = _evaluate_safe_expression("2 * pi", EngineeringCalculator())

    assert pytest.approx(result, rel=1e-12) == 6.283185307179586


def test_execute_mode_stays_enabled_between_runs(monkeypatch):
    """Bir çalıştırmadan sonra mod açık kalmalı; ikinci komut sessizce yutulmamalı."""
    calc = DummyCalculator()
    calc.execute_mode = True
    calc.result_text.get.return_value = "2 + 2"
    monkeypatch.setattr("tkinter.messagebox.showwarning", MagicMock())

    calc.execute_calculation()
    calc.execute_calculation()

    assert calc.execute_mode is True
    assert _inserted_text(calc.result_text).count("Sonuç: 4") == 2
