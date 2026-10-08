"""Student email delivery, using the project's existing SMTP environment."""

import logging
import os
import smtplib
from email.utils import formataddr
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from dotenv import load_dotenv

logger = logging.getLogger(__name__)
load_dotenv()

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
OTP_EXPIRE_MINUTES = max(1, int(os.getenv("OTP_EXPIRE_MINUTES", "5")))
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
MAIL_FROM = os.getenv("SMTP_FROM_EMAIL", os.getenv("MAIL_FROM", SMTP_USERNAME))
MAIL_FROM_NAME = "EPS TOPIK EXAM"


def _send_email(to_email: str, subject: str, body: str, purpose: str) -> bool:
    if not SMTP_USERNAME or not SMTP_PASSWORD or not MAIL_FROM:
        logger.error("Student %s email is not configured", purpose)
        return False

    message = MIMEMultipart()
    message["From"] = formataddr((MAIL_FROM_NAME, MAIL_FROM))
    message["To"] = to_email
    message["Subject"] = subject
    message.attach(MIMEText(body.strip(), "plain"))

    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=30) as server:
            server.starttls()
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.sendmail(MAIL_FROM, to_email, message.as_string())
        logger.info("Student %s email sent", purpose)
        return True
    except smtplib.SMTPAuthenticationError:
        logger.error("Student %s email authentication failed", purpose)
    except smtplib.SMTPException as exc:
        logger.error("Student %s email failed (%s)", purpose, type(exc).__name__)
    except Exception:
        logger.exception("Student %s email failed", purpose)
    return False


def send_otp_email(to_email: str, otp: str) -> bool:
    """Send the existing student password reset OTP email."""
    return _send_email(
        to_email,
        "Quiz Platform - Password Reset OTP",
        f"""Hello,

You requested to reset your password for Quiz Platform.

Your OTP is:

{otp}

This OTP will expire in 10 minutes.

If you did not request a password reset, please ignore this email.

Regards,
Quiz Platform Team""",
        "password reset",
    )


def send_registration_otp_email(to_email: str, otp: str) -> bool:
    """Send a registration verification code without logging its value."""
    return _send_email(
        to_email,
        "Verify your EPS-TOPIK account",
        f"""Hello,

Your EPS-TOPIK verification code is:

{otp}

This code expires in {OTP_EXPIRE_MINUTES} minutes. If you did not request this registration,
you can ignore this email.

Regards,
EPS-TOPIK Team""",
        "registration verification",
    )
