import sys
import os
import ctypes

from PySide6.QtCore import Qt, QTimer, QEvent, QObject
from PySide6.QtWidgets import QApplication, QWidget, QLineEdit, QSpinBox, QLabel, QTextBrowser
from PySide6.QtGui import QFocusEvent, QIcon
from ui.main_window import MainWindow
from ui.theme import apply_theme


_orig_label_init = QLabel.__init__
def _label_init(self, *args, **kwargs):
    _orig_label_init(self, *args, **kwargs)
    self.setTextInteractionFlags(Qt.NoTextInteraction)
    self.setAutoFillBackground(False)
QLabel.__init__ = _label_init


class NoSelectionFilter(QObject):
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


_orig_set_tooltip = QWidget.setToolTip
QWidget.setToolTip = lambda self, text: _orig_set_tooltip(self, _wrap_tooltip(text) if text else "")

app = QApplication(sys.argv)
app.setApplicationName("ITMetric")


try:
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("ITMetric.ITMetric")
except Exception:
    pass
apply_theme(app)
try:
    ico_path = os.path.join(os.path.dirname(__file__), "ui", "icons", "icon.ico")
    if os.path.exists(ico_path):
        app.setWindowIcon(QIcon(ico_path))
except Exception:
    pass
app.installEventFilter(NoSelectionFilter(app))
win = MainWindow()
win.show()
sys.exit(app.exec())
