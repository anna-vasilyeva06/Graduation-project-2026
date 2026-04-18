import threading

from PySide6.QtCharts import QAreaSeries, QChart, QChartView, QLineSeries
from PySide6.QtCore import QTimer, Qt, Signal
from PySide6.QtWidgets import (
    QLabel,
    QVBoxLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QPushButton,
    QListWidget,
)

from core.gpu_processes import get_top_gpu_vram_rows
from core.processes import get_top_processes
from ui.pages.base import BasePage
from ui.widgets import PageHeader, section_title
from ui.theme.charts import apply_perf_chart_theme, update_perf_chart_x_range


class GpuPage(BasePage):
    """Результат опроса GPU из фона — только через Signal (нельзя QTimer.singleShot из worker-thread)."""
    _gpu_frac_ready = Signal(object)

    def __init__(self):
        super().__init__()
        root = QVBoxLayout(self)
        root.setAlignment(Qt.AlignTop)
        root.setSpacing(10)
        root.setContentsMargins(16, 16, 16, 16)

        root.addWidget(
            PageHeader(
                "GPU",
                "Видеокарта, график загрузки и топ процессов",
            )
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

        root.addSpacing(10)
        box_proc = QGroupBox()
        box_proc.setTitle("")
        box_proc.setToolTip(
            "По памяти GPU - данные nvidia-smi (NVIDIA). Если драйвера нет - топ по системной RAM. "
            "По CPU - как на странице CPU."
        )
        lay_proc = QVBoxLayout(box_proc)
        lay_proc.addWidget(section_title("Топ процессов"))
        row_btn = QHBoxLayout()
        btn_vram = QPushButton("По памяти GPU")
        btn_cpu = QPushButton("По CPU")
        btn_vram.clicked.connect(lambda: self._refresh_top("vram"))
        btn_cpu.clicked.connect(lambda: self._refresh_top("cpu"))
        row_btn.addWidget(btn_vram)
        row_btn.addWidget(btn_cpu)
        row_btn.addStretch()
        lay_proc.addLayout(row_btn)
        self._proc_list = QListWidget()
        self._proc_list.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._proc_list.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self._proc_list.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        lay_proc.addWidget(self._proc_list)
        root.addWidget(box_proc)
        QTimer.singleShot(50, lambda: self._refresh_top("vram"))

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
        """QAreaSeries без ≥2 точек часто не рисуется; базовая линия по оси X."""
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
            self._gpu_model_lbl.setText("Модель: —")

    def set_monitoring_active(self, active: bool) -> None:
        """Частота опроса: выше на вкладке GPU, ниже в фоне (таймер не останавливаем)."""
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
        """Опрос GPU в фоне; результат в GUI только через Signal (очередь в главный поток)."""
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

    def _refresh_top(self, sort_by: str) -> None:
        self._proc_list.clear()
        if sort_by == "cpu":
            for p in get_top_processes(sort_by="cpu", n=10):
                name = (p.get("name") or "-")[:40]
                pid = p.get("pid", "-")
                cpu = p.get("cpu") or 0
                mem = p.get("memory") or 0
                self._proc_list.addItem(
                    f"{name} (PID {pid}) - CPU: {cpu:.1f}%, RAM: {mem:.1f}%"
                )
        else:
            rows, mode = get_top_gpu_vram_rows(n=10)
            if mode == "nvidia_empty":
                self._proc_list.addItem(
                    "Нет процессов с выделенной памятью GPU (NVIDIA)."
                )
            elif mode == "nvidia":
                for p in rows:
                    name = (p.get("name") or "-")[:48]
                    pid = p.get("pid", "-")
                    mib = float(p.get("gpu_mem_mib") or 0)
                    self._proc_list.addItem(
                        f"{name} (PID {pid}) - GPU RAM: {mib:.0f} МиБ"
                    )
            else:
                for p in rows:
                    name = (p.get("name") or "-")[:40]
                    pid = p.get("pid", "-")
                    cpu = p.get("cpu") or 0
                    mem = p.get("memory") or 0
                    self._proc_list.addItem(
                        f"{name} (PID {pid}) - RAM: {mem:.1f}%, CPU: {cpu:.1f}%"
                    )
        self._fit_proc_list_height()

    def _fit_proc_list_height(self) -> None:
        w = self._proc_list
        n = w.count()
        if n == 0:
            w.setFixedHeight(0)
            return
        row_fallback = max(w.fontMetrics().height() + 6, 24)
        h = 0
        for i in range(n):
            rh = w.sizeHintForRow(i)
            h += row_fallback if rh <= 0 else rh
        h += 2 * w.frameWidth() + 4
        w.setFixedHeight(h)
