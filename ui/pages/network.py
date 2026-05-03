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
from ui.widgets import section_title


def _iface_group(iface: dict) -> QGroupBox:
    box = QGroupBox()
    box.setTitle("")
    lay = QVBoxLayout(box)
    lay.addWidget(section_title(iface.get("name", "-")))
    lay.setSpacing(8)
    lay.addWidget(QLabel(f"Тип: {iface.get('type', '-')}"))
    lay.addWidget(QLabel("Статус: подключено"))

    ipv4 = iface.get("ipv4") or []
    if ipv4:
        w = QLabel(f"IPv4: {', '.join(ipv4)}")
        w.setToolTip("Адрес устройства в локальной сети (формат x.x.x.x)")
        lay.addWidget(w)
    ipv6 = (iface.get("ipv6") or [])[:2]
    if ipv6:
        w = QLabel(f"IPv6: {', '.join(ipv6)}")
        w.setToolTip("Адрес нового поколения (формат с двоеточиями)")
        lay.addWidget(w)

    mac = iface.get("mac") or ""
    if mac:
        w = QLabel(f"MAC: {mac}")
        w.setToolTip("Уникальный идентификатор сетевого адаптера")
        lay.addWidget(w)

    sp = QLabel(f"Скорость: {iface.get('speed', '-')}")
    sp.setToolTip("Максимальная пропускная способность интерфейса (Мбит/с)")
    lay.addWidget(sp)
    mtu = QLabel(f"MTU: {iface.get('mtu', '-')}")
    mtu.setToolTip("Максимальный размер пакета данных в байтах")
    lay.addWidget(mtu)
    return box


class NetworkPage(BasePage):
    def __init__(self):
        super().__init__()
        root = self.build_root(
            "Сеть",
            "Интерфейсы, адреса, скорость и проверка ping/порта.",
            spacing=14,
        )

        lbl = QLabel("Активные подключения")
        lbl.setToolTip(
            "Сетевые интерфейсы (Wi‑Fi, Ethernet и др.) с их параметрами и статусом"
        )
        lbl.setStyleSheet("font-weight:bold; margin-top:12px; margin-bottom:4px;")
        root.addWidget(lbl)

        try:
            infos = get_network_info()
        except Exception:
            infos = []
        if not infos:
            root.addWidget(QLabel("Нет активных сетевых подключений"))
        else:
            for iface in infos:
                root.addWidget(_iface_group(iface))

        adv = QLabel("Проверка доступности")
        adv.setStyleSheet("font-weight:bold; margin-top:20px; margin-bottom:8px;")
        adv.setToolTip(
            "Ping - доступность узла. Порт - открыт ли указанный TCP-порт"
        )
        root.addWidget(adv)

        adv_box = QGroupBox()
        adv_box.setTitle("")
        adv_box.setToolTip(
            "Укажите IP или домен для ping или проверки открытого TCP-порта"
        )
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
        ping_btn = QPushButton("Ping")
        ping_btn.clicked.connect(self._do_ping)
        port_btn = QPushButton("Проверить порт")
        port_btn.clicked.connect(self._do_port)
        btn_row.addWidget(ping_btn)
        btn_row.addWidget(port_btn)
        btn_row.addStretch()
        adv_lay.addLayout(btn_row)

        self._result_label = QLabel("")
        self._result_label.setWordWrap(True)
        self._result_label.setStyleSheet(f"color:{COLORS['text']}; margin-top:4px;")
        adv_lay.addWidget(self._result_label)
        root.addWidget(adv_box)
        root.addStretch()

    def _set_result(self, ok: bool, text: str) -> None:
        self._result_label.setText(text)
        c = COLORS["success"] if ok else COLORS["error"]
        self._result_label.setStyleSheet(f"color:{c}; margin-top:4px;")

    def _do_ping(self) -> None:
        ok, msg = ping_host(self._host_input.text().strip())
        self._set_result(ok, msg)

    def _do_port(self) -> None:
        ok, msg = check_port(self._host_input.text().strip(), self._port_input.value())
        self._set_result(ok, (f"OK {msg}" if ok else f"NOT OK {msg}"))
