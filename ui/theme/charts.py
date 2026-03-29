"""Графики производительности: острые линии (как в диспетчере задач), заливка под кривой, без скругления."""
from __future__ import annotations

from PySide6.QtCharts import QAreaSeries, QChart, QChartView, QLineSeries
from PySide6.QtCore import QMargins, Qt
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QGradient,
    QLinearGradient,
    QPainter,
    QPen,
)


def apply_perf_chart_theme(
    chart: QChart,
    line_series: QLineSeries,
    area_series: QAreaSeries,
    view: QChartView | None = None,
) -> None:
    """Линия без сглаживания (не spline), плоские стыки — острые пики; заливка снизу."""
    plot_bg = QColor(245, 247, 250)
    plot_edge = QColor(190, 200, 215)
    grid_major = QColor(210, 215, 225)
    grid_minor = QColor(228, 232, 240)
    axis_text = QColor(55, 65, 85)
    line = QColor(0, 120, 212)

    chart.setMargins(QMargins(4, 4, 4, 4))
    chart.setAnimationOptions(QChart.AnimationOption.NoAnimation)

    # Прозрачный фон — видна карточка QFrame#chartCard
    chart.setBackgroundVisible(True)
    chart.setBackgroundBrush(QBrush(QColor(0, 0, 0, 0)))
    chart.setBackgroundRoundness(0)

    chart.setPlotAreaBackgroundVisible(True)
    chart.setPlotAreaBackgroundBrush(QBrush(plot_bg))
    chart.setPlotAreaBackgroundPen(QPen(plot_edge, 1))

    grad = QLinearGradient(0, 0, 0, 1)
    grad.setCoordinateMode(QGradient.CoordinateMode.ObjectBoundingMode)
    grad.setColorAt(0.0, QColor(0, 120, 212, 190))
    grad.setColorAt(0.55, QColor(0, 120, 212, 70))
    grad.setColorAt(1.0, QColor(0, 120, 212, 8))
    area_series.setBrush(QBrush(grad))
    area_series.setPen(QPen(Qt.PenStyle.NoPen))

    pen = QPen(line)
    pen.setWidthF(1.5)
    pen.setCosmetic(True)
    pen.setCapStyle(Qt.PenCapStyle.FlatCap)
    pen.setJoinStyle(Qt.PenJoinStyle.MiterJoin)
    line_series.setPen(pen)

    axis_font = QFont()
    axis_font.setPixelSize(11)
    axis_font.setWeight(QFont.Weight.Medium)

    for ax in chart.axes():
        ax.setLabelsFont(axis_font)
        ax.setTitleBrush(QBrush(axis_text))
        ax.setLabelsBrush(QBrush(axis_text))
        try:
            ax.setGridLinePen(QPen(grid_major, 1))
        except Exception:
            pass
        try:
            ax.setMinorGridLinePen(QPen(grid_minor, 1))
            ax.setMinorGridLineVisible(True)
        except Exception:
            pass
        try:
            ax.setLinePen(QPen(QColor(140, 150, 170), 1))
        except Exception:
            pass

    if view is not None:
        view.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        view.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
