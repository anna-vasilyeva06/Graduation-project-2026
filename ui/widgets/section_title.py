from __future__ import annotations

from PySide6.QtWidgets import QLabel


def section_title(text: str) -> QLabel:
    """Заголовок секции внутри карточки (не на границе QGroupBox)."""
    lbl = QLabel(text)
    lbl.setObjectName("sectionTitle")
    return lbl
