from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QTimer


def apply_monitoring_interval(timer: QTimer, active: bool, on_activate: Callable[[], None]) -> None:
    """Частота опроса: выше на активной вкладке, ниже в фоне (таймер не останавливаем)."""
    from config import CHART_REFRESH_BACKGROUND_MS, REFRESH_INTERVAL_MS

    timer.setInterval(REFRESH_INTERVAL_MS if active else CHART_REFRESH_BACKGROUND_MS)
    if active:
        QTimer.singleShot(0, on_activate)

