import threading

import pytest

from machining_formulas.gui.v3_gui import V3Calculator


class FakeRoot:
    """Collects ``after`` callbacks so tests can run them on the calling thread."""

    def __init__(self):
        self.pending = []

    def after(self, _delay, callback):
        self.pending.append(callback)

    def dispatch(self, timeout=5.0):
        deadline = threading.Event()
        waited = 0.0
        while not self.pending and waited < timeout:
            deadline.wait(0.01)
            waited += 0.01
        if not self.pending:
            raise AssertionError("arka plan işi zamanında tamamlanmadı")
        while self.pending:
            self.pending.pop(0)()


@pytest.fixture()
def background_app():
    app = V3Calculator.__new__(V3Calculator)
    app.root = FakeRoot()
    return app


def test_run_background_applies_result(background_app):
    seen = []
    background_app._run_background(lambda: 2 + 2, seen.append, lambda e: seen.append(e))

    background_app.root.dispatch()

    assert seen == [4]


def test_run_background_reports_error(background_app):
    seen = []

    def work():
        raise RuntimeError("ağ hatası")

    background_app._run_background(work, seen.append, seen.append)

    background_app.root.dispatch()

    assert len(seen) == 1
    assert isinstance(seen[0], RuntimeError)
    assert str(seen[0]) == "ağ hatası"
