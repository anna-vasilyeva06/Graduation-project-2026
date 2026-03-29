"""Отрисовка пунктов боковой панели: иконка + зазор + текст (без сжатия QIcon из-за DPR)."""
from __future__ import annotations

from PySide6.QtCore import QModelIndex, QRect, QSize, Qt
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPalette
from PySide6.QtWidgets import QApplication, QStyledItemDelegate, QStyle, QStyleOptionViewItem

from ui.theme.colors import COLORS
from ui.icons.loader import sidebar_icon


class SidebarNavDelegate(QStyledItemDelegate):
    """Зазор иконка–текст; выделение — тёмный текст и акцентные SVG (не белый HighlightedText)."""

    ICON_LEFT = 8
    ICON_TEXT_GAP = 12
    TEXT_RIGHT = 8

    def paint(self, painter: QPainter, option, index: QModelIndex) -> None:
        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)
        style = opt.widget.style() if opt.widget else QApplication.style()

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing, True)

        style.drawPrimitive(
            QStyle.PrimitiveElement.PE_PanelItemViewItem, opt, painter, opt.widget
        )

        rect = opt.rect
        text = str(index.data(Qt.ItemDataRole.DisplayRole) or "")
        icon_sz = opt.decorationSize
        if icon_sz.isEmpty():
            icon_sz = QSize(24, 24)

        selected = bool(opt.state & QStyle.StateFlag.State_Selected)
        fname = index.data(Qt.ItemDataRole.UserRole)
        icon: QIcon | None = None
        if isinstance(fname, str) and fname:
            icon = sidebar_icon(fname, icon_sz.width(), selected)
        if icon is None or icon.isNull():
            raw = index.data(Qt.ItemDataRole.DecorationRole)
            icon = raw if isinstance(raw, QIcon) else QIcon()

        ix = rect.left() + self.ICON_LEFT
        iy = rect.top() + (rect.height() - icon_sz.height()) // 2
        icon_rect = QRect(ix, iy, icon_sz.width(), icon_sz.height())

        if not icon.isNull():
            icon.paint(painter, icon_rect, Qt.AlignmentFlag.AlignCenter)

        text_left = icon_rect.right() + self.ICON_TEXT_GAP
        text_rect = QRect(
            text_left,
            rect.top(),
            rect.right() - text_left - self.TEXT_RIGHT,
            rect.height(),
        )
        # Не HighlightedText (белый) — на светлом градиенте нечитаемо; как в QSS — акцент при выборе
        if selected:
            color = QColor(COLORS["accent"])
        else:
            color = opt.palette.color(QPalette.ColorGroup.Active, QPalette.ColorRole.Text)
        painter.setPen(color)
        if selected:
            f = QFont(opt.font)
            f.setWeight(QFont.Weight.DemiBold)
            painter.setFont(f)

        fm = painter.fontMetrics()
        line = fm.elidedText(text, Qt.TextElideMode.ElideRight, text_rect.width())
        painter.drawText(
            text_rect,
            int(Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft),
            line,
        )
        painter.restore()

    def sizeHint(self, option, index: QModelIndex) -> QSize:
        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)
        fm = opt.fontMetrics
        text = str(index.data(Qt.ItemDataRole.DisplayRole) or "")
        iw = opt.decorationSize.width() if not opt.decorationSize.isEmpty() else 24
        ih = opt.decorationSize.height() if not opt.decorationSize.isEmpty() else 24
        tw = fm.horizontalAdvance(text)
        w = self.ICON_LEFT + iw + self.ICON_TEXT_GAP + tw + self.TEXT_RIGHT
        # Высота строки как у «крупных» вкладок раньше
        h = max(ih + 8, fm.height() + 14)
        return QSize(w, h)
