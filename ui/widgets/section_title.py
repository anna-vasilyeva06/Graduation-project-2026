from __future__ import annotations

from PySide6.QtWidgets import QLabel


def section_title(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setObjectName("sectionTitle")
    return lbl
