"""Asset and configuration path helpers.

Read-only assets (images, tooltips) live next to the package under
``project/assets/``. User settings must not be written into the source tree,
so they live in the per-user configuration directory instead.
"""

from __future__ import annotations

import os
from pathlib import Path


def project_root() -> Path:
    """Return the project directory that contains ``assets/``."""
    # .../src/machining_formulas/assets.py -> parents[2] == project root
    return Path(__file__).resolve().parents[2]


def asset_path(relative: str) -> Path:
    """Resolve a read-only asset path under ``project/assets``."""
    return project_root() / "assets" / relative


def config_dir() -> Path:
    """Return the per-user configuration directory.

    ``MACHINING_FORMULAS_CONFIG_DIR`` overrides the default location so tests
    and portable installs can redirect writes.
    """
    override = os.environ.get("MACHINING_FORMULAS_CONFIG_DIR")
    if override:
        return Path(override).expanduser()
    return Path.home() / ".config" / "machining_formulas"


def settings_path() -> Path:
    """Return the path of the persisted user settings file."""
    return config_dir() / "settings.json"
