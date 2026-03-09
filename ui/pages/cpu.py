from PySide6.QtCharts import QChart, QChartView, QLineSeries
from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import (
    QLabel,
    QVBoxLayout,
    QGroupBox,
    QHBoxLayout,
    QPushButton,
    QListWidget,
)

import psutil

from core.processes import get_top_processes
from ui.pages.base import BasePage


class CpuPage(BasePage):
    def __init__(self):
        super().__init__()
        root = QVBoxLayout(self)
        root.setAlignment(Qt.AlignTop)
        root.setSpacing(6)
        root.setContentsMargins(12, 12, 12, 12)

        from core.cpu import get_cpu

        cpu = get_cpu()
        lbl_cpu = QLabel("<b>Процессор</b>")
        lbl_cpu.setToolTip("Центральный процессор: модель, ядра, потоки и текущая загрузка в реальном времени")
        root.addWidget(lbl_cpu)
        root.addWidget(QLabel("Модель: " + str(cpu.get("Model", "—"))))
        lbl_cores = QLabel("Ядер: " + str(cpu.get("Cores", "—")))
        lbl_cores.setToolTip("Физические ядра процессора")
        root.addWidget(lbl_cores)
        lbl_threads = QLabel("Потоков: " + str(cpu.get("Threads", "—")))
        lbl_threads.setToolTip("Логические процессоры. Обычно ≥ ядер (Hyper-Threading)")
        root.addWidget(lbl_threads)

        root.addSpacing(6)
        lbl_load = QLabel("Загрузка CPU (%)")
        lbl_load.setToolTip("Процент использования процессора. Высокая загрузка (>85%) может вызывать тормоза")
        root.addWidget(lbl_load)

        self.series = QLineSeries()
        self.chart = QChart()
        self.chart.legend().hide()
        self.chart.addSeries(self.series)
        self.chart.createDefaultAxes()
        self.chart.axisY().setRange(0,100)
        self.chart.axisX().setTitleText("секунды")
        self.chart.axisY().setTitleText("%")

        view = QChartView(self.chart)
        view.setFixedHeight(420)
        root.addWidget(view)

        root.addSpacing(10)
        box_proc = QGroupBox("Топ процессов")
        box_proc.setToolTip("10 процессов, потребляющих больше всего CPU или RAM. PID — идентификатор процесса")
        lay_proc = QVBoxLayout(box_proc)
        row_btn = QHBoxLayout()
        btn_cpu = QPushButton("По CPU")
        btn_ram = QPushButton("По RAM")
        btn_cpu.clicked.connect(lambda: self._refresh_top("cpu"))
        btn_ram.clicked.connect(lambda: self._refresh_top("memory"))
        row_btn.addWidget(btn_cpu)
        row_btn.addWidget(btn_ram)
        row_btn.addStretch()
        lay_proc.addLayout(row_btn)
        self._proc_list = QListWidget()
        self._proc_list.setMaximumHeight(140)
        lay_proc.addWidget(self._proc_list)
        root.addWidget(box_proc)
        self._refresh_top("cpu")

        self.x = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.tick)
        from config import REFRESH_INTERVAL_MS

        self.timer.start(REFRESH_INTERVAL_MS)

        root.addStretch(1)
    def tick(self):
        y = psutil.cpu_percent()
        self.series.append(self.x, y)
        from config import HISTORY_LENGTH

        if self.series.count() > HISTORY_LENGTH:
            self.series.remove(0)
            self.chart.axisX().setRange(self.x - HISTORY_LENGTH, self.x)
        self.x += 1

    def _refresh_top(self, sort_by: str):
        self._proc_list.clear()
        procs = get_top_processes(sort_by=sort_by, n=10)
        for p in procs:
            name = (p.get("name") or "—")[:40]
            pid = p.get("pid", "—")
            cpu = p.get("cpu") or 0
            mem = p.get("memory") or 0
            if sort_by == "cpu":
                self._proc_list.addItem(f"{name} (PID {pid}) — CPU: {cpu:.1f}%, RAM: {mem:.1f}%")
            else:
                self._proc_list.addItem(f"{name} (PID {pid}) — RAM: {mem:.1f}%, CPU: {cpu:.1f}%")