"""Базовый шрифт приложения: Windows — Segoe UI Variable / Segoe UI."""
from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtGui import QFont

if TYPE_CHECKING:
    from PySide6.QtWidgets import QApplication


def setup_app_font(app: "QApplication") -> None:
    """Назначает читаемый UI-шрифт с антиалиасингом (лучше, чем один QSS font-family)."""
    candidates = (
        "Segoe UI Variable Text",
        "Segoe UI Variable",
        "Segoe UI",
    )
    font = QFont()
    for name in candidates:
        font.setFamily(name)
        if font.exactMatch():
            break
    else:
        font.setFamily("Segoe UI")

    font.setPixelSize(14)
    font.setWeight(QFont.Weight.Normal)
    font.setHintingPreference(QFont.HintingPreference.PreferDefaultHinting)
    font.setStyleStrategy(
        QFont.StyleStrategy.PreferAntialias | QFont.StyleStrategy.PreferQuality
    )
    app.setFont(font)
