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
from core.cpu import get_cpu_temperature
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


class CpuPage(BasePage):
    def __init__(self):
        super().__init__()
<<<<<<< Updated upstream
        root = QVBoxLayout(self)
        root.setAlignment(Qt.AlignTop)
        root.setSpacing(6)
        root.setContentsMargins(12, 12, 12, 12)
=======
        root = make_page_root(self, spacing=10)
>>>>>>> Stashed changes

        from core.cpu import get_cpu

        cpu = get_cpu()
<<<<<<< Updated upstream
=======
        add_page_header(root, "CPU", "Модель, ядра, загрузка в реальном времени и топ процессов.")

>>>>>>> Stashed changes
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

        # Текущая частота и температура
        freq = cpu.get("Frequency MHz")
        self._freq_label = QLabel(
            "Частота: " + (f"{freq:.0f} МГц" if isinstance(freq, (int, float)) and freq else "нет данных")
        )
        self._freq_label.setToolTip("Текущая частота процессора (по данным ОС)")
        root.addWidget(self._freq_label)

        temp = get_cpu_temperature()
        self._temp_label = QLabel(
            "Температура: " + (f"{temp:.1f} °C" if temp is not None else "нет данных")
        )
        self._temp_label.setToolTip("Оценка температуры CPU. Может быть недоступна на некоторых системах")
        root.addWidget(self._temp_label)

        root.addSpacing(6)
        lbl_load = QLabel("Загрузка CPU (%)")
        lbl_load.setToolTip("Процент использования процессора. Высокая загрузка (>85%) может вызывать тормоза")
        root.addWidget(lbl_load)

<<<<<<< Updated upstream
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
=======
        perf = build_perf_area_chart_card(height=420)
        self.chart = perf.chart
        self._chart_view = perf.view
        self.line_series = perf.line_series
        self.base_series = perf.base_series
        self.area_series = perf.area_series
        self.x = seed_area_series_baseline(self.line_series, self.base_series, self.chart)
        root.addWidget(perf.card)
>>>>>>> Stashed changes

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

<<<<<<< Updated upstream
=======
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        from config import CHART_REFRESH_BACKGROUND_MS

        self.timer.start(CHART_REFRESH_BACKGROUND_MS)

    def set_monitoring_active(self, active: bool) -> None:
        apply_monitoring_interval(self.timer, active, self.tick)

>>>>>>> Stashed changes
    def tick(self):
        y = psutil.cpu_percent()
        self.series.append(self.x, y)
        # Обновляем частоту и температуру «в реальном времени»
        freq = None
        try:
            f = psutil.cpu_freq()
            freq = f.current if f else None
        except Exception:
            pass
        if freq:
            self._freq_label.setText(f"Частота: {freq:.0f} МГц")

        temp = get_cpu_temperature()
        if temp is not None:
            self._temp_label.setText(f"Температура: {temp:.1f} °C")
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
<<<<<<< Updated upstream
                self._proc_list.addItem(f"{name} (PID {pid}) — RAM: {mem:.1f}%, CPU: {cpu:.1f}%")
=======
                self._proc_list.addItem(
                    f"{name} (PID {pid}) - RAM: {mem:.1f}%, CPU: {cpu:.1f}%"
                )
        fit_list_height(self._proc_list)
>>>>>>> Stashed changes
