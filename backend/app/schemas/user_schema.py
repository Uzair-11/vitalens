from typing import Optional
from datetime import date, datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict

class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, description="Password must be at least 6 characters")
    full_name: str = Field(..., min_length=2)
    phone: Optional[str] = None
    date_of_birth: Optional[date] = None
    biological_sex: Optional[str] = "Prefer not to say"
    blood_group: Optional[str] = None
    emergency_contact: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class PasswordResetRequest(BaseModel):
    email: EmailStr
    new_password: str = Field(..., min_length=6, description="Password must be at least 6 characters")
    otp: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in_minutes: int = 30
    user_id: str
    role: str = "PATIENT"

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class RefreshTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_minutes: int = 30

class UserProfileResponse(BaseModel):
    id: str
    email: str
    full_name: str
    role: str = "PATIENT"
    phone: Optional[str] = None
    date_of_birth: Optional[date] = None
    biological_sex: Optional[str] = None
    blood_group: Optional[str] = None
    emergency_contact: Optional[str] = None
    abha_number: Optional[str] = None
    avatar_url: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = "India"
    is_verified: bool = False
    email_verified: bool = False
    phone_verified: bool = False
    is_active: bool = True
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class UserProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    date_of_birth: Optional[date] = None
    biological_sex: Optional[str] = None
    blood_group: Optional[str] = None
    emergency_contact: Optional[str] = None
    abha_number: Optional[str] = None
    avatar_url: Optional[str] = None
    address_line1: Optional[str] = None
    address_line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None

class SendEmailOTPRequest(BaseModel):
    email: EmailStr
    purpose: Optional[str] = "EMAIL_VERIFICATION"  # EMAIL_VERIFICATION or PASSWORD_RESET

class VerifyEmailOTPRequest(BaseModel):
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6)

class ForgotPasswordRequestOTP(BaseModel):
    email: EmailStr

class ForgotPasswordResetOTP(BaseModel):
    email: EmailStr
    otp: str = Field(..., min_length=6, max_length=6)
    new_password: str = Field(..., min_length=6, description="Password must be at least 6 characters")

class ABHALinkRequest(BaseModel):
    abha_number: str = Field(..., description="14-digit ABHA number, formatted e.g. 91-1234-5678-9012 or 14 digits")

class ABHALinkResponse(BaseModel):
    status: str
    message: str
    abha_number: str
    user_id: str

