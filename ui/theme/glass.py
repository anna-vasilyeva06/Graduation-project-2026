"""
Стиль Liquid Glass / Frutiger Aero — углублённая версия:
градиенты, карточки, типографика, акцентная навигация.
"""

# Цветовая палитра
COLORS = {
    "bg_main": "#e8f0fa",
    "bg_surface": "rgba(255, 255, 255, 165)",
    "bg_sidebar": "rgba(215, 232, 252, 150)",
    "bg_input": "rgba(255, 255, 255, 200)",
    "border": "rgba(140, 175, 215, 140)",
    "border_light": "rgba(190, 210, 235, 100)",
    "accent": "#1e88d4",
    "accent_hover": "#3a9fe8",
    "accent_soft": "rgba(30, 136, 212, 0.12)",
    "glass_highlight": "rgba(255, 255, 255, 0.55)",
    "text": "#1a2b3d",
    "text_secondary": "#5a6d82",
    "success": "#16a34a",
    "success_soft": "rgba(22, 163, 74, 0.12)",
    "warning": "#d97706",
    "warning_soft": "rgba(217, 119, 6, 0.12)",
    "error": "#dc2626",
    "error_soft": "rgba(220, 38, 38, 0.12)",
}

# Дублирует семейство из setup_app_font (шрифт задаётся в Python, не только здесь)
FONT_FAMILY = '"Segoe UI Variable Text", "Segoe UI Variable", "Segoe UI", sans-serif'

STYLESHEET = f"""
/* === Глобальные настройки === */
QWidget {{
    background-color: transparent;
    color: {COLORS["text"]};
    font-family: {FONT_FAMILY};
    font-size: 13px;
}}

QLabel {{
    background-color: transparent;
    selection-background-color: transparent;
}}

QLabel#welcomeLabel {{
    font-size: 18px;
    font-weight: 600;
    letter-spacing: 0.1px;
    color: {COLORS["text"]};
    white-space: nowrap;
}}

/* Заголовок страницы */
QLabel#pageTitle {{
    font-size: 24px;
    font-weight: 700;
    letter-spacing: -0.4px;
    color: {COLORS["text"]};
}}

QLabel#pageSubtitle {{
    font-size: 13px;
    font-weight: normal;
    color: {COLORS["text_secondary"]};
    max-width: 720px;
}}

/* Карточки KPI */
QFrame#metricCard {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 rgba(255, 255, 255, 230), stop:1 rgba(245, 250, 255, 200));
    border: 1px solid {COLORS["border_light"]};
    border-radius: 8px;
}}

QLabel#metricCardTitle {{
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.6px;
    color: {COLORS["text_secondary"]};
}}

QLabel#metricCardValue {{
    font-size: 26px;
    font-weight: 700;
    letter-spacing: -0.5px;
    color: {COLORS["text"]};
}}

QLabel#metricCardHint {{
    font-size: 12px;
    color: {COLORS["text_secondary"]};
}}

/* Верхняя панель — без отдельной «карточки», вровень с фоном окна */
QFrame#topBar {{
    background: transparent;
    border: none;
    border-radius: 0px;
}}

QWidget#centralWidget {{
    background: transparent;
}}

QMainWindow {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
        stop:0 #e4f0fb, stop:0.35 #dceaf8, stop:0.65 #d4e4f4, stop:1 #c8dcf0);
}}

/* Боковая навигация */
QListWidget#sidebarNav {{
    background-color: rgba(200, 225, 250, 95);
    border: 1px solid rgba(130, 170, 215, 160);
    border-radius: 8px;
    padding: 10px 8px;
    outline: none;
    font-size: 16px;
}}
QListWidget#sidebarNav::item {{
    padding: 10px 12px;
    border-radius: 5px;
    margin: 2px 4px;
    min-height: 48px;
}}
QListWidget#sidebarNav::item:hover {{
    background-color: rgba(255, 255, 255, 140);
}}
QListWidget#sidebarNav::item:selected {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 rgba(255, 255, 255, 220), stop:1 rgba(220, 238, 255, 200));
    border: 1px solid rgba(30, 136, 212, 0.35);
    color: {COLORS["text"]};
    font-weight: 600;
}}
QListWidget#sidebarNav::item:selected:!active {{
    background-color: rgba(255, 255, 255, 210);
}}

QListWidget {{
    background-color: {COLORS["bg_sidebar"]};
    border: 1px solid {COLORS["border_light"]};
    border-radius: 6px;
    padding: 10px;
    outline: none;
}}
QListWidget::item {{
    padding: 10px 14px;
    border-radius: 4px;
    margin: 2px 0;
}}
QListWidget::item:hover {{
    background-color: rgba(255, 255, 255, 120);
}}
QListWidget::item:selected {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 rgba(255, 255, 255, 200), stop:1 rgba(220, 238, 255, 180));
    border: 1px solid rgba(30, 136, 212, 0.35);
    color: {COLORS["accent"]};
}}

QLineEdit {{
    background-color: {COLORS["bg_input"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 6px;
    padding: 10px 14px;
    selection-background-color: rgba(30, 136, 212, 0.25);
}}
QLineEdit:focus {{
    border-color: {COLORS["accent"]};
    background-color: rgba(255, 255, 255, 235);
}}
QLineEdit:hover {{
    border-color: {COLORS["accent"]};
}}

QPushButton {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 rgba(255, 255, 255, 220), stop:1 rgba(230, 242, 255, 180));
    border: 1px solid {COLORS["border"]};
    border-radius: 6px;
    padding: 10px 18px;
    min-height: 22px;
    font-weight: 500;
}}
QPushButton:hover {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 rgba(255, 255, 255, 245), stop:1 rgba(210, 235, 255, 220));
    border-color: {COLORS["accent"]};
}}
QPushButton:pressed {{
    background-color: rgba(190, 215, 240, 200);
}}

/* Карточки: заголовок — QLabel#sectionTitle внутри, не QGroupBox::title */
QGroupBox {{
    background-color: {COLORS["bg_surface"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 9px;
    margin-top: 0px;
    margin-bottom: 10px;
    padding-top: 16px;
    padding-left: 22px;
    padding-right: 22px;
    padding-bottom: 20px;
    font-weight: normal;
    font-size: 13px;
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    height: 0px;
    width: 0px;
    padding: 0px;
    margin: 0px;
    color: transparent;
}}

QLabel#sectionTitle {{
    font-size: 15px;
    font-weight: 700;
    letter-spacing: -0.02em;
    color: {COLORS["text"]};
    padding: 4px 0 14px 0;
    margin: 0px;
}}

/* Обёртка графика — как у QGroupBox / карточек */
QFrame#chartCard {{
    background-color: {COLORS["bg_surface"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 9px;
    margin-bottom: 10px;
}}
QFrame#chartCard QChartView {{
    background: transparent;
    border: none;
}}

QProgressBar {{
    border: 1px solid rgba(175, 200, 230, 0.95);
    border-radius: 5px;
    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 rgba(248, 251, 255, 1), stop:1 rgba(228, 236, 248, 0.95));
    min-height: 15px;
    max-height: 17px;
    text-align: center;
}}
QProgressBar::chunk {{
    margin: 3px;
    border-radius: 3px;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #5eb4f0, stop:0.4 #2d9fe8, stop:1 #1565c0);
    border: 1px solid rgba(20, 90, 160, 0.25);
}}

QSpinBox {{
    background-color: {COLORS["bg_input"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 5px;
    padding: 8px 12px;
    min-height: 22px;
}}
QSpinBox:focus {{
    border-color: {COLORS["accent"]};
}}

QTextEdit {{
    background-color: rgba(255, 255, 255, 175);
    border: 1px solid {COLORS["border"]};
    border-radius: 6px;
    padding: 12px;
}}

QTextBrowser {{
    background-color: rgba(255, 255, 255, 145);
    border: 1px solid {COLORS["border_light"]};
    border-radius: 7px;
    padding: 22px;
}}

QFrame#helpCard {{
    background: rgba(255, 255, 255, 160);
    border: 1px solid {COLORS["border_light"]};
    border-radius: 8px;
}}
QFrame#helpCard QTextBrowser {{
    border: none;
    background: transparent;
    padding: 8px 4px;
}}

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
    border-radius: 3px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background-color: rgba(150, 180, 210, 190);
    border-radius: 3px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background-color: rgba(30, 136, 212, 210);
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

/* Прямоугольные подсказки (скругление на Windows с нативным стилем часто не работает) */
QToolTip {{
    font-size: 12px;
    font-weight: normal;
    padding: 8px 12px;
    background-color: rgba(255, 255, 255, 245);
    border: 1px solid {COLORS["border"]};
    border-radius: 0px;
    color: {COLORS["text"]};
}}
"""


def apply_theme(app: "QApplication") -> None:
    """Применяет тему и базовый шрифт к приложению."""
    from ui.theme.fonts import setup_app_font

    setup_app_font(app)
    app.setStyleSheet(STYLESHEET)
