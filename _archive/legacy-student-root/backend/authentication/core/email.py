import os
import smtplib

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from dotenv import load_dotenv


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

    print("========================================")
    print("OTP EMAIL FUNCTION STARTED")
    print("========================================")

    if not SMTP_USERNAME:
        print("ERROR: SMTP_USERNAME is missing")
        return False

    if not SMTP_PASSWORD:
        print("ERROR: SMTP_PASSWORD is missing")
        return False

    if not MAIL_FROM:
        print("ERROR: MAIL_FROM is missing")
        return False

    print("SMTP Host:", SMTP_HOST)
    print("SMTP Port:", SMTP_PORT)
    print("Sender:", SMTP_USERNAME)
    print("Receiver:", to_email)

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

        print("Connecting to Gmail...")

        with smtplib.SMTP(
            SMTP_HOST,
            SMTP_PORT,
            timeout=30
        ) as server:

            print("Starting TLS...")

            server.starttls()

            print("Logging into Gmail...")

            server.login(
                SMTP_USERNAME,
                SMTP_PASSWORD
            )

            print("Sending OTP email...")

            server.sendmail(
                MAIL_FROM,
                to_email,
                message.as_string()
            )

        print("========================================")
        print("EMAIL SENT SUCCESSFULLY")
        print("========================================")

        return True

    except smtplib.SMTPAuthenticationError as e:

        print("========================================")
        print("GMAIL LOGIN FAILED")
        print("Check your Gmail App Password.")
        print("========================================")
        print(e)

        return False

    except smtplib.SMTPException as e:

        print("========================================")
        print("SMTP ERROR")
        print("========================================")
        print(e)

        return False

    except Exception as e:

        print("========================================")
        print("EMAIL ERROR")
        print("========================================")
        print(type(e).__name__)
        print(e)

        return False