"""V3 GUI entrypoint (package wrapper).

Bu repo geçiş sürecinde hem kökteki `v3_gui.py` hem de `src/` paket yapısı
birlikte bulunuyor. Bu modül, `python -m machining_formulas` çalıştırıldığında
V3 arayüzünü başlatmak için bir köprü görevi görür.

Not: GUI'nin asıl uygulaması şimdilik depo kökündeki `v3_gui.py` içindedir.
"""

from __future__ import annotations


def main() -> None:
    """Start the V3 GUI."""
    # Root-level module import (repo usage)
    from v3_gui import main as root_main  # type: ignore

    root_main()


if __name__ == "__main__":
    main()
