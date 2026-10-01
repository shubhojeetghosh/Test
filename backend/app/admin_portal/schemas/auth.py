from pydantic import BaseModel, EmailStr


# =========================================================
# NORMAL ADMIN LOGIN
# =========================================================

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    name: str
    email: str
    role: str


# =========================================================
# STUDENT REGISTER - SEND OTP
# =========================================================

class RegisterSendOTPRequest(BaseModel):
    email: EmailStr


class RegisterSendOTPResponse(BaseModel):
    message: str


# =========================================================
# STUDENT REGISTER - VERIFY OTP
# =========================================================

class RegisterVerifyOTPRequest(BaseModel):
    email: EmailStr
    otp: str


class RegisterVerifyOTPResponse(BaseModel):
    message: str
    verified: bool


# =========================================================
# STUDENT REGISTER - CREATE ACCOUNT
# =========================================================

class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str


class RegisterResponse(BaseModel):
    message: str
    user_id: int
    name: str
    email: str
    role: str


# =========================================================
# ADMIN - CREATE NEW ADMIN
# STEP 1: SEND OTP
# =========================================================

class CreateAdminRequest(BaseModel):
    email: EmailStr


class CreateAdminResponse(BaseModel):
    message: str


# =========================================================
# ADMIN - CREATE NEW ADMIN
# STEP 2: VERIFY OTP
# =========================================================

class CreateAdminVerifyOTPRequest(BaseModel):
    email: EmailStr
    otp: str


class CreateAdminVerifyOTPResponse(BaseModel):
    message: str
    verified: bool


# =========================================================
# ADMIN - CREATE NEW ADMIN
# STEP 3: SET DETAILS + PASSWORD
# =========================================================

class CreateAdminPasswordRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    confirm_password: str


class CreateAdminPasswordResponse(BaseModel):
    message: str
    user_id: int
    name: str
    email: str
    role: str


# =========================================================
# ADMIN - CHANGE PASSWORD
# =========================================================

class ChangeAdminPasswordRequest(BaseModel):
    current_password: str
    new_password: str
    confirm_password: str


class ChangeAdminPasswordResponse(BaseModel):
    message: str


# =========================================================
# ADMIN - FORGOT PASSWORD
# STEP 1: SEND RESET LINK
# =========================================================

class AdminForgotPasswordRequest(BaseModel):
    email: EmailStr


class AdminForgotPasswordResponse(BaseModel):
    message: str


# =========================================================
# ADMIN - RESET PASSWORD
# STEP 2: USE EMAIL RESET LINK
# =========================================================

class AdminResetPasswordRequest(BaseModel):
    token: str
    new_password: str
    confirm_password: str


class AdminResetPasswordResponse(BaseModel):
    message: str