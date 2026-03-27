from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QGroupBox, QGridLayout, QProgressBar

from core.system import get_system_info
from ui.pages.base import BasePage

class HomePage(BasePage):
    def __init__(self):
        super().__init__()

        info = get_system_info()

        root = QVBoxLayout(self)
        root.setAlignment(Qt.AlignTop)
        root.setSpacing(10)
        root.setContentsMargins(12, 12, 12, 12)

        title = QLabel("Общая сводка по системе")
        title.setStyleSheet("font-size:16px; font-weight:bold")
        root.addWidget(title)
        root.addSpacing(16)

        box_system = QGroupBox("Система")
        grid_sys = QGridLayout(box_system)
        grid_sys.setSpacing(8)
        grid_sys.setColumnStretch(1, 1)

        def add_row(grid, row, label, value):
            k = QLabel(label)
            k.setStyleSheet("color:#5a6c7d;")
            v = QLabel(str(value))
            grid.addWidget(k, row, 0, alignment=Qt.AlignLeft)
            grid.addWidget(v, row, 1, alignment=Qt.AlignLeft)

        add_row(grid_sys, 0, "ПК", info.get("pc_name", "—"))
        add_row(grid_sys, 1, "Пользователь / домен", info.get("user", "—"))
        add_row(grid_sys, 2, "ОС", info.get("os", "—"))
        add_row(grid_sys, 3, "Архитектура", info.get("architecture", "—"))
        add_row(grid_sys, 4, "MAC-адрес", info.get("mac", "—"))
        add_row(grid_sys, 5, "BIOS / UEFI", info.get("bios", "—"))
        add_row(grid_sys, 6, "Последнее обновление Windows", info.get("last_update", "—"))
        add_row(grid_sys, 7, "Время последней загрузки", info.get("boot_time", "—"))
        add_row(grid_sys, 8, "Время работы системы", info.get("uptime", "—"))

        root.addWidget(box_system)
        root.addSpacing(16)

        box_hw = QGroupBox("Аппаратные ресурсы")
        grid_hw = QGridLayout(box_hw)
        grid_hw.setSpacing(8)
        grid_hw.setColumnStretch(1, 1)

        add_row(grid_hw, 0, "Процессор", info.get("cpu", "—"))
        ram_total = info.get("ram_gb")
        ram_used = info.get("ram_used_gb")
        ram_pct = info.get("ram_usage_percent")

        if ram_total is not None and ram_pct is not None:
            bar = QProgressBar()
            bar.setFixedHeight(12)
            bar.setRange(0, 100)
            bar.setValue(int(ram_pct))
            bar.setTextVisible(False)

            mem_label = QLabel(f"{ram_used} / {ram_total} GB ({ram_pct}%)")
            mem_layout_row = 1
            lbl_ram = QLabel("ОЗУ")
            lbl_ram.setStyleSheet("color:#5a6c7d;")
            grid_hw.addWidget(lbl_ram, mem_layout_row, 0, alignment=Qt.AlignLeft)
            grid_hw.addWidget(mem_label, mem_layout_row, 1, alignment=Qt.AlignLeft)
            grid_hw.addWidget(bar, mem_layout_row + 1, 0, 1, 2)
        else:
            add_row(grid_hw, 1, "ОЗУ", "нет данных")

        add_row(grid_hw, 3, "Суммарный объём дисков", f'{info.get("total_disk_gb","—")} GB')

        battery = info.get("battery_percent")
        if battery is not None:
            bar_bat = QProgressBar()
            bar_bat.setFixedHeight(12)
            bar_bat.setRange(0, 100)
            bar_bat.setValue(int(battery))
            bar_bat.setTextVisible(False)
            lbl_bat = QLabel("Батарея")
            lbl_bat.setStyleSheet("color:#5a6c7d;")
            grid_hw.addWidget(lbl_bat, 4, 0, alignment=Qt.AlignLeft)
            grid_hw.addWidget(QLabel(f"{battery}%"), 4, 1, alignment=Qt.AlignLeft)
            grid_hw.addWidget(bar_bat, 5, 0, 1, 2)

        root.addWidget(box_hw)

        root.addStretch(1)
