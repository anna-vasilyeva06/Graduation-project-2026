import json
import os
import subprocess

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QProgressBar, QVBoxLayout, QGroupBox

from ui.pages.base import BasePage
from ui.widgets import PageHeader, section_title


class MemoryPage(BasePage):
    def __init__(self):
        super().__init__()
        root = QVBoxLayout(self)
        root.setAlignment(Qt.AlignTop)
        root.setSpacing(10)
        root.setContentsMargins(16, 16, 16, 16)

        from core.memory import get_memory, get_largest_paths

        root.addWidget(
            PageHeader(
                "Память",
                "ОЗУ, диски и крупные папки и файлы.",
            )
        )

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

        try:
            cmd = [
                "powershell",
                "-NoProfile",
                "-Command",
                "Get-Volume | Where DriveType -eq 'Fixed' | "
                "Select DriveLetter,Size,SizeRemaining | ConvertTo-Json"
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
                percent = int((used/size)*100)

                bar = QProgressBar()
                bar.setFixedHeight(12)
                bar.setValue(percent)
                bar.setFormat(f"{name}   {round(used/1e9,1)} / {round(size/1e9,1)} GB")
                root.addWidget(bar)

        except Exception as e:
            root.addWidget(QLabel("Ошибка получения дисков: " + str(e)))

        root.addSpacing(16)
        lbl_heavy = QLabel("<b>Крупные объекты (по дискам)</b>")
        lbl_heavy.setToolTip("Папки и файлы, занимающие больше всего места. Помогает найти, что можно удалить для освобождения места")
        root.addWidget(lbl_heavy)
        root.addSpacing(6)

        try:
            heavy = get_largest_paths()
            drives = heavy.get("drives") or []

            if not drives:
                root.addWidget(QLabel("Нет данных по крупным объектам"))
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
                root.addWidget(title_drive)

                box_dirs = QGroupBox()
                box_dirs.setTitle("")
                box_dirs.setToolTip("Папки, занимающие больше всего места на диске. Отсортированы по размеру")
                lay_dirs = QVBoxLayout(box_dirs)
                lay_dirs.addWidget(section_title("Крупные папки"))
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

                root.addWidget(box_dirs)

                box_files = QGroupBox()
                box_files.setTitle("")
                box_files.setToolTip("Отдельные файлы с наибольшим размером. Помогает найти кандидатов на удаление")
                lay_files = QVBoxLayout(box_files)
                lay_files.addWidget(section_title("Крупные файлы"))
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

                root.addWidget(box_files)

                note = QLabel(f"Проанализировано файлов: {scanned} (путь: {base})")
                note.setStyleSheet("color:#666; font-size:10px")
                root.addWidget(note)

        except Exception as e:
            root.addWidget(QLabel("Ошибка анализа папок и файлов: " + str(e)))
