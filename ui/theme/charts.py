"""Графики производительности: острые линии (как в диспетчере задач), заливка под кривой, без скругления."""
from __future__ import annotations

from PySide6.QtCharts import QAreaSeries, QChart, QChartView, QLineSeries
from PySide6.QtCore import QMargins, Qt
from PySide6.QtWidgets import QFrame, QGraphicsView
from PySide6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QGradient,
    QLinearGradient,
    QPainter,
    QPen,
)


def update_perf_chart_x_range(chart: QChart, line_series: QLineSeries) -> None:
    """Диапазон оси X по первой и последней точке — иначе при фиксированном (0,1) новые точки невидимы."""
    ax = chart.axisX()
    if ax is None:
        return
    n = line_series.count()
    if n < 1:
        return
    if n == 1:
        x = float(line_series.at(0).x())
        ax.setRange(x - 0.5, x + 0.5)
        return
    x0 = float(line_series.at(0).x())
    x1 = float(line_series.at(n - 1).x())
    if x1 <= x0:
        ax.setRange(x0 - 1.0, x0 + 1.0)
    else:
        ax.setRange(x0, x1)


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
    # Линия графика — контур области (QLineSeries не добавляем на chart, чтобы не дублировать ось Y).
    pen = QPen(line)
    pen.setWidthF(1.5)
    pen.setCosmetic(True)
    pen.setCapStyle(Qt.PenCapStyle.FlatCap)
    pen.setJoinStyle(Qt.PenJoinStyle.MiterJoin)
    area_series.setPen(pen)
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
        # QSS на родителе иногда обрезает отрисовку QGraphicsView / QChartView по высоте.
        view.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, False)
        view.setFrameShape(QFrame.Shape.NoFrame)
        view.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        view.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        view.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)
