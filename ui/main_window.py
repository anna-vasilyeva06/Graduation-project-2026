from PySide6.QtWidgets import *
from PySide6.QtCore import Qt
import getpass

from ui.pages.home import HomePage
from ui.pages.cpu import CpuPage
from ui.pages.gpu import GpuPage
from ui.pages.memory import MemoryPage
from ui.pages.battery import BatteryPage
from ui.pages.network import NetworkPage
from ui.pages.devices import DevicesPage
from ui.pages.help import HelpPage
from ui.pages.feedback import FeedbackPage


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("IT Analytics")
        self.setFixedSize(980, 600)

        # центр экрана
        rect = self.frameGeometry()
        rect.moveCenter(self.screen().availableGeometry().center())
        self.move(rect.topLeft())

        central = QWidget()
        self.setCentralWidget(central)
        main = QVBoxLayout(central)
        main.setContentsMargins(8,8,8,8)
        main.setSpacing(6)

        # верхняя панель
        top = QHBoxLayout()
        self.welcome = QLabel(f"Здравствуйте, {getpass.getuser()}!")
        self.search = QLineEdit()
        self.search.setMaximumWidth(260)
        self.search.setPlaceholderText("Поиск...")
        top.addWidget(self.welcome)
        top.addStretch()
        top.addWidget(self.search)
        main.addLayout(top)

        # тело
        body = QHBoxLayout()
        main.addLayout(body,1)

        self.sidebar = QListWidget()
        self.sidebar.setFixedWidth(170)
        self.sidebar.addItems(["Главная","CPU","GPU","Память","Батарея","Сеть","Периферия","Руководство","Обратная связь"])
        body.addWidget(self.sidebar)

        self.stack = QStackedWidget()
        # pages (content widgets)
        self.pages = [
            HomePage(), CpuPage(), GpuPage(), MemoryPage(),
            BatteryPage(), NetworkPage(), DevicesPage(),
            HelpPage(), FeedbackPage()
        ]

        self.stack_widgets = []
        for p in self.pages:
            if isinstance(p, HelpPage):
                self.stack.addWidget(p)
                self.stack_widgets.append(p)
                continue

            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setFrameShape(QFrame.NoFrame)
            scroll.setWidget(p)

            self.stack.addWidget(scroll)
            self.stack_widgets.append(scroll)
        body.addWidget(self.stack,1)

        self.sidebar.currentRowChanged.connect(self.switch_page)
        self.search.textChanged.connect(self.search_text)

    def switch_page(self, i):
        if 0 <= i < len(self.stack_widgets):
            self.stack.setCurrentIndex(i)

    def search_text(self, t):
        w = self.stack.currentWidget()
        if isinstance(w, QScrollArea) and w.widget() is not None:
            w = w.widget()

        if t:
            if hasattr(w, "filter"):
                w.filter(t)
        else:
            if hasattr(w, "clear_filter"):
                w.clear_filter()
