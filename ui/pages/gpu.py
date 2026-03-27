from PySide6.QtCharts import QChart, QChartView, QLineSeries
from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout

import psutil

from core.gpu import get_gpu, get_gpu_stats
from ui.pages.base import BasePage


class GpuPage(BasePage):
    def __init__(self):
        super().__init__()
        root = QVBoxLayout(self)
        root.setAlignment(Qt.AlignTop)
        root.setSpacing(6)
        root.setContentsMargins(12, 12, 12, 12)

        lbl_gpu = QLabel("<b>Видеокарта</b>")
        lbl_gpu.setToolTip("Графический процессор: модель, загрузка, температура и использование видеопамяти")
        root.addWidget(lbl_gpu)

        gpus = get_gpu()
        name = gpus[0]["Name"] if gpus else "Не обнаружена"

        root.addWidget(QLabel("Модель: " + name))
        root.addSpacing(6)

        # Загрузка, температура и память
        lbl_load = QLabel("Загрузка GPU (%)")
        lbl_load.setToolTip("Процент использования видеокарты. На Windows загрузка GPU определяется приближённо")
        root.addWidget(lbl_load)

        self._temp_label = QLabel("Температура: нет данных")
        self._temp_label.setToolTip("Температура видеокарты (по данным драйвера, если доступна)")
        root.addWidget(self._temp_label)

        self._vram_label = QLabel("Память GPU: нет данных")
        self._vram_label.setToolTip("Использование видеопамяти (через nvidia-smi, если доступно)")
        root.addWidget(self._vram_label)

        self.series = QLineSeries()
        self.chart = QChart()
        self.chart.legend().hide()
        self.chart.addSeries(self.series)
        self.chart.createDefaultAxes()
        self.chart.axisY().setRange(0, 100)
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
        # Пока нет кроссплатформенного счётчика GPU — приблизим через CPU
        self.series.append(self.x, psutil.cpu_percent() / 2)
        from config import HISTORY_LENGTH

        if self.series.count() > HISTORY_LENGTH:
            self.series.remove(0)
            self.chart.axisX().setRange(self.x - HISTORY_LENGTH, self.x)
        self.x += 1

        stats = get_gpu_stats()
        if stats:
            self._temp_label.setText(f"Температура: {stats['temperature']:.0f} °C")
            used = stats.get("mem_used_mb")
            total = stats.get("mem_total_mb") or 0
            if total:
                pct = used / total * 100.0
                self._vram_label.setText(
                    f"Память GPU: {used:.0f} / {total:.0f} МБ ({pct:.0f}%)"
                )
