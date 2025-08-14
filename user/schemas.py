from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr, validator
import re

# =============================================================================
# REQUEST SCHEMAS
# =============================================================================

class UserProfileUpdateRequest(BaseModel):
    """Request schema for updating user profile"""
    full_name: Optional[str] = Field(None, min_length=2, max_length=255, description="User's full name")
    email: Optional[EmailStr] = Field(None, description="User's email address")
    phone_number: Optional[str] = Field(None, description="User's phone number")
    
    @validator('phone_number')
    def validate_phone_number(cls, v):
        if v is not None:
            if not re.match(r'^\+[1-9]\d{1,14}$', v):
                raise ValueError('Phone number must be in international format (e.g., +201234567890)')
        return v

class PasswordChangeRequest(BaseModel):
    """Request schema for changing password"""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")
    
    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        return v

class AccountDeletionRequest(BaseModel):
    """Request schema for account deletion"""
    confirmation: str = Field(..., description="Type 'DELETE' to confirm account deletion")
    reason: Optional[str] = Field(None, max_length=500, description="Reason for deletion")
    
    @validator('confirmation')
    def validate_confirmation(cls, v):
        if v != 'DELETE':
            raise ValueError("Please type 'DELETE' to confirm account deletion")
        return v

# =============================================================================
# ADDRESS MANAGEMENT SCHEMAS
# =============================================================================

class AddressCreateRequest(BaseModel):
    """Request schema for creating a new address"""
    address_type: str = Field(..., description="Type of address (e.g., 'Home', 'Work', 'Other')")
    full_name: str = Field(..., min_length=2, max_length=255, description="Full name for delivery")
    phone_number: str = Field(..., description="Phone number for delivery")
    email: Optional[EmailStr] = Field(None, description="Email for delivery notifications")
    street_address: str = Field(..., min_length=5, description="Street address")
    building_number: Optional[str] = Field(None, max_length=50, description="Building number")
    flat_number: Optional[str] = Field(None, max_length=50, description="Flat/Apartment number")
    city: str = Field(..., min_length=2, max_length=100, description="City name")
    area: Optional[str] = Field(None, max_length=100, description="Area/Neighborhood")
    is_default: bool = Field(False, description="Set as default address")
    
    @validator('phone_number')
    def validate_phone_number(cls, v):
        if not re.match(r'^\+[1-9]\d{1,14}$', v):
            raise ValueError('Phone number must be in international format (e.g., +201234567890)')
        return v
    
    @validator('address_type')
    def validate_address_type(cls, v):
        allowed_types = ['Home', 'Work', 'Other', 'home', 'work', 'other']
        if v not in allowed_types:
            raise ValueError('Address type must be one of: Home, Work, Other')
        return v.title()  # Normalize to title case

class AddressUpdateRequest(BaseModel):
    """Request schema for updating an existing address"""
    address_type: Optional[str] = Field(None, description="Type of address")
    full_name: Optional[str] = Field(None, min_length=2, max_length=255, description="Full name for delivery")
    phone_number: Optional[str] = Field(None, description="Phone number for delivery")
    email: Optional[EmailStr] = Field(None, description="Email for delivery notifications")
    street_address: Optional[str] = Field(None, min_length=5, description="Street address")
    building_number: Optional[str] = Field(None, max_length=50, description="Building number")
    flat_number: Optional[str] = Field(None, max_length=50, description="Flat/Apartment number")
    city: Optional[str] = Field(None, min_length=2, max_length=100, description="City name")
    area: Optional[str] = Field(None, max_length=100, description="Area/Neighborhood")
    
    @validator('phone_number')
    def validate_phone_number(cls, v):
        if v is not None:
            if not re.match(r'^\+[1-9]\d{1,14}$', v):
                raise ValueError('Phone number must be in international format (e.g., +201234567890)')
        return v
    
    @validator('address_type')
    def validate_address_type(cls, v):
        if v is not None:
            allowed_types = ['Home', 'Work', 'Other', 'home', 'work', 'other']
            if v not in allowed_types:
                raise ValueError('Address type must be one of: Home, Work, Other')
            return v.title()  # Normalize to title case
        return v

# =============================================================================
# RESPONSE SCHEMAS
# =============================================================================

class UserProfileResponse(BaseModel):
    """Response schema for user profile"""
    user_id: str = Field(..., description="User unique identifier")
    phone_number: str = Field(..., description="User's phone number")
    full_name: Optional[str] = Field(None, description="User's full name")
    email: Optional[str] = Field(None, description="User's email address")
    facebook_id: Optional[str] = Field(None, description="Facebook ID if connected")
    google_id: Optional[str] = Field(None, description="Google ID if connected")
    points_balance: int = Field(..., description="User's loyalty points")
    points_expiry_date: Optional[datetime] = Field(None, description="Points expiration date")
    is_verified: bool = Field(..., description="Whether user is verified")
    is_active: bool = Field(..., description="Whether user account is active")
    created_at: datetime = Field(..., description="Account creation date")
    updated_at: datetime = Field(..., description="Last profile update date")
    
    class Config:
        from_attributes = True

class UserPointsResponse(BaseModel):
    """Response schema for user points"""
    user_id: str = Field(..., description="User unique identifier")
    points_balance: int = Field(..., description="Current points balance")
    points_expiry_date: Optional[datetime] = Field(None, description="Points expiration date")
    points_earned_total: int = Field(..., description="Total points earned")
    points_used_total: int = Field(..., description="Total points used")
    points_expired_total: int = Field(..., description="Total points expired")
    next_expiry_batch: Optional[datetime] = Field(None, description="Next batch of points to expire")
    
    class Config:
        from_attributes = True

class UserPointsHistoryResponse(BaseModel):
    """Response schema for user points history"""
    history_id: str = Field(..., description="History record ID")
    points_change: int = Field(..., description="Points added/subtracted")
    change_type: str = Field(..., description="Type of change: EARNED, USED, EXPIRED, ADJUSTED")
    description: str = Field(..., description="Description of the change")
    order_id: Optional[str] = Field(None, description="Related order ID if applicable")
    created_at: datetime = Field(..., description="When the change occurred")
    
    class Config:
        from_attributes = True

class UserStatsResponse(BaseModel):
    """Response schema for user statistics"""
    user_id: str = Field(..., description="User unique identifier")
    total_orders: int = Field(..., description="Total number of orders")
    total_spent: float = Field(..., description="Total amount spent")
    average_order_value: float = Field(..., description="Average order value")
    favorite_categories: List[str] = Field(..., description="Most ordered categories")
    last_order_date: Optional[datetime] = Field(None, description="Date of last order")
    member_since: datetime = Field(..., description="When user joined")
    
    class Config:
        from_attributes = True

class AccountDeletionResponse(BaseModel):
    """Response schema for account deletion"""
    message: str = Field(..., description="Deletion confirmation message")
    deletion_date: datetime = Field(..., description="When account was deleted")
    data_retention_period: int = Field(..., description="Days data will be retained")
    reactivation_deadline: datetime = Field(..., description="Deadline to reactivate account")

class AddressResponse(BaseModel):
    """Response schema for user address"""
    address_id: str = Field(..., description="Address unique identifier")
    user_id: str = Field(..., description="User who owns this address")
    address_type: str = Field(..., description="Type of address (Home, Work, Other)")
    full_name: str = Field(..., description="Full name for delivery")
    phone_number: str = Field(..., description="Phone number for delivery")
    email: Optional[str] = Field(None, description="Email for delivery notifications")
    street_address: str = Field(..., description="Street address")
    building_number: Optional[str] = Field(None, description="Building number")
    flat_number: Optional[str] = Field(None, description="Flat/Apartment number")
    city: str = Field(..., description="City name")
    area: Optional[str] = Field(None, description="Area/Neighborhood")
    is_default: bool = Field(..., description="Whether this is the default address")
    created_at: datetime = Field(..., description="When address was created")
    updated_at: datetime = Field(..., description="When address was last updated")
    
    class Config:
        from_attributes = True

class AddressListResponse(BaseModel):
    """Response schema for list of addresses"""
    addresses: List[AddressResponse] = Field(..., description="List of user addresses")
    total_count: int = Field(..., description="Total number of addresses")
    default_address_id: Optional[str] = Field(None, description="ID of default address if exists")

# =============================================================================
# INTERNAL SCHEMAS
# =============================================================================

class UserUpdate(BaseModel):
    """Internal schema for updating user"""
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None
    is_verified: Optional[bool] = None
    is_active: Optional[bool] = None

class PointsUpdate(BaseModel):
    """Internal schema for updating points"""
    points_change: int
    change_type: str
    description: str
    order_id: Optional[str] = None

class AddressCreate(BaseModel):
    """Internal schema for creating address"""
    user_id: str
    address_type: str
    full_name: str
    phone_number: str
    email: Optional[str] = None
    street_address: str
    building_number: Optional[str] = None
    flat_number: Optional[str] = None
    city: str
    area: Optional[str] = None
    is_default: bool = False

class AddressUpdate(BaseModel):
    """Internal schema for updating address"""
    address_type: Optional[str] = None
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None
    street_address: Optional[str] = None
    building_number: Optional[str] = None
    flat_number: Optional[str] = None
    city: Optional[str] = None
    area: Optional[str] = None

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

class EmailValidation(BaseModel):
    """Schema for email validation"""
    email: EmailStr
    
    @validator('email')
    def validate_email_format(cls, v):
        # Basic email validation (Pydantic handles the rest)
        if not v or '@' not in v:
            raise ValueError('Invalid email format')
        return v