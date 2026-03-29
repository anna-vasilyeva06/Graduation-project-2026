import re
from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import QVBoxLayout, QTextBrowser, QFrame

from ui.pages.base import BasePage
from ui.widgets import PageHeader


HELP_HTML = """
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
"""


class HelpPage(BasePage):
    def __init__(self):
        super().__init__()

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        main_layout.addWidget(
            PageHeader("Руководство", "Описание разделов и интерфейса приложения.")
        )

        card = QFrame()
        card.setObjectName("helpCard")
        card_lay = QVBoxLayout(card)
        card_lay.setContentsMargins(0, 0, 0, 0)

        self.browser = QTextBrowser()
        self.browser.setOpenExternalLinks(False)
        self.browser.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # Жёлтая подсветка для span с классом .search-highlight (Qt в документе)
        self.browser.document().setDefaultStyleSheet(
            "body { word-wrap: break-word; } "
            "span.search-highlight { background-color: #ffeb3b; }"
        )
        self.browser.setHtml(HELP_HTML)
        self.browser.setReadOnly(True)
        self.browser.setTextInteractionFlags(Qt.NoTextInteraction)

        card_lay.addWidget(self.browser)
        main_layout.addWidget(card)

        self._highlight_timer = None

    def _restore_help(self) -> None:
        """Возвращает исходный текст руководства (убирает подсветку)."""
        self.browser.setHtml(HELP_HTML)
        if self._highlight_timer is not None:
            self._highlight_timer.stop()
            self._highlight_timer = None

    def jump_to_text(self, query: str) -> None:
        """
        Ищет query в тексте, подсвечивает первое вхождение жёлтым через HTML,
        прокручивает к нему. Через 3 секунды подсветка убирается.
        """
        if not query or not query.strip():
            return

        q = query.strip()

        if self._highlight_timer is not None:
            self._highlight_timer.stop()
            self._highlight_timer = None

        # Экранируем для использования в регулярном выражении
        pattern = re.escape(q)
        # Ищем первое вхождение (без учёта регистра)
        match = re.search(pattern, HELP_HTML, re.IGNORECASE)
        if not match:
            cursor = self.browser.textCursor()
            cursor.movePosition(QTextCursor.Start)
            self.browser.setTextCursor(cursor)
            self.browser.ensureCursorVisible()
            return

        # Подставляем подсветку: span с классом (цвет задаётся в defaultStyleSheet)
        start, end = match.span()
        before = HELP_HTML[:start]
        found_text = HELP_HTML[start:end]
        after = HELP_HTML[end:]
        # Якорь для прокрутки; подсветка — класс + inline (жёлтый)
        highlighted_html = (
            before
            + '<a name="search-hit"></a><span class="search-highlight" style="background-color:#ffeb3b;">'
            + found_text
            + "</span>"
            + after
        )

        self.browser.setHtml(highlighted_html)

        # Прокручиваем к якорю (без find() — иначе появляется серое выделение)
        self.browser.setSource(QUrl("#search-hit"))

        # Через 3 секунды возвращаем исходный текст (подсветка исчезнет)
        if self._highlight_timer is not None:
            self._highlight_timer.stop()
        self._highlight_timer = QTimer(self)
        self._highlight_timer.setSingleShot(True)
        self._highlight_timer.timeout.connect(self._restore_help)
        self._highlight_timer.start(3000)
