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
            lbl_no = QLabel("Батарея не обнаружена")
            lbl_no.setToolTip("На стационарных ПК батарея отсутствует. Раздел актуален для ноутбуков и планшетов")
            root.addWidget(lbl_no)
            return

        percent = int(b["Percent"])
        plugged = bool(b["Plugged"])

        lbl_bat = QLabel("<b>Батарея</b>")
        lbl_bat.setToolTip("Уровень заряда и состояние питания. При низком заряде рекомендуется подключить зарядку")
        root.addWidget(lbl_bat)

        bar = QProgressBar()
        bar.setValue(percent)
        bar.setFixedHeight(12)
        bar.setTextVisible(False)

        root.addWidget(bar)
        lbl_pct = QLabel(f"Заряд: {percent}%")
        lbl_pct.setToolTip("Текущий уровень заряда батареи (0–100%)")
        root.addWidget(lbl_pct)
        lbl_st = QLabel("Состояние: " + ("Подключено к сети" if plugged else "Работа от батареи"))
        lbl_st.setToolTip("Подключено к сети — батарея заряжается. Работа от батареи — питание от аккумулятора")
        root.addWidget(lbl_st)

        mins_left = b.get("Time left min")
        if mins_left and mins_left > 0:
            h = mins_left // 60
            m = mins_left % 60
            lbl_time = QLabel(f"Осталось: {h} ч {m} мин")
            lbl_time.setToolTip("Примерное время работы до полной разрядки (при текущей нагрузке)")
            root.addWidget(lbl_time)

        root.addStretch()
