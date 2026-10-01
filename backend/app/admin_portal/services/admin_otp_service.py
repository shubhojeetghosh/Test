import hashlib
import secrets
from datetime import datetime, timedelta

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.admin_portal.models.email_otp import EmailOTP
from app.admin_portal.services.email_service import (
    send_otp_email,
    send_admin_approval_email,
)
from app.admin_portal.core.config import settings


# =========================================================
# SETTINGS
# =========================================================

ADMIN_OTP_EXPIRY_MINUTES = 10


# =========================================================
# OTP HELPERS
# =========================================================

def hash_otp(otp: str) -> str:
    """
    Hash an OTP before storing it in the database.
    """

    return hashlib.sha256(
        otp.encode("utf-8")
    ).hexdigest()


def generate_otp() -> str:
    """
    Generate a secure 6-digit OTP.
    """

    return f"{secrets.randbelow(1_000_000):06d}"


# =========================================================
# SEND PERSONAL OTP
# =========================================================

def create_personal_admin_otp(
    db: Session,
    personal_email: str,
) -> None:
    """
    Generate and send OTP #1.

    This OTP is sent ONLY to the applicant's
    personal email address.
    """

    personal_email = personal_email.lower().strip()

    # -----------------------------------------------------
    # Remove any previous personal OTP
    # -----------------------------------------------------

    db.execute(
        delete(EmailOTP).where(
            EmailOTP.email == personal_email,
            EmailOTP.purpose == "ADMIN_PERSONAL",
        )
    )

    # -----------------------------------------------------
    # Generate new OTP
    # -----------------------------------------------------

    otp = generate_otp()

    # -----------------------------------------------------
    # Store hashed OTP
    # -----------------------------------------------------

    otp_record = EmailOTP(
        email=personal_email,
        otp_hash=hash_otp(otp),
        purpose="ADMIN_PERSONAL",
        expires_at=(
            datetime.utcnow()
            + timedelta(minutes=ADMIN_OTP_EXPIRY_MINUTES)
        ),
        verified=False,
    )

    db.add(otp_record)
    db.commit()

    # -----------------------------------------------------
    # OTP #1
    #
    # ONLY applicant receives this OTP.
    # -----------------------------------------------------

    send_otp_email(
        recipient_email=personal_email,
        otp=otp,
    )


# =========================================================
# VERIFY PERSONAL OTP
# =========================================================

def verify_personal_admin_otp(
    db: Session,
    personal_email: str,
    otp: str,
) -> bool:
    """
    Verify OTP #1 belonging to the applicant.
    """

    personal_email = personal_email.lower().strip()

    record = db.scalar(
        select(EmailOTP)
        .where(
            EmailOTP.email == personal_email,
            EmailOTP.purpose == "ADMIN_PERSONAL",
            EmailOTP.verified == False,
        )
        .order_by(
            EmailOTP.id.desc()
        )
    )

    # -----------------------------------------------------
    # OTP record not found
    # -----------------------------------------------------

    if record is None:
        return False

    # -----------------------------------------------------
    # OTP expired
    # -----------------------------------------------------

    if datetime.utcnow() > record.expires_at:
        return False

    # -----------------------------------------------------
    # OTP does not match
    # -----------------------------------------------------

    if hash_otp(otp) != record.otp_hash:
        return False

    # -----------------------------------------------------
    # Mark OTP as verified
    # -----------------------------------------------------

    record.verified = True

    db.commit()

    return True


# =========================================================
# SEND ADMIN APPROVAL OTP
# =========================================================

def create_admin_approval_otp(
    db: Session,
    personal_email: str,
    applicant_name: str | None = None,
) -> None:
    """
    Generate OTP #2 for Admin Registration approval.

    The approval OTP is sent ONLY to:

    1. Main Admin
    2. Developer

    It is NOT sent to:
    - Applicant
    - Existing admins
    - Students
    - Teachers
    - Any other email address
    """

    personal_email = personal_email.lower().strip()

    # -----------------------------------------------------
    # Remove previous approval OTP for this applicant
    # -----------------------------------------------------

    db.execute(
        delete(EmailOTP).where(
            EmailOTP.email == personal_email,
            EmailOTP.purpose == "ADMIN_APPROVAL",
        )
    )

    # -----------------------------------------------------
    # Generate approval OTP
    # -----------------------------------------------------

    otp = generate_otp()

    # -----------------------------------------------------
    # Store hashed approval OTP
    # -----------------------------------------------------

    otp_record = EmailOTP(
        email=personal_email,
        otp_hash=hash_otp(otp),
        purpose="ADMIN_APPROVAL",
        expires_at=(
            datetime.utcnow()
            + timedelta(minutes=ADMIN_OTP_EXPIRY_MINUTES)
        ),
        verified=False,
    )

    db.add(otp_record)
    db.commit()

    # =====================================================
    # AUTHORIZED APPROVAL RECIPIENTS
    # =====================================================
    #
    # ONLY these two configured addresses receive
    # the Admin Registration approval OTP.
    #
    # Existing admins are deliberately NOT included.
    #
    # =====================================================

    approval_recipients = [
        settings.ADMIN_EMAIL,
        settings.DEVELOPER_EMAIL,
    ]

    # -----------------------------------------------------
    # Normalize and remove duplicate addresses
    # -----------------------------------------------------

    approval_recipients = list(
        dict.fromkeys(
            email.lower().strip()
            for email in approval_recipients
            if email and email.strip()
        )
    )

    # -----------------------------------------------------
    # Send the SAME approval OTP to both authorities.
    #
    # Each email also contains:
    # - Applicant name
    # - Applicant email
    # - Approval OTP
    # -----------------------------------------------------

    for recipient_email in approval_recipients:

        send_admin_approval_email(
            recipient_email=recipient_email,
            otp=otp,
            applicant_email=personal_email,
            applicant_name=applicant_name,
        )


# =========================================================
# VERIFY ADMIN APPROVAL OTP
# =========================================================

def verify_admin_approval_otp(
    db: Session,
    personal_email: str,
    otp: str,
) -> bool:
    """
    Verify OTP #2 for the specific Admin Registration
    request identified by personal_email.
    """

    personal_email = personal_email.lower().strip()

    record = db.scalar(
        select(EmailOTP)
        .where(
            EmailOTP.email == personal_email,
            EmailOTP.purpose == "ADMIN_APPROVAL",
            EmailOTP.verified == False,
        )
        .order_by(
            EmailOTP.id.desc()
        )
    )

    # -----------------------------------------------------
    # OTP record not found
    # -----------------------------------------------------

    if record is None:
        return False

    # -----------------------------------------------------
    # OTP expired
    # -----------------------------------------------------

    if datetime.utcnow() > record.expires_at:
        return False

    # -----------------------------------------------------
    # OTP does not match
    # -----------------------------------------------------

    if hash_otp(otp) != record.otp_hash:
        return False

    # -----------------------------------------------------
    # Mark OTP as verified
    # -----------------------------------------------------

    record.verified = True

    db.commit()

    return True
