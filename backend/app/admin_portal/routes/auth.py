import hashlib
import secrets

from datetime import datetime, timedelta

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from pydantic import BaseModel

from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)

from sqlalchemy import delete, select, func
from sqlalchemy.orm import Session

from app.database.database import get_db

from app.admin_portal.models.user import User
from app.admin_portal.models.email_otp import EmailOTP

from app.admin_portal.schemas.auth import (
    LoginRequest,
    LoginResponse,

    CreateAdminRequest,
    CreateAdminResponse,

    CreateAdminVerifyOTPRequest,
    CreateAdminVerifyOTPResponse,

    CreateAdminPasswordRequest,
    CreateAdminPasswordResponse,

    ChangeAdminPasswordRequest,
    ChangeAdminPasswordResponse,
)

from app.admin_portal.core.security import (
    verify_password,
    hash_password,
    create_access_token,
    decode_access_token,
)

from app.admin_portal.services.email_service import (
    send_otp_email,
    send_admin_forgot_password_email,
)


# =========================================================
# CONFIGURATION
# =========================================================

ADMIN_CREATE_OTP_PURPOSE = "ADMIN_CREATE"
ADMIN_FORGOT_PASSWORD_PURPOSE = "ADMIN_FORGOT_PASSWORD"

ADMIN_CREATE_OTP_EXPIRY_MINUTES = 10
ADMIN_FORGOT_PASSWORD_EXPIRY_MINUTES = 10


# =========================================================
# ROUTER
# =========================================================

router = APIRouter(
    prefix="/auth",
    tags=["Admin Authentication"],
)


# =========================================================
# JWT AUTHENTICATION
# =========================================================

security = HTTPBearer()


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def _normalize_email(email: str) -> str:
    """
    Normalize an email address.

    Emails are stored and compared in lowercase.
    """

    return str(email).strip().lower()


def _hash_value(value: str) -> str:
    """
    SHA-256 hash.

    Used for:
    - OTPs
    - Password reset tokens

    Raw OTPs and reset tokens are never stored
    in the database.
    """

    return hashlib.sha256(
        value.encode("utf-8")
    ).hexdigest()


def _generate_otp() -> str:
    """
    Generate a secure six-digit OTP.
    """

    return f"{secrets.randbelow(1_000_000):06d}"


def _validate_password(password: str) -> str:
    """
    Validate password.

    Current rule:
    - Minimum 8 characters
    """

    if password is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password is required",
        )

    password = password.strip()

    if len(password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must contain at least 8 characters",
        )

    return password


# =========================================================
# ADMIN PROFILE SCHEMAS
# =========================================================
#
# Used by:
#
# PUT /auth/admin/profile
#
# The currently logged-in Admin can update:
# - name
# - email
#
# The Admin ID is NOT accepted from the frontend.
# The Admin is identified from the JWT token.
# =========================================================

class AdminProfileUpdateRequest(BaseModel):
    name: str
    email: str


class AdminProfileUpdateResponse(BaseModel):
    message: str
    user_id: int
    name: str
    email: str
    role: str


# =========================================================
# GET CURRENT ADMIN
# =========================================================

def get_current_admin(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """
    Validate the JWT and return the authenticated Admin.

    Requirements:
    - Bearer token exists
    - Token is valid
    - Token is not expired
    - Token contains valid user ID
    - Token role is admin
    - User still exists
    - User still has role='admin'
    """

    token = credentials.credentials

    # -----------------------------------------------------
    # Decode JWT
    # -----------------------------------------------------

    try:
        payload = decode_access_token(token)

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    # -----------------------------------------------------
    # Get user ID
    # -----------------------------------------------------

    user_id = payload.get("sub")

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        )

    try:
        user_id = int(user_id)

    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
        )

    # -----------------------------------------------------
    # Check JWT role
    # -----------------------------------------------------

    token_role = str(
        payload.get("role", "")
    ).strip().lower()

    if token_role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access is required",
        )

    # -----------------------------------------------------
    # Get user from database
    # -----------------------------------------------------

    user = db.scalar(
        select(User).where(
            User.id == user_id
        )
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin account no longer exists",
        )

    # -----------------------------------------------------
    # Check database role
    # -----------------------------------------------------

    database_role = str(
        user.role
    ).strip().lower()

    if database_role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access is required",
        )

    return user


# =========================================================
# ADMIN LOGIN
# =========================================================

@router.post(
    "/admin/login",
    response_model=LoginResponse,
)
def admin_login(
    login_data: LoginRequest,
    db: Session = Depends(get_db),
):
    """
    Normal Admin login.

    Login requires:
    - Gmail/email
    - Password
    - Existing Admin account

    OTP is NOT required for login.
    """

    email = _normalize_email(
        login_data.email
    )

    user = db.scalar(
        select(User).where(
            User.email == email
        )
    )

    # -----------------------------------------------------
    # Account not found
    # -----------------------------------------------------

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin email or password",
        )

    # -----------------------------------------------------
    # Account must be Admin
    # -----------------------------------------------------

    if str(user.role).strip().lower() != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account is not authorized for the Admin portal",
        )

    # -----------------------------------------------------
    # Verify password
    # -----------------------------------------------------

    if not verify_password(
        login_data.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin email or password",
        )

    # -----------------------------------------------------
    # Create JWT
    # -----------------------------------------------------

    access_token = create_access_token(
        user_id=user.id,
        role="ADMIN",
    )

    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        user_id=user.id,
        name=user.name,
        email=user.email,
        role="ADMIN",
    )


# =========================================================
# SAVE ADMIN PROFILE / SETTINGS
# =========================================================
#
# Endpoint:
#
# PUT /auth/admin/profile
#
# Used by:
#
# Admin Dashboard
#     -> Settings
#     -> Save Changes
#
# The frontend sends:
#
# {
#     "name": "Admin Name",
#     "email": "admin@gmail.com"
# }
#
# The admin ID is NOT accepted from the frontend.
# get_current_admin() gets the authenticated admin
# directly from the JWT.
# =========================================================

@router.put(
    "/admin/profile",
    response_model=AdminProfileUpdateResponse,
)
def update_admin_profile(
    request: AdminProfileUpdateRequest,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    Update the currently authenticated Admin's profile.

    Editable fields:
    - name
    - email

    Security:
    - Requires valid Admin JWT
    - Cannot update another user's profile
    - Email must remain unique
    """

    # -----------------------------------------------------
    # Validate name
    # -----------------------------------------------------

    name = str(
        request.name
    ).strip()

    if not name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin name is required",
        )

    if len(name) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin name cannot exceed 100 characters",
        )

    # -----------------------------------------------------
    # Normalize email
    # -----------------------------------------------------

    email = _normalize_email(
        request.email
    )

    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin email is required",
        )

    if len(email) > 255:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin email cannot exceed 255 characters",
        )

    # -----------------------------------------------------
    # Check whether another account already uses
    # this email.
    #
    # The current Admin's own account is excluded.
    # -----------------------------------------------------

    existing_user = db.scalar(
        select(User).where(
            func.lower(User.email) == email,
            User.id != current_admin.id,
        )
    )

    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This email address is already registered to another account",
        )

    # -----------------------------------------------------
    # Update current Admin
    # -----------------------------------------------------

    current_admin.name = name
    current_admin.email = email

    db.commit()
    db.refresh(current_admin)

    # -----------------------------------------------------
    # Return updated Admin
    # -----------------------------------------------------

    return AdminProfileUpdateResponse(
        message="Admin profile updated successfully",
        user_id=current_admin.id,
        name=current_admin.name,
        email=current_admin.email,
        role="ADMIN",
    )


# =========================================================
# CREATE ADMIN
# STEP 1
# SEND OTP
# =========================================================

@router.post(
    "/admin/create",
    response_model=CreateAdminResponse,
)
def create_admin(
    request: CreateAdminRequest,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    Start creation of a new Admin account.

    STEP 1:

    The existing Admin enters ONLY the new Admin's
    Gmail address.

    The system:
    - checks the email
    - generates an OTP
    - sends the OTP to that Gmail

    Full name and password are collected only
    after successful OTP verification.
    """

    email = _normalize_email(
        request.email
    )

    # -----------------------------------------------------
    # Validate email
    # -----------------------------------------------------

    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin email is required",
        )

    # -----------------------------------------------------
    # Check whether account already exists
    # -----------------------------------------------------

    existing_user = db.scalar(
        select(User).where(
            User.email == email
        )
    )

    if existing_user is not None:

        existing_role = str(
            existing_user.role
        ).strip().lower()

        if existing_role == "admin":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="An Admin account already exists for this email",
            )

        if existing_role == "student":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="A student account cannot be converted into an Admin account",
            )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account already exists for this email",
        )

    # -----------------------------------------------------
    # Delete previous Admin creation OTPs
    # -----------------------------------------------------

    db.execute(
        delete(EmailOTP).where(
            EmailOTP.email == email,
            EmailOTP.purpose == ADMIN_CREATE_OTP_PURPOSE,
        )
    )

    # -----------------------------------------------------
    # Generate OTP
    # -----------------------------------------------------

    otp = _generate_otp()

    otp_record = EmailOTP(
        email=email,
        otp_hash=_hash_value(otp),
        purpose=ADMIN_CREATE_OTP_PURPOSE,
        expires_at=(
            datetime.utcnow()
            + timedelta(
                minutes=ADMIN_CREATE_OTP_EXPIRY_MINUTES
            )
        ),
        verified=False,
    )

    db.add(otp_record)
    db.commit()

    # -----------------------------------------------------
    # Send OTP email
    # -----------------------------------------------------

    try:

        send_otp_email(
            recipient_email=email,
            otp=otp,
        )

    except Exception:

        db.execute(
            delete(EmailOTP).where(
                EmailOTP.email == email,
                EmailOTP.purpose == ADMIN_CREATE_OTP_PURPOSE,
            )
        )

        db.commit()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to send verification code. Please try again.",
        )

    return CreateAdminResponse(
        message="Verification code sent to the new Admin's email",
    )


# =========================================================
# CREATE ADMIN
# STEP 2
# VERIFY OTP
# =========================================================

@router.post(
    "/admin/create/verify-otp",
    response_model=CreateAdminVerifyOTPResponse,
)
def verify_create_admin_otp(
    request: CreateAdminVerifyOTPRequest,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    STEP 2:

    Verify the OTP sent to the new Admin's Gmail.

    Successful verification allows the frontend
    to move to the Admin details form.
    """

    email = _normalize_email(
        request.email
    )

    # -----------------------------------------------------
    # Make sure account wasn't created already
    # -----------------------------------------------------

    existing_user = db.scalar(
        select(User).where(
            User.email == email
        )
    )

    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account already exists for this email",
        )

    # -----------------------------------------------------
    # Find active OTP
    # -----------------------------------------------------

    otp_record = db.scalar(
        select(EmailOTP)
        .where(
            EmailOTP.email == email,
            EmailOTP.purpose == ADMIN_CREATE_OTP_PURPOSE,
            EmailOTP.verified == False,
        )
        .order_by(
            EmailOTP.id.desc()
        )
    )

    if otp_record is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active verification code found. Please request a new code.",
        )

    # -----------------------------------------------------
    # Check expiry
    # -----------------------------------------------------

    if datetime.utcnow() > otp_record.expires_at:

        db.delete(otp_record)
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Verification code has expired. Please request a new code.",
        )

    # -----------------------------------------------------
    # Verify OTP
    # -----------------------------------------------------

    entered_otp = request.otp.strip()

    if _hash_value(entered_otp) != otp_record.otp_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid verification code",
        )

    # -----------------------------------------------------
    # Mark OTP as verified
    # -----------------------------------------------------

    otp_record.verified = True

    db.commit()

    return CreateAdminVerifyOTPResponse(
        message="Email verified successfully",
        verified=True,
    )


# =========================================================
# CREATE ADMIN
# STEP 3
# SET DETAILS + PASSWORD
# =========================================================

@router.post(
    "/admin/create/set-password",
    response_model=CreateAdminPasswordResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_admin_password(
    request: CreateAdminPasswordRequest,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    STEP 3:

    Create the new Admin account.

    At this stage the frontend provides:
    - Full name
    - Verified Gmail
    - Password
    - Confirm password

    Requirements:
    - Existing Admin must be logged in
    - Gmail must have been OTP verified
    - OTP must still be valid
    - Account must not already exist
    - Password must be valid
    - Password confirmation must match
    """

    name = request.name.strip()

    email = _normalize_email(
        request.email
    )

    # -----------------------------------------------------
    # Validate name
    # -----------------------------------------------------

    if not name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin full name is required",
        )

    # -----------------------------------------------------
    # Validate password
    # -----------------------------------------------------

    password = _validate_password(
        request.password
    )

    if password != request.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Passwords do not match",
        )

    # -----------------------------------------------------
    # Make sure account doesn't exist
    # -----------------------------------------------------

    existing_user = db.scalar(
        select(User).where(
            User.email == email
        )
    )

    if existing_user is not None:

        existing_role = str(
            existing_user.role
        ).strip().lower()

        if existing_role == "student":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="A student account cannot be converted into an Admin account",
            )

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account already exists for this email",
        )

    # -----------------------------------------------------
    # Find verified OTP
    # -----------------------------------------------------

    verified_otp = db.scalar(
        select(EmailOTP)
        .where(
            EmailOTP.email == email,
            EmailOTP.purpose == ADMIN_CREATE_OTP_PURPOSE,
            EmailOTP.verified == True,
        )
        .order_by(
            EmailOTP.id.desc()
        )
    )

    if verified_otp is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New Admin email verification is required",
        )

    # -----------------------------------------------------
    # Check OTP expiry again
    # -----------------------------------------------------

    if datetime.utcnow() > verified_otp.expires_at:

        db.execute(
            delete(EmailOTP).where(
                EmailOTP.email == email,
                EmailOTP.purpose == ADMIN_CREATE_OTP_PURPOSE,
            )
        )

        db.commit()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email verification has expired. Please start again.",
        )

    # -----------------------------------------------------
    # Create Admin
    # -----------------------------------------------------

    user = User(
        name=name,
        email=email,
        password_hash=hash_password(password),
        role="admin",
    )

    db.add(user)

    # -----------------------------------------------------
    # Delete OTP after successful account creation
    # -----------------------------------------------------

    db.execute(
        delete(EmailOTP).where(
            EmailOTP.email == email,
            EmailOTP.purpose == ADMIN_CREATE_OTP_PURPOSE,
        )
    )

    db.commit()

    db.refresh(user)

    return CreateAdminPasswordResponse(
        message="Admin account created successfully",
        user_id=user.id,
        name=user.name,
        email=user.email,
        role="ADMIN",
    )


# =========================================================
# CHANGE ADMIN PASSWORD
# =========================================================

@router.post(
    "/admin/change-password",
    response_model=ChangeAdminPasswordResponse,
)
def change_admin_password(
    request: ChangeAdminPasswordRequest,
    current_admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    Change password while already logged in.

    Used from:
    Settings → Change Password

    OTP is NOT required.
    """

    # -----------------------------------------------------
    # Verify current password
    # -----------------------------------------------------

    if not verify_password(
        request.current_password,
        current_admin.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    # -----------------------------------------------------
    # Validate new password
    # -----------------------------------------------------

    new_password = _validate_password(
        request.new_password
    )

    if new_password != request.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New passwords do not match",
        )

    # -----------------------------------------------------
    # Prevent same password
    # -----------------------------------------------------

    if verify_password(
        new_password,
        current_admin.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from the current password",
        )

    # -----------------------------------------------------
    # Update password
    # -----------------------------------------------------

    current_admin.password_hash = hash_password(
        new_password
    )

    db.commit()

    return ChangeAdminPasswordResponse(
        message="Password changed successfully",
    )


# =========================================================
# ADMIN FORGOT PASSWORD - OTP RECOVERY
# =========================================================

class AdminForgotPasswordOTPRequest(BaseModel):
    email: str


class AdminForgotPasswordOTPResponse(BaseModel):
    message: str


class AdminVerifyForgotOTPRequest(BaseModel):
    email: str
    otp: str


class AdminVerifyForgotOTPResponse(BaseModel):
    message: str
    verified: bool


class AdminResetPasswordOTPRequest(BaseModel):
    email: str
    password: str


class AdminResetPasswordOTPResponse(BaseModel):
    message: str


# =========================================================
# STEP 1
# SEND 6-DIGIT OTP
# =========================================================

@router.post(
    "/admin/forgot-password",
    response_model=AdminForgotPasswordOTPResponse,
)
def admin_forgot_password(
    request: AdminForgotPasswordOTPRequest,
    db: Session = Depends(get_db),
):
    """
    Admin password recovery - Step 1.

    The administrator enters the registered Gmail address.
    A six-digit OTP is generated and emailed to that address.

    No password-reset link is generated or sent.
    """

    email = _normalize_email(request.email)

    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin email is required",
        )

    user = db.scalar(
        select(User).where(User.email == email)
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email is not registered",
        )

    if str(user.role).strip().lower() != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This email is not registered as an Admin account",
        )

    # Delete any previous recovery OTP for this email.

    db.execute(
        delete(EmailOTP).where(
            EmailOTP.email == email,
            EmailOTP.purpose == ADMIN_FORGOT_PASSWORD_PURPOSE,
        )
    )

    otp = _generate_otp()

    otp_record = EmailOTP(
        email=email,
        otp_hash=_hash_value(otp),
        purpose=ADMIN_FORGOT_PASSWORD_PURPOSE,
        expires_at=(
            datetime.utcnow()
            + timedelta(minutes=ADMIN_FORGOT_PASSWORD_EXPIRY_MINUTES)
        ),
        verified=False,
    )

    db.add(otp_record)
    db.commit()

    try:
        send_admin_forgot_password_email(
            recipient_email=email,
            otp=otp,
        )

    except Exception:

        # Never leave a usable OTP behind if email delivery fails.

        db.execute(
            delete(EmailOTP).where(
                EmailOTP.email == email,
                EmailOTP.purpose == ADMIN_FORGOT_PASSWORD_PURPOSE,
            )
        )

        db.commit()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to send password reset OTP. Please try again.",
        )

    return AdminForgotPasswordOTPResponse(
        message="A 6-digit password reset OTP has been sent to your email.",
    )


# =========================================================
# STEP 2
# VERIFY OTP
# =========================================================

@router.post(
    "/admin/verify-forgot-otp",
    response_model=AdminVerifyForgotOTPResponse,
)
def admin_verify_forgot_otp(
    request: AdminVerifyForgotOTPRequest,
    db: Session = Depends(get_db),
):
    """
    Admin password recovery - Step 2.

    Verifies the latest unexpired six-digit OTP.
    """

    email = _normalize_email(request.email)
    otp = str(request.otp).strip()

    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin email is required",
        )

    if len(otp) != 6 or not otp.isdigit():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP must be exactly 6 digits",
        )

    user = db.scalar(
        select(User).where(User.email == email)
    )

    if user is None or str(user.role).strip().lower() != "admin":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid password reset request",
        )

    otp_record = db.scalar(
        select(EmailOTP)
        .where(
            EmailOTP.email == email,
            EmailOTP.purpose == ADMIN_FORGOT_PASSWORD_PURPOSE,
            EmailOTP.verified == False,
        )
        .order_by(EmailOTP.id.desc())
    )

    if otp_record is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active OTP found. Please request a new OTP.",
        )

    if datetime.utcnow() > otp_record.expires_at:

        db.delete(otp_record)
        db.commit()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP has expired. Please request a new OTP.",
        )

    if _hash_value(otp) != otp_record.otp_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP",
        )

    otp_record.verified = True

    db.commit()

    return AdminVerifyForgotOTPResponse(
        message="OTP verified successfully.",
        verified=True,
    )


# =========================================================
# STEP 3
# SET NEW PASSWORD
# =========================================================

@router.post(
    "/admin/reset-password",
    response_model=AdminResetPasswordOTPResponse,
)
def admin_reset_password(
    request: AdminResetPasswordOTPRequest,
    db: Session = Depends(get_db),
):
    """
    Admin password recovery - Step 3.

    A password can be changed only when a verified,
    unexpired recovery OTP exists for the same email.

    The verified OTP is deleted after a successful reset,
    making the recovery process single-use.
    """

    email = _normalize_email(request.email)

    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin email is required",
        )

    user = db.scalar(
        select(User).where(User.email == email)
    )

    if user is None or str(user.role).strip().lower() != "admin":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid password reset request",
        )

    # -----------------------------------------------------
    # Only an OTP that was successfully verified may
    # reset the password.
    # -----------------------------------------------------

    verified_otp = db.scalar(
        select(EmailOTP)
        .where(
            EmailOTP.email == email,
            EmailOTP.purpose == ADMIN_FORGOT_PASSWORD_PURPOSE,
            EmailOTP.verified == True,
        )
        .order_by(EmailOTP.id.desc())
    )

    if verified_otp is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP verification is required before setting a new password.",
        )

    if datetime.utcnow() > verified_otp.expires_at:

        db.execute(
            delete(EmailOTP).where(
                EmailOTP.email == email,
                EmailOTP.purpose == ADMIN_FORGOT_PASSWORD_PURPOSE,
            )
        )

        db.commit()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP verification has expired. Please start again.",
        )

    new_password = _validate_password(
        request.password
    )

    if verify_password(
        new_password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be different from the current password",
        )

    user.password_hash = hash_password(
        new_password
    )

    # OTP recovery is single-use.

    db.execute(
        delete(EmailOTP).where(
            EmailOTP.email == email,
            EmailOTP.purpose == ADMIN_FORGOT_PASSWORD_PURPOSE,
        )
    )

    db.commit()

    return AdminResetPasswordOTPResponse(
        message="Password reset successfully.",
    )