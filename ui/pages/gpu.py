from PySide6.QtCharts import QAreaSeries, QChart, QChartView, QLineSeries
from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QFrame

import psutil

from ui.pages.base import BasePage
from ui.widgets import PageHeader
from ui.theme.charts import apply_perf_chart_theme


class GpuPage(BasePage):
    def __init__(self):
        super().__init__()
        root = QVBoxLayout(self)
        root.setAlignment(Qt.AlignTop)
        root.setSpacing(10)
        root.setContentsMargins(16, 16, 16, 16)

        root.addWidget(
            PageHeader(
                "GPU",
                "Видеокарта и динамика загрузки (приблизительно на Windows).",
            )
        )

        lbl_gpu = QLabel("<b>Видеокарта</b>")
        lbl_gpu.setToolTip(
            "Графический процессор: модель и текущая загрузка. Важно для игр и тяжёлых приложений"
        )
        root.addWidget(lbl_gpu)

        from core.gpu import get_gpu

        gpus = get_gpu()
        name = gpus[0]["Name"] if gpus else "Не обнаружена"

        root.addWidget(QLabel("Модель: " + name))
        root.addSpacing(6)
        lbl_load = QLabel("Загрузка GPU (%)")
        lbl_load.setToolTip(
            "Процент использования видеокарты. На Windows загрузка GPU определяется приближённо"
        )
        root.addWidget(lbl_load)

        self.line_series = QLineSeries()
        self.base_series = QLineSeries()
        self.area_series = QAreaSeries()
        self.area_series.setUpperSeries(self.line_series)
        self.area_series.setLowerSeries(self.base_series)

        self.chart = QChart()
        self.chart.legend().hide()
        self.chart.addSeries(self.area_series)
        self.chart.addSeries(self.line_series)
        self.chart.createDefaultAxes()
        self.chart.axisY().setRange(0, 100)
        self.chart.axisX().setTitleText("секунды")
        self.chart.axisY().setTitleText("%")

        view = QChartView(self.chart)
        view.setFixedHeight(420)
        apply_perf_chart_theme(self.chart, self.line_series, self.area_series, view)

        chart_card = QFrame()
        chart_card.setObjectName("chartCard")
        wrap = QVBoxLayout(chart_card)
        wrap.setContentsMargins(12, 12, 12, 12)
        wrap.addWidget(view)
        root.addWidget(chart_card)

        self.x = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.tick)
        from config import REFRESH_INTERVAL_MS

        self.timer.start(REFRESH_INTERVAL_MS)

        root.addStretch(1)

    def tick(self):
        y = psutil.cpu_percent() / 2
        self.line_series.append(self.x, y)
        self.base_series.append(self.x, 0.0)
        from config import HISTORY_LENGTH

        if self.line_series.count() > HISTORY_LENGTH:
            self.line_series.remove(0)
            self.base_series.remove(0)
            self.chart.axisX().setRange(self.x - HISTORY_LENGTH, self.x)
        self.x += 1
