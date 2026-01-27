from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QGroupBox, QVBoxLayout

import psutil

from core.network import get_network
from ui.pages.base import BasePage


class NetworkPage(BasePage):
    def __init__(self):
        super().__init__()

        root = QVBoxLayout(self)
        root.setAlignment(Qt.AlignTop)
        root.setSpacing(10)
        root.setContentsMargins(12, 12, 12, 12)

        title = QLabel("<b>Сетевые подключения</b>")
        title.setStyleSheet("font-size:16px;")
        root.addWidget(title)

        stats = psutil.net_if_stats()
        addrs = psutil.net_if_addrs()
        net = get_network()

        found = False

        for name, addr_list in addrs.items():
            stat = stats.get(name)
            if not stat:
                continue

            if not stat.isup:
                continue

            found = True

            box = QGroupBox(name)
            layout = QVBoxLayout(box)
            layout.setSpacing(4)

            lname = name.lower()
            if "wi-fi" in lname or "wireless" in lname or "wlan" in lname:
                conn_type = "Беспроводное (Wi-Fi)"
            elif "ethernet" in lname:
                conn_type = "Проводное (Ethernet)"
            else:
                conn_type = "Сетевое подключение"

            layout.addWidget(QLabel(f"Тип подключения: {conn_type}"))
            layout.addWidget(QLabel("Статус: подключено"))

            ip = None
            mac = None

            for a in addr_list:
                if a.family.name == "AF_INET":
                    ip = a.address
                if a.family.name == "AF_PACKET":
                    mac = a.address

            if ip:
                layout.addWidget(QLabel(f"IPv4-адрес: {ip}"))
            if mac:
                layout.addWidget(QLabel(f"MAC-адрес: {mac}"))
            # extra IPs (if any)
            ips = net.get(name) or []
            extra = [x for x in ips if x != ip]
            if extra:
                layout.addWidget(QLabel("Доп. IPv4: " + ", ".join(extra)))

            root.addWidget(box)

        if not found:
            root.addWidget(QLabel("Нет активных сетевых подключений"))

        root.addStretch()
