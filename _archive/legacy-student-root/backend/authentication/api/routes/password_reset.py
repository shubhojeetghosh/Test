from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from backend.authentication.core.database import get_db
from backend.authentication.core.email import send_otp_email
from backend.authentication.core.otp import generate_otp
from backend.authentication.core.security import hash_otp
from backend.authentication.models.password_reset_otp import PasswordResetOTP
from backend.authentication.models.user import User
from backend.authentication.schemas.password_reset import ForgotPasswordRequest


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


@router.post("/forgot-password")
def forgot_password(
    request: ForgotPasswordRequest,
    db: Session = Depends(get_db)
):
    # 1. Find user by email
    user = (
        db.query(User)
        .filter(User.email == request.email)
        .first()
    )

    # 2. Always return a generic message
    # This prevents revealing whether an email exists.
    if not user:
        return {
            "message": (
                "If an account exists with this email, "
                "an OTP has been sent."
            )
        }

    # 3. Generate OTP
    otp = generate_otp()

    # 4. Hash OTP
    otp_hash = hash_otp(otp)

    # 5. Set expiry to 10 minutes
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=10)

    # 6. Invalidate previous unused OTPs
    old_otps = (
        db.query(PasswordResetOTP)
        .filter(
            PasswordResetOTP.user_id == user.id,
            PasswordResetOTP.used == False
        )
        .all()
    )

    for old_otp in old_otps:
        old_otp.used = True

    # 7. Create new OTP record
    otp_record = PasswordResetOTP(
        user_id=user.id,
        otp_hash=otp_hash,
        expires_at=expires_at,
        attempts=0,
        used=False
    )

    db.add(otp_record)
    db.commit()

    # 8. Send OTP by email
    email_sent = send_otp_email(
        request.email,
        otp
    )

    if not email_sent:
        return {
            "message": "Unable to send OTP email."
        }

    return {
        "message": (
            "If an account exists with this email, "
            "an OTP has been sent."
        )
    }
