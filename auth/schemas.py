from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr, validator
import re

# =============================================================================
# REQUEST SCHEMAS
# =============================================================================

class PhoneNumberRequest(BaseModel):
    """Request schema for phone number operations"""
    phone_number: str = Field(..., description="Phone number with country code")
    
    @validator('phone_number')
    def validate_phone_number(cls, v):
        # Basic phone number validation (international format)
        if not re.match(r'^\+[1-9]\d{1,14}$', v):
            raise ValueError('Phone number must be in international format (e.g., +201234567890)')
        return v

class OTPVerificationRequest(BaseModel):
    """Request schema for OTP verification"""
    phone_number: str = Field(..., description="Phone number with country code")
    otp_code: str = Field(..., min_length=4, max_length=6, description="OTP code")
    otp_type: str = Field(..., description="Type of OTP: REGISTRATION, LOGIN, RESET_PASSWORD")

class UserRegistrationRequest(BaseModel):
    """Request schema for user registration"""
    phone_number: str = Field(..., description="Phone number with country code")
    full_name: str = Field(..., min_length=2, max_length=255, description="User's full name")
    email: Optional[EmailStr] = Field(None, description="User's email address")
    password: Optional[str] = Field(None, min_length=8, description="Password (optional for phone-only auth)")

class UserLoginRequest(BaseModel):
    """Request schema for user login"""
    phone_number: str = Field(..., description="Phone number with country code")
    password: Optional[str] = Field(None, description="Password (optional for phone-only auth)")

class PasswordResetRequest(BaseModel):
    """Request schema for password reset"""
    phone_number: str = Field(..., description="Phone number with country code")
    new_password: str = Field(..., min_length=8, description="New password")

class UserProfileUpdateRequest(BaseModel):
    """Request schema for updating user profile"""
    full_name: Optional[str] = Field(None, min_length=2, max_length=255)
    email: Optional[EmailStr] = None
    password: Optional[str] = Field(None, min_length=8)

class RefreshTokenRequest(BaseModel):
    """Request schema for refreshing access token"""
    refresh_token: str = Field(..., description="Refresh token")

class SocialLoginRequest(BaseModel):
    """Request schema for social media login"""
    access_token: str = Field(..., description="Social media access token")
    provider: str = Field(..., description="Provider: facebook or google")

# =============================================================================
# RESPONSE SCHEMAS
# =============================================================================

class TokenResponse(BaseModel):
    """Response schema for authentication tokens"""
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Access token expiration time in seconds")
    refresh_expires_in: int = Field(..., description="Refresh token expiration time in seconds")

class UserProfileResponse(BaseModel):
    """Response schema for user profile"""
    user_id: str = Field(..., description="User unique identifier")
    phone_number: str = Field(..., description="User's phone number")
    full_name: Optional[str] = Field(None, description="User's full name")
    email: Optional[str] = Field(None, description="User's email address")
    points_balance: int = Field(..., description="User's loyalty points")
    points_expiry_date: Optional[datetime] = Field(None, description="Points expiration date")
    is_verified: bool = Field(..., description="Whether user is verified")
    is_active: bool = Field(..., description="Whether user account is active")
    created_at: datetime = Field(..., description="Account creation date")
    updated_at: datetime = Field(..., description="Last profile update date")

class OTPResponse(BaseModel):
    """Response schema for OTP operations"""
    message: str = Field(..., description="Operation message")
    expires_in: int = Field(..., description="OTP expiration time in seconds")
    phone_number: str = Field(..., description="Phone number OTP was sent to")

class LoginResponse(BaseModel):
    """Response schema for successful login"""
    user: UserProfileResponse = Field(..., description="User profile information")
    tokens: TokenResponse = Field(..., description="Authentication tokens")
    message: str = Field(default="Login successful", description="Success message")

class RegistrationResponse(BaseModel):
    """Response schema for successful registration"""
    user: UserProfileResponse = Field(..., description="User profile information")
    message: str = Field(default="Registration successful", description="Success message")

class PasswordResetResponse(BaseModel):
    """Response schema for password reset"""
    message: str = Field(..., description="Success message")
    phone_number: str = Field(..., description="Phone number password was reset for")

# =============================================================================
# INTERNAL SCHEMAS
# =============================================================================

class UserCreate(BaseModel):
    """Internal schema for creating user"""
    phone_number: str
    full_name: str
    email: Optional[str] = None
    password_hash: Optional[str] = None
    facebook_id: Optional[str] = None
    google_id: Optional[str] = None

class UserUpdate(BaseModel):
    """Internal schema for updating user"""
    full_name: Optional[str] = None
    email: Optional[str] = None
    password_hash: Optional[str] = None
    is_verified: Optional[bool] = None
    is_active: Optional[bool] = None

class OTPCreate(BaseModel):
    """Internal schema for creating OTP"""
    user_id: str
    phone_number: str
    otp_code: str
    otp_type: str
    expires_at: datetime

class SessionCreate(BaseModel):
    """Internal schema for creating user session"""
    user_id: str
    refresh_token: str
    device_info: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    expires_at: datetime

# =============================================================================
# VALIDATION SCHEMAS
# =============================================================================

class PhoneNumberValidation(BaseModel):
    """Schema for phone number validation"""
    phone_number: str
    
    @validator('phone_number')
    def validate_phone_format(cls, v):
        if not re.match(r'^\+[1-9]\d{1,14}$', v):
            raise ValueError('Invalid phone number format')
        return v

class PasswordValidation(BaseModel):
    """Schema for password validation"""
    password: str
    
    @validator('password')
    def validate_password_strength(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        return v