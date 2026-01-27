from PySide6.QtCharts import QChart, QChartView, QLineSeries
from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout

import psutil

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
        root.addWidget(QLabel("<b>Процессор</b>"))
        root.addWidget(QLabel("Модель: " + str(cpu.get("Model", "—"))))
        root.addWidget(QLabel("Ядер: " + str(cpu.get("Cores", "—"))))
        root.addWidget(QLabel("Потоков: " + str(cpu.get("Threads", "—"))))

        root.addSpacing(6)
        root.addWidget(QLabel("Загрузка CPU (%)"))

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