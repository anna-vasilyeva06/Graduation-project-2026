import re
from PySide6.QtCore import Qt
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import QVBoxLayout, QTextBrowser

from ui.pages.base import BasePage
<<<<<<< Updated upstream
=======
from ui.widgets import PageHeader, add_page_header, make_page_root
>>>>>>> Stashed changes


HELP_HTML = """
<b>Руководство пользователя</b><br><br>

<b>Назначение приложения</b><br>
Приложение предназначено для комплексного анализа состояния персонального компьютера
и подключённой периферии. <br><br>

<b>Интерфейс приложения</b><br>
Окно приложения разделено на несколько областей:
<ul>
<<<<<<< Updated upstream
<li>левая панель навигации — переход между разделами;</li>
<li>верхняя панель — приветствие пользователя и поиск;</li>
<li>основная область — отображение информации выбранного раздела.</li>
=======
<li>отображение <b>общей информации</b> о компьютере и операционной системе;</li>
<li><b>мониторинг</b> ключевых ресурсов (ЦП, ОЗУ, диски, сеть, батарея);</li>
<li><b>оценку состояния системы</b> по правилам и с помощью встроенной <b>ординарной логистической регрессии</b> по <b>шести признакам</b> (файл <b>ml_health_model.json</b>);</li>
<li><b>диагностические операции</b> (проверка доступности узла сети, проверка TCP-порта);</li>
<li>просмотр <b>настоящего руководства</b> и подготовку текста обратной связи.</li>
</ul>
<p>Программа <b>не предназначена</b> для удалённого администрирования, изменения настроек оборудования и ОС, а также для замены штатных средств диагностики производителя оборудования. Оценка "здоровья" носит справочный характер и не заменяет диагностику специалиста.</p>

<a name="s2-2"></a>
<p><b>2.2. Условия применения</b></p>
<p><b>Аппаратные требования</b>: персональный компьютер, соответствующий минимальным требованиям установленной версии Windows.</p>
<p><b>Программная среда:</b> ОС <b>Microsoft Windows</b>. Часть функций использует системные механизмы Windows (WMI, PowerShell, при наличии - утилиты драйвера видеокарты, например nvidia-smi). Отдельная установка <b>Python не требуется</b> при работе с готовым файлом .exe.</p>
<p><b>Права пользователя:</b> для корректного сбора данных о дисках, сети и устройствах рекомендуется запуск от учётной записи с правами, достаточными для чтения системной информации. Некоторые сведения могут быть недоступны при ограничениях политик безопасности.</p>
<p><b>Сеть:</b> большинство функций работают без подключения к Интернету; переход по ссылкам обратной связи и открытие почтовых веб-интерфейсов требуют доступа к сети и браузера по умолчанию.</p>

<a name="s3"></a>
<p><b>3. ПОДГОТОВКА К РАБОТЕ</b></p>

<a name="s3-1"></a>
<p><b>3.1. Установка и запуск (сборка .exe)</b></p>
<p>Поставка программы предполагает использование <b>готового исполняемого модуля</b> и сопутствующих файлов библиотек.</p>
<ol>
<li><b>Получите дистрибутив</b> - папку или установочный пакет, содержащий файл <b>ITMetric.exe</b> и необходимые зависимости в той же структуре каталогов.</li>
<li>При <b>установщике</b> (msi/innosetup и т.п.): запустите установку, следуйте шагам мастера, при необходимости выберите каталог установки и создание ярлыка в меню «Пуск» или на рабочем столе.</li>
<li>При <b>портативной папке</b>: скопируйте всю папку целиком на локальный диск (не отделяйте .exe от вложенных библиотек и ресурсов).</li>
<li><b>Запуск:</b> двойной щелчок по <b>ITMetric.exe</b> или выбор ярлыка в меню Пуск / на рабочем столе.</li>
<li>При первом запуске <b>антивирус или Защитник Windows</b> может запросить подтверждение - разрешите запуск, если дистрибутив получен из доверенного источника.</li>
<li>Если приложение не запускается, убедитесь, что не заблокирован доступ к папке установки, и что файл запускается из <b>полной копии</b> дистрибутива, а не один перенесённый .exe без остальных файлов.</li>
</ol>

<a name="s3-2"></a>
<p><b>3.2. Первый запуск</b></p>
<ol>
<li>Дождитесь открытия главного окна приложения.</li>
<li>Ознакомьтесь с настоящим разделом <b>"Руководство"</b>.</li>
<li>При необходимости настройте масштаб отображения Windows, если элементы интерфейса мелкие на высоком разрешении экрана.</li>
</ol>

<a name="s3-3"></a>
<p><b>3.3. Рекомендации перед использованием диагностики</b></p>
<ul>
<li>Для раздела <b>"Сеть"</b> при необходимости подготовьте <b>IP-адрес или доменное имя</b> узла и <b>номер TCP-порта</b> для проверки.</li>
<li>Учтите, что брандмауэр и политики сети могут блокировать ICMP (ping) или подключения к портам - это не всегда ошибка приложения.</li>
>>>>>>> Stashed changes
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

<<<<<<< Updated upstream
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
=======
        main_layout = make_page_root(self, spacing=12)
        add_page_header(
            main_layout,
            "Руководство",
            "Руководство пользователя: содержание, установка и запуск .exe, операции, типовые ошибки.",
        )

        card = QFrame()
        card.setObjectName("helpCard")
        card_lay = QVBoxLayout(card)
        card_lay.setContentsMargins(0, 0, 0, 0)
>>>>>>> Stashed changes

        self.browser = QTextBrowser()
        self.browser.setOpenExternalLinks(False)
        self.browser.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
<<<<<<< Updated upstream
        # Жёлтая подсветка для span с классом .search-highlight (Qt в документе)
        self.browser.document().setDefaultStyleSheet(
            "body { word-wrap: break-word; } "
            "span.search-highlight { background-color: #ffeb3b; }"
        )
=======

        self.browser.setStyleSheet("QTextBrowser { selection-background-color: #ffcc00; }")
>>>>>>> Stashed changes
        self.browser.setHtml(HELP_HTML)
        self.browser.setReadOnly(True)
        self.browser.setTextInteractionFlags(Qt.NoTextInteraction)

        main_layout.addWidget(self.browser)

        self._highlight_timer = None

    def _restore_help(self) -> None:
        """Возвращает исходный текст руководства (убирает подсветку)."""
        self.browser.setHtml(HELP_HTML)
        if self._highlight_timer is not None:
            self._highlight_timer.stop()
            self._highlight_timer = None

    # использование встроенного поиска QTextBrowser
    def jump_to_text(self, query: str) -> None:
<<<<<<< Updated upstream
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
=======
        if not query or not query.strip():
            return

        # просто ищем и подсвечиваем встроенным методом
        self.browser.find(query.strip())
>>>>>>> Stashed changes
