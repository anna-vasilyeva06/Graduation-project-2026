from PySide6.QtCharts import QAreaSeries, QChart, QChartView, QLineSeries
from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import (
    QLabel,
    QVBoxLayout,
    QGroupBox,
    QHBoxLayout,
    QPushButton,
    QListWidget,
    QFrame,
)

import psutil

from core.processes import get_top_processes
from ui.pages.base import BasePage
from ui.widgets import PageHeader, section_title
from ui.theme.charts import apply_perf_chart_theme, update_perf_chart_x_range


class CpuPage(BasePage):
    def __init__(self):
        super().__init__()
        root = QVBoxLayout(self)
        root.setAlignment(Qt.AlignTop)
        root.setSpacing(10)
        root.setContentsMargins(16, 16, 16, 16)

        from core.cpu import get_cpu

        cpu = get_cpu()
        root.addWidget(
            PageHeader(
                "CPU",
                "Модель, ядра, загрузка в реальном времени и топ процессов.",
            )
        )

        lbl_cpu = QLabel("<b>Процессор</b>")
        lbl_cpu.setToolTip(
            "Центральный процессор: модель, ядра, потоки и текущая загрузка в реальном времени"
        )
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
        lbl_load.setToolTip(
            "Процент использования процессора. Высокая загрузка (>85%) может вызывать зависание"
        )
        root.addWidget(lbl_load)

        self.line_series = QLineSeries()
        self.base_series = QLineSeries()
        self.area_series = QAreaSeries()
        self.area_series.setUpperSeries(self.line_series)
        self.area_series.setLowerSeries(self.base_series)

        self.chart = QChart()
        self.chart.legend().hide()
        # Только QAreaSeries: дублирующая QLineSeries на том же графике ломала масштаб оси Y (обрезка сверху).
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
            "10 процессов, потребляющих больше всего CPU или RAM. PID - идентификатор процесса"
        )
        lay_proc = QVBoxLayout(box_proc)
        lay_proc.addWidget(section_title("Топ процессов"))
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
        self._proc_list.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._proc_list.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self._proc_list.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        lay_proc.addWidget(self._proc_list)
        root.addWidget(box_proc)
        self._refresh_top("cpu")

        root.addStretch(1)

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

    def set_monitoring_active(self, active: bool) -> None:
        """Частота опроса: выше на вкладке CPU, ниже в фоне (таймер не останавливаем)."""
        from config import CHART_REFRESH_BACKGROUND_MS, REFRESH_INTERVAL_MS

        self.timer.setInterval(
            REFRESH_INTERVAL_MS if active else CHART_REFRESH_BACKGROUND_MS
        )
        if active:
            QTimer.singleShot(0, self.tick)

    def tick(self):
        y = psutil.cpu_percent(interval=None)
        self.line_series.append(self.x, y)
        self.base_series.append(self.x, 0.0)
        from config import HISTORY_LENGTH

        if self.line_series.count() > HISTORY_LENGTH:
            self.line_series.remove(0)
            self.base_series.remove(0)
        self.x += 1
        update_perf_chart_x_range(self.chart, self.line_series)
        self._chart_view.viewport().update()

    def _refresh_top(self, sort_by: str):
        self._proc_list.clear()
        procs = get_top_processes(sort_by=sort_by, n=10)
        for p in procs:
            name = (p.get("name") or "-")[:40]
            pid = p.get("pid", "-")
            cpu = p.get("cpu") or 0
            mem = p.get("memory") or 0
            if sort_by == "cpu":
                self._proc_list.addItem(
                    f"{name} (PID {pid}) - CPU: {cpu:.1f}%, RAM: {mem:.1f}%"
                )
            else:
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
