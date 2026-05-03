from __future__ import annotations

from PySide6.QtWidgets import QListWidget


def fit_list_widget_height(w: QListWidget) -> None:
    """Подгоняет высоту QListWidget под содержимое (без внутреннего скролла)."""
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

