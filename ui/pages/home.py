from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QGroupBox, QGridLayout, QProgressBar

from core.system import get_system_info
from ui.pages.base import BasePage
<<<<<<< Updated upstream
=======
from ui.widgets import KpiCard, add_page_header, make_page_root, section_title

>>>>>>> Stashed changes

class HomePage(BasePage):
    def __init__(self):
        super().__init__()

<<<<<<< Updated upstream
=======
        root = make_page_root(self, spacing=18)
        add_page_header(root, "Главная", "Сводка по системе, ресурсам и времени работы.")

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
        self._hw_bat_pct = QLabel("—")
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
>>>>>>> Stashed changes
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
