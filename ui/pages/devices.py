from PySide6.QtWidgets import QVBoxLayout, QLabel, QGroupBox
import wmi

from ui.pages.base import BasePage

class DevicesPage(BasePage):
    def __init__(self):
        super().__init__()

        root = QVBoxLayout(self)
        root.setSpacing(12)

        title = QLabel("Подключённые устройства")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        root.addWidget(title)

        pc = wmi.WMI()

        active_box = QGroupBox("Подключено и используется сейчас")
        active_layout = QVBoxLayout(active_box)

        found = False

        try:
            mice = pc.Win32_PointingDevice()
            if mice:
                active_layout.addWidget(
                    QLabel(f"• Указательные устройства (мышь / тачпад): {len(mice)}")
                )
                found = True
        except Exception:
            pass

        try:
            if pc.Win32_Keyboard():
                active_layout.addWidget(QLabel("• Клавиатура"))
                found = True
        except Exception:
            pass

        try:
            for p in pc.Win32_Printer():
                name = p.Name.lower()
                if any(x in name for x in ["pdf", "xps", "fax"]):
                    continue
                if not p.WorkOffline:
                    active_layout.addWidget(QLabel(f"• Принтер: {p.Name}"))
                    found = True
        except Exception:
            pass

        if not found:
            active_layout.addWidget(QLabel("Нет активных периферийных устройств"))

        root.addWidget(active_box)

        bt_box = QGroupBox("Ранее сопряжённые Bluetooth-устройства")
        bt_layout = QVBoxLayout(bt_box)

        try:
            bluetooth_devices = [
                d for d in pc.Win32_PnPEntity()
                if d.Name and "bluetooth" in d.Name.lower()
            ]

            shown = set()
            for d in bluetooth_devices:
                name = d.Name.strip()
                if name not in shown:
                    bt_layout.addWidget(QLabel(f"• {name}"))
                    shown.add(name)

            if not shown:
                bt_layout.addWidget(QLabel("Нет данных о Bluetooth-устройствах"))

        except Exception:
            bt_layout.addWidget(QLabel("История Bluetooth недоступна"))

        root.addWidget(bt_box)
        root.addStretch()
