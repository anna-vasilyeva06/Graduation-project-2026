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

        self._value_label = QLabel(value)
        self._value_label.setObjectName("metricCardValue")
        self._value_label.setWordWrap(True)
        lay.addWidget(self._value_label)

        self._hint_label: QLabel | None = None
        if subtitle:
            self._hint_label = QLabel(subtitle)
            self._hint_label.setObjectName("metricCardHint")
            self._hint_label.setWordWrap(True)
            lay.addWidget(self._hint_label)

    def set_metric(self, value: str, subtitle: str | None = None) -> None:
        """Обновляет значение; subtitle=None — не трогать подпись; '' — скрыть подпись."""
        self._value_label.setText(value)
        if subtitle is None:
            return
        if subtitle:
            if self._hint_label is None:
                lay = self.layout()
                self._hint_label = QLabel(subtitle)
                self._hint_label.setObjectName("metricCardHint")
                self._hint_label.setWordWrap(True)
                lay.addWidget(self._hint_label)
            self._hint_label.setText(subtitle)
            self._hint_label.setVisible(True)
        elif self._hint_label is not None:
            self._hint_label.setVisible(False)
