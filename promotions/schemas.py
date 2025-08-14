from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal
from pydantic import BaseModel, Field, validator
from enum import Enum

# =============================================================================
# ENUMS
# =============================================================================

class PromotionType(str, Enum):
    """Promotion type values"""
    PERCENTAGE_DISCOUNT = "percentage_discount"
    FIXED_AMOUNT_DISCOUNT = "fixed_amount_discount"
    BUY_ONE_GET_ONE = "buy_one_get_one"
    BUY_X_GET_Y = "buy_x_get_y"
    FREE_SHIPPING = "free_shipping"
    BUNDLE_DISCOUNT = "bundle_discount"
    CASHBACK = "cashback"
    LOYALTY_POINTS = "loyalty_points"
    FIRST_TIME_PURCHASE = "first_time_purchase"
    BIRTHDAY_OFFER = "birthday_offer"
    SEASONAL_SALE = "seasonal_sale"
    FLASH_SALE = "flash_sale"

class PromotionStatus(str, Enum):
    """Promotion status values"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"
    SCHEDULED = "scheduled"
    PAUSED = "paused"
    DEPLETED = "depleted"

class DiscountType(str, Enum):
    """Discount type values"""
    PERCENTAGE = "percentage"
    FIXED_AMOUNT = "fixed_amount"
    FREE_ITEM = "free_item"
    FREE_SHIPPING = "free_shipping"
    CASHBACK = "cashback"
    POINTS = "points"

class PromotionTrigger(str, Enum):
    """Promotion trigger values"""
    MANUAL = "manual"
    AUTOMATIC = "automatic"
    SCHEDULED = "scheduled"
    EVENT_BASED = "event_based"
    USER_ACTION = "user_action"
    SYSTEM_GENERATED = "system_generated"

# =============================================================================
# RESPONSE SCHEMAS
# =============================================================================

class PromotionResponse(BaseModel):
    """Response schema for promotion"""
    promotion_id: str = Field(..., description="Promotion unique identifier")
    promotion_name: str = Field(..., description="Promotion name")
    description: Optional[str] = Field(None, description="Promotion description")
    promotion_type: PromotionType = Field(..., description="Type of promotion")
    discount_type: DiscountType = Field(..., description="Type of discount")
    discount_value: float = Field(..., description="Discount value (percentage or amount)")
    min_purchase_amount: Optional[float] = Field(None, description="Minimum purchase amount required")
    max_discount_amount: Optional[float] = Field(None, description="Maximum discount amount allowed")
    buy_quantity: Optional[int] = Field(None, description="Quantity to buy for BOGO promotions")
    get_quantity: Optional[int] = Field(None, description="Quantity to get for BOGO promotions")
    applicable_products: List[str] = Field(..., description="List of applicable product IDs")
    applicable_categories: List[str] = Field(..., description="List of applicable category IDs")
    excluded_products: List[str] = Field(..., description="List of excluded product IDs")
    excluded_categories: List[str] = Field(..., description="List of excluded category IDs")
    user_groups: List[str] = Field(..., description="User groups eligible for promotion")
    usage_limit_per_user: Optional[int] = Field(None, description="Usage limit per user")
    total_usage_limit: Optional[int] = Field(None, description="Total usage limit for the promotion")
    current_usage_count: int = Field(..., description="Current usage count")
    start_date: datetime = Field(..., description="Promotion start date")
    end_date: datetime = Field(..., description="Promotion end date")
    is_active: bool = Field(..., description="Whether promotion is currently active")
    status: PromotionStatus = Field(..., description="Current promotion status")
    priority: int = Field(..., description="Promotion priority (higher = more important)")
    trigger_type: PromotionTrigger = Field(..., description="How promotion is triggered")
    conditions: Dict[str, Any] = Field(..., description="Additional promotion conditions")
    created_at: datetime = Field(..., description="When promotion was created")
    updated_at: datetime = Field(..., description="When promotion was last updated")
    
    class Config:
        from_attributes = True

class ActivePromotionsResponse(BaseModel):
    """Response schema for active promotions"""
    promotions: List[PromotionResponse] = Field(..., description="List of active promotions")
    total_count: int = Field(..., description="Total number of active promotions")
    categories_with_promotions: List[str] = Field(..., description="Categories that have active promotions")
    promotion_types_available: List[PromotionType] = Field(..., description="Types of promotions available")
    summary: Dict[str, Any] = Field(..., description="Summary of active promotions")
    user_specific_promotions: List[PromotionResponse] = Field(..., description="Promotions specific to current user")

class PromotionValidationRequest(BaseModel):
    """Request schema for validating promotion applicability"""
    promotion_code: Optional[str] = Field(None, description="Promotion code to validate")
    product_ids: List[str] = Field(..., description="Product IDs to check")
    category_ids: List[str] = Field(..., description="Category IDs to check")
    cart_total: float = Field(..., ge=0, description="Cart total amount")
    user_id: str = Field(..., description="User ID for validation")
    user_groups: List[str] = Field(..., description="User groups for validation")
    purchase_history: Dict[str, Any] = Field(..., description="User purchase history")

class PromotionValidationResponse(BaseModel):
    """Response schema for promotion validation results"""
    is_valid: bool = Field(..., description="Whether promotion is valid for the request")
    promotion: Optional[PromotionResponse] = Field(None, description="Promotion details if valid")
    discount_amount: float = Field(..., description="Calculated discount amount")
    discount_percentage: float = Field(..., description="Calculated discount percentage")
    final_price: float = Field(..., description="Final price after discount")
    savings_amount: float = Field(..., description="Amount saved")
    validation_errors: List[str] = Field(..., description="Any validation errors")
    warnings: List[str] = Field(..., description="Any warnings")
    recommendations: List[str] = Field(..., description="Recommendations for better promotions")
    terms_and_conditions: List[str] = Field(..., description="Terms and conditions for the promotion")

class PromotionApplicationRequest(BaseModel):
    """Request schema for applying promotion"""
    promotion_id: str = Field(..., description="Promotion ID to apply")
    user_id: str = Field(..., description="User ID applying the promotion")
    cart_items: List[Dict[str, Any]] = Field(..., description="Cart items to apply promotion to")
    cart_total: float = Field(..., ge=0, description="Cart total amount")
    session_id: Optional[str] = Field(None, description="Session ID for tracking")

class PromotionApplicationResponse(BaseModel):
    """Response schema for promotion application results"""
    success: bool = Field(..., description="Whether promotion was applied successfully")
    promotion_id: str = Field(..., description="Promotion ID that was applied")
    promotion_name: str = Field(..., description="Name of applied promotion")
    discount_amount: float = Field(..., description="Total discount amount applied")
    discount_percentage: float = Field(..., description="Total discount percentage")
    final_cart_total: float = Field(..., description="Final cart total after promotion")
    savings_amount: float = Field(..., description="Total amount saved")
    applied_items: List[Dict[str, Any]] = Field(..., description="Items that had promotion applied")
    remaining_usage: Optional[int] = Field(None, description="Remaining usage for user")
    expiration_time: Optional[datetime] = Field(None, description="When promotion expires")
    message: str = Field(..., description="Application result message")
    warnings: List[str] = Field(..., description="Any warnings about the application")

class PromotionRemovalRequest(BaseModel):
    """Request schema for removing promotion"""
    promotion_id: str = Field(..., description="Promotion ID to remove")
    user_id: str = Field(..., description="User ID removing the promotion")
    cart_items: List[Dict[str, Any]] = Field(..., description="Cart items to remove promotion from")
    reason: Optional[str] = Field(None, description="Reason for removal")

class PromotionRemovalResponse(BaseModel):
    """Response schema for promotion removal results"""
    success: bool = Field(..., description="Whether promotion was removed successfully")
    promotion_id: str = Field(..., description="Promotion ID that was removed")
    promotion_name: str = Field(..., description="Name of removed promotion")
    original_cart_total: float = Field(..., description="Original cart total before promotion")
    new_cart_total: float = Field(..., description="New cart total after removal")
    removed_discount: float = Field(..., description="Discount amount that was removed")
    affected_items: List[Dict[str, Any]] = Field(..., description="Items that were affected")
    message: str = Field(..., description="Removal result message")

# =============================================================================
# REQUEST SCHEMAS
# =============================================================================

class PromotionCreateRequest(BaseModel):
    """Request schema for creating a new promotion"""
    promotion_name: str = Field(..., min_length=3, max_length=255, description="Promotion name")
    description: Optional[str] = Field(None, max_length=1000, description="Promotion description")
    promotion_type: PromotionType = Field(..., description="Type of promotion")
    discount_type: DiscountType = Field(..., description="Type of discount")
    discount_value: float = Field(..., gt=0, description="Discount value")
    min_purchase_amount: Optional[float] = Field(None, ge=0, description="Minimum purchase amount")
    max_discount_amount: Optional[float] = Field(None, ge=0, description="Maximum discount amount")
    buy_quantity: Optional[int] = Field(None, ge=1, description="Quantity to buy for BOGO promotions")
    get_quantity: Optional[int] = Field(None, ge=1, description="Quantity to get for BOGO promotions")
    applicable_products: List[str] = Field(default=[], description="List of applicable product IDs")
    applicable_categories: List[str] = Field(default=[], description="List of applicable category IDs")
    excluded_products: List[str] = Field(default=[], description="List of excluded product IDs")
    excluded_categories: List[str] = Field(default=[], description="List of excluded category IDs")
    user_groups: List[str] = Field(default=[], description="User groups eligible for promotion")
    usage_limit_per_user: Optional[int] = Field(None, ge=1, description="Usage limit per user")
    total_usage_limit: Optional[int] = Field(None, ge=1, description="Total usage limit")
    start_date: datetime = Field(..., description="Promotion start date")
    end_date: datetime = Field(..., description="Promotion end date")
    priority: int = Field(1, ge=1, le=100, description="Promotion priority")
    trigger_type: PromotionTrigger = Field(PromotionTrigger.MANUAL, description="How promotion is triggered")
    conditions: Dict[str, Any] = Field(default={}, description="Additional promotion conditions")
    
    @validator('end_date')
    def validate_end_date(cls, v, values):
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError('End date must be after start date')
        return v
    
    @validator('discount_value')
    def validate_discount_value(cls, v, values):
        if 'discount_type' in values:
            if values['discount_type'] == DiscountType.PERCENTAGE and v > 100:
                raise ValueError('Percentage discount cannot exceed 100%')
            if values['discount_type'] == DiscountType.FIXED_AMOUNT and v <= 0:
                raise ValueError('Fixed amount discount must be greater than 0')
        return v

class PromotionUpdateRequest(BaseModel):
    """Request schema for updating an existing promotion"""
    promotion_name: Optional[str] = Field(None, min_length=3, max_length=255, description="Promotion name")
    description: Optional[str] = Field(None, max_length=1000, description="Promotion description")
    discount_value: Optional[float] = Field(None, gt=0, description="Discount value")
    min_purchase_amount: Optional[float] = Field(None, ge=0, description="Minimum purchase amount")
    max_discount_amount: Optional[float] = Field(None, ge=0, description="Maximum discount amount")
    buy_quantity: Optional[int] = Field(None, ge=1, description="Quantity to buy for BOGO promotions")
    get_quantity: Optional[int] = Field(None, ge=1, description="Quantity to get for BOGO promotions")
    applicable_products: Optional[List[str]] = Field(None, description="List of applicable product IDs")
    applicable_categories: Optional[List[str]] = Field(None, description="List of applicable category IDs")
    excluded_products: Optional[List[str]] = Field(None, description="List of excluded product IDs")
    excluded_categories: Optional[List[str]] = Field(None, description="List of excluded category IDs")
    user_groups: Optional[List[str]] = Field(None, description="User groups eligible for promotion")
    usage_limit_per_user: Optional[int] = Field(None, ge=1, description="Usage limit per user")
    total_usage_limit: Optional[int] = Field(None, ge=1, description="Total usage limit")
    start_date: Optional[datetime] = Field(None, description="Promotion start date")
    end_date: Optional[datetime] = Field(None, description="Promotion end date")
    priority: Optional[int] = Field(None, ge=1, le=100, description="Promotion priority")
    trigger_type: Optional[PromotionTrigger] = Field(None, description="How promotion is triggered")
    conditions: Optional[Dict[str, Any]] = Field(None, description="Additional promotion conditions")
    is_active: Optional[bool] = Field(None, description="Whether promotion is active")

# =============================================================================
# FILTER SCHEMAS
# =============================================================================

class PromotionFilter(BaseModel):
    """Schema for filtering promotions"""
    promotion_type: Optional[PromotionType] = Field(None, description="Filter by promotion type")
    discount_type: Optional[DiscountType] = Field(None, description="Filter by discount type")
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    status: Optional[PromotionStatus] = Field(None, description="Filter by promotion status")
    trigger_type: Optional[PromotionTrigger] = Field(None, description="Filter by trigger type")
    min_discount_value: Optional[float] = Field(None, ge=0, description="Minimum discount value")
    max_discount_value: Optional[float] = Field(None, ge=0, description="Maximum discount value")
    category_id: Optional[str] = Field(None, description="Filter by category")
    product_id: Optional[str] = Field(None, description="Filter by product")
    user_group: Optional[str] = Field(None, description="Filter by user group")
    start_date_from: Optional[datetime] = Field(None, description="Start date from")
    start_date_to: Optional[datetime] = Field(None, description="Start date to")
    end_date_from: Optional[datetime] = Field(None, description="End date from")
    end_date_to: Optional[datetime] = Field(None, description="End date to")
    search: Optional[str] = Field(None, description="Search in promotion name and description")
    sort_by: str = Field("priority", description="Sort field")
    sort_order: str = Field("desc", description="Sort order (asc/desc)")

# =============================================================================
# INTERNAL SCHEMAS
# =============================================================================

class PromotionCreate(BaseModel):
    """Internal schema for creating promotion"""
    promotion_name: str
    description: Optional[str] = None
    promotion_type: PromotionType
    discount_type: DiscountType
    discount_value: float
    min_purchase_amount: Optional[float] = None
    max_discount_amount: Optional[float] = None
    buy_quantity: Optional[int] = None
    get_quantity: Optional[int] = None
    applicable_products: List[str] = []
    applicable_categories: List[str] = []
    excluded_products: List[str] = []
    excluded_categories: List[str] = []
    user_groups: List[str] = []
    usage_limit_per_user: Optional[int] = None
    total_usage_limit: Optional[int] = None
    start_date: datetime
    end_date: datetime
    priority: int = 1
    trigger_type: PromotionTrigger = PromotionTrigger.MANUAL
    conditions: Dict[str, Any] = {}
    is_active: bool = True
    status: PromotionStatus = PromotionStatus.SCHEDULED

class PromotionUpdate(BaseModel):
    """Internal schema for updating promotion"""
    promotion_name: Optional[str] = None
    description: Optional[str] = None
    discount_value: Optional[float] = None
    min_purchase_amount: Optional[float] = None
    max_discount_amount: Optional[float] = None
    buy_quantity: Optional[int] = None
    get_quantity: Optional[int] = None
    applicable_products: Optional[List[str]] = None
    applicable_categories: Optional[List[str]] = None
    excluded_products: Optional[List[str]] = None
    excluded_categories: Optional[List[str]] = None
    user_groups: Optional[List[str]] = None
    usage_limit_per_user: Optional[int] = None
    total_usage_limit: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    priority: Optional[int] = None
    trigger_type: Optional[PromotionTrigger] = None
    conditions: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    status: Optional[PromotionStatus] = None

# =============================================================================
# PAGINATION SCHEMAS
# =============================================================================

class PaginationParams(BaseModel):
    """Schema for pagination parameters"""
    page: int = Field(1, ge=1, description="Page number")
    size: int = Field(20, ge=1, le=100, description="Page size")
    
    @property
    def offset(self) -> int:
        return (self.page - 1) * self.size

class PaginatedPromotionsResponse(BaseModel):
    """Paginated response for promotions"""
    promotions: List[PromotionResponse] = Field(..., description="Promotions in current page")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Page size")
    total: int = Field(..., description="Total number of promotions")
    pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_prev: bool = Field(..., description="Whether there is a previous page")

# =============================================================================
# STATISTICS SCHEMAS
# =============================================================================

class PromotionStatsResponse(BaseModel):
    """Response schema for promotion statistics"""
    promotion_id: str = Field(..., description="Promotion unique identifier")
    promotion_name: str = Field(..., description="Promotion name")
    total_usage: int = Field(..., description="Total times promotion was used")
    total_discount_given: float = Field(..., description="Total discount amount given")
    average_order_value: float = Field(..., description="Average order value with this promotion")
    conversion_rate: float = Field(..., description="Conversion rate for this promotion")
    user_engagement: int = Field(..., description="Number of unique users who used this promotion")
    revenue_impact: float = Field(..., description="Revenue impact of this promotion")
    performance_score: float = Field(..., description="Overall performance score")

class PromotionAnalyticsResponse(BaseModel):
    """Response schema for promotion analytics"""
    total_promotions: int = Field(..., description="Total number of promotions")
    active_promotions: int = Field(..., description="Number of active promotions")
    expired_promotions: int = Field(..., description="Number of expired promotions")
    scheduled_promotions: int = Field(..., description="Number of scheduled promotions")
    total_discount_given: float = Field(..., description="Total discount amount given")
    total_orders_with_promotions: int = Field(..., description="Total orders that used promotions")
    average_discount_per_order: float = Field(..., description="Average discount per order")
    top_performing_promotions: List[Dict[str, Any]] = Field(..., description="Top performing promotions")
    promotion_type_distribution: Dict[str, int] = Field(..., description="Distribution of promotion types")
    category_performance: List[Dict[str, Any]] = Field(..., description="Category performance with promotions")

# =============================================================================
# USER PROMOTION SCHEMAS
# =============================================================================

class UserPromotionResponse(BaseModel):
    """Response schema for user-specific promotions"""
    promotion_id: str = Field(..., description="Promotion unique identifier")
    promotion_name: str = Field(..., description="Promotion name")
    description: Optional[str] = Field(None, description="Promotion description")
    promotion_type: PromotionType = Field(..., description="Type of promotion")
    discount_type: DiscountType = Field(..., description="Type of discount")
    discount_value: float = Field(..., description="Discount value")
    min_purchase_amount: Optional[float] = Field(None, description="Minimum purchase amount")
    max_discount_amount: Optional[float] = Field(None, description="Maximum discount amount")
    usage_limit_per_user: Optional[int] = Field(None, description="Usage limit per user")
    current_usage: int = Field(..., description="Current usage by user")
    remaining_usage: int = Field(..., description="Remaining usage for user")
    start_date: datetime = Field(..., description="Promotion start date")
    end_date: datetime = Field(..., description="Promotion end date")
    is_eligible: bool = Field(..., description="Whether user is eligible for this promotion")
    eligibility_reason: Optional[str] = Field(None, description="Reason for eligibility or ineligibility")
    priority: int = Field(..., description="Promotion priority")
    estimated_savings: float = Field(..., description="Estimated savings if applied")
    
    class Config:
        from_attributes = True

class UserPromotionsResponse(BaseModel):
    """Response schema for user promotions list"""
    user_id: str = Field(..., description="User ID")
    available_promotions: List[UserPromotionResponse] = Field(..., description="Promotions available to user")
    applied_promotions: List[UserPromotionResponse] = Field(..., description="Promotions currently applied")
    expired_promotions: List[UserPromotionResponse] = Field(..., description="Promotions that expired")
    total_available: int = Field(..., description="Total available promotions")
    total_applied: int = Field(..., description="Total applied promotions")
    total_savings: float = Field(..., description="Total savings from applied promotions")