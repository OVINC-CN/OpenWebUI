import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from open_webui.config import (
    SMTP_USERNAME,
    SMTP_HOST,
    SMTP_PORT,
    SMTP_PASSWORD,
    SMTP_SENT_FROM,
)


def send_email(receiver: str, subject: str, body: str):
    message = MIMEMultipart()
    message["From"] = SMTP_SENT_FROM.value or SMTP_USERNAME.value
    message["To"] = receiver
    message["Subject"] = subject
    message.attach(MIMEText(body, "html"))

    port = str(SMTP_PORT.value)
    if port == "587":
        server = smtplib.SMTP(SMTP_HOST.value, int(port))
        server.starttls()
    elif port == "465":
        server = smtplib.SMTP_SSL(SMTP_HOST.value, int(port))
    else:
        raise ValueError(f"Invalid SMTP port {port}")

    try:
        server.login(SMTP_USERNAME.value, SMTP_PASSWORD.value)
        server.send_message(message)
    finally:
        server.quit()
