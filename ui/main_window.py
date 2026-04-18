from datetime import datetime
from PySide6.QtWidgets import (
    QGraphicsDropShadowEffect,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QStackedWidget,
    QScrollArea,
    QFrame,
    QStyle,
    QApplication,
)
from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QColor
import getpass

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
from ui.icons.loader import NAV_ICON_FILES, nav_icons
from ui.widgets.sidebar_delegate import SidebarNavDelegate


def _get_greeting() -> str:
    hour = datetime.now().hour
    if 5 <= hour < 12:
        return "Доброе утро"
    if 12 <= hour < 17:
        return "Добрый день"
    if 17 <= hour < 21:
        return "Добрый вечер"
    return "Доброй ночи"


def _nav_icon_entries():
    SP = QStyle.StandardPixmap
    battery = SP.SP_BatteryIcon if hasattr(SP, "SP_BatteryIcon") else SP.SP_MediaVolume
    return [
        ("Главная", SP.SP_DirHomeIcon),
        ("Здоровье системы", SP.SP_MessageBoxInformation),
        ("CPU", SP.SP_ComputerIcon),
        ("GPU", SP.SP_DesktopIcon),
        ("Память", SP.SP_DriveHDIcon),
        ("Батарея", battery),
        ("Сеть", SP.SP_DriveNetIcon),
        ("Периферия", SP.SP_FileDialogListView),
        ("Руководство", SP.SP_DialogHelpButton),
        ("Обратная связь", SP.SP_MessageBoxQuestion),
    ]


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("IT Analytics")
        self.resize(1020, 640)
        self.setMinimumSize(820, 520)

        rect = self.frameGeometry()
        rect.moveCenter(self.screen().availableGeometry().center())
        self.move(rect.topLeft())

        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)
        main = QVBoxLayout(central)
        main.setContentsMargins(12, 12, 12, 12)
        main.setSpacing(10)

        top_frame = QFrame()
        top_frame.setObjectName("topBar")
        top_frame.setFrameShape(QFrame.Shape.NoFrame)
        top = QHBoxLayout(top_frame)
        top.setContentsMargins(16, 12, 16, 12)
        top.setSpacing(12)

        greeting = _get_greeting()
        user = getpass.getuser()
        self.welcome = QLabel(f"{greeting}, {user}!")
        self.welcome.setObjectName("welcomeLabel")
        self.welcome.setToolTip(
            "Текущий пользователь Windows. Переключение разделов - через левую панель"
        )
        self.search = QLineEdit()
        self.search.setMaximumWidth(280)
        self.search.setPlaceholderText("Поиск")
        self.search.setToolTip(
            "Поиск. Enter - переход в Руководство и поиск по тексту"
        )
        top.addWidget(self.welcome)
        top.addStretch()
        top.addWidget(self.search)
        main.addWidget(top_frame)

        body = QHBoxLayout()
        main.addLayout(body, 1)

        self.sidebar = QListWidget()
        self.sidebar.setObjectName("sidebarNav")
        self.sidebar.setItemDelegate(SidebarNavDelegate(self.sidebar))
        # Размер иконок = nav_icons(); делегат рисует иконку+текст с зазором (обход бага QIcon+DPR)
        _nav_icon_px = 26
        self.sidebar.setFixedWidth(240)
        self.sidebar.setIconSize(QSize(_nav_icon_px, _nav_icon_px))
        self.sidebar.setSpacing(0)

        style = QApplication.instance().style() if QApplication.instance() else self.style()
        svg_nav = nav_icons(_nav_icon_px)
        fallback = _nav_icon_entries()
        for i, (label, icon) in enumerate(svg_nav):
            if icon is None and i < len(fallback):
                icon = style.standardIcon(fallback[i][1])
            if icon is None:
                icon = style.standardIcon(QStyle.StandardPixmap.SP_FileIcon)
            item = QListWidgetItem(icon, label)
            if i < len(NAV_ICON_FILES):
                item.setData(Qt.ItemDataRole.UserRole, NAV_ICON_FILES[i][1])
            self.sidebar.addItem(item)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(18)
        shadow.setXOffset(0)
        shadow.setYOffset(4)
        shadow.setColor(QColor(60, 100, 150, 45))
        self.sidebar.setGraphicsEffect(shadow)
        body.addWidget(self.sidebar)

        self.stack = QStackedWidget()
        self.pages = [
            HomePage(),
            HealthPage(),
            CpuPage(),
            GpuPage(),
            MemoryPage(),
            BatteryPage(),
            NetworkPage(),
            DevicesPage(),
            HelpPage(),
            FeedbackPage(),
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
        body.addWidget(self.stack, 1)

        self.stack.currentChanged.connect(self._sync_chart_page_monitors)

        self.sidebar.currentRowChanged.connect(self.switch_page)
        if self.sidebar.count() > 0:
            self.sidebar.setCurrentRow(0)
            self.switch_page(0)
        self.search.textChanged.connect(self.search_text)
        self.search.returnPressed.connect(self._search_enter)

        self._suggest = QListWidget(self)
        self._suggest.setWindowFlags(Qt.Popup)
        self._suggest.hide()
        self._selection_fix_done = False

    def showEvent(self, event):
        super().showEvent(event)
        # Один раз: обход всего дерева виджетов дорогой, не повторять при каждом показе окна
        if not self._selection_fix_done:
            self._selection_fix_done = True
            self._disable_text_selection()

    def _disable_text_selection(self):
        for w in self.findChildren(QLabel):
            w.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
            w.setAutoFillBackground(False)

    def _sync_chart_page_monitors(self, stack_index: int) -> None:
        """CPU/GPU: интервал опроса выше на активной вкладке, в фоне реже (графики всегда копятся)."""
        for i, page in enumerate(self.pages):
            fn = getattr(page, "set_monitoring_active", None)
            if callable(fn):
                fn(i == stack_index)

    def switch_page(self, i):
        if 0 <= i < len(self.stack_widgets):
            self.stack.setCurrentIndex(i)
            # currentChanged не срабатывает, если индекс не изменился — синхронизируем таймеры всегда
            self._sync_chart_page_monitors(i)

    def search_text(self, t):
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
        query = self.search.text().strip()
        if not query:
            return

        self.sidebar.setCurrentRow(8)

        def do_search():
            if hasattr(self.help_page, "jump_to_text"):
                self.help_page.jump_to_text(query)

        QTimer.singleShot(300, do_search)
