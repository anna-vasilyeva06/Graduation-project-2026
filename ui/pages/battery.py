from PySide6.QtWidgets import QVBoxLayout, QLabel, QProgressBar
from PySide6.QtCore import Qt
from ui.pages.base import BasePage

class BatteryPage(BasePage):
    def __init__(self):
        super().__init__()

        root = QVBoxLayout(self)
        root.setAlignment(Qt.AlignTop)
        root.setSpacing(6)
        root.setContentsMargins(12, 12, 12, 12)

        from core.battery import get_battery

        b = get_battery()
        if not b:
            root.addWidget(QLabel("Батарея не обнаружена"))
            return

        percent = int(b["Percent"])
        plugged = bool(b["Plugged"])

        root.addWidget(QLabel("<b>Батарея</b>"))

        bar = QProgressBar()
        bar.setValue(percent)
        bar.setFixedHeight(12)
        bar.setTextVisible(False)
        bar.setStyleSheet("""
            QProgressBar { background:#eee; border:1px solid #bbb; }
            QProgressBar::chunk { background:#5c9ded; }
        """)

        root.addWidget(bar)
        root.addWidget(QLabel(f"Заряд: {percent}%"))
        root.addWidget(QLabel(
            "Состояние: " + ("Подключено к сети" if plugged else "Работа от батареи")
        ))

        mins_left = b.get("Time left min")
        if mins_left and mins_left > 0:
            h = mins_left // 60
            m = mins_left % 60
            root.addWidget(QLabel(f"Осталось: {h} ч {m} мин"))

        root.addStretch()
