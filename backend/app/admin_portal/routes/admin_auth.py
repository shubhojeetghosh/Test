from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.database import get_db

from app.admin_portal.models.user import User
from app.admin_portal.models.email_otp import EmailOTP

from app.admin_portal.schemas.auth import (
    AdminStartRequest,
    AdminStartResponse,
    AdminVerifyPersonalOTPRequest,
    AdminVerifyPersonalOTPResponse,
    AdminVerifyMainOTPRequest,
    AdminVerifyMainOTPResponse,
    AdminSetPasswordRequest,
    AdminSetPasswordResponse,
)

from app.admin_portal.core.security import hash_password

from app.admin_portal.services.admin_otp_service import (
    create_personal_admin_otp,
    verify_personal_admin_otp,
    create_admin_approval_otp,
    verify_admin_approval_otp,
)


# =========================================================
# ADMIN AUTHENTICATION ROUTER
# =========================================================

router = APIRouter(
    prefix="/admin/auth",
    tags=["Admin Authentication"],
)


# =========================================================
# STEP 1
# PERSON ENTERS THEIR GMAIL
# =========================================================

@router.post(
    "/start",
    response_model=AdminStartResponse,
)
def admin_start(
    request: AdminStartRequest,
    db: Session = Depends(get_db),
):
    email = str(request.email).lower().strip()

    # -----------------------------------------------------
    # CHECK EXISTING ACCOUNT
    # -----------------------------------------------------

    existing_user = db.scalar(
        select(User).where(
            User.email == email
        )
    )

    if existing_user is not None:

        # Existing admin should use normal login
        if existing_user.role == "ADMIN":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Admin account already exists. Please use admin login.",
            )

        # Existing student cannot become admin
        if existing_user.role == "STUDENT":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This email belongs to a student account and cannot be used for admin access.",
            )

    # -----------------------------------------------------
    # SEND OTP #1
    # TO PERSON'S PERSONAL GMAIL
    # -----------------------------------------------------

    create_personal_admin_otp(
        db=db,
        personal_email=email,
    )

    return AdminStartResponse(
        message="Verification code sent to your Gmail.",
    )


# =========================================================
# STEP 2
# VERIFY PERSONAL GMAIL OTP
# =========================================================

@router.post(
    "/verify-personal-otp",
    response_model=AdminVerifyPersonalOTPResponse,
)
def admin_verify_personal_otp(
    request: AdminVerifyPersonalOTPRequest,
    db: Session = Depends(get_db),
):
    email = str(request.email).lower().strip()

    # -----------------------------------------------------
    # VERIFY OTP #1
    # -----------------------------------------------------

    verified = verify_personal_admin_otp(
        db=db,
        personal_email=email,
        otp=request.otp,
    )

    if not verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired personal verification code.",
        )

    # -----------------------------------------------------
    # PERSONAL EMAIL VERIFIED
    #
    # NOW SEND OTP #2
    #
    # SAME OTP GOES TO:
    #
    # 1. MAIN ADMIN EMAIL
    # 2. DEVELOPER EMAIL
    #
    # The person does NOT receive OTP #2.
    # -----------------------------------------------------

    create_admin_approval_otp(
        db=db,
        personal_email=email,
    )

    return AdminVerifyPersonalOTPResponse(
        message=(
            "Personal email verified. "
            "Approval code has been sent to the authorized admin "
            "and developer."
        ),
        verified=True,
    )


# =========================================================
# STEP 3
# VERIFY ADMIN/DEVELOPER OTP
# =========================================================

@router.post(
    "/verify-main-otp",
    response_model=AdminVerifyMainOTPResponse,
)
def admin_verify_main_otp(
    request: AdminVerifyMainOTPRequest,
    db: Session = Depends(get_db),
):
    email = str(request.email).lower().strip()

    # -----------------------------------------------------
    # VERIFY OTP #2
    #
    # The OTP entered here must be the OTP received by
    # either the main admin or developer.
    # -----------------------------------------------------

    verified = verify_admin_approval_otp(
        db=db,
        personal_email=email,
        otp=request.otp,
    )

    if not verified:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired admin approval code.",
        )

    return AdminVerifyMainOTPResponse(
        message="Admin approval verified successfully.",
        verified=True,
    )


# =========================================================
# STEP 4
# CREATE ADMIN PASSWORD
# =========================================================

@router.post(
    "/set-password",
    response_model=AdminSetPasswordResponse,
    status_code=status.HTTP_201_CREATED,
)
def admin_set_password(
    request: AdminSetPasswordRequest,
    db: Session = Depends(get_db),
):
    email = str(request.email).lower().strip()

    # =====================================================
    # CHECK PERSONAL EMAIL VERIFICATION
    # =====================================================

    personal_verified = db.scalar(
        select(EmailOTP)
        .where(
            EmailOTP.email == email,
            EmailOTP.purpose == "ADMIN_PERSONAL",
            EmailOTP.verified == True,
        )
        .order_by(
            EmailOTP.id.desc()
        )
    )

    if personal_verified is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Personal email verification has not been completed.",
        )

    # =====================================================
    # CHECK ADMIN/DEVELOPER APPROVAL
    # =====================================================

    approval_verified = db.scalar(
        select(EmailOTP)
        .where(
            EmailOTP.email == email,
            EmailOTP.purpose == "ADMIN_APPROVAL",
            EmailOTP.verified == True,
        )
        .order_by(
            EmailOTP.id.desc()
        )
    )

    if approval_verified is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin approval has not been completed.",
        )

    # =====================================================
    # CHECK IF ACCOUNT ALREADY EXISTS
    # =====================================================

    existing_user = db.scalar(
        select(User).where(
            User.email == email
        )
    )

    if existing_user is not None:

        # Existing admin
        if existing_user.role == "ADMIN":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Admin account already exists.",
            )

        # Existing student
        if existing_user.role == "STUDENT":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    "This email belongs to a student account "
                    "and cannot become an admin."
                ),
            )

    # =====================================================
    # CREATE ADMIN USER
    # =====================================================

    admin_user = User(
        name=request.name.strip(),
        email=email,
        password_hash=hash_password(
            request.password
        ),
        role="ADMIN",
    )

    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)

    # =====================================================
    # RESPONSE
    # =====================================================

    return AdminSetPasswordResponse(
        message="Admin account created successfully.",
        user_id=admin_user.id,
        name=admin_user.name,
        email=admin_user.email,
        role=admin_user.role,
    )
