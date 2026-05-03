import threading

from PySide6.QtCharts import QAreaSeries, QChart, QChartView, QLineSeries
from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtWidgets import (
    QLabel,
    QVBoxLayout,
    QFrame,
)

from ui.pages.base import BasePage
from ui.theme.charts import apply_perf_chart_theme, update_perf_chart_x_range


class GpuPage(BasePage):
    _gpu_frac_ready = Signal(object)

    def __init__(self):
        super().__init__()
        root = self.build_root(
            "GPU",
            "Видеокарта и график загрузки GPU",
            spacing=10,
        )

        lbl_gpu = QLabel("<b>Видеокарта</b>")
        lbl_gpu.setToolTip(
            "Графический процессор: модель и текущая загрузка. Важно для игр и тяжёлых приложений"
        )
        root.addWidget(lbl_gpu)

        self._gpu_model_lbl = QLabel("Модель: …")
        root.addWidget(self._gpu_model_lbl)
        QTimer.singleShot(0, self._load_gpu_model_name)
        root.addSpacing(6)
        lbl_load = QLabel("Загрузка GPU (%)")
        lbl_load.setToolTip(
            "Процент использования видеокарты."
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
        self.chart.createDefaultAxes()
        for ax in self.chart.axes(Qt.Orientation.Vertical):
            ax.setRange(0, 100)
        self.chart.axisX().setTitleText("секунды")
        self.chart.axisY().setTitleText("%")

        view = QChartView(self.chart)
        view.setFixedHeight(420)
        apply_perf_chart_theme(self.chart, self.line_series, self.area_series, view)

        self._chart_view = view
        self._seed_chart_baseline()

        chart_card = QFrame()
        chart_card.setObjectName("chartCard")
        wrap = QVBoxLayout(chart_card)
        wrap.setContentsMargins(12, 12, 12, 12)
        wrap.addWidget(view)
        root.addWidget(chart_card)

        root.addStretch(1)

        self._last_gpu_pct = 0.0
        self._gpu_sample_lock = threading.Lock()
        self._gpu_sample_inflight = False
        self._gpu_frac_ready.connect(self._on_gpu_frac_ready)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        from config import CHART_REFRESH_BACKGROUND_MS

        self.timer.start(CHART_REFRESH_BACKGROUND_MS)

    def _seed_chart_baseline(self) -> None:
        for bx in (0, 1):
            self.line_series.append(bx, 0.0)
            self.base_series.append(bx, 0.0)
        self.x = 2
        self.chart.axisX().setRange(0, 1)

    def _load_gpu_model_name(self) -> None:
        try:
            from core.gpu import get_gpu

            gpus = get_gpu()
            name = gpus[0]["Name"] if gpus else "Не обнаружена"
            self._gpu_model_lbl.setText("Модель: " + str(name))
        except Exception:
            self._gpu_model_lbl.setText("Модель: -")

    def set_monitoring_active(self, active: bool) -> None:
        from config import CHART_REFRESH_BACKGROUND_MS, REFRESH_INTERVAL_MS

        self.timer.setInterval(
            REFRESH_INTERVAL_MS if active else CHART_REFRESH_BACKGROUND_MS
        )
        if active:
            QTimer.singleShot(0, self.tick)

    def _append_chart_point(self, y: float) -> None:
        self.line_series.append(self.x, y)
        self.base_series.append(self.x, 0.0)
        from config import HISTORY_LENGTH

        if self.line_series.count() > HISTORY_LENGTH:
            self.line_series.remove(0)
            self.base_series.remove(0)
        self.x += 1
        update_perf_chart_x_range(self.chart, self.line_series)
        self._chart_view.viewport().update()

    def _on_gpu_frac_ready(self, frac: object) -> None:
        try:
            if frac is not None:
                self._last_gpu_pct = max(0.0, min(100.0, float(frac) * 100.0))
            self._append_chart_point(self._last_gpu_pct)
        finally:
            with self._gpu_sample_lock:
                self._gpu_sample_inflight = False

    def tick(self) -> None:
        with self._gpu_sample_lock:
            if self._gpu_sample_inflight:
                self._append_chart_point(self._last_gpu_pct)
                return
            self._gpu_sample_inflight = True

        def work() -> None:
            frac = None
            try:
                from core.ml_health import sample_gpu_util_fraction

                frac = sample_gpu_util_fraction(2.0)
            except Exception:
                pass
            self._gpu_frac_ready.emit(frac)

        threading.Thread(target=work, daemon=True).start()
