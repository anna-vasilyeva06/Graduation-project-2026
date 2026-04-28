from __future__ import annotations

from PySide6.QtWidgets import QFrame


def status_dot(color: str, size: int = 10) -> QFrame:
    """Красный/зелёный/жёлтый индикатор-точка."""
    dot = QFrame()
    dot.setFixedSize(int(size), int(size))
    dot.setStyleSheet(
        f"QFrame {{ background-color: {color}; border-radius: {int(size) // 2}px; border: none; }}"
    )
    return dot

