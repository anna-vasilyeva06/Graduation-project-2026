from datetime import datetime
from PySide6.QtWidgets import (
    QGraphicsDropShadowEffect,
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QListWidget,
    QStackedWidget, QScrollArea, QFrame,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor
import getpass
import re

from ui.pages.home import HomePage
from ui.pages.health import HealthPage
from ui.pages.cpu import CpuPage
from ui.pages.gpu import GpuPage
from ui.pages.memory import MemoryPage
from ui.pages.battery import BatteryPage
from ui.pages.network import NetworkPage
from ui.pages.devices import DevicesPage
from ui.pages.help import HelpPage
from ui.pages.feedback import FeedbackPage


def _get_greeting() -> str:
    """Приветствие в зависимости от времени суток."""
    hour = datetime.now().hour
    if 5 <= hour < 12:
        return "Доброе утро"
    if 12 <= hour < 17:
        return "Добрый день"
    if 17 <= hour < 21:
        return "Добрый вечер"
    return "Доброй ночи"


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("IT Analytics")
        self.resize(980, 600)
        self.setMinimumSize(800, 500)

        # центр экрана
        rect = self.frameGeometry()
        rect.moveCenter(self.screen().availableGeometry().center())
        self.move(rect.topLeft())

        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)
        main = QVBoxLayout(central)
        main.setContentsMargins(8, 8, 8, 8)
        main.setSpacing(6)

        # верхняя панель
        top = QHBoxLayout()
        greeting = _get_greeting()
        user = getpass.getuser()
        self.welcome = QLabel(f"{greeting}, {user}!")
        self.welcome.setObjectName("welcomeLabel")
        self.welcome.setToolTip("Текущий пользователь Windows. Переключение разделов — через левую панель")
        self.search = QLineEdit()
        self.search.setMaximumWidth(260)
        self.search.setPlaceholderText("Поиск...")
        self.search.setToolTip("Поиск по текущей странице. Enter — переход в Руководство и поиск по тексту")
        top.addWidget(self.welcome)
        top.addStretch()
        top.addWidget(self.search)
        main.addLayout(top)

        # тело
        body = QHBoxLayout()
        main.addLayout(body,1)

        self.sidebar = QListWidget()
        self.sidebar.setObjectName("sidebarNav")
        self.sidebar.setFixedWidth(170)
        self.sidebar.addItems(["Главная","Здоровье системы","CPU","GPU","Память","Батарея","Сеть","Периферия","Руководство","Обратная связь"])
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(14)
        shadow.setXOffset(2)
        shadow.setYOffset(2)
        shadow.setColor(QColor(100, 130, 170, 60))
        self.sidebar.setGraphicsEffect(shadow)
        body.addWidget(self.sidebar)

        self.stack = QStackedWidget()
        # pages (content widgets)
        self.pages = [
            HomePage(), HealthPage(), CpuPage(), GpuPage(), MemoryPage(),
            BatteryPage(), NetworkPage(), DevicesPage(),
            HelpPage(), FeedbackPage()
        ]
        self.help_page: HelpPage = self.pages[8]

        self.stack_widgets = []
        for p in self.pages:
            if isinstance(p, HelpPage):
                self.stack.addWidget(p)
                self.stack_widgets.append(p)
                continue

            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.NoFrame)
            scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            scroll.setWidget(p)

            self.stack.addWidget(scroll)
            self.stack_widgets.append(scroll)
        body.addWidget(self.stack,1)

        self.sidebar.currentRowChanged.connect(self.switch_page)
        self.search.textChanged.connect(self.search_text)
        self.search.returnPressed.connect(self._search_enter)

        # popup подсказок (отключен, чтобы не вызывать зависания)
        self._suggest = QListWidget(self)
        self._suggest.setWindowFlags(Qt.Popup)
        self._suggest.hide()

    def showEvent(self, event):
        super().showEvent(event)
        self._disable_text_selection()

    def _disable_text_selection(self):
        """Отключает выделение текста и фон у всех QLabel (в т.ч. заголовках)."""
        for w in self.findChildren(QLabel):
            w.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
            w.setAutoFillBackground(False)

    def switch_page(self, i):
        if 0 <= i < len(self.stack_widgets):
            self.stack.setCurrentIndex(i)

    def search_text(self, t):
        # УБРАНО: автоматические подсказки по руководству (вызывали зависания)
        # Теперь поиск работает только для фильтрации текущей страницы
        self._suggest.hide()

        w = self.stack.currentWidget()
        if isinstance(w, QScrollArea) and w.widget() is not None:
            w = w.widget()

        if t:
            if hasattr(w, "filter"):
                w.filter(t)
        else:
            if hasattr(w, "clear_filter"):
                w.clear_filter()

    def _search_enter(self) -> None:
        # При нажатии Enter переключаемся на руководство и ищем текст
        query = self.search.text().strip()
        if not query:
            return
        
        # Переключаемся на раздел "Руководство" (индекс 8)
        self.sidebar.setCurrentRow(8)
        
        # Даем время на переключение страницы, затем ищем текст
        def do_search():
            if hasattr(self.help_page, "jump_to_text"):
                self.help_page.jump_to_text(query)
        QTimer.singleShot(300, do_search)
