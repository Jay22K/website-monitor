import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import date

from app.config import settings

logger = logging.getLogger(__name__)


def send_report_email(report_body: str, report_date: date | None = None) -> None:
    """
    Send the monitoring report via SMTP.

    If SMTP credentials are not configured the function logs a warning and
    returns without raising so the scheduler is not disrupted.
    """
    if not all([settings.SMTP_USER, settings.SMTP_PASSWORD, settings.EMAIL_TO]):
        logger.warning(
            "Email not configured. Set SMTP_USER, SMTP_PASSWORD and EMAIL_TO to enable reports."
        )
        return

    if report_date is None:
        report_date = date.today()

    subject = f"Website Monitoring Report — {report_date.isoformat()}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.EMAIL_FROM or settings.SMTP_USER
    msg["To"] = settings.EMAIL_TO

    # Plain-text part
    msg.attach(MIMEText(report_body, "plain"))

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(
                msg["From"],
                [settings.EMAIL_TO],
                msg.as_string(),
            )
        logger.info("Monitoring report sent to %s", settings.EMAIL_TO)
    except smtplib.SMTPException as exc:
        logger.error("Failed to send monitoring report: %s", exc)
        raise
