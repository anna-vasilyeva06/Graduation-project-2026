from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QLabel,
    QVBoxLayout,
    QGroupBox,
    QGridLayout,
    QProgressBar,
    QHBoxLayout,
    QPushButton,
)

from core.system import get_system_info
from ui.pages.base import BasePage
from ui.widgets import KpiCard, section_title


class HomePage(BasePage):
    def __init__(self):
        super().__init__()

        root = self.build_root(
            "Главная",
            "Сводка по системе, ресурсам и времени работы.",
            spacing=18,
        )

        kpi_grid = QGridLayout()
        kpi_grid.setSpacing(12)

        self._card_ram = KpiCard("ОЗУ", "—", "")
        self._card_disk = KpiCard("Диски (сумма)", "—", "Логические разделы")
        self._card_up = KpiCard("Аптайм", "—", "с последней загрузки")
        self._card_bat = KpiCard("Батарея", "—", "")

        kpi_grid.addWidget(self._card_ram, 0, 0)
        kpi_grid.addWidget(self._card_disk, 0, 1)
        kpi_grid.addWidget(self._card_up, 1, 0)
        kpi_grid.addWidget(self._card_bat, 1, 1)
        kpi_grid.setColumnStretch(0, 1)
        kpi_grid.setColumnStretch(1, 1)

        root.addLayout(kpi_grid)

        box_system = QGroupBox()
        box_system.setTitle("")
        lay_sys = QVBoxLayout(box_system)
        lay_sys.addWidget(section_title("Система"))
        grid_sys = QGridLayout()
        grid_sys.setSpacing(10)
        grid_sys.setColumnStretch(1, 1)
        self._sys_value_labels: list[QLabel] = []
        sys_labels = [
            "ПК",
            "Пользователь / домен",
            "ОС",
            "Архитектура",
            "MAC-адрес",
            "Время последней загрузки",
        ]
        for row, text in enumerate(sys_labels):
            k = QLabel(text)
            k.setStyleSheet("color:#5a6d82;")
            v = QLabel("—")
            grid_sys.addWidget(k, row, 0, alignment=Qt.AlignLeft)
            grid_sys.addWidget(v, row, 1, alignment=Qt.AlignLeft)
            self._sys_value_labels.append(v)
        lay_sys.addLayout(grid_sys)
        root.addWidget(box_system)

        box_hw = QGroupBox()
        box_hw.setTitle("")
        lay_hw = QVBoxLayout(box_hw)
        lay_hw.addWidget(section_title("Аппаратные ресурсы"))
        grid_hw = QGridLayout()
        grid_hw.setSpacing(10)
        grid_hw.setColumnStretch(1, 1)

        lbl_cpu = QLabel("Процессор")
        lbl_cpu.setStyleSheet("color:#5a6d82;")
        self._hw_cpu_value = QLabel("—")
        grid_hw.addWidget(lbl_cpu, 0, 0, alignment=Qt.AlignLeft)
        grid_hw.addWidget(self._hw_cpu_value, 0, 1, alignment=Qt.AlignLeft)

        self._hw_ram_lbl = QLabel("ОЗУ")
        self._hw_ram_lbl.setStyleSheet("color:#5a6d82;")
        self._hw_mem_text = QLabel("—")
        self._hw_mem_bar = QProgressBar()
        self._hw_mem_bar.setFixedHeight(12)
        self._hw_mem_bar.setRange(0, 100)
        self._hw_mem_bar.setTextVisible(False)
        grid_hw.addWidget(self._hw_ram_lbl, 1, 0, alignment=Qt.AlignLeft)
        grid_hw.addWidget(self._hw_mem_text, 1, 1, alignment=Qt.AlignLeft)
        grid_hw.addWidget(self._hw_mem_bar, 2, 0, 1, 2)

        self._hw_disk_lbl = QLabel("Суммарный объём дисков")
        self._hw_disk_lbl.setStyleSheet("color:#5a6d82;")
        self._hw_disk_value = QLabel("—")
        grid_hw.addWidget(self._hw_disk_lbl, 3, 0, alignment=Qt.AlignLeft)
        grid_hw.addWidget(self._hw_disk_value, 3, 1, alignment=Qt.AlignLeft)

        self._hw_bat_lbl = QLabel("Батарея")
        self._hw_bat_lbl.setStyleSheet("color:#5a6d82;")
        self._hw_bat_pct = QLabel("-")
        self._hw_bat_bar = QProgressBar()
        self._hw_bat_bar.setFixedHeight(12)
        self._hw_bat_bar.setRange(0, 100)
        self._hw_bat_bar.setTextVisible(False)
        grid_hw.addWidget(self._hw_bat_lbl, 4, 0, alignment=Qt.AlignLeft)
        grid_hw.addWidget(self._hw_bat_pct, 4, 1, alignment=Qt.AlignLeft)
        grid_hw.addWidget(self._hw_bat_bar, 5, 0, 1, 2)

        lay_hw.addLayout(grid_hw)
        root.addWidget(box_hw)

        root.addStretch(1)

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_refresh = QPushButton("Обновить")
        btn_refresh.setToolTip("Пересчитать показатели ОЗУ, дисков, аптайма и батареи")
        btn_refresh.clicked.connect(self._refresh_home)
        btn_row.addWidget(btn_refresh)
        root.addLayout(btn_row)

        self._refresh_home()

    def _refresh_home(self) -> None:
        info = get_system_info()

        ram_pct = info.get("ram_usage_percent")
        if ram_pct is not None:
            ram_used = info.get("ram_used_gb")
            ram_total = info.get("ram_gb")
            hint = (
                f"{ram_used} / {ram_total} GB"
                if ram_used is not None and ram_total is not None
                else ""
            )
            self._card_ram.set_metric(f"{int(ram_pct)}%", hint)
        else:
            self._card_ram.set_metric("-", "")

        disk = info.get("total_disk_gb")
        self._card_disk.set_metric(
            f"{disk} GB" if disk not in (None, 0) else "-",
            "Логические разделы",
        )

        self._card_up.set_metric(
            str(info.get("uptime", "-")).split(".")[0],
            "с последней загрузки",
        )

        bat = info.get("battery_percent")
        if bat is not None:
            self._card_bat.set_metric(f"{int(bat)}%", "")
        else:
            self._card_bat.set_metric("Нет", "стационарный ПК")

        keys_sys = [
            "pc_name",
            "user",
            "os",
            "architecture",
            "mac",
            "boot_time",
        ]
        for i, key in enumerate(keys_sys):
            self._sys_value_labels[i].setText(str(info.get(key, "-")))

        self._hw_cpu_value.setText(str(info.get("cpu", "-")))

        ram_total = info.get("ram_gb")
        ram_used = info.get("ram_used_gb")
        ram_pct_hw = info.get("ram_usage_percent")
        if ram_total is not None and ram_pct_hw is not None:
            self._hw_mem_text.setText(f"{ram_used} / {ram_total} GB ({ram_pct_hw}%)")
            self._hw_mem_bar.setValue(int(ram_pct_hw))
            self._hw_mem_bar.setVisible(True)
            self._hw_ram_lbl.setVisible(True)
            self._hw_mem_text.setVisible(True)
        else:
            self._hw_mem_text.setText("нет данных")
            self._hw_mem_bar.setVisible(False)

        _disk_gb = info.get("total_disk_gb")
        self._hw_disk_value.setText(
            f"{_disk_gb} GB" if _disk_gb not in (None, 0) else "—"
        )

        battery = info.get("battery_percent")
        if battery is not None:
            self._hw_bat_pct.setText(f"{battery}%")
            self._hw_bat_bar.setValue(int(battery))
            self._hw_bat_lbl.setVisible(True)
            self._hw_bat_pct.setVisible(True)
            self._hw_bat_bar.setVisible(True)
        else:
            self._hw_bat_lbl.setVisible(False)
            self._hw_bat_pct.setVisible(False)
            self._hw_bat_bar.setVisible(False)
