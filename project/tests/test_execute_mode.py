import pytest
from unittest.mock import MagicMock
from machining_formulas.gui.execute_mode import ExecuteModeMixin

class DummyCalculator(ExecuteModeMixin):
    def __init__(self):
        super().__init__()
        self.result_text = MagicMock()

    def _get_exec_mode_calculator(self):
        return MagicMock()


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
    assert calc.execute_mode is False


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
    assert calc.execute_mode is False
