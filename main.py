import sys

from PySide6.QtCore import Qt, QTimer, QEvent, QObject
from PySide6.QtWidgets import QApplication, QWidget, QLineEdit, QSpinBox, QLabel, QTextBrowser
from PySide6.QtGui import QFocusEvent
from ui.main_window import MainWindow
from ui.icons import app_icon
from ui.theme import apply_theme


# Отключаем выделение текста в QLabel
_orig_label_init = QLabel.__init__
def _label_init(self, *args, **kwargs):
    _orig_label_init(self, *args, **kwargs)
    self.setTextInteractionFlags(Qt.NoTextInteraction)
    self.setAutoFillBackground(False)
QLabel.__init__ = _label_init


class NoSelectionFilter(QObject):
    """Глобальный фильтр: сбрасывает выделение при любом клике."""
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.MouseButtonPress:
            fw = QApplication.instance().focusWidget()
            QTimer.singleShot(0, lambda: self._clear_selection(fw))
        return False

    def _clear_selection(self, w):
        if not w:
            return
        try:
            if hasattr(w, "deselect"):
                w.deselect()
            elif hasattr(w, "textCursor"):
                tc = w.textCursor()
                tc.clearSelection()
                w.setTextCursor(tc)
        except RuntimeError:
            pass


# Отключаем выделение всего текста при фокусе
def _deselect_on_focus(widget):
    QTimer.singleShot(0, widget.deselect)

_orig_lineedit_focus = QLineEdit.focusInEvent
def _lineedit_focus_in(self, event: QFocusEvent):
    _orig_lineedit_focus(self, event)
    _deselect_on_focus(self)
QLineEdit.focusInEvent = _lineedit_focus_in

_orig_spinbox_focus = QSpinBox.focusInEvent
def _spinbox_focus_in(self, event: QFocusEvent):
    _orig_spinbox_focus(self, event)
    le = self.lineEdit()
    if le:
        QTimer.singleShot(0, le.deselect)
QSpinBox.focusInEvent = _spinbox_focus_in


def _wrap_tooltip(text: str, max_len: int = 55) -> str:
    """Разбивает длинный текст на строки по словам (без HTML)."""
    if not text or not isinstance(text, str):
        return text
    words = text.split()
    lines = []
    current = []
    for w in words:
        test = " ".join(current + [w])
        if len(test) > max_len and current:
            lines.append(" ".join(current))
            current = [w]
        else:
            current.append(w)
    if current:
        lines.append(" ".join(current))
    return "\n".join(lines)


# Патч setToolTip — все подсказки разбиваются на блоки
_orig_set_tooltip = QWidget.setToolTip
QWidget.setToolTip = lambda self, text: _orig_set_tooltip(self, _wrap_tooltip(text) if text else "")

if sys.platform == "win32":
    # Ensures correct taskbar grouping/icon when launched via python.exe.
    try:
        import ctypes  # noqa: PLC0415

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("ITMetric.ITMetric")
    except Exception:
        pass

app = QApplication(sys.argv)
apply_theme(app)
app.setApplicationName("ITMetric")
app.setApplicationDisplayName("ITMetric")
app.setWindowIcon(app_icon())
app.installEventFilter(NoSelectionFilter(app))
win = MainWindow()
win.setWindowIcon(app_icon())
win.show()
sys.exit(app.exec())
