"""
Монохромные SVG-иконки для навигации (единый цвет и толщина линий).
Рендер в QIcon через QSvgRenderer (PySide6.QtSvg).
"""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap

try:
    from PySide6.QtSvg import QSvgRenderer
except ImportError:  # pragma: no cover
    QSvgRenderer = None  # type: ignore[misc, assignment]

_SVG_DIR = Path(__file__).resolve().parent / "svg"

# Во всех svg/*.svg обводка этого цвета (замена при выделении и т.п.)
SVG_STROKE_DEFAULT = "#1e6dad"

# Кэш QIcon: (файл, размер, цвет обводки) — делегат не перерисовывает SVG каждый кадр
_ICON_CACHE: dict[tuple[str, int, str], QIcon] = {}
_CACHE_MAX = 48

# Имя файла для каждого пункта меню (порядок как в main_window)
NAV_ICON_FILES: tuple[tuple[str, str], ...] = (
    ("Главная", "home.svg"),
    ("Здоровье системы", "activity.svg"),
    ("CPU", "cpu.svg"),
    ("GPU", "gpu.svg"),
    ("Память", "hard-drive.svg"),
    ("Батарея", "battery.svg"),
    ("Сеть", "wifi.svg"),
    ("Периферия", "keyboard.svg"),
    ("Руководство", "book-open.svg"),
    ("Обратная связь", "mail.svg"),
)


def _trim_icon_cache() -> None:
    while len(_ICON_CACHE) > _CACHE_MAX:
        _ICON_CACHE.pop(next(iter(_ICON_CACHE)))


def svg_to_icon(
    filename: str,
    size: int = 24,
    inset_ratio: float = 0.08,
    stroke_color: str | None = None,
) -> QIcon | None:
    """
    Рендер SVG в квадрат size×size (логических пикселей).

    stroke_color — подмена цвета обводки (в файлах используется SVG_STROKE_DEFAULT).

    Важно: не выставлять devicePixelRatio на QPixmap при помещении в QIcon для QListWidget —
    иначе Qt часто масштабирует неверно и виден только «уголок» иконки (обрывки линий).
    """
    stroke_key = stroke_color or SVG_STROKE_DEFAULT
    cache_key = (filename, size, stroke_key)
    if cache_key in _ICON_CACHE:
        return _ICON_CACHE[cache_key]

    if QSvgRenderer is None:
        return None
    path = _SVG_DIR / filename
    if not path.is_file():
        return None
    try:
        xml = path.read_text(encoding="utf-8")
        if stroke_color and stroke_color != SVG_STROKE_DEFAULT:
            xml = xml.replace(SVG_STROKE_DEFAULT, stroke_color)
        renderer = QSvgRenderer(xml.encode("utf-8"))
        if not renderer.isValid():
            return None
        px = max(16, int(size))
        margin = float(px) * inset_ratio
        inner = QRectF(margin, margin, float(px) - 2 * margin, float(px) - 2 * margin)
        pix = QPixmap(px, px)
        pix.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pix)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, True)
        renderer.render(painter, inner)
        painter.end()
        icon = QIcon(pix)
        _ICON_CACHE[cache_key] = icon
        _trim_icon_cache()
        return icon
    except Exception:
        return None


def sidebar_icon(filename: str, size: int, selected: bool) -> QIcon | None:
    """Иконка навигации: обычная или в цвете акцента при выделении."""
    from ui.theme.colors import COLORS

    if selected:
        return svg_to_icon(filename, size, stroke_color=COLORS["accent"])
    return svg_to_icon(filename, size)


def nav_icons(size: int = 24) -> list[tuple[str, QIcon | None]]:
    """Список (подпись, QIcon) для боковой панели."""
    out: list[tuple[str, QIcon | None]] = []
    for label, fname in NAV_ICON_FILES:
        out.append((label, svg_to_icon(fname, size)))
    return out
