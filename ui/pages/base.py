from __future__ import annotations

from PySide6.QtWidgets import QWidget


class BasePage(QWidget):

    def filter(self, text: str) -> None:
        return

    def clear_filter(self) -> None:
        return

