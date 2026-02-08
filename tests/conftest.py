"""Pytest configuration.

Bu depo `src/` layout kullandığı için testlerde `machining_formulas` paketinin
bulunabilmesi adına `src` dizinini `sys.path`'e ekliyoruz.
"""

from __future__ import annotations

import sys
from pathlib import Path


SRC_PATH = (Path(__file__).resolve().parents[1] / "src").as_posix()
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)
