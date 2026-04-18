from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QLabel,
    QGroupBox,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QSpinBox,
    QPushButton,
)

from core.network import get_network_info, ping_host, check_port
from ui.pages.base import BasePage
from ui.theme.colors import COLORS
from ui.widgets import PageHeader, section_title


class NetworkPage(BasePage):
    def __init__(self):
        super().__init__()

        root = QVBoxLayout(self)
        root.setAlignment(Qt.AlignTop)
        root.setSpacing(14)
        root.setContentsMargins(16, 16, 16, 16)

        root.addWidget(
            PageHeader(
                "Сеть",
                "Интерфейсы, адреса, скорость и проверка ping / порта.",
            )
        )

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
                box = QGroupBox()
                box.setTitle("")
                layout = QVBoxLayout(box)
                layout.addWidget(section_title(iface.get("name", "-")))
                layout.setSpacing(8)

                # Тип и статус
                conn_type = iface.get("type", "-")
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
        adv_label = QLabel("Проверка доступности")
        adv_label.setStyleSheet("font-weight:bold; margin-top:20px; margin-bottom:8px;")
        adv_label.setToolTip("Ping - проверка доступности по сети. Порт - проверка, открыт ли указанный TCP-порт")
        root.addWidget(adv_label)

        adv_box = QGroupBox()
        adv_box.setTitle("")
        adv_box.setToolTip("Укажите IP или домен для проверки доступности (ping) или проверки открытого TCP-порта")
        adv_lay = QVBoxLayout(adv_box)
        adv_lay.addWidget(section_title("Проверка хоста или узла"))
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

        root.addStretch()

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

