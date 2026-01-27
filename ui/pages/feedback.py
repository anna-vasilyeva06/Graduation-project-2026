from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout

from ui.pages.base import BasePage

class FeedbackPage(BasePage):
    def __init__(self):
        super().__init__()

        root = QVBoxLayout(self)
        root.setAlignment(Qt.AlignTop)
        root.setContentsMargins(15,15,15,15)
        root.setSpacing(8)

        title = QLabel("Обратная связь")
        title.setStyleSheet("font-weight:bold; font-size:14px")
        root.addWidget(title)

        info = QLabel("""
Если вы нашли ошибку, есть предложения или вопросы

E-mail: app.system@gmail.com  
""")
        info.setWordWrap(True)
        root.addWidget(info)

        root.addStretch(1)
