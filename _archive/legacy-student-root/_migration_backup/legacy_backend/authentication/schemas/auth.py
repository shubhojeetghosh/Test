from pydantic import BaseModel, EmailStr, Field


# ============================================================
# REGISTER
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


# ============================================================
# LOGIN
# ============================================================

class LoginRequest(BaseModel):

    email: EmailStr

    password: str


# ============================================================
# FORGOT PASSWORD
# ============================================================

class ForgotPasswordRequest(BaseModel):

    email: EmailStr


# ============================================================
# VERIFY OTP
# ============================================================

class VerifyOTPRequest(BaseModel):

    email: EmailStr

    otp: str = Field(
        min_length=6,
        max_length=6
    )


# ============================================================
# RESET PASSWORD
# ============================================================

class ResetPasswordRequest(BaseModel):

    email: EmailStr

    otp: str = Field(
        min_length=6,
        max_length=6
    )

    new_password: str = Field(
        min_length=8
    )