from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QPushButton,
    QWidget,
    QFrame,
)

from core.system_health import get_system_health
from ui.pages.base import BasePage
from ui.theme.colors import COLORS


def _status_indicator(color: str, size: int = 10) -> QWidget:
    """Красный/зелёный/жёлтый индикатор-точка."""
    dot = QFrame()
    dot.setFixedSize(size, size)
    dot.setStyleSheet(f"""
        QFrame {{
            background-color: {color};
            border-radius: {size // 2}px;
            border: none;
        }}
    """)
    return dot

# Понятные пользователю формулировки
STATUS_HEADING = {
    "ok": "Всё в порядке",
    "warning": "Есть замечания",
    "error": "Требуется внимание",
}


def _is_valid_value(val: str) -> bool:
    """Проверяет, что value содержит осмысленные данные (например, процент)."""
    if not val or val == "—":
        return False
    return "%" in val or val.replace(".", "").replace(",", "").isdigit()


def _parse_disk_pct(val: str) -> float:
    """Извлекает процент из строки вида '92%' или '85%'."""
    if not val:
        return 0.0
    try:
        return float(str(val).replace("%", "").replace(",", ".").strip())
    except (ValueError, TypeError):
        return 0.0


def _enrich_advice(advice: list, details: list) -> list:
    """Добавляет конкретику в советы: диск, %, и т.д."""
    result = []
    for tip in advice:
        tip_lower = tip.lower()
        # Совет про диск — добавляем диски с проблемой (warning/error) или заполнением >= 80%
        if "диск" in tip_lower:
            relevant_disks = []
            for d in details:
                comp = d.get("component") or ""
                if not comp.startswith("Диск"):
                    continue
                val = d.get("value") or ""
                pct = _parse_disk_pct(val)
                if d.get("status") in ("warning", "error") or pct >= 80:
                    relevant_disks.append(d)
            if relevant_disks:
                parts = [f"{d['component']} ({d['value']})" for d in relevant_disks]
                tip = f"{tip.rstrip('.,')} — {', '.join(parts)}."
            result.append(tip)
        # Совет про CPU — добавляем текущий %
        elif "процессор" in tip_lower or "cpu" in tip_lower:
            cpu_d = next((d for d in details if d.get("component") == "CPU"), None)
            if cpu_d and _is_valid_value(cpu_d.get("value")):
                tip = f"{tip.rstrip('.,')} (сейчас {cpu_d['value']})."
            result.append(tip)
        # Совет про ОЗУ — добавляем %
        elif "озу" in tip_lower or ("память" in tip_lower and "диск" not in tip_lower):
            ram_d = next((d for d in details if "Память" in (d.get("component") or "") and "ОЗУ" in (d.get("component") or "")), None)
            if not ram_d:
                ram_d = next((d for d in details if (d.get("component") or "").startswith("Память")), None)
            if ram_d and _is_valid_value(ram_d.get("value")):
                tip = f"{tip.rstrip('.,')} (сейчас {ram_d['value']})."
            result.append(tip)
        # Совет про батарею — добавляем %
        elif "батаре" in tip_lower or "заряд" in tip_lower:
            bat_d = next((d for d in details if d.get("component") == "Батарея"), None)
            if bat_d and _is_valid_value(bat_d.get("value")):
                tip = f"{tip.rstrip('.,')} (сейчас {bat_d['value']})."
            result.append(tip)
        else:
            result.append(tip)
    return result


class HealthPage(BasePage):
    """Раздел «Здоровье системы»: понятная оценка состояния ПК."""

    def __init__(self):
        super().__init__()

        self._root = QVBoxLayout(self)
        self._root.setAlignment(Qt.AlignTop)
        self._root.setSpacing(12)
        self._root.setContentsMargins(12, 12, 12, 12)

        title = QLabel("Здоровье системы")
        title.setStyleSheet("font-size:18px; font-weight:bold;")
        self._root.addWidget(title)
        self._root.addSpacing(16)

        self._box_health = None
        self._refresh_health_block()

        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_refresh = QPushButton("Обновить")
        btn_refresh.clicked.connect(self._refresh_health_block)
        btn_row.addWidget(btn_refresh)
        self._root.addLayout(btn_row)

        self._root.addStretch(1)

    def _refresh_health_block(self):
        if self._box_health is not None:
            self._box_health.setParent(None)
            self._box_health.deleteLater()
            self._box_health = None

        try:
            health = get_system_health()
            details = health.get("details") or []
            summary = health.get("summary", "")
            ml = health.get("ml")

            # Итоговый статус: по модели, если есть, иначе по правилам
            if ml and ml.get("model_trained") and ml.get("ml_status"):
                status = ml["ml_status"]
            else:
                status = health.get("status", "ok")

            # Рекомендации: из ML-модуля (анализ признаков) или summary
            advice = (ml or {}).get("advice") or []
            if not advice and summary:
                advice = [summary]
            advice = _enrich_advice(advice, details)

            self._box_health = QGroupBox("Состояние компьютера")
            lay = QVBoxLayout(self._box_health)
            lay.setSpacing(12)
            lay.setContentsMargins(4, 8, 4, 4)

            # Главный вердикт — крупно и понятно
            heading = STATUS_HEADING.get(status, status)
            if status == "error":
                style = f"color:{COLORS['error']}; font-size:16px; font-weight:bold;"
            elif status == "warning":
                style = f"color:{COLORS['warning']}; font-size:16px; font-weight:bold;"
            else:
                style = f"color:{COLORS['success']}; font-size:16px; font-weight:bold;"

            row_heading = QHBoxLayout()
            row_heading.setSpacing(8)
            ind_color = COLORS["error"] if status == "error" else (COLORS["warning"] if status == "warning" else COLORS["success"])
            row_heading.addWidget(_status_indicator(ind_color, 12))
            lbl_heading = QLabel(heading)
            lbl_heading.setStyleSheet(style)
            row_heading.addWidget(lbl_heading)
            row_heading.addStretch()
            lay.addLayout(row_heading)

            # Рекомендации (полезные советы на основе анализа)
            if advice:
                advice_label = QLabel("Рекомендации:")
                advice_label.setStyleSheet("font-weight:bold;")
                lay.addWidget(advice_label)
                for tip in advice:
                    lay.addWidget(QLabel("• " + tip))
                lay.addWidget(QLabel(""))

            # Компоненты — простым списком
            comp_label = QLabel("По компонентам:")
            comp_label.setStyleSheet("font-weight:bold;")
            lay.addWidget(comp_label)

            for d in details:
                comp = d.get("component", "—")
                val = d.get("value", "—")
                st = d.get("status", "ok")
                reason = d.get("reason")
                if st == "ok":
                    line = f"{comp}: {val}"
                elif reason:
                    line = f"{comp}: {val} — {reason}"
                else:
                    line = f"{comp}: {val}"
                row = QHBoxLayout()
                row.setSpacing(8)
                ind_color = COLORS["error"] if st == "error" else (COLORS["warning"] if st == "warning" else COLORS["success"])
                row.addWidget(_status_indicator(ind_color))
                lbl = QLabel(line)
                if st == "error":
                    lbl.setStyleSheet(f"color:{COLORS['error']};")
                elif st == "warning":
                    lbl.setStyleSheet(f"color:{COLORS['warning']};")
                row.addWidget(lbl)
                row.addStretch()
                lay.addLayout(row)

            self._root.insertWidget(1, self._box_health)
        except Exception as e:
            self._box_health = QGroupBox("Состояние компьютера")
            self._root.insertWidget(1, self._box_health)
            self._box_health.setLayout(QVBoxLayout())
            self._box_health.layout().addWidget(
                QLabel("Не удалось оценить состояние. Ошибка: " + str(e))
            )
