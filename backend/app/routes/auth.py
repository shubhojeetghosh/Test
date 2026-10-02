# ============================================================
# AUTHENTICATION ROUTES
# File:
# C:\Users\user\quiz-platform\backend\app\routes\auth.py
# ============================================================

from datetime import datetime, timedelta
import secrets

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.rate_limit import enforce_rate_limit

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    hash_otp,
    verify_otp,
    decode_access_token,
)

from app.core.email import send_otp_email

from app.models import PasswordResetOTP, User

security = HTTPBearer()

def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> int:
    token = credentials.credentials

    try:
        payload = decode_access_token(token)

        user_id = payload.get("sub")

        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token",
            )

        user_id = int(user_id)

    except HTTPException:
        raise

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        )

    user = db.scalar(select(User).where(User.id == user_id))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        )
    if str(user.role).strip().lower() != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Student account required",
        )
    return user_id

# ============================================================
# ROUTER
# ============================================================

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


# ============================================================
# REQUEST SCHEMAS
# ============================================================

class RegisterRequest(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=100
    )

    email: EmailStr

    password: str = Field(
        min_length=8
    )


class LoginRequest(BaseModel):
    email: EmailStr

    password: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class VerifyOTPRequest(BaseModel):
    email: EmailStr

    otp: str = Field(
        min_length=6,
        max_length=6
    )


class ResetPasswordRequest(BaseModel):
    email: EmailStr

    otp: str = Field(
        min_length=6,
        max_length=6
    )

    new_password: str = Field(
        min_length=8
    )


@router.post("/register")
def register(
    data: RegisterRequest,
    request: Request,
    db: Session = Depends(get_db)
):

    normalized_email = str(data.email).strip().lower()
    enforce_rate_limit(
        db,
        scope="student-register",
        subject=normalized_email,
        limit=3,
        window_seconds=3600,
    )

    # 1. Check whether email already exists
    existing_user = (
        db.query(User)
        .filter(User.email == normalized_email)
        .first()
    )

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # 2. Hash password
    hashed_password = hash_password(data.password)

    # 3. Create user
    new_user = User(
        name=data.name,
        email=normalized_email,
        password_hash=hashed_password
    )

    # 4. Save user
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        ) from exc
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not create the account. Please try again.",
        ) from exc

    # 5. Return response
    return {
        "message": "User registered successfully",
        "user_id": new_user.id,
        "name": new_user.name,
        "email": new_user.email
    }

# ============================================================
# LOGIN
# ============================================================

@router.post("/login")
def login(
    data: LoginRequest,
    request: Request,
    db: Session = Depends(get_db)
):

    # --------------------------------------------------------
    # 1. Find user
    # --------------------------------------------------------

    normalized_email = str(data.email).strip().lower()
    enforce_rate_limit(
        db,
        scope="student-login",
        subject=normalized_email,
        limit=10,
        window_seconds=900,
    )
    user = (
        db.query(User)
        .filter(User.email == normalized_email)
        .first()
    )

    if not user:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    if str(user.role).strip().lower() != "student":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Use the Admin portal to sign in to this account.",
        )

    # --------------------------------------------------------
    # 2. Verify password
    # --------------------------------------------------------

    password_valid = verify_password(
        data.password,
        user.password_hash
    )

    if not password_valid:

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    # --------------------------------------------------------
    # 3. Create JWT
    # --------------------------------------------------------

    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "email": user.email
        }
    )

    # --------------------------------------------------------
    # 4. Return token + user information
    # --------------------------------------------------------

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role
    }

# ============================================================
# GET CURRENT USER PROFILE
# ============================================================

@router.get("/profile")
def get_profile(
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    user = db.scalar(select(User).where(User.id == current_user_id))
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        )
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
    }

# ============================================================
# FORGOT PASSWORD
# ============================================================

@router.post("/forgot-password")
def forgot_password(
    data: ForgotPasswordRequest,
    request: Request,
    db: Session = Depends(get_db)
):

    # --------------------------------------------------------
    # 1. Find user
    # --------------------------------------------------------

    normalized_email = str(data.email).strip().lower()
    enforce_rate_limit(
        db,
        scope="student-password-reset-start",
        subject=normalized_email,
        limit=3,
        window_seconds=3600,
    )
    user = (
        db.query(User)
        .filter(User.email == normalized_email)
        .first()
    )

    if not user or str(user.role).strip().lower() != "student":

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # --------------------------------------------------------
    # 2. Invalidate previous unused OTPs
    #
    # This makes the newest OTP the only active OTP.
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # 3. Generate 6-digit OTP
    # --------------------------------------------------------

    otp = f"{secrets.randbelow(1000000):06d}"

    # --------------------------------------------------------
    # 4. Hash OTP
    # --------------------------------------------------------

    otp_hash = hash_otp(otp)

    # --------------------------------------------------------
    # 5. OTP expires after 10 minutes
    # --------------------------------------------------------

    expires_at = datetime.utcnow() + timedelta(
        minutes=10
    )

    # --------------------------------------------------------
    # 6. Create OTP database record
    # --------------------------------------------------------

    otp_record = PasswordResetOTP(
        user_id=user.id,
        otp_hash=otp_hash,
        expires_at=expires_at,
        attempts=0,
        used=False
    )

    db.add(otp_record)

    db.commit()

    # --------------------------------------------------------
    # 7. Send OTP email
    # --------------------------------------------------------

    email_sent = send_otp_email(
        data.email,
        otp
    )

    if not email_sent:

        # Remove the OTP record if email failed
        db.delete(otp_record)

        db.commit()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send OTP email"
        )

    # --------------------------------------------------------
    # 8. Response
    # --------------------------------------------------------

    return {
        "message": "OTP sent successfully",
        "email": data.email,
        "expires_in_minutes": 10
    }


# ============================================================
# VERIFY OTP
# ============================================================

@router.post("/verify-otp")
def verify_otp_endpoint(
    data: VerifyOTPRequest,
    request: Request,
    db: Session = Depends(get_db)
):

    # --------------------------------------------------------
    # 1. Find user
    # --------------------------------------------------------

    normalized_email = str(data.email).strip().lower()
    enforce_rate_limit(
        db,
        scope="student-otp-verify",
        subject=normalized_email,
        limit=8,
        window_seconds=900,
    )
    user = (
        db.query(User)
        .filter(User.email == normalized_email)
        .first()
    )

    if not user or str(user.role).strip().lower() != "student":

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # --------------------------------------------------------
    # 2. Find latest unused OTP
    # --------------------------------------------------------

    otp_record = (
        db.query(PasswordResetOTP)
        .filter(
            PasswordResetOTP.user_id == user.id,
            PasswordResetOTP.used == False
        )
        .order_by(
            PasswordResetOTP.created_at.desc()
        )
        .first()
    )

    if not otp_record:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP not found or already used"
        )

    # --------------------------------------------------------
    # 3. Check expiration FIRST
    # --------------------------------------------------------

    if otp_record.expires_at < datetime.utcnow():

        otp_record.used = True

        db.commit()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP has expired"
        )

    # --------------------------------------------------------
    # 4. Check maximum attempts
    # --------------------------------------------------------

    if otp_record.attempts >= 5:

        otp_record.used = True

        db.commit()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Too many incorrect OTP attempts"
        )

    # --------------------------------------------------------
    # 5. Verify OTP
    # --------------------------------------------------------

    if not verify_otp(
        data.otp,
        otp_record.otp_hash
    ):

        otp_record.attempts += 1

        db.commit()

        remaining_attempts = 5 - otp_record.attempts

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid OTP. {remaining_attempts} attempts remaining."
        )

    # --------------------------------------------------------
    # IMPORTANT:
    #
    # DO NOT set:
    #
    # otp_record.used = True
    #
    # here.
    #
    # The same OTP must still be available to
    # /reset-password.
    # --------------------------------------------------------

    return {
        "message": "OTP verified successfully",
        "email": data.email
    }


# ============================================================
# RESET PASSWORD
# ============================================================

@router.post("/reset-password")
def reset_password(
    data: ResetPasswordRequest,
    request: Request,
    db: Session = Depends(get_db)
):

    # --------------------------------------------------------
    # 1. Find user
    # --------------------------------------------------------

    normalized_email = str(data.email).strip().lower()
    enforce_rate_limit(
        db,
        scope="student-password-reset-complete",
        subject=normalized_email,
        limit=6,
        window_seconds=900,
    )
    user = (
        db.query(User)
        .filter(User.email == normalized_email)
        .first()
    )

    if not user or str(user.role).strip().lower() != "student":

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # --------------------------------------------------------
    # 2. Find latest unused OTP
    # --------------------------------------------------------

    otp_record = (
        db.query(PasswordResetOTP)
        .filter(
            PasswordResetOTP.user_id == user.id,
            PasswordResetOTP.used == False
        )
        .order_by(
            PasswordResetOTP.created_at.desc()
        )
        .first()
    )

    if not otp_record:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP not found or already used"
        )

    # --------------------------------------------------------
    # 3. Check expiration
    # --------------------------------------------------------

    if otp_record.expires_at < datetime.utcnow():

        otp_record.used = True

        db.commit()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP has expired"
        )

    # --------------------------------------------------------
    # 4. Check attempts
    # --------------------------------------------------------

    if otp_record.attempts >= 5:

        otp_record.used = True

        db.commit()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Too many incorrect OTP attempts"
        )

    # --------------------------------------------------------
    # 5. Verify OTP again
    #
    # This is important for security.
    # --------------------------------------------------------

    if not verify_otp(
        data.otp,
        otp_record.otp_hash
    ):

        otp_record.attempts += 1

        db.commit()

        remaining_attempts = 5 - otp_record.attempts

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid OTP. {remaining_attempts} attempts remaining."
        )

    # --------------------------------------------------------
    # 6. Hash new password
    # --------------------------------------------------------

    new_password_hash = hash_password(
        data.new_password
    )

    # --------------------------------------------------------
    # 7. Update password
    # --------------------------------------------------------

    user.password_hash = new_password_hash

    # --------------------------------------------------------
    # 8. Mark OTP as USED
    #
    # This is where the OTP should become unusable.
    # --------------------------------------------------------

    otp_record.used = True

    # --------------------------------------------------------
    # 9. Save everything
    # --------------------------------------------------------

    try:

        db.commit()

    except Exception:

        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset password"
        )

    # --------------------------------------------------------
    # 10. Return response
    # --------------------------------------------------------

    return {
        "message": "Password reset successfully",
        "email": data.email
    }

