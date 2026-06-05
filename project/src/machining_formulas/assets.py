"""Asset path helpers.

Assets live in the repository root under the `assets/` folder.
"""

from __future__ import annotations

from pathlib import Path


def repo_root() -> Path:
    """Return repository root based on this file location.

    Works for editable installs and local runs.
    """
    # .../src/machining_formulas/assets.py -> parents[2] == repo root
    return Path(__file__).resolve().parents[2]


def asset_path(relative: str) -> Path:
    """Resolve an asset file path under repo-root/assets."""
    return repo_root() / "assets" / relative
