from __future__ import annotations

from pathlib import Path
import sys

from ui.icons.loader import NAV_ICON_FILES, nav_icons, svg_to_icon


def _resource_root() -> Path:
    # PyInstaller: sys._MEIPASS points to the unpacked bundle root.
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        return Path(meipass)
    # Source run: repo root (two levels above ui/icons)
    return Path(__file__).resolve().parents[2]


def app_icon() -> QIcon:
    """
    Application/window icon.

    Prefer .ico on Windows; fallback to .svg when running from sources.
    """
    # Lazy import: avoids importing QtGui for modules that only need nav icon helpers.
    from PySide6.QtGui import QIcon

    root = _resource_root()
    candidates = [
        root / "ui" / "icons" / "svg" / "icon.ico",
        root / "ui" / "icons" / "icon.svg",
    ]
    for p in candidates:
        if p.is_file():
            ico = QIcon(str(p))
            if not ico.isNull():
                return ico
    return QIcon()

__all__ = ["NAV_ICON_FILES", "nav_icons", "svg_to_icon", "app_icon"]
