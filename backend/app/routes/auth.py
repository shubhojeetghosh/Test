# ============================================================
# AUTHENTICATION ROUTES
# File:
# C:\Users\user\quiz-platform\backend\app\routes\auth.py
# ============================================================

from datetime import datetime, timedelta, timezone
import logging
import secrets

import httpx
from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from email_validator import EmailNotValidError, validate_email
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import settings
from app.core.rate_limit import enforce_rate_limit

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    hash_otp,
    verify_otp,
    decode_access_token,
)

from app.core.email import send_otp_email, send_registration_otp_email

from app.models import PasswordResetOTP, PendingStudentRegistration, User
from app.services.media_storage import resolve_media_urls, upload_media

logger = logging.getLogger(__name__)
security = HTTPBearer()
MAX_PROFILE_PHOTO_BYTES = 2 * 1024 * 1024


class StudentProfileUpdateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=100)


class StudentPasswordChangeRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)

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

    if not user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Please verify your email first. Open Register and enter this email to receive a verification code.",
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
    otp: str = Field(pattern=r"^\d{6}$")


class VerifyRegistrationOTPRequest(BaseModel):
    email: EmailStr
    otp: str = Field(pattern=r"^\d{6}$")


class ResetPasswordRequest(BaseModel):
    email: EmailStr

    otp: str = Field(
        min_length=6,
        max_length=6
    )

    new_password: str = Field(
        min_length=8
    )


def _validate_registration_email(email: str) -> str:
    """Validate syntax, mail domain, and mailbox before any registration OTP is sent."""
    try:
        validated = validate_email(
            email,
            check_deliverability=True,
            timeout=5,
        )
    except EmailNotValidError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "Please use a valid email address with a domain that can "
                "receive email."
            ),
        ) from exc

    api_key = settings.ZEROBOUNCE_API_KEY
    if not api_key:
        logger.error("Registration blocked because mailbox validation is not configured")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Email verification is temporarily unavailable. Please try again later.",
        )

    try:
        response = httpx.post(
            "https://api.zerobounce.net/v2/validate",
            data={
                "api_key": api_key,
                "email": validated.normalized,
                "ip_address": "",
                "timeout": 15,
            },
            timeout=httpx.Timeout(20.0, connect=5.0),
        )
        result = response.json()
    except (httpx.HTTPError, ValueError):
        logger.warning("Registration mailbox validation service is unavailable")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="We could not verify this email right now. Please try again shortly.",
        ) from None

    if response.status_code != 200 or not isinstance(result, dict) or result.get("error"):
        logger.warning(
            "Registration mailbox validation failed with status %s",
            response.status_code,
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="We could not verify this email right now. Please try again shortly.",
        )

    if str(result.get("status", "")).strip().lower() != "valid":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid email address. Please enter a working email address that you can access.",
        )

    return validated.normalized


@router.post("/register")
def register(
    data: RegisterRequest,
    request: Request,
    db: Session = Depends(get_db)
):

    name = data.name.strip()
    if len(name) < 2:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Please enter your full name.",
        )

    normalized_email = str(data.email).strip().lower()
    enforce_rate_limit(
        db,
        scope="student-register",
        subject=normalized_email,
        limit=3,
        window_seconds=3600,
    )

    existing_user = db.scalar(select(User).where(User.email == normalized_email))
    if existing_user and existing_user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    normalized_email = _validate_registration_email(normalized_email)

    # Legacy pending accounts used to be inserted into `users` before email
    # verification. Keep their existing OTPs usable, but never create new
    # unverified rows in the registered-users table.
    if existing_user:
        _send_registration_code(db, existing_user)
        return {
            "message": "A verification code has been sent to your email.",
            "email": normalized_email,
            "requires_verification": True,
        }

    pending = db.scalar(
        select(PendingStudentRegistration)
        .where(PendingStudentRegistration.email == normalized_email)
        .with_for_update()
    )
    if pending is None:
        pending = PendingStudentRegistration(
            name=name,
            email=normalized_email,
            password_hash=hash_password(data.password),
            otp_hash="pending",
            expires_at=datetime.now(timezone.utc).replace(tzinfo=None),
            attempts=0,
        )
        db.add(pending)
        db.flush()
    elif (datetime.now(timezone.utc).replace(tzinfo=None) - pending.created_at).total_seconds() < REGISTRATION_OTP_COOLDOWN_SECONDS:
        wait = max(
            1,
            int(REGISTRATION_OTP_COOLDOWN_SECONDS - (datetime.now(timezone.utc).replace(tzinfo=None) - pending.created_at).total_seconds()),
        )
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Please wait before requesting another verification code.",
            headers={"Retry-After": str(wait)},
        )

    _send_pending_registration_code(db, pending)
    return {
        "message": "A verification code has been sent to your email.",
        "email": normalized_email,
        "requires_verification": True,
    }


REGISTRATION_OTP_PURPOSE = "student_registration"
REGISTRATION_OTP_MINUTES = max(1, settings.OTP_EXPIRE_MINUTES)
REGISTRATION_OTP_COOLDOWN_SECONDS = max(1, settings.OTP_RESEND_COOLDOWN_SECONDS)
REGISTRATION_OTP_MAX_ATTEMPTS = max(1, settings.OTP_MAX_ATTEMPTS)


def _send_pending_registration_code(
    db: Session, pending: PendingStudentRegistration
) -> None:
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    enforce_rate_limit(
        db,
        scope="student-registration-resend",
        subject=pending.email,
        limit=5,
        window_seconds=3600,
    )
    code = f"{secrets.randbelow(1_000_000):06d}"
    pending.otp_hash = hash_otp(code)
    pending.expires_at = now + timedelta(minutes=REGISTRATION_OTP_MINUTES)
    pending.attempts = 0
    pending.created_at = now
    db.add(pending)
    db.commit()
    if not send_registration_otp_email(pending.email, code):
        db.delete(pending)
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="We could not send the verification email. Please check the address and try again.",
        )


def _send_registration_code(db: Session, user: User) -> None:
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    active_otp = db.scalar(
        select(PasswordResetOTP)
        .where(
            PasswordResetOTP.user_id == user.id,
            PasswordResetOTP.purpose == REGISTRATION_OTP_PURPOSE,
            PasswordResetOTP.used.is_(False),
        )
        .order_by(PasswordResetOTP.id.desc())
    )
    if active_otp and (now - active_otp.created_at).total_seconds() < REGISTRATION_OTP_COOLDOWN_SECONDS:
        wait = max(1, int(REGISTRATION_OTP_COOLDOWN_SECONDS - (now - active_otp.created_at).total_seconds()))
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Please wait before requesting another verification code.",
            headers={"Retry-After": str(wait)},
        )

    enforce_rate_limit(
        db,
        scope="student-registration-resend",
        subject=user.email,
        limit=5,
        window_seconds=3600,
    )
    if active_otp:
        active_otp.used = True

    code = f"{secrets.randbelow(1_000_000):06d}"
    otp_record = PasswordResetOTP(
        user_id=user.id,
        otp_hash=hash_otp(code),
        purpose=REGISTRATION_OTP_PURPOSE,
        expires_at=now + timedelta(minutes=REGISTRATION_OTP_MINUTES),
        attempts=0,
        used=False,
        created_at=now,
    )
    db.add(otp_record)
    db.commit()
    if not send_registration_otp_email(user.email, code):
        otp_record.used = True
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="We could not send the verification email. Please try again shortly.",
        )


@router.post("/verify-registration-otp")
def verify_registration_otp(
    data: VerifyRegistrationOTPRequest,
    db: Session = Depends(get_db),
):
    email = str(data.email).strip().lower()
    enforce_rate_limit(
        db,
        scope="student-registration-verify",
        subject=email,
        limit=10,
        window_seconds=3600,
    )
    pending = db.scalar(
        select(PendingStudentRegistration)
        .where(PendingStudentRegistration.email == email)
        .with_for_update()
    )
    if pending is not None:
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        if pending.expires_at <= now or pending.attempts >= REGISTRATION_OTP_MAX_ATTEMPTS:
            db.delete(pending)
            db.commit()
            raise HTTPException(status_code=400, detail="Invalid or expired verification code.")
        if not verify_otp(data.otp, pending.otp_hash):
            pending.attempts += 1
            if pending.attempts >= REGISTRATION_OTP_MAX_ATTEMPTS:
                db.delete(pending)
            db.commit()
            raise HTTPException(status_code=400, detail="Invalid or expired verification code.")

        user = User(
            name=pending.name,
            email=pending.email,
            password_hash=pending.password_hash,
            role="student",
            email_verified=True,
        )
        try:
            db.add(user)
            db.flush()
            db.delete(pending)
            db.commit()
            db.refresh(user)
        except IntegrityError as exc:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered. Please log in.",
            ) from exc

        token = create_access_token(
            {"sub": str(user.id), "email": user.email},
            expires_minutes=settings.STUDENT_ACCESS_TOKEN_EXPIRE_MINUTES,
        )
        return {
            "message": "Email verified successfully.",
            "access_token": token,
            "token_type": "bearer",
            "user_id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
        }

    # Complete older pending registrations that were stored as users before
    # this change. New registrations always use the pending table above.
    user = db.scalar(select(User).where(User.email == email).with_for_update())
    if user is None or str(user.role).strip().lower() != "student":
        raise HTTPException(status_code=400, detail="Invalid or expired verification code.")
    if user.email_verified:
        raise HTTPException(status_code=400, detail="This email is already verified. Please log in.")

    record = db.scalar(
        select(PasswordResetOTP)
        .where(
            PasswordResetOTP.user_id == user.id,
            PasswordResetOTP.purpose == REGISTRATION_OTP_PURPOSE,
            PasswordResetOTP.used.is_(False),
        )
        .order_by(PasswordResetOTP.id.desc())
        .with_for_update()
    )
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    if record is None or record.expires_at <= now or record.attempts >= REGISTRATION_OTP_MAX_ATTEMPTS:
        if record is not None:
            record.used = True
            db.commit()
        raise HTTPException(status_code=400, detail="Invalid or expired verification code.")

    if not verify_otp(data.otp, record.otp_hash):
        record.attempts += 1
        if record.attempts >= REGISTRATION_OTP_MAX_ATTEMPTS:
            record.used = True
        db.commit()
        raise HTTPException(status_code=400, detail="Invalid or expired verification code.")

    record.used = True
    user.email_verified = True
    db.commit()
    token = create_access_token(
        {"sub": str(user.id), "email": user.email},
        expires_minutes=settings.STUDENT_ACCESS_TOKEN_EXPIRE_MINUTES,
    )
    return {
        "message": "Email verified successfully.",
        "access_token": token,
        "token_type": "bearer",
        "user_id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
    }


@router.post("/resend-registration-otp")
def resend_registration_otp(
    data: ForgotPasswordRequest,
    db: Session = Depends(get_db),
):
    email = str(data.email).strip().lower()
    enforce_rate_limit(
        db,
        scope="student-registration-resend-request",
        subject=email,
        limit=5,
        window_seconds=3600,
    )
    pending = db.scalar(
        select(PendingStudentRegistration)
        .where(PendingStudentRegistration.email == email)
        .with_for_update()
    )
    if pending is not None:
        email = _validate_registration_email(email)
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        elapsed = (now - pending.created_at).total_seconds()
        if elapsed < REGISTRATION_OTP_COOLDOWN_SECONDS:
            wait = max(1, int(REGISTRATION_OTP_COOLDOWN_SECONDS - elapsed))
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Please wait before requesting another verification code.",
                headers={"Retry-After": str(wait)},
            )
        _send_pending_registration_code(db, pending)
        return {"message": "A new verification code has been sent to your email."}

    user = db.scalar(select(User).where(User.email == email))
    if user is None or str(user.role).strip().lower() != "student" or user.email_verified:
        # Avoid disclosing account state to unauthenticated callers.
        return {"message": "If registration is pending, a verification code will be sent."}
    email = _validate_registration_email(email)
    _send_registration_code(db, user)
    return {"message": "A new verification code has been sent to your email."}

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

    # Accounts already stored in `users` are registered accounts. The current
    # signup flow only creates a user after OTP verification, so an unverified
    # flag here identifies an older account from before that flow. Correct
    # password authentication is sufficient to restore that account; new
    # registrations remain in PendingStudentRegistration until OTP succeeds.
    if not user.email_verified:
        user.email_verified = True
        db.add(user)
        db.commit()
        db.refresh(user)

    # --------------------------------------------------------
    # 3. Create JWT
    # --------------------------------------------------------

    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "email": user.email
        },
        expires_minutes=settings.STUDENT_ACCESS_TOKEN_EXPIRE_MINUTES,
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
    try:
        signed_photo = resolve_media_urls([user.profile_photo_url]).get(
            user.profile_photo_url, user.profile_photo_url
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail="Profile photo is temporarily unavailable.") from exc
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "student_id": user.student_id or user.roll_no,
        "profile_photo_url": signed_photo,
    }


@router.put("/profile")
def update_profile(
    data: StudentProfileUpdateRequest,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    user = db.scalar(select(User).where(User.id == current_user_id))
    if user is None or str(user.role).strip().lower() != "student":
        raise HTTPException(status_code=404, detail="Student account not found.")
    name = data.name.strip()
    if not name:
        raise HTTPException(status_code=422, detail="Name cannot be empty.")
    user.name = name
    db.commit()
    return {"message": "Profile updated successfully.", "name": user.name}


@router.post("/profile/photo")
async def upload_profile_photo(
    photo: UploadFile = File(...),
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    user = db.scalar(select(User).where(User.id == current_user_id))
    if user is None or str(user.role).strip().lower() != "student":
        raise HTTPException(status_code=404, detail="Student account not found.")
    content_type = (photo.content_type or "").lower()
    extensions = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}
    if content_type not in extensions:
        raise HTTPException(status_code=400, detail="Choose a JPG, PNG, or WEBP image.")
    content = await photo.read(MAX_PROFILE_PHOTO_BYTES + 1)
    if not content or len(content) > MAX_PROFILE_PHOTO_BYTES:
        raise HTTPException(status_code=413, detail="Profile photo must be smaller than 2 MB.")
    try:
        stored_url = upload_media(
            content,
            content_type,
            f"profile.{extensions[content_type]}",
            folder="profiles",
        )
        signed_url = resolve_media_urls([stored_url]).get(stored_url, stored_url)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail="Could not save the profile photo. Please try again.") from exc
    user.profile_photo_url = stored_url
    db.commit()
    return {"message": "Profile photo updated.", "profile_photo_url": signed_url}


@router.delete("/profile/photo")
def remove_profile_photo(
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    user = db.scalar(select(User).where(User.id == current_user_id))
    if user is None or str(user.role).strip().lower() != "student":
        raise HTTPException(status_code=404, detail="Student account not found.")
    user.profile_photo_url = None
    db.commit()
    return {"message": "Profile photo removed."}


@router.post("/change-password")
def change_student_password(
    data: StudentPasswordChangeRequest,
    current_user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    user = db.scalar(select(User).where(User.id == current_user_id))
    if user is None or str(user.role).strip().lower() != "student":
        raise HTTPException(status_code=404, detail="Student account not found.")
    if not verify_password(data.current_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect.")
    if verify_password(data.new_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Choose a new password different from your current one.")
    user.password_hash = hash_password(data.new_password)
    db.commit()
    return {"message": "Password changed successfully."}

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
            PasswordResetOTP.purpose == "password_reset",
            PasswordResetOTP.used == False,
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
        purpose="password_reset",
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
            PasswordResetOTP.purpose == "password_reset",
            PasswordResetOTP.used == False,
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
            PasswordResetOTP.purpose == "password_reset",
            PasswordResetOTP.used == False,
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
