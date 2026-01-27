from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QScrollArea, QVBoxLayout

from ui.pages.base import BasePage


class HelpPage(BasePage):
    def __init__(self):
        super().__init__()

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        content = BasePage()
        layout = QVBoxLayout(content)
        layout.setAlignment(Qt.AlignTop)
        layout.setSpacing(10)
        layout.setContentsMargins(16, 16, 16, 16)

        text = QLabel("""
<b>Руководство пользователя</b><br><br>

<b>Назначение приложения</b><br>
Приложение предназначено для комплексного анализа состояния персонального компьютера
и подключённой периферии. <br><br>

<b>Интерфейс приложения</b><br>
Окно приложения разделено на несколько областей:
<ul>
<li>левая панель навигации — переход между разделами;</li>
<li>верхняя панель — приветствие пользователя и поиск;</li>
<li>основная область — отображение информации выбранного раздела.</li>
</ul>

<b>Описание разделов</b><br><br>

<b>Главная</b><br>
Отображает общую информацию о системе: имя компьютера, операционную систему,
архитектуру и объём оперативной памяти.<br><br>

<b>CPU</b><br>
Содержит сведения о процессоре и график его текущей загрузки в реальном времени.<br><br>

<b>GPU</b><br>
Отображает информацию о видеоподсистеме и текущую загрузку графического процессора.<br><br>

<b>Память</b><br>
Показывает использование оперативной памяти и логических дисков
с визуальной индикацией заполненности.<br><br>

<b>Батарея</b><br>
Отображает уровень заряда батареи, состояние питания и актуален для портативных устройств.<br><br>

<b>Сеть</b><br>
Содержит сведения об активных сетевых подключениях и интерфейсах.<br><br>

<b>Периферия</b><br>
Отображает подключённые и используемые устройства (мыши, клавиатуры, принтеры),
а также ранее сопряжённые Bluetooth-устройства.<br><br>

<b>Обратная связь</b><br>
Содержит контактные данные автора приложения для связи и отправки предложений.<br><br>

<b>Заключение</b><br>
Приложение предназначено для быстрого и удобного мониторинга состояния ПК
и не вносит изменений в работу системы.
        """)

        text.setWordWrap(True)
        text.setTextInteractionFlags(Qt.TextSelectableByMouse)

        layout.addWidget(text)
        layout.addStretch()

        scroll.setWidget(content)
        main_layout.addWidget(scroll)
