import json
import os
import subprocess

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QProgressBar, QVBoxLayout, QGroupBox

from ui.pages.base import BasePage

class MemoryPage(BasePage):
    def __init__(self):
        super().__init__()
        root = QVBoxLayout(self)
        root.setAlignment(Qt.AlignTop)
        root.setSpacing(4)
        root.setContentsMargins(12,12,12,12)

        from core.memory import get_memory, get_largest_paths

        mem = get_memory()
        root.addWidget(QLabel("<b>Оперативная память</b>"))

        bar = QProgressBar()
        bar.setFixedHeight(12)
        bar.setValue(int(mem["Usage %"]))
        bar.setTextVisible(False)
        bar.setStyleSheet("""
            QProgressBar { background:#eee; border:1px solid #bbb; }
            QProgressBar::chunk { background:#5c9ded; }
        """)
        root.addWidget(bar)
        root.addWidget(QLabel(f'{mem["Used GB"]} GB / {mem["Total GB"]} GB'))

        root.addSpacing(10)
        root.addWidget(QLabel("<b>Локальные диски</b>"))

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
                bar.setStyleSheet("""
                    QProgressBar { background:#eee; border:1px solid #bbb; }
                    QProgressBar::chunk { background:#82c91e; }
                """)
                root.addWidget(bar)

        except Exception as e:
            root.addWidget(QLabel("Ошибка получения дисков: " + str(e)))

        root.addSpacing(12)
        root.addWidget(QLabel("<b>Крупные объекты (по дискам)</b>"))

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
                root.addWidget(title_drive)

                box_dirs = QGroupBox("Крупные папки")
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

                root.addWidget(box_dirs)

                box_files = QGroupBox("Крупные файлы")
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

                root.addWidget(box_files)

                note = QLabel(f"Проанализировано файлов: {scanned} (путь: {base})")
                note.setStyleSheet("color:#666; font-size:10px")
                root.addWidget(note)

        except Exception as e:
            root.addWidget(QLabel("Ошибка анализа папок и файлов: " + str(e)))
