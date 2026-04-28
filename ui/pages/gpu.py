from PySide6.QtCharts import QChart, QChartView, QLineSeries
from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout

import psutil

from core.gpu import get_gpu, get_gpu_stats
from ui.pages.base import BasePage
<<<<<<< Updated upstream
=======
from ui.widgets import (
    add_page_header,
    apply_monitoring_interval,
    build_perf_area_chart_card,
    fit_list_height,
    make_page_root,
    section_title,
    seed_area_series_baseline,
)
from ui.theme.charts import update_perf_chart_x_range
>>>>>>> Stashed changes


class GpuPage(BasePage):
    def __init__(self):
        super().__init__()
<<<<<<< Updated upstream
        root = QVBoxLayout(self)
        root.setAlignment(Qt.AlignTop)
        root.setSpacing(6)
        root.setContentsMargins(12, 12, 12, 12)
=======
        root = make_page_root(self, spacing=10)

        add_page_header(root, "GPU", "Видеокарта, график загрузки и топ процессов")
>>>>>>> Stashed changes

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

<<<<<<< Updated upstream
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
=======
        perf = build_perf_area_chart_card(height=420)
        self.chart = perf.chart
        self._chart_view = perf.view
        self.line_series = perf.line_series
        self.base_series = perf.base_series
        self.area_series = perf.area_series
        self.x = seed_area_series_baseline(self.line_series, self.base_series, self.chart)
        root.addWidget(perf.card)

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

    def _load_gpu_model_name(self) -> None:
        try:
            from core.gpu import get_gpu

            gpus = get_gpu()
            name = gpus[0]["Name"] if gpus else "Не обнаружена"
            self._gpu_model_lbl.setText("Модель: " + str(name))
        except Exception:
            self._gpu_model_lbl.setText("Модель: —")

    def set_monitoring_active(self, active: bool) -> None:
        apply_monitoring_interval(self.timer, active, self.tick)

    def _append_chart_point(self, y: float) -> None:
        self.line_series.append(self.x, y)
        self.base_series.append(self.x, 0.0)
>>>>>>> Stashed changes
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
<<<<<<< Updated upstream
=======
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
        fit_list_height(self._proc_list)
>>>>>>> Stashed changes
