import datetime
import json
import os
import subprocess

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QLabel,
    QProgressBar,
    QVBoxLayout,
    QGroupBox,
    QPushButton,
    QWidget,
)

from ui.pages.base import BasePage


class MemoryPage(BasePage):
    def __init__(self):
        super().__init__()
        root = QVBoxLayout(self)
        root.setAlignment(Qt.AlignTop)
        root.setSpacing(4)
        root.setContentsMargins(12, 12, 12, 12)
        self._root = root

        from core.memory import get_memory

        mem = get_memory()
        lbl_ram = QLabel("<b>Оперативная память</b>")
        lbl_ram.setToolTip("ОЗУ используется программами. При нехватке система использует файл подкачки — работа замедляется")
        root.addWidget(lbl_ram)
        root.addSpacing(6)

        bar = QProgressBar()
        bar.setFixedHeight(12)
        bar.setValue(int(mem["Usage %"]))
        bar.setTextVisible(False)
        root.addWidget(bar)
        root.addWidget(QLabel(f'{mem["Used GB"]} GB / {mem["Total GB"]} GB'))

        root.addSpacing(14)
        lbl_disk = QLabel("<b>Локальные диски</b>")
        lbl_disk.setToolTip("Заполненность дисков. Мало свободного места может мешать обновлениям и установке программ")
        root.addWidget(lbl_disk)
        root.addSpacing(6)

        self._build_disks_block()

        self._root.addSpacing(16)
        lbl_heavy = QLabel("<b>Крупные объекты (по дискам)</b>")
        lbl_heavy.setToolTip("Папки и файлы, занимающие больше всего места. Помогает найти, что можно удалить для освобождения места")
        self._root.addWidget(lbl_heavy)

        # Кнопка обновления анализа
        btn = QPushButton("Обновить анализ")
        btn.setToolTip("Повторно просканировать диски и обновить список крупных папок и файлов")
        btn.clicked.connect(self._rebuild_heavy_section)
        self._root.addWidget(btn)

        self._root.addSpacing(6)

        # Контейнер для результатов анализа
        self._heavy_container = QWidget()
        self._heavy_layout = QVBoxLayout(self._heavy_container)
        self._heavy_layout.setContentsMargins(0, 0, 0, 0)
        self._heavy_layout.setSpacing(6)
        self._root.addWidget(self._heavy_container)

        self._rebuild_heavy_section()

    def _build_disks_block(self):
        """Информация по локальным дискам (объём и свободное место)."""
        try:
            cmd = [
                "powershell",
                "-NoProfile",
                "-Command",
                "Get-Volume | Where DriveType -eq 'Fixed' | "
                "Select DriveLetter,Size,SizeRemaining | ConvertTo-Json",
            ]

            raw = subprocess.check_output(cmd, shell=True)
            data = json.loads(raw.decode("utf-8"))

            if isinstance(data, dict):
                data = [data]

            for d in data:
                if not d.get("DriveLetter"):
                    continue

                if not d.get("Size") or not d.get("SizeRemaining"):
                    continue
                name = d["DriveLetter"] + ":"
                size = d["Size"]
                free = d["SizeRemaining"]

                used = size - free
                percent = int((used / size) * 100)

                bar = QProgressBar()
                bar.setFixedHeight(12)
                bar.setValue(percent)
                bar.setFormat(f"{name}   {round(used/1e9,1)} / {round(size/1e9,1)} GB")
                self._root.addWidget(bar)

        except Exception as e:
            self._root.addWidget(QLabel("Ошибка получения дисков: " + str(e)))

    def _clear_heavy_layout(self):
        while self._heavy_layout.count():
            item = self._heavy_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.setParent(None)

    def _rebuild_heavy_section(self):
        """Перестраивает блок «Крупные объекты», обновляя дату анализа."""
        from core.memory import get_largest_paths

        self._clear_heavy_layout()

        # Дата и время анализа
        ts = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")
        lbl_ts = QLabel(f"Анализ от: {ts}")
        lbl_ts.setStyleSheet("color:#666; font-size:10px;")
        self._heavy_layout.addWidget(lbl_ts)

        try:
            heavy = get_largest_paths()
            drives = heavy.get("drives") or []

            if not drives:
                self._heavy_layout.addWidget(QLabel("Нет данных по крупным объектам"))
            for drive in drives:
                base = drive.get("root", "")
                dirs = drive.get("dirs", []) or []
                files = drive.get("files", []) or []
                scanned = drive.get("scanned_files", 0)

                def pretty_rel(path: str) -> str:
                    try:
                        rel = os.path.relpath(path, base) if base else path
                    except ValueError:
                        rel = path
                    return rel

                title_drive = QLabel(f"Диск/путь: {base}")
                title_drive.setStyleSheet("font-weight:bold; margin-top:6px;")
                title_drive.setToolTip("Корневой путь, с которого выполнен анализ крупных папок и файлов")
                self._heavy_layout.addWidget(title_drive)

                box_dirs = QGroupBox("Крупные папки")
                box_dirs.setToolTip("Папки, занимающие больше всего места на диске. Отсортированы по размеру")
                lay_dirs = QVBoxLayout(box_dirs)
                lay_dirs.setSpacing(4)

                if dirs:
                    for d in dirs:
                        p = str(d.get("path", ""))
                        sz = d.get("size_gb", "—")
                        lay_dirs.addWidget(
                            QLabel(f"• {pretty_rel(p)} — {sz} GB")
                        )
                else:
                    lay_dirs.addWidget(QLabel("Нет данных по папкам"))

                self._heavy_layout.addWidget(box_dirs)

                box_files = QGroupBox("Крупные файлы")
                box_files.setToolTip("Отдельные файлы с наибольшим размером. Помогает найти кандидатов на удаление")
                lay_files = QVBoxLayout(box_files)
                lay_files.setSpacing(4)

                if files:
                    for f in files:
                        p = str(f.get("path", ""))
                        sz = f.get("size_gb", "—")
                        lay_files.addWidget(
                            QLabel(f"• {pretty_rel(p)} — {sz} GB")
                        )
                else:
                    lay_files.addWidget(QLabel("Нет данных по файлам"))

                self._heavy_layout.addWidget(box_files)

                note = QLabel(f"Проанализировано файлов: {scanned} (путь: {base})")
                note.setStyleSheet("color:#666; font-size:10px")
                self._heavy_layout.addWidget(note)

        except Exception as e:
            self._heavy_layout.addWidget(QLabel("Ошибка анализа папок и файлов: " + str(e)))
