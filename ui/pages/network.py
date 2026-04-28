from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QLabel,
    QGroupBox,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QSpinBox,
    QPushButton,
)

import psutil
import time

from core.network import get_network_info, ping_host, check_port
from ui.pages.base import BasePage
from ui.theme.colors import COLORS
<<<<<<< Updated upstream
=======
from ui.widgets import add_page_header, make_page_root, section_title
>>>>>>> Stashed changes


class NetworkPage(BasePage):
    def __init__(self):
        super().__init__()

<<<<<<< Updated upstream
        root = QVBoxLayout(self)
        root.setAlignment(Qt.AlignTop)
        root.setSpacing(12)
        root.setContentsMargins(12, 12, 12, 12)

        title = QLabel("Сеть")
        title.setStyleSheet("font-size:18px; font-weight:bold;")
        title.setToolTip("Активные сетевые подключения, IP-адреса, скорость интерфейсов и проверка доступности хостов")
        root.addWidget(title)
        root.addSpacing(16)
=======
        root = make_page_root(self, spacing=14)
        add_page_header(root, "Сеть", "Интерфейсы, адреса, скорость и проверка ping / порта.")
>>>>>>> Stashed changes

        # Активные интерфейсы
        interfaces_label = QLabel("Активные подключения")
        interfaces_label.setToolTip("Сетевые интерфейсы (Wi‑Fi, Ethernet и др.) с их параметрами и статусом")
        interfaces_label.setStyleSheet("font-weight:bold; margin-top:12px; margin-bottom:4px;")
        root.addWidget(interfaces_label)

        try:
            infos = get_network_info()
        except Exception:
            infos = []

        if not infos:
            root.addWidget(QLabel("Нет активных сетевых подключений"))
        else:
            for iface in infos:
                box = QGroupBox(iface.get("name", "—"))
                box.setStyleSheet(
                    "QGroupBox { padding-top: 22px; } "
                    "QGroupBox::title { subcontrol-origin: margin; left: 12px; top: 4px; padding: 4px 10px; }"
                )
                layout = QVBoxLayout(box)
                layout.setSpacing(8)

                # Тип и статус
                conn_type = iface.get("type", "—")
                layout.addWidget(QLabel(f"Тип: {conn_type}"))
                layout.addWidget(QLabel("Статус: подключено"))

                # IPv4
                ipv4 = iface.get("ipv4") or []
                if ipv4:
                    l = QLabel(f"IPv4: {', '.join(ipv4)}")
                    l.setToolTip("Адрес устройства в локальной сети (формат x.x.x.x)")
                    layout.addWidget(l)

                # IPv6 (если есть)
                ipv6 = iface.get("ipv6") or []
                if ipv6:
                    ipv6_show = ipv6[:2]
                    l = QLabel(f"IPv6: {', '.join(ipv6_show)}")
                    l.setToolTip("Адрес нового поколения (формат с двоеточиями)")
                    layout.addWidget(l)

                # MAC
                mac = iface.get("mac") or ""
                if mac:
                    l = QLabel(f"MAC: {mac}")
                    l.setToolTip("Уникальный идентификатор сетевого адаптера")
                    layout.addWidget(l)

                # Скорость и MTU
                speed = iface.get("speed", "—")
                mtu = iface.get("mtu", "—")
                l_speed = QLabel(f"Скорость: {speed}")
                l_speed.setToolTip("Максимальная пропускная способность интерфейса (Мбит/с)")
                layout.addWidget(l_speed)
                l_mtu = QLabel(f"MTU: {mtu}")
                l_mtu.setToolTip("Максимальный размер пакета данных в байтах")
                layout.addWidget(l_mtu)

                root.addWidget(box)

        # --- Продвинутые: проверка доступности ---
        adv_label = QLabel("Проверка доступности (для продвинутых пользователей)")
        adv_label.setStyleSheet("font-weight:bold; margin-top:20px; margin-bottom:8px;")
        adv_label.setToolTip("Ping — проверка доступности по сети. Порт — проверка, открыт ли указанный TCP-порт")
        root.addWidget(adv_label)

        adv_box = QGroupBox("Проверка хоста или узла")
        adv_box.setToolTip("Укажите IP или домен для проверки доступности (ping) или проверки открытого TCP-порта")
        adv_lay = QVBoxLayout(adv_box)
        adv_lay.setSpacing(8)

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Хост:"))
        self._host_input = QLineEdit()
        self._host_input.setPlaceholderText("google.com или 8.8.8.8")
        self._host_input.setMinimumWidth(200)
        row1.addWidget(self._host_input)
        row1.addWidget(QLabel("Порт:"))
        self._port_input = QSpinBox()
        self._port_input.setRange(1, 65535)
        self._port_input.setValue(80)
        row1.addWidget(self._port_input)
        row1.addStretch()
        adv_lay.addLayout(row1)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        btn_ping = QPushButton("Ping")
        btn_ping.clicked.connect(self._do_ping)
        btn_port = QPushButton("Проверить порт")
        btn_port.clicked.connect(self._do_port)
        btn_row.addWidget(btn_ping)
        btn_row.addWidget(btn_port)
        btn_row.addStretch()
        adv_lay.addLayout(btn_row)

        self._result_label = QLabel("")
        self._result_label.setWordWrap(True)
        self._result_label.setStyleSheet(f"color:{COLORS['text']}; margin-top:4px;")
        adv_lay.addWidget(self._result_label)

        root.addWidget(adv_box)

        root.addSpacing(10)

        # Текущая скорость (суммарно по всем интерфейсам)
        self._speed_label = QLabel("Текущая скорость: —")
        self._speed_label.setToolTip("Оценка суммарной скорости входящего и исходящего трафика по всем интерфейсам")
        root.addWidget(self._speed_label)

        root.addStretch()

        # Исходные значения счётчиков для вычисления скорости
        try:
            self._prev_counters = psutil.net_io_counters()
        except Exception:
            self._prev_counters = None
        self._prev_time = time.time()

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_speed)
        self._timer.start(1000)

    def _do_ping(self):
        host = self._host_input.text().strip()
        ok, msg = ping_host(host)
        if ok:
            self._result_label.setText(f"{msg}")
            self._result_label.setStyleSheet(f"color:{COLORS['success']}; margin-top:4px;")
        else:
            self._result_label.setText(f"{msg}")
            self._result_label.setStyleSheet(f"color:{COLORS['error']}; margin-top:4px;")

    def _do_port(self):
        host = self._host_input.text().strip()
        port = self._port_input.value()
        ok, msg = check_port(host, port)
        if ok:
            self._result_label.setText(f"✓ {msg}")
            self._result_label.setStyleSheet(f"color:{COLORS['success']}; margin-top:4px;")
        else:
            self._result_label.setText(f"✗ {msg}")
            self._result_label.setStyleSheet(f"color:{COLORS['error']}; margin-top:4px;")

    def _update_speed(self):
        """Обновляет текст с примерной текущей скоростью сети (Мбит/с)."""
        if self._prev_counters is None:
            try:
                self._prev_counters = psutil.net_io_counters()
            except Exception:
                return
            self._prev_time = time.time()
            return

        try:
            cur = psutil.net_io_counters()
        except Exception:
            return

        now = time.time()
        dt = now - self._prev_time
        if dt <= 0:
            return

        d_recv = max(0, cur.bytes_recv - self._prev_counters.bytes_recv)
        d_sent = max(0, cur.bytes_sent - self._prev_counters.bytes_sent)

        total_bits = (d_recv + d_sent) * 8.0
        mbit_per_s = total_bits / dt / 1e6

        self._speed_label.setText(f"Текущая скорость: {mbit_per_s:.2f} Мбит/с (вх+исх)")

        self._prev_counters = cur
        self._prev_time = now

