from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout

from ui.widgets import PageHeader


class BasePage(QWidget):

    def build_root(
        self,
        title: str,
        subtitle: str,
        *,
        spacing: int = 12,
        margins: tuple[int, int, int, int] = (16, 16, 16, 16),
        align_top: bool = True,
    ) -> QVBoxLayout:
        root = QVBoxLayout(self)
        if align_top:
            root.setAlignment(Qt.AlignTop)
        root.setSpacing(spacing)
        root.setContentsMargins(*margins)
        root.addWidget(PageHeader(title, subtitle))
        return root

    def filter(self, text: str) -> None:
        return

    def clear_filter(self) -> None:
        return

