from __future__ import annotations

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget


class PageHeader(QWidget):
    """Заголовок страницы и подзаголовок в едином стиле."""

    def __init__(self, title: str, subtitle: str = "", parent=None):
        super().__init__(parent)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 18)
        lay.setSpacing(6)

        t = QLabel(title)
        t.setObjectName("pageTitle")
        lay.addWidget(t)

        if subtitle:
            s = QLabel(subtitle)
            s.setObjectName("pageSubtitle")
            s.setWordWrap(True)
            lay.addWidget(s)
