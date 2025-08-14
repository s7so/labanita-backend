from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, validator
from enum import Enum

# =============================================================================
# ENUMS
# =============================================================================

class OfferType(str, Enum):
    """Offer type values"""
    PERCENTAGE_DISCOUNT = "percentage_discount"
    FIXED_AMOUNT_DISCOUNT = "fixed_amount_discount"
    BUY_ONE_GET_ONE = "buy_one_get_one"
    BUY_X_GET_Y = "buy_x_get_y"
    FREE_SHIPPING = "free_shipping"
    BUNDLE_DISCOUNT = "bundle_discount"

class OfferStatus(str, Enum):
    """Offer status values"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"
    SCHEDULED = "scheduled"
    PAUSED = "paused"

class DiscountType(str, Enum):
    """Discount type values"""
    PERCENTAGE = "percentage"
    FIXED_AMOUNT = "fixed_amount"
    FREE_ITEM = "free_item"
    FREE_SHIPPING = "free_shipping"

# =============================================================================
# RESPONSE SCHEMAS
# =============================================================================

class OfferResponse(BaseModel):
    """Response schema for offer"""
    offer_id: str = Field(..., description="Offer unique identifier")
    offer_name: str = Field(..., description="Offer name")
    description: Optional[str] = Field(None, description="Offer description")
    offer_type: OfferType = Field(..., description="Type of offer")
    discount_type: DiscountType = Field(..., description="Type of discount")
    discount_value: float = Field(..., description="Discount value (percentage or amount)")
    min_purchase_amount: Optional[float] = Field(None, description="Minimum purchase amount required")
    max_discount_amount: Optional[float] = Field(None, description="Maximum discount amount allowed")
    buy_quantity: Optional[int] = Field(None, description="Quantity to buy for BOGO offers")
    get_quantity: Optional[int] = Field(None, description="Quantity to get for BOGO offers")
    applicable_products: List[str] = Field(..., description="List of applicable product IDs")
    applicable_categories: List[str] = Field(..., description="List of applicable category IDs")
    excluded_products: List[str] = Field(..., description="List of excluded product IDs")
    excluded_categories: List[str] = Field(..., description="List of excluded category IDs")
    usage_limit_per_user: Optional[int] = Field(None, description="Usage limit per user")
    total_usage_limit: Optional[int] = Field(None, description="Total usage limit for the offer")
    current_usage_count: int = Field(..., description="Current usage count")
    start_date: datetime = Field(..., description="Offer start date")
    end_date: datetime = Field(..., description="Offer end date")
    is_active: bool = Field(..., description="Whether offer is currently active")
    status: OfferStatus = Field(..., description="Current offer status")
    priority: int = Field(..., description="Offer priority (higher = more important)")
    created_at: datetime = Field(..., description="When offer was created")
    updated_at: datetime = Field(..., description="When offer was last updated")
    
    class Config:
        from_attributes = True

class ProductOfferResponse(BaseModel):
    """Response schema for product-specific offer"""
    offer_id: str = Field(..., description="Offer unique identifier")
    product_id: str = Field(..., description="Product ID")
    offer_name: str = Field(..., description="Offer name")
    description: Optional[str] = Field(None, description="Offer description")
    offer_type: OfferType = Field(..., description="Type of offer")
    discount_type: DiscountType = Field(..., description="Type of discount")
    discount_value: float = Field(..., description="Discount value")
    original_price: float = Field(..., description="Original product price")
    discounted_price: float = Field(..., description="Price after discount")
    savings_amount: float = Field(..., description="Amount saved")
    savings_percentage: float = Field(..., description="Percentage saved")
    min_purchase_amount: Optional[float] = Field(None, description="Minimum purchase amount")
    max_discount_amount: Optional[float] = Field(None, description="Maximum discount amount")
    usage_limit_per_user: Optional[int] = Field(None, description="Usage limit per user")
    remaining_usage: Optional[int] = Field(None, description="Remaining usage for current user")
    start_date: datetime = Field(..., description="Offer start date")
    end_date: datetime = Field(..., description="Offer end date")
    is_active: bool = Field(..., description="Whether offer is active")
    priority: int = Field(..., description="Offer priority")
    
    class Config:
        from_attributes = True

class ActiveOffersResponse(BaseModel):
    """Response schema for active offers"""
    offers: List[OfferResponse] = Field(..., description="List of active offers")
    total_count: int = Field(..., description="Total number of active offers")
    categories_with_offers: List[str] = Field(..., description="Categories that have active offers")
    offer_types_available: List[OfferType] = Field(..., description="Types of offers available")
    summary: Dict[str, Any] = Field(..., description="Summary of active offers")

class OfferListResponse(BaseModel):
    """Response schema for list of offers"""
    offers: List[OfferResponse] = Field(..., description="List of offers")
    total_count: int = Field(..., description="Total number of offers")
    active_count: int = Field(..., description="Number of active offers")
    expired_count: int = Field(..., description="Number of expired offers")
    scheduled_count: int = Field(..., description="Number of scheduled offers")

class OfferDetailResponse(BaseModel):
    """Response schema for detailed offer information"""
    offer: OfferResponse = Field(..., description="Offer information")
    applicable_products_details: List[Dict[str, Any]] = Field(..., description="Details of applicable products")
    usage_statistics: Dict[str, Any] = Field(..., description="Offer usage statistics")
    performance_metrics: Dict[str, Any] = Field(..., description="Offer performance metrics")
    related_offers: List[OfferResponse] = Field(..., description="Related or similar offers")

# =============================================================================
# REQUEST SCHEMAS
# =============================================================================

class OfferCreateRequest(BaseModel):
    """Request schema for creating a new offer"""
    offer_name: str = Field(..., min_length=3, max_length=255, description="Offer name")
    description: Optional[str] = Field(None, max_length=1000, description="Offer description")
    offer_type: OfferType = Field(..., description="Type of offer")
    discount_type: DiscountType = Field(..., description="Type of discount")
    discount_value: float = Field(..., gt=0, description="Discount value")
    min_purchase_amount: Optional[float] = Field(None, ge=0, description="Minimum purchase amount")
    max_discount_amount: Optional[float] = Field(None, ge=0, description="Maximum discount amount")
    buy_quantity: Optional[int] = Field(None, ge=1, description="Quantity to buy for BOGO offers")
    get_quantity: Optional[int] = Field(None, ge=1, description="Quantity to get for BOGO offers")
    applicable_products: List[str] = Field(default=[], description="List of applicable product IDs")
    applicable_categories: List[str] = Field(default=[], description="List of applicable category IDs")
    excluded_products: List[str] = Field(default=[], description="List of excluded product IDs")
    excluded_categories: List[str] = Field(default=[], description="List of excluded category IDs")
    usage_limit_per_user: Optional[int] = Field(None, ge=1, description="Usage limit per user")
    total_usage_limit: Optional[int] = Field(None, ge=1, description="Total usage limit")
    start_date: datetime = Field(..., description="Offer start date")
    end_date: datetime = Field(..., description="Offer end date")
    priority: int = Field(1, ge=1, le=100, description="Offer priority")
    
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

class OfferUpdateRequest(BaseModel):
    """Request schema for updating an existing offer"""
    offer_name: Optional[str] = Field(None, min_length=3, max_length=255, description="Offer name")
    description: Optional[str] = Field(None, max_length=1000, description="Offer description")
    discount_value: Optional[float] = Field(None, gt=0, description="Discount value")
    min_purchase_amount: Optional[float] = Field(None, ge=0, description="Minimum purchase amount")
    max_discount_amount: Optional[float] = Field(None, ge=0, description="Maximum discount amount")
    buy_quantity: Optional[int] = Field(None, ge=1, description="Quantity to buy for BOGO offers")
    get_quantity: Optional[int] = Field(None, ge=1, description="Quantity to get for BOGO offers")
    applicable_products: Optional[List[str]] = Field(None, description="List of applicable product IDs")
    applicable_categories: Optional[List[str]] = Field(None, description="List of applicable category IDs")
    excluded_products: Optional[List[str]] = Field(None, description="List of excluded product IDs")
    excluded_categories: Optional[List[str]] = Field(None, description="List of excluded category IDs")
    usage_limit_per_user: Optional[int] = Field(None, ge=1, description="Usage limit per user")
    total_usage_limit: Optional[int] = Field(None, ge=1, description="Total usage limit")
    start_date: Optional[datetime] = Field(None, description="Offer start date")
    end_date: Optional[datetime] = Field(None, description="Offer end date")
    priority: Optional[int] = Field(None, ge=1, le=100, description="Offer priority")
    is_active: Optional[bool] = Field(None, description="Whether offer is active")

# =============================================================================
# FILTER SCHEMAS
# =============================================================================

class OfferFilter(BaseModel):
    """Schema for filtering offers"""
    offer_type: Optional[OfferType] = Field(None, description="Filter by offer type")
    discount_type: Optional[DiscountType] = Field(None, description="Filter by discount type")
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    status: Optional[OfferStatus] = Field(None, description="Filter by offer status")
    min_discount_value: Optional[float] = Field(None, ge=0, description="Minimum discount value")
    max_discount_value: Optional[float] = Field(None, ge=0, description="Maximum discount value")
    category_id: Optional[str] = Field(None, description="Filter by category")
    product_id: Optional[str] = Field(None, description="Filter by product")
    start_date_from: Optional[datetime] = Field(None, description="Start date from")
    start_date_to: Optional[datetime] = Field(None, description="Start date to")
    end_date_from: Optional[datetime] = Field(None, description="End date from")
    end_date_to: Optional[datetime] = Field(None, description="End date to")
    search: Optional[str] = Field(None, description="Search in offer name and description")
    sort_by: str = Field("priority", description="Sort field")
    sort_order: str = Field("desc", description="Sort order (asc/desc)")

# =============================================================================
# INTERNAL SCHEMAS
# =============================================================================

class OfferCreate(BaseModel):
    """Internal schema for creating offer"""
    offer_name: str
    description: Optional[str] = None
    offer_type: OfferType
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
    usage_limit_per_user: Optional[int] = None
    total_usage_limit: Optional[int] = None
    start_date: datetime
    end_date: datetime
    priority: int = 1
    is_active: bool = True
    status: OfferStatus = OfferStatus.SCHEDULED

class OfferUpdate(BaseModel):
    """Internal schema for updating offer"""
    offer_name: Optional[str] = None
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
    usage_limit_per_user: Optional[int] = None
    total_usage_limit: Optional[int] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    priority: Optional[int] = None
    is_active: Optional[bool] = None
    status: Optional[OfferStatus] = None

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

class PaginatedOffersResponse(BaseModel):
    """Paginated response for offers"""
    offers: List[OfferResponse] = Field(..., description="Offers in current page")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Page size")
    total: int = Field(..., description="Total number of offers")
    pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_prev: bool = Field(..., description="Whether there is a previous page")

# =============================================================================
# STATISTICS SCHEMAS
# =============================================================================

class OfferStatsResponse(BaseModel):
    """Response schema for offer statistics"""
    offer_id: str = Field(..., description="Offer unique identifier")
    offer_name: str = Field(..., description="Offer name")
    total_usage: int = Field(..., description="Total times offer was used")
    total_discount_given: float = Field(..., description="Total discount amount given")
    average_order_value: float = Field(..., description="Average order value with this offer")
    conversion_rate: float = Field(..., description="Conversion rate for this offer")
    user_engagement: int = Field(..., description="Number of unique users who used this offer")
    revenue_impact: float = Field(..., description="Revenue impact of this offer")
    performance_score: float = Field(..., description="Overall performance score")

class OfferAnalyticsResponse(BaseModel):
    """Response schema for offer analytics"""
    total_offers: int = Field(..., description="Total number of offers")
    active_offers: int = Field(..., description="Number of active offers")
    expired_offers: int = Field(..., description="Number of expired offers")
    scheduled_offers: int = Field(..., description="Number of scheduled offers")
    total_discount_given: float = Field(..., description="Total discount amount given")
    total_orders_with_offers: int = Field(..., description="Total orders that used offers")
    average_discount_per_order: float = Field(..., description="Average discount per order")
    top_performing_offers: List[Dict[str, Any]] = Field(..., description="Top performing offers")
    offer_type_distribution: Dict[str, int] = Field(..., description="Distribution of offer types")
    category_performance: List[Dict[str, Any]] = Field(..., description="Category performance with offers")

# =============================================================================
# VALIDATION SCHEMAS
# =============================================================================

class OfferValidationRequest(BaseModel):
    """Request schema for validating offer applicability"""
    product_ids: List[str] = Field(..., description="Product IDs to check")
    category_ids: List[str] = Field(..., description="Category IDs to check")
    cart_total: float = Field(..., ge=0, description="Cart total amount")
    user_id: Optional[str] = Field(None, description="User ID for usage limit checking")

class OfferValidationResponse(BaseModel):
    """Response schema for offer validation results"""
    applicable_offers: List[OfferResponse] = Field(..., description="Offers that can be applied")
    best_offer: Optional[OfferResponse] = Field(None, description="Best offer to apply")
    total_savings: float = Field(..., description="Total potential savings")
    validation_errors: List[str] = Field(..., description="Any validation errors")
    recommendations: List[str] = Field(..., description="Recommendations for better offers")