import hashlib
import secrets
from datetime import datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.admin_portal.core.config import settings
from app.admin_portal.models.email_otp import EmailOTP
from app.admin_portal.services.email_service import send_otp_email


OTP_EXPIRY_MINUTES = 10


# =========================================================
# OTP HASHING
# =========================================================

def hash_otp(otp: str) -> str:
    return hashlib.sha256(
        otp.encode("utf-8")
    ).hexdigest()


# =========================================================
# OTP GENERATION
# =========================================================

def generate_otp() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


# =========================================================
# NORMAL OTP
# Used for student registration/password recovery
# =========================================================

def create_and_send_otp(
    db: Session,
    email: str,
    purpose: str,
) -> None:

    # Remove previous OTPs for this email and purpose
    db.execute(
        delete(EmailOTP).where(
            EmailOTP.email == email,
            EmailOTP.purpose == purpose,
        )
    )

    # Generate OTP
    otp = generate_otp()

    # Store hashed OTP
    otp_record = EmailOTP(
        email=email,
        otp_hash=hash_otp(otp),
        purpose=purpose,
        expires_at=datetime.utcnow()
        + timedelta(minutes=OTP_EXPIRY_MINUTES),
        verified=False,
    )

    db.add(otp_record)
    db.commit()

    # Send OTP to user's email
    send_otp_email(
        recipient_email=email,
        otp=otp,
    )


# =========================================================
# NORMAL OTP VERIFICATION
# =========================================================

def verify_otp(
    db: Session,
    email: str,
    otp: str,
    purpose: str,
) -> bool:

    record = db.scalar(
        select(EmailOTP)
        .where(
            EmailOTP.email == email,
            EmailOTP.purpose == purpose,
            EmailOTP.verified == False,
        )
        .order_by(EmailOTP.id.desc())
    )

    if record is None:
        return False

    # Check expiry
    if datetime.utcnow() > record.expires_at:
        return False

    # Check OTP
    if hash_otp(otp) != record.otp_hash:
        return False

    # Mark verified
    record.verified = True

    db.commit()

    return True


# =========================================================
# ADMIN OTP
#
# Generates ONE OTP and sends the SAME OTP to:
#
# ADMIN_EMAIL_1
# ADMIN_EMAIL_2
#
# This OTP is used for administrator verification.
# =========================================================

def create_and_send_admin_otp(
    db: Session,
    purpose: str,
) -> None:

    # Remove previous admin OTP
    db.execute(
        delete(EmailOTP).where(
            EmailOTP.purpose == purpose,
        )
    )

    # Generate ONE OTP
    otp = generate_otp()

    # Store the OTP against the main admin email
    otp_record = EmailOTP(
        email=settings.ADMIN_EMAIL_1,
        otp_hash=hash_otp(otp),
        purpose=purpose,
        expires_at=datetime.utcnow()
        + timedelta(minutes=OTP_EXPIRY_MINUTES),
        verified=False,
    )

    db.add(otp_record)
    db.commit()

    # -----------------------------------------------------
    # Send SAME OTP to main admin
    # -----------------------------------------------------

    send_otp_email(
        recipient_email=settings.ADMIN_EMAIL_1,
        otp=otp,
    )

    # -----------------------------------------------------
    # Send SAME OTP to developer
    # -----------------------------------------------------

    send_otp_email(
        recipient_email=settings.ADMIN_EMAIL_2,
        otp=otp,
    )


# =========================================================
# ADMIN OTP VERIFICATION
#
# The user enters the OTP received by the admin/developer.
# The OTP is stored against ADMIN_EMAIL_1.
# =========================================================

def verify_admin_otp(
    db: Session,
    otp: str,
    purpose: str,
) -> bool:

    record = db.scalar(
        select(EmailOTP)
        .where(
            EmailOTP.email == settings.ADMIN_EMAIL_1,
            EmailOTP.purpose == purpose,
            EmailOTP.verified == False,
        )
        .order_by(EmailOTP.id.desc())
    )

    if record is None:
        return False

    # Check expiry
    if datetime.utcnow() > record.expires_at:
        return False

    # Check OTP
    if hash_otp(otp) != record.otp_hash:
        return False

    # Mark verified
    record.verified = True

    db.commit()

    return True
