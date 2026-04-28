from __future__ import annotations

from PySide6.QtWidgets import QListWidget


def fit_list_height(w: QListWidget, *, min_row_px: int = 24, extra_px: int = 4) -> None:
    n = w.count()
    if n == 0:
        w.setFixedHeight(0)
        return

    row_fallback = max(w.fontMetrics().height() + 6, int(min_row_px))
    h = 0
    for i in range(n):
        rh = w.sizeHintForRow(i)
        h += row_fallback if rh <= 0 else rh
    h += 2 * w.frameWidth() + int(extra_px)
    w.setFixedHeight(h)

