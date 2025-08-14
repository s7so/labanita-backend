from typing import Optional, List, Dict, Any
from datetime import datetime, time
from decimal import Decimal
from pydantic import BaseModel, Field, validator
from enum import Enum

# =============================================================================
# ENUMS
# =============================================================================

class StoreStatus(str, Enum):
    """Store status values"""
    OPEN = "open"
    CLOSED = "closed"
    MAINTENANCE = "maintenance"
    HOLIDAY = "holiday"
    TEMPORARILY_CLOSED = "temporarily_closed"

class DeliveryAreaType(str, Enum):
    """Delivery area type values"""
    LOCAL = "local"
    REGIONAL = "regional"
    NATIONAL = "national"
    INTERNATIONAL = "international"
    SAME_DAY = "same_day"
    NEXT_DAY = "next_day"

class DeliveryFeeType(str, Enum):
    """Delivery fee type values"""
    FIXED = "fixed"
    PERCENTAGE = "percentage"
    TIERED = "tiered"
    FREE_ABOVE_THRESHOLD = "free_above_threshold"
    DISTANCE_BASED = "distance_based"

class OperatingDay(str, Enum):
    """Operating day values"""
    MONDAY = "monday"
    TUESDAY = "tuesday"
    WEDNESDAY = "wednesday"
    THURSDAY = "thursday"
    FRIDAY = "friday"
    SATURDAY = "saturday"
    SUNDAY = "sunday"

# =============================================================================
# STORE INFO SCHEMAS
# =============================================================================

class StoreContactInfo(BaseModel):
    """Store contact information"""
    phone: str = Field(..., description="Store phone number")
    email: str = Field(..., description="Store email address")
    website: Optional[str] = Field(None, description="Store website URL")
    whatsapp: Optional[str] = Field(None, description="Store WhatsApp number")
    social_media: Dict[str, str] = Field(default_factory=dict, description="Social media links")

class StoreLocation(BaseModel):
    """Store physical location"""
    address: str = Field(..., description="Store address")
    city: str = Field(..., description="Store city")
    state: str = Field(..., description="Store state/province")
    country: str = Field(..., description="Store country")
    postal_code: str = Field(..., description="Store postal code")
    latitude: Optional[float] = Field(None, description="Store latitude coordinate")
    longitude: Optional[float] = Field(None, description="Store longitude coordinate")
    landmark: Optional[str] = Field(None, description="Nearby landmark")

class StoreInfoResponse(BaseModel):
    """Response schema for store information"""
    store_id: str = Field(..., description="Store unique identifier")
    store_name: str = Field(..., description="Store name")
    store_description: str = Field(..., description="Store description")
    store_logo: Optional[str] = Field(None, description="Store logo URL")
    store_banner: Optional[str] = Field(None, description="Store banner image URL")
    store_status: StoreStatus = Field(..., description="Current store status")
    contact_info: StoreContactInfo = Field(..., description="Store contact information")
    location: StoreLocation = Field(..., description="Store physical location")
    features: List[str] = Field(..., description="Store features and amenities")
    policies: Dict[str, str] = Field(..., description="Store policies")
    created_at: datetime = Field(..., description="When store was created")
    updated_at: datetime = Field(..., description="When store was last updated")
    
    class Config:
        from_attributes = True

# =============================================================================
# DELIVERY AREA SCHEMAS
# =============================================================================

class DeliveryAreaResponse(BaseModel):
    """Response schema for delivery area"""
    area_id: str = Field(..., description="Delivery area unique identifier")
    area_name: str = Field(..., description="Delivery area name")
    area_type: DeliveryAreaType = Field(..., description="Type of delivery area")
    description: str = Field(..., description="Area description")
    cities: List[str] = Field(..., description="Cities covered in this area")
    postal_codes: List[str] = Field(..., description="Postal codes covered")
    estimated_delivery_time: str = Field(..., description="Estimated delivery time")
    is_active: bool = Field(..., description="Whether area is active for delivery")
    created_at: datetime = Field(..., description="When area was created")
    updated_at: datetime = Field(..., description="When area was last updated")
    
    class Config:
        from_attributes = True

class DeliveryAreasResponse(BaseModel):
    """Response schema for list of delivery areas"""
    areas: List[DeliveryAreaResponse] = Field(..., description="List of delivery areas")
    total_count: int = Field(..., description="Total number of delivery areas")
    active_areas: int = Field(..., description="Number of active delivery areas")
    coverage_summary: Dict[str, int] = Field(..., description="Coverage summary by type")

# =============================================================================
# DELIVERY FEE SCHEMAS
# =============================================================================

class DeliveryFeeTier(BaseModel):
    """Delivery fee tier for tiered pricing"""
    min_amount: float = Field(..., ge=0, description="Minimum order amount for this tier")
    max_amount: Optional[float] = Field(None, ge=0, description="Maximum order amount for this tier")
    fee: float = Field(..., ge=0, description="Delivery fee for this tier")
    description: str = Field(..., description="Tier description")

class DeliveryFeeResponse(BaseModel):
    """Response schema for delivery fee calculation"""
    area_id: str = Field(..., description="Delivery area ID")
    area_name: str = Field(..., description="Delivery area name")
    fee_type: DeliveryFeeType = Field(..., description="Type of delivery fee calculation")
    base_fee: float = Field(..., description="Base delivery fee")
    final_fee: float = Field(..., description="Final calculated delivery fee")
    currency: str = Field(..., description="Currency for the fee")
    calculation_details: Dict[str, Any] = Field(..., description="Detailed calculation breakdown")
    free_delivery_threshold: Optional[float] = Field(None, description="Amount needed for free delivery")
    estimated_delivery_time: str = Field(..., description="Estimated delivery time")
    is_free_delivery: bool = Field(..., description="Whether delivery is free")
    applied_discounts: List[Dict[str, Any]] = Field(..., description="Applied delivery discounts")
    
    class Config:
        from_attributes = True

class DeliveryFeeRequest(BaseModel):
    """Request schema for delivery fee calculation"""
    area_id: str = Field(..., description="Delivery area ID")
    order_amount: float = Field(..., ge=0, description="Order subtotal amount")
    order_weight: Optional[float] = Field(None, ge=0, description="Order total weight in kg")
    delivery_date: Optional[datetime] = Field(None, description="Preferred delivery date")
    is_express: bool = Field(False, description="Whether express delivery is requested")
    
    @validator('order_amount')
    def validate_order_amount(cls, v):
        if v < 0:
            raise ValueError('Order amount cannot be negative')
        return v

# =============================================================================
# OPERATING HOURS SCHEMAS
# =============================================================================

class TimeSlot(BaseModel):
    """Time slot for operating hours"""
    start_time: time = Field(..., description="Start time")
    end_time: time = Field(..., description="End time")
    is_break: bool = Field(False, description="Whether this is a break period")
    description: Optional[str] = Field(None, description="Time slot description")

class OperatingDaySchedule(BaseModel):
    """Operating schedule for a specific day"""
    day: OperatingDay = Field(..., description="Day of the week")
    is_open: bool = Field(..., description="Whether store is open on this day")
    time_slots: List[TimeSlot] = Field(..., description="Operating time slots")
    special_notes: Optional[str] = Field(None, description="Special notes for this day")
    is_holiday: bool = Field(False, description="Whether this is a holiday")
    holiday_name: Optional[str] = Field(None, description="Holiday name if applicable")

class OperatingHoursResponse(BaseModel):
    """Response schema for store operating hours"""
    store_id: str = Field(..., description="Store ID")
    store_name: str = Field(..., description="Store name")
    current_status: StoreStatus = Field(..., description="Current store status")
    is_currently_open: bool = Field(..., description="Whether store is currently open")
    next_open_time: Optional[datetime] = Field(None, description="Next time store will open")
    weekly_schedule: List[OperatingDaySchedule] = Field(..., description="Weekly operating schedule")
    special_hours: List[Dict[str, Any]] = Field(..., description="Special operating hours")
    holidays: List[Dict[str, Any]] = Field(..., description="Upcoming holidays")
    timezone: str = Field(..., description="Store timezone")
    last_updated: datetime = Field(..., description="When operating hours were last updated")
    
    class Config:
        from_attributes = True

# =============================================================================
# INTERNAL SCHEMAS
# =============================================================================

class StoreInfoCreate(BaseModel):
    """Internal schema for creating store info"""
    store_name: str = Field(..., description="Store name")
    store_description: str = Field(..., description="Store description")
    store_logo: Optional[str] = Field(None, description="Store logo URL")
    store_banner: Optional[str] = Field(None, description="Store banner image URL")
    contact_info: StoreContactInfo = Field(..., description="Store contact information")
    location: StoreLocation = Field(..., description="Store physical location")
    features: List[str] = Field(..., description="Store features and amenities")
    policies: Dict[str, str] = Field(..., description="Store policies")

class StoreInfoUpdate(BaseModel):
    """Internal schema for updating store info"""
    store_name: Optional[str] = Field(None, description="Store name")
    store_description: Optional[str] = Field(None, description="Store description")
    store_logo: Optional[str] = Field(None, description="Store logo URL")
    store_banner: Optional[str] = Field(None, description="Store banner image URL")
    store_status: Optional[StoreStatus] = Field(None, description="Store status")
    contact_info: Optional[StoreContactInfo] = Field(None, description="Store contact information")
    location: Optional[StoreLocation] = Field(None, description="Store physical location")
    features: Optional[List[str]] = Field(None, description="Store features and amenities")
    policies: Optional[Dict[str, str]] = Field(None, description="Store policies")

class DeliveryAreaCreate(BaseModel):
    """Internal schema for creating delivery area"""
    area_name: str = Field(..., description="Delivery area name")
    area_type: DeliveryAreaType = Field(..., description="Type of delivery area")
    description: str = Field(..., description="Area description")
    cities: List[str] = Field(..., description="Cities covered in this area")
    postal_codes: List[str] = Field(..., description="Postal codes covered")
    estimated_delivery_time: str = Field(..., description="Estimated delivery time")
    is_active: bool = Field(True, description="Whether area is active for delivery")

class DeliveryAreaUpdate(BaseModel):
    """Internal schema for updating delivery area"""
    area_name: Optional[str] = Field(None, description="Delivery area name")
    area_type: Optional[DeliveryAreaType] = Field(None, description="Type of delivery area")
    description: Optional[str] = Field(None, description="Area description")
    cities: Optional[List[str]] = Field(None, description="Cities covered in this area")
    postal_codes: Optional[List[str]] = Field(None, description="Postal codes covered")
    estimated_delivery_time: Optional[str] = Field(None, description="Estimated delivery time")
    is_active: Optional[bool] = Field(None, description="Whether area is active for delivery")

class OperatingHoursCreate(BaseModel):
    """Internal schema for creating operating hours"""
    weekly_schedule: List[OperatingDaySchedule] = Field(..., description="Weekly operating schedule")
    timezone: str = Field(..., description="Store timezone")
    special_hours: Optional[List[Dict[str, Any]]] = Field(None, description="Special operating hours")
    holidays: Optional[List[Dict[str, Any]]] = Field(None, description="Upcoming holidays")

class OperatingHoursUpdate(BaseModel):
    """Internal schema for updating operating hours"""
    weekly_schedule: Optional[List[OperatingDaySchedule]] = Field(None, description="Weekly operating schedule")
    timezone: Optional[str] = Field(None, description="Store timezone")
    special_hours: Optional[List[Dict[str, Any]]] = Field(None, description="Special operating hours")
    holidays: Optional[List[Dict[str, Any]]] = Field(None, description="Upcoming holidays")