from __future__ import annotations

from typing import Optional

from PySide6.QtWidgets import QLabel


def wrap_label(text: str, *, tooltip: Optional[str] = None) -> QLabel:
    """QLabel, который не распирает ширину и корректно переносится."""
    l = QLabel(text)
    l.setWordWrap(True)
    l.setMinimumWidth(0)
    if tooltip:
        l.setToolTip(tooltip)
    return l


def elide_middle(s: str, max_len: int = 80) -> str:
    """Сокращает длинную строку по центру: left…right."""
    s = str(s or "")
    if len(s) <= max_len:
        return s
    keep = max_len - 1
    left = max(10, keep // 2)
    right = max(10, keep - left)
    return s[:left] + "…" + s[-right:]

