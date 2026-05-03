from datetime import datetime
import os
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
    QSystemTrayIcon,
    QMenu,
)
from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QColor, QAction, QIcon
import getpass
from typing import Optional

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
from core.system_health import get_system_health


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
        self.setWindowTitle("ITMetric")
        self._app_icon = self._load_app_icon()
        if not self._app_icon.isNull():
            self.setWindowIcon(self._app_icon)
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

        # --- system notifications (tray) ---
        self._tray: Optional[QSystemTrayIcon] = None
        self._tray_menu: Optional[QMenu] = None
        self._tray_act_show: Optional[QAction] = None
        self._tray_act_quit: Optional[QAction] = None
        self._health_watch_timer: Optional[QTimer] = None
        self._last_health_status: str = "ok"
        self._init_tray_and_health_watch()

    def _load_app_icon(self) -> QIcon:
        try:
            base = os.path.dirname(os.path.abspath(__file__))
            ico_path = os.path.join(base, "icons", "icon.ico")
            if os.path.exists(ico_path):
                return QIcon(ico_path)
        except Exception:
            pass
        return QIcon()

    def _init_tray_and_health_watch(self) -> None:
        """В фоне следит за статусом и шлёт уведомления при warning/error."""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return

        qicon = self._app_icon if self._app_icon and not self._app_icon.isNull() else QIcon()
        if qicon.isNull():
            style = QApplication.instance().style() if QApplication.instance() else self.style()
            icon = style.standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)
            qicon = icon if isinstance(icon, QIcon) else QIcon()

        tray = QSystemTrayIcon(qicon, self)
        tray.setToolTip("ITMetric")

        # Важно хранить QMenu/QAction в self, иначе на Windows меню может "исчезать".
        menu = QMenu()
        menu.setObjectName("trayMenu")
        # Тема приложения может задавать глобальный stylesheet для QMenu (тёмный фон + тёмный текст).
        # Для трея принудительно задаём читаемые "системные" цвета через palette(...).
        menu.setStyleSheet(
            """
            QMenu#trayMenu {
                background-color: palette(window);
                color: palette(windowText);
                border: 1px solid palette(mid);
            }
            QMenu#trayMenu::item {
                padding: 6px 22px;
                background-color: transparent;
                color: palette(windowText);
            }
            QMenu#trayMenu::item:selected {
                background-color: palette(highlight);
                color: palette(highlightedText);
            }
            QMenu#trayMenu::separator {
                height: 1px;
                margin: 6px 8px;
                background: palette(mid);
            }
            """
        )
        act_show = QAction("Показать окно", self)
        act_quit = QAction("Выход", self)
        act_show.triggered.connect(self._show_from_tray)
        act_quit.triggered.connect(QApplication.instance().quit)
        menu.addAction(act_show)
        menu.addSeparator()
        menu.addAction(act_quit)

        self._tray_menu = menu
        self._tray_act_show = act_show
        self._tray_act_quit = act_quit

        tray.setContextMenu(self._tray_menu)
        tray.activated.connect(self._on_tray_activated)
        tray.show()

        self._tray = tray

        # Периодический опрос без участия пользователя (не зависит от активной вкладки)
        t = QTimer(self)
        t.setInterval(60_000)  # 60s
        t.timeout.connect(self._poll_health_and_notify)
        t.start()
        self._health_watch_timer = t

        # Стартовый снапшот (без уведомления)
        self._poll_health_and_notify(silent=True)

    def _on_tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason in (
            QSystemTrayIcon.ActivationReason.Trigger,
            QSystemTrayIcon.ActivationReason.DoubleClick,
        ):
            self._show_from_tray()

    def _show_from_tray(self) -> None:
        self.showNormal()
        self.raise_()
        self.activateWindow()

    @staticmethod
    def _severity_rank(status: str) -> int:
        return {"ok": 0, "warning": 1, "error": 2}.get(status or "ok", 0)

    @staticmethod
    def _health_message(health: dict) -> tuple[str, str]:
        """Короткий заголовок + текст для toast/balloon."""
        status = (health or {}).get("status") or "ok"
        heading = {"ok": "Всё в порядке", "warning": "Есть замечания", "error": "Требуется внимание"}.get(
            status, str(status)
        )

        details = (health or {}).get("details") or []
        bad = []
        for d in details:
            st = d.get("status")
            if st in ("warning", "error"):
                comp = d.get("component") or "Компонент"
                val = d.get("value") or "-"
                reason = d.get("reason")
                line = f"{comp}: {val}"
                if reason:
                    line += f" - {reason}"
                bad.append(line)

        if bad:
            text = "\n".join(bad[:4])
            if len(bad) > 4:
                text += "\n…"
        else:
            text = (health or {}).get("summary") or ""
        return heading, text

    def _poll_health_and_notify(self, silent: bool = False) -> None:
        if self._tray is None:
            return
        try:
            health = get_system_health()
        except Exception:
            return

        status = (health or {}).get("status") or "ok"
        prev = self._last_health_status or "ok"
        self._last_health_status = status

        # Уведомляем только при ухудшении или входе в warning/error
        worsened = self._severity_rank(status) > self._severity_rank(prev)
        entered_problem = prev == "ok" and status in ("warning", "error")
        if silent or not (worsened or entered_problem):
            return

        title, msg = self._health_message(health)
        icon = (
            QSystemTrayIcon.MessageIcon.Critical
            if status == "error"
            else QSystemTrayIcon.MessageIcon.Warning
        )
        # timeoutMs: 0 = по умолчанию ОС
        self._tray.showMessage(title, msg, icon, 0)

    def showEvent(self, event):
        super().showEvent(event)
        # Один раз: обход всего дерева виджетов дорогой, не повторять при каждом показе окна
        if not self._selection_fix_done:
            self._selection_fix_done = True
            self._disable_text_selection()

    def closeEvent(self, event):
        # Крестик = сворачиваем в трей, приложение остаётся работать.
        if self._tray is not None and QSystemTrayIcon.isSystemTrayAvailable():
            event.ignore()
            self.hide()
            return
        super().closeEvent(event)

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
            mods = QApplication.keyboardModifiers()
            if mods & Qt.KeyboardModifier.ShiftModifier:
                fn = getattr(self.help_page, "prev_match", None)
                if callable(fn):
                    fn(query)
                    return
            fn = getattr(self.help_page, "next_match", None)
            if callable(fn):
                fn(query)
                return
            fn = getattr(self.help_page, "jump_to_text", None)
            if callable(fn):
                fn(query)

        QTimer.singleShot(300, do_search)
