from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QGroupBox, QGridLayout, QProgressBar

from core.system import get_system_info
from ui.pages.base import BasePage
from ui.widgets import PageHeader, KpiCard, section_title


class HomePage(BasePage):
    def __init__(self):
        super().__init__()

        info = get_system_info()

        root = QVBoxLayout(self)
        root.setAlignment(Qt.AlignTop)
        root.setSpacing(18)
        root.setContentsMargins(16, 16, 16, 16)

        root.addWidget(
            PageHeader(
                "Главная",
                "Сводка по системе, ресурсам и времени работы.",
            )
        )

        # KPI-плитки (сетка 2×2)
        kpi_grid = QGridLayout()
        kpi_grid.setSpacing(12)

        ram_pct = info.get("ram_usage_percent")
        ram_hint = ""
        if ram_pct is not None:
            ram_used = info.get("ram_used_gb")
            ram_total = info.get("ram_gb")
            ram_hint = (
                f"{ram_used} / {ram_total} GB"
                if ram_used is not None and ram_total is not None
                else ""
            )
            card_ram = KpiCard("ОЗУ", f"{int(ram_pct)}%", ram_hint)
        else:
            card_ram = KpiCard("ОЗУ", "—", "")

        disk = info.get("total_disk_gb")
        card_disk = KpiCard(
            "Диски (сумма)",
            f"{disk} GB" if disk is not None else "—",
            "Логические разделы",
        )

        card_up = KpiCard(
            "Аптайм",
            str(info.get("uptime", "—")).split(".")[0],
            "с последней загрузки",
        )

        bat = info.get("battery_percent")
        if bat is not None:
            card_bat = KpiCard("Батарея", f"{int(bat)}%", "ноутбук / планшет")
        else:
            card_bat = KpiCard("Батарея", "Нет", "стационарный ПК")

        kpi_grid.addWidget(card_ram, 0, 0)
        kpi_grid.addWidget(card_disk, 0, 1)
        kpi_grid.addWidget(card_up, 1, 0)
        kpi_grid.addWidget(card_bat, 1, 1)
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

        def add_row(grid, row, label, value):
            k = QLabel(label)
            k.setStyleSheet("color:#5a6d82;")
            v = QLabel(str(value))
            grid.addWidget(k, row, 0, alignment=Qt.AlignLeft)
            grid.addWidget(v, row, 1, alignment=Qt.AlignLeft)

        add_row(grid_sys, 0, "ПК", info.get("pc_name", "—"))
        add_row(grid_sys, 1, "Пользователь / домен", info.get("user", "—"))
        add_row(grid_sys, 2, "ОС", info.get("os", "—"))
        add_row(grid_sys, 3, "Архитектура", info.get("architecture", "—"))
        add_row(grid_sys, 4, "MAC-адрес", info.get("mac", "—"))
        add_row(grid_sys, 5, "Время последней загрузки", info.get("boot_time", "—"))
        lay_sys.addLayout(grid_sys)

        root.addWidget(box_system)

        box_hw = QGroupBox()
        box_hw.setTitle("")
        lay_hw = QVBoxLayout(box_hw)
        lay_hw.addWidget(section_title("Аппаратные ресурсы"))
        grid_hw = QGridLayout()
        grid_hw.setSpacing(10)
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
            lbl_ram.setStyleSheet("color:#5a6d82;")
            grid_hw.addWidget(lbl_ram, mem_layout_row, 0, alignment=Qt.AlignLeft)
            grid_hw.addWidget(mem_label, mem_layout_row, 1, alignment=Qt.AlignLeft)
            grid_hw.addWidget(bar, mem_layout_row + 1, 0, 1, 2)
        else:
            add_row(grid_hw, 1, "ОЗУ", "нет данных")

        add_row(grid_hw, 3, "Суммарный объём дисков", f'{info.get("total_disk_gb", "—")} GB')

        battery = info.get("battery_percent")
        if battery is not None:
            bar_bat = QProgressBar()
            bar_bat.setFixedHeight(12)
            bar_bat.setRange(0, 100)
            bar_bat.setValue(int(battery))
            bar_bat.setTextVisible(False)
            lbl_bat = QLabel("Батарея")
            lbl_bat.setStyleSheet("color:#5a6d82;")
            grid_hw.addWidget(lbl_bat, 4, 0, alignment=Qt.AlignLeft)
            grid_hw.addWidget(QLabel(f"{battery}%"), 4, 1, alignment=Qt.AlignLeft)
            grid_hw.addWidget(bar_bat, 5, 0, 1, 2)

        lay_hw.addLayout(grid_hw)
        root.addWidget(box_hw)

        root.addStretch(1)
