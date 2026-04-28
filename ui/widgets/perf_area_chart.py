from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCharts import QAreaSeries, QChart, QChartView, QLineSeries
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QVBoxLayout

from ui.theme.charts import apply_perf_chart_theme


@dataclass(frozen=True)
class PerfAreaChart:
    card: QFrame
    chart: QChart
    view: QChartView
    line_series: QLineSeries
    base_series: QLineSeries
    area_series: QAreaSeries


def seed_area_series_baseline(line_series: QLineSeries, base_series: QLineSeries, chart: QChart) -> int:
    """QAreaSeries без ≥2 точек часто не рисуется; базовая линия по оси X."""
    for bx in (0, 1):
        line_series.append(bx, 0.0)
        base_series.append(bx, 0.0)
    ax = chart.axisX()
    if ax is not None:
        ax.setRange(0, 1)
    return 2


def build_perf_area_chart_card(*, height: int = 420) -> PerfAreaChart:
    line_series = QLineSeries()
    base_series = QLineSeries()
    area_series = QAreaSeries()
    area_series.setUpperSeries(line_series)
    area_series.setLowerSeries(base_series)

    chart = QChart()
    chart.legend().hide()
    # Добавляем только QAreaSeries, линия рисуется как контур области (см. apply_perf_chart_theme()).
    chart.addSeries(area_series)
    chart.createDefaultAxes()
    for ax in chart.axes(Qt.Orientation.Vertical):
        ax.setRange(0, 100)
    if chart.axisX() is not None:
        chart.axisX().setTitleText("секунды")
    if chart.axisY() is not None:
        chart.axisY().setTitleText("%")

    view = QChartView(chart)
    view.setFixedHeight(int(height))
    apply_perf_chart_theme(chart, line_series, area_series, view)

    card = QFrame()
    card.setObjectName("chartCard")
    wrap = QVBoxLayout(card)
    wrap.setContentsMargins(12, 12, 12, 12)
    wrap.addWidget(view)

    return PerfAreaChart(
        card=card,
        chart=chart,
        view=view,
        line_series=line_series,
        base_series=base_series,
        area_series=area_series,
    )

