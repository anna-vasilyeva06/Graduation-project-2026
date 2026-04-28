from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QVBoxLayout, QWidget

from ui.widgets.page_header import PageHeader


def make_page_root(widget: QWidget, *, spacing: int = 10, margins: tuple[int, int, int, int] = (16, 16, 16, 16)) -> QVBoxLayout:
    root = QVBoxLayout(widget)
    root.setAlignment(Qt.AlignmentFlag.AlignTop)
    root.setSpacing(int(spacing))
    root.setContentsMargins(*[int(x) for x in margins])
    return root


def add_page_header(root: QVBoxLayout, title: str, subtitle: str = "") -> PageHeader:
    hdr = PageHeader(title, subtitle)
    root.addWidget(hdr)
    return hdr

