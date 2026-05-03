from urllib.parse import quote
import platform

from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QTextEdit,
    QGroupBox,
)

from ui.pages.base import BasePage
from ui.widgets import section_title

FEEDBACK_EMAIL = "app.system@gmail.com"
FEEDBACK_SUBJECT = "Обратная связь — ITMetric"


def _get_body_template() -> str:
    return (
        "Здравствуйте!\n\n"
        "[Опишите вашу проблему, предложение или вопрос]\n\n"
        "---\n"
        f"Система: {platform.system()} {platform.release()}\n"
        f"Пользователь: {platform.node()}"
    )


class FeedbackPage(BasePage):
    def __init__(self):
        super().__init__()

        root = self.build_root(
            "Обратная связь",
            "Сообщение откроется в выбранном веб-клиенте почты.",
            spacing=12,
        )

        info = QLabel(
            "Напишите сообщение и выберите почтовый сервис — откроется веб-интерфейс "
            "с уже заполненным письмом."
        )
        info.setWordWrap(True)
        root.addWidget(info)

        box = QGroupBox()
        box.setTitle("")
        lay = QVBoxLayout(box)
        lay.addWidget(section_title("Написать письмо"))
        self._text = QTextEdit()
        self._text.setPlaceholderText("Введите текст письма...")
        self._text.setPlainText(_get_body_template())
        self._text.setMaximumHeight(120)
        lay.addWidget(self._text)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        btn_gmail = QPushButton("Gmail")
        btn_gmail.clicked.connect(lambda: self._open_webmail("gmail"))
        btn_mailru = QPushButton("Mail.ru")
        btn_mailru.clicked.connect(lambda: self._open_webmail("mailru"))
        btn_yandex = QPushButton("Яндекс")
        btn_yandex.clicked.connect(lambda: self._open_webmail("yandex"))
        btn_row.addWidget(btn_gmail)
        btn_row.addWidget(btn_mailru)
        btn_row.addWidget(btn_yandex)
        btn_row.addStretch()
        lay.addLayout(btn_row)
        root.addWidget(box)

        root.addWidget(QLabel(f"Получатель: {FEEDBACK_EMAIL}"))

        root.addStretch(1)

    def _open_webmail(self, service: str):
        body = self._text.toPlainText() or _get_body_template()
        body_encoded = quote(body, safe="")
        subject_encoded = quote(FEEDBACK_SUBJECT, safe="")
        email_encoded = quote(FEEDBACK_EMAIL, safe="")

        if service == "gmail":
            url = (
                f"https://mail.google.com/mail/?view=cm&fs=1"
                f"&to={email_encoded}&su={subject_encoded}&body={body_encoded}"
            )
        elif service == "mailru":
            url = (
                f"https://e.mail.ru/compose/"
                f"?to={email_encoded}&subject={subject_encoded}&body={body_encoded}"
            )
        elif service == "yandex":
            url = (
                f"https://mail.yandex.ru/compose/"
                f"?to={email_encoded}&subject={subject_encoded}&body={body_encoded}"
            )
        else:
            return

        QDesktopServices.openUrl(QUrl(url))
