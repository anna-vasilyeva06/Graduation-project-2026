from PySide6.QtWidgets import QLabel, QProgressBar, QHBoxLayout, QPushButton, QVBoxLayout, QWidget
from PySide6.QtCore import Qt
from ui.pages.base import BasePage

class BatteryPage(BasePage):
    def __init__(self):
        super().__init__()

        self._root = self.build_root(
            "Батарея",
            "Заряд и режим питания.",
            spacing=12,
        )
        self._content = QWidget()
        self._content_lay = QVBoxLayout(self._content)
        self._content_lay.setContentsMargins(0, 0, 0, 0)
        self._content_lay.setSpacing(12)
        self._root.addWidget(self._content)
        self._root.addStretch(1)
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_refresh = QPushButton("Обновить")
        btn_refresh.setToolTip("Обновить данные по батарее и питанию")
        btn_refresh.clicked.connect(self._refresh)
        btn_row.addWidget(btn_refresh)
        self._root.addLayout(btn_row)
        self._refresh()

    def _clear_layout(self, lay: QVBoxLayout) -> None:
        while lay.count():
            item = lay.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)
                w.deleteLater()

    def _refresh(self) -> None:
        self._clear_layout(self._content_lay)
        root = self._content_lay

        from core.battery import get_battery
        b = get_battery()
        if not b:
            lbl_no = QLabel("Батарея не обнаружена")
            lbl_no.setToolTip(
                "На стационарных ПК батарея отсутствует. Раздел актуален для ноутбуков"
            )
            root.addWidget(lbl_no)
            return
        percent = int(b["Percent"])
        plugged = bool(b["Plugged"])

        lbl_bat = QLabel("<b>Батарея</b>")
        lbl_bat.setToolTip(
            "Уровень заряда и состояние питания. При низком заряде рекомендуется подключить зарядку"
        )
        root.addWidget(lbl_bat)
        bar = QProgressBar()
        bar.setValue(percent)
        bar.setFixedHeight(12)
        bar.setTextVisible(False)
        root.addWidget(bar)
        lbl_pct = QLabel(f"Заряд: {percent}%")
        lbl_pct.setToolTip("Текущий уровень заряда батареи (0-100%)")
        root.addWidget(lbl_pct)
        lbl_st = QLabel(
            "Состояние: " + ("Подключено к сети" if plugged else "Работа от батареи")
        )
        lbl_st.setToolTip(
            "Подключено к сети - батарея заряжается. Работа от батареи - питание от аккумулятора"
        )
        root.addWidget(lbl_st)
        mins_left = b.get("Time left min")
        if mins_left and mins_left > 0:
            h = mins_left // 60
            m = mins_left % 60
            lbl_time = QLabel(f"Осталось: {h} ч {m} мин")
            lbl_time.setToolTip(
                "Примерное время работы до полной разрядки (при текущей нагрузке)"
            )
            root.addWidget(lbl_time)
