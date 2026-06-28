from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QGraphicsDropShadowEffect,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from ui.theme.glass import COLORS


class StartupSplash(QWidget):
    def __init__(self) -> None:
        super().__init__(
            None,
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.SplashScreen,
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFixedSize(135, 135)

        panel = QWidget(self)
        panel.setObjectName("startupSplashPanel")
        panel.setGeometry(0, 0, 135, 135)
        panel.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        panel.setStyleSheet(
            f"""
            QWidget#startupSplashPanel {{
                background-color: {COLORS["bg_main"]};
                border: 1px solid {COLORS["border_light"]};
                border-radius: 0px;
            }}
            QLabel#startupSplashTitle {{
                color: {COLORS["text"]};
                font-size: 20px;
                font-weight: 700;
                letter-spacing: -0.3px;
            }}
            QLabel#startupSplashHint {{
                color: {COLORS["text_secondary"]};
                font-size: 13px;
            }}
            """
        )

        lay = QVBoxLayout(panel)
        lay.setContentsMargins(28, 24, 28, 24)
        lay.setSpacing(8)

        title = QLabel("ITMetric")
        title.setObjectName("startupSplashTitle")
        hint = QLabel("Загрузка...")
        hint.setObjectName("startupSplashHint")

        lay.addStretch(1)
        lay.addWidget(title)
        lay.addWidget(hint)
        lay.addStretch(1)

        shadow = QGraphicsDropShadowEffect(panel)
        shadow.setBlurRadius(28)
        shadow.setOffset(0, 6)
        shadow.setColor(QColor(30, 136, 212, 55))

        panel.setGraphicsEffect(shadow)

    def center_on_screen(self) -> None:
        screen = self.screen()
        if screen is None:
            return
        g = self.frameGeometry()
        g.moveCenter(screen.availableGeometry().center())
        self.move(g.topLeft())
