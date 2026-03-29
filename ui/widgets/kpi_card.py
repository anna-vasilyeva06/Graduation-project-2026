from __future__ import annotations

from PySide6.QtWidgets import QFrame, QLabel, QVBoxLayout


class KpiCard(QFrame):
    """Карточка метрики: подпись, крупное значение, необязательная строка."""

    def __init__(
        self,
        title: str,
        value: str,
        subtitle: str = "",
        parent=None,
    ):
        super().__init__(parent)
        self.setObjectName("metricCard")

        lay = QVBoxLayout(self)
        lay.setContentsMargins(18, 16, 18, 16)
        lay.setSpacing(6)

        tl = QLabel(title)
        tl.setObjectName("metricCardTitle")
        lay.addWidget(tl)

        vl = QLabel(value)
        vl.setObjectName("metricCardValue")
        vl.setWordWrap(True)
        lay.addWidget(vl)

        if subtitle:
            sl = QLabel(subtitle)
            sl.setObjectName("metricCardHint")
            sl.setWordWrap(True)
            lay.addWidget(sl)
