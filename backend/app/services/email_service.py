import smtplib
from email.message import EmailMessage

from app.core.config import settings
from app.core.logging import logger


def send_email(to: str, subject: str, body: str) -> str:
    if settings.email_mode == "console":
        logger.info("email.console", to=to, subject=subject, body=body)
        return "console"
    if not settings.smtp_host:
        raise RuntimeError("SMTP_HOST is required when EMAIL_MODE=smtp")
    message = EmailMessage()
    message["From"] = settings.smtp_from_email
    message["To"] = to
    message["Subject"] = subject
    message.set_content(body)
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as smtp:
        smtp.starttls()
        if settings.smtp_username:
            smtp.login(settings.smtp_username, settings.smtp_password)
        smtp.send_message(message)
    return message["Message-ID"] or "smtp"
