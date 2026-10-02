import logging
import os
import smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from dotenv import load_dotenv

logger = logging.getLogger(__name__)


# ============================================================
# LOAD .ENV
# ============================================================

load_dotenv()


# ============================================================
# SMTP SETTINGS
# ============================================================

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))

SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

MAIL_FROM = os.getenv(
    "MAIL_FROM",
    SMTP_USERNAME
)


# ============================================================
# SEND OTP EMAIL
# ============================================================

def send_otp_email(
    to_email: str,
    otp: str
) -> bool:

    if not SMTP_USERNAME:
        logger.error("Student password reset email is not configured: SMTP_USERNAME missing")
        return False

    if not SMTP_PASSWORD:
        logger.error("Student password reset email is not configured: SMTP_PASSWORD missing")
        return False

    if not MAIL_FROM:
        logger.error("Student password reset email is not configured: MAIL_FROM missing")
        return False

    subject = "Quiz Platform - Password Reset OTP"

    body = f"""
Hello,

You requested to reset your password for Quiz Platform.

Your OTP is:

{otp}

This OTP will expire in 10 minutes.

If you did not request a password reset, please ignore this email.

Regards,
Quiz Platform Team
"""

    message = MIMEMultipart()

    message["From"] = MAIL_FROM
    message["To"] = to_email
    message["Subject"] = subject

    message.attach(
        MIMEText(
            body,
            "plain"
        )
    )

    try:

        with smtplib.SMTP(
            SMTP_HOST,
            SMTP_PORT,
            timeout=30
        ) as server:

            server.starttls()

            server.login(
                SMTP_USERNAME,
                SMTP_PASSWORD
            )


            server.sendmail(
                MAIL_FROM,
                to_email,
                message.as_string()
            )

        logger.info("Student password reset email sent")

        return True

    except smtplib.SMTPAuthenticationError as e:

        logger.error("Student password reset email authentication failed")

        return False

    except smtplib.SMTPException as e:

        logger.error("Student password reset email failed (%s)", type(e).__name__)

        return False

    except Exception as e:

        logger.exception("Student password reset email failed")

        return False
