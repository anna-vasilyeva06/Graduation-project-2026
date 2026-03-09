"""
Стиль Liquid Glass / Frutiger Aero.
Светлые тона, прозрачность, градиенты, стеклянные поверхности, минимализм.
"""

# Цветовая палитра — Liquid Glass: прозрачность, оттенки неба и воды
COLORS = {
    "bg_main": "#eef5fb",           # Основной фон
    "bg_surface": "rgba(255, 255, 255, 140)",   # Стекло — полупрозрачные карточки
    "bg_sidebar": "rgba(220, 235, 250, 160)",   # Стеклянная боковая панель
    "bg_input": "rgba(255, 255, 255, 180)",    # Поля ввода как стекло
    "border": "rgba(170, 200, 230, 120)",      # Границы
    "border_light": "rgba(200, 220, 240, 80)",  # Светлые границы
    "accent": "#4a9fd9",            # Акцент (голубой)
    "accent_hover": "#5eb0e8",      # Акцент при наведении
    "glass_highlight": "rgba(255, 255, 255, 0.5)",  # Блик на стекле
    "text": "#2c3e50",              # Основной текст
    "text_secondary": "#6b7c8d",    # Вторичный текст
    "success": "#22c55e",           # Успех (зелёный)
    "success_soft": "rgba(34, 197, 94, 38)",    # Мягкий зелёный фон
    "warning": "#f59e0b",           # Предупреждение (янтарный)
    "warning_soft": "rgba(245, 158, 11, 31)",   # Мягкий янтарный
    "error": "#ef4444",             # Ошибка (красный)
    "error_soft": "rgba(239, 68, 68, 31)",      # Мягкий красный
}

# Шрифт — минималистичный, читаемый
FONT_FAMILY = '"Segoe UI Variable", "Segoe UI", "Inter", "SF Pro Display", sans-serif'

STYLESHEET = f"""
/* === Глобальные настройки === */
QWidget {{
    background-color: transparent;
    color: {COLORS["text"]};
    font-family: {FONT_FAMILY};
}}

/* === Метки и заголовки — без фона, без выделения === */
QLabel {{
    background-color: transparent;
    selection-background-color: transparent;
}}

/* === Приветствие пользователя — в одну строку === */
QLabel#welcomeLabel {{
    font-size: 15px;
    font-weight: 500;
    letter-spacing: 0.3px;
    color: {COLORS["text"]};
    white-space: nowrap;
}}

/* === Центральная область === */
QWidget#centralWidget {{
    background: transparent;
}}

/* === Главное окно — Frutiger Aero градиент (небо/вода) === */
QMainWindow {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #e8f4fc, stop:0.3 #e0eef8, stop:0.7 #d8e8f4, stop:1 #d0e2f0);
}}

/* === Боковая панель — стекло, контур, тень (через QGraphicsDropShadowEffect) === */
QListWidget#sidebarNav {{
    background-color: rgba(210, 228, 248, 100);
    border: 1px solid rgba(140, 170, 210, 180);
    border-radius: 14px;
    padding: 12px;
    outline: none;
}}
QListWidget {{
    background-color: {COLORS["bg_sidebar"]};
    border: 1px solid {COLORS["border_light"]};
    border-radius: 12px;
    padding: 10px;
    outline: none;
}}
QListWidget::item {{
    padding: 10px 14px;
    border-radius: 8px;
    margin: 2px 0;
}}
QListWidget::item:hover {{
    background-color: rgba(255, 255, 255, 120);
}}
QListWidget::item:selected {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 rgba(255, 255, 255, 200), stop:1 rgba(220, 238, 255, 180));
    border: 1px solid rgba(74, 159, 217, 0.4);
    color: {COLORS["accent"]};
}}
QListWidget::item:selected:!active {{
    background-color: rgba(255, 255, 255, 204);
}}

/* === Поле поиска — стеклянный эффект === */
QLineEdit {{
    background-color: {COLORS["bg_input"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 12px;
    padding: 10px 14px;
    selection-background-color: rgba(74, 159, 217, 0.3);
}}
QLineEdit:focus {{
    border-color: {COLORS["accent"]};
    background-color: rgba(255, 255, 255, 220);
}}
QLineEdit:hover {{
    border-color: {COLORS["accent"]};
}}

/* === Кнопки — стеклянные === */
QPushButton {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 rgba(255, 255, 255, 200), stop:1 rgba(235, 245, 255, 170));
    border: 1px solid {COLORS["border"]};
    border-radius: 12px;
    padding: 10px 18px;
    min-height: 22px;
}}
QPushButton:hover {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 rgba(255, 255, 255, 230), stop:1 rgba(220, 238, 255, 200));
    border-color: {COLORS["accent"]};
}}
QPushButton:pressed {{
    background-color: rgba(200, 220, 240, 180);
}}

/* === Группы (карточки) — Liquid Glass эффект === */
QGroupBox {{
    background-color: {COLORS["bg_surface"]};
    border: 1px solid {COLORS["border_light"]};
    border-radius: 14px;
    margin-top: 20px;
    padding-top: 24px;
    padding-left: 18px;
    padding-right: 18px;
    padding-bottom: 18px;
    font-weight: bold;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 16px;
    top: 4px;
    padding: 4px 12px;
    background-color: transparent;
}}

/* === Прогресс-бары — стеклянный градиент === */
QProgressBar {{
    background-color: rgba(200, 220, 240, 100);
    border: none;
    border-radius: 10px;
    text-align: center;
}}
QProgressBar::chunk {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #a0d8f5, stop:0.4 #78c4ec, stop:0.7 #58b0e0, stop:1 #4a9fd9);
    border-radius: 10px;
}}

/* === Числовой ввод === */
QSpinBox {{
    background-color: {COLORS["bg_input"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 10px;
    padding: 8px 12px;
    min-height: 22px;
}}
QSpinBox:focus {{
    border-color: {COLORS["accent"]};
}}

/* === Текстовое поле (обратная связь) — стекло === */
QTextEdit {{
    background-color: rgba(255, 255, 255, 160);
    border: 1px solid {COLORS["border"]};
    border-radius: 12px;
    padding: 12px;
}}

/* === Текстовый браузер — стекло === */
QTextBrowser {{
    background-color: rgba(255, 255, 255, 130);
    border: 1px solid {COLORS["border_light"]};
    border-radius: 12px;
    padding: 20px;
}}

/* === Область прокрутки === */
QScrollArea {{
    border: none;
    background-color: transparent;
}}
QScrollBar:horizontal {{
    height: 0;
    max-height: 0;
}}
QScrollBar:vertical {{
    background-color: rgba(210, 220, 240, 90);
    width: 10px;
    border-radius: 5px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #b8d4e8, stop:0.5 #a0c4dc, stop:1 #90b8d4);
    border-radius: 5px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background-color: {COLORS["accent"]};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

/* === Подсказки — стеклянные === */
QToolTip {{
    font-size: 12px;
    font-weight: normal;
    padding: 10px 12px;
    background-color: rgba(255, 255, 255, 200);
    border: 1px solid {COLORS["border"]};
    border-radius: 8px;
    color: {COLORS["text"]};
}}
"""


def apply_theme(app: "QApplication") -> None:
    """Применяет тему Liquid Glass к приложению."""
    app.setStyleSheet(STYLESHEET)
