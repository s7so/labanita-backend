"""
Pydantic schemas for Labanita API.
Provides data validation, request bodies, and response models for all API endpoints.
"""

from datetime import datetime
from typing import List, Optional, Union
from decimal import Decimal
from pydantic import BaseModel, Field, validator, UUID4
from enum import Enum


# ========================================
# ENUM DEFINITIONS
# ========================================

class PaymentTypeEnum(str, Enum):
    """Payment method types."""
    CARD = "CARD"
    APPLE_PAY = "APPLE_PAY"
    CASH = "CASH"


class DiscountTypeEnum(str, Enum):
    """Discount types for promotions and offers."""
    PERCENTAGE = "PERCENTAGE"
    FIXED_AMOUNT = "FIXED_AMOUNT"


class OrderStatusEnum(str, Enum):
    """Order status values."""
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    PREPARING = "PREPARING"
    OUT_FOR_DELIVERY = "OUT_FOR_DELIVERY"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


# ========================================
# BASE SCHEMAS
# ========================================

class TimestampBase(BaseModel):
    """Base schema with timestamp fields."""
    created_at: datetime
    updated_at: datetime


class UUIDBase(BaseModel):
    """Base schema with UUID ID field."""
    id: UUID4 = Field(..., alias="id")


# ========================================
# USER SCHEMAS
# ========================================

class UserBase(BaseModel):
    """Base user schema with common fields."""
    phone_number: str = Field(..., min_length=1, max_length=20)
    full_name: Optional[str] = Field(None, max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    facebook_id: Optional[str] = Field(None, max_length=255)
    google_id: Optional[str] = Field(None, max_length=255)
    points_balance: int = Field(0, ge=0)
    points_expiry_date: Optional[datetime] = None
    is_active: bool = True


class UserCreate(UserBase):
    """Schema for creating a new user."""
    pass


class UserUpdate(BaseModel):
    """Schema for updating user information."""
    full_name: Optional[str] = Field(None, max_length=255)
    email: Optional[str] = Field(None, max_length=255)
    facebook_id: Optional[str] = Field(None, max_length=255)
    google_id: Optional[str] = Field(None, max_length=255)
    points_balance: Optional[int] = Field(None, ge=0)
    points_expiry_date: Optional[datetime] = None
    is_active: Optional[bool] = None


class UserResponse(UserBase, TimestampBase):
    """Schema for user response."""
    user_id: UUID4
    points_balance: int
    is_active: bool

    class Config:
        from_attributes = True
        populate_by_name = True


# ========================================
# CATEGORY SCHEMAS
# ========================================

class CategoryBase(BaseModel):
    """Base category schema with common fields."""
    category_name: str = Field(..., min_length=1, max_length=100)
    category_slug: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    image_url: Optional[str] = Field(None, max_length=500)
    sort_order: int = Field(0, ge=0)
    is_active: bool = True


class CategoryCreate(CategoryBase):
    """Schema for creating a new category."""
    pass


class CategoryUpdate(BaseModel):
    """Schema for updating category information."""
    category_name: Optional[str] = Field(None, min_length=1, max_length=100)
    category_slug: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    image_url: Optional[str] = Field(None, max_length=500)
    sort_order: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None


class CategoryResponse(CategoryBase, TimestampBase):
    """Schema for category response."""
    category_id: UUID4

    class Config:
        from_attributes = True
        populate_by_name = True


# ========================================
# PRODUCT SCHEMAS
# ========================================

class ProductBase(BaseModel):
    """Base product schema with common fields."""
    product_name: str = Field(..., min_length=1, max_length=255)
    product_slug: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    base_price: Decimal = Field(..., ge=0, decimal_places=2)
    image_url: Optional[str] = Field(None, max_length=500)
    sort_order: int = Field(0, ge=0)
    is_featured: bool = False
    is_new_arrival: bool = False
    is_best_selling: bool = False
    is_active: bool = True


class ProductCreate(ProductBase):
    """Schema for creating a new product."""
    category_id: UUID4


class ProductUpdate(BaseModel):
    """Schema for updating product information."""
    product_name: Optional[str] = Field(None, min_length=1, max_length=255)
    product_slug: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    base_price: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    image_url: Optional[str] = Field(None, max_length=500)
    sort_order: Optional[int] = Field(None, ge=0)
    is_featured: Optional[bool] = None
    is_new_arrival: Optional[bool] = None
    is_best_selling: Optional[bool] = None
    is_active: Optional[bool] = None
    category_id: Optional[UUID4] = None


class ProductResponse(ProductBase, TimestampBase):
    """Schema for product response."""
    product_id: UUID4
    category_id: UUID4
    category: Optional[CategoryResponse] = None

    class Config:
        from_attributes = True
        populate_by_name = True


class ProductWithCategory(ProductResponse):
    """Product response with category information."""
    category: CategoryResponse


# ========================================
# ADDRESS SCHEMAS
# ========================================

class AddressBase(BaseModel):
    """Base address schema with common fields."""
    address_type: str = Field(..., min_length=1, max_length=50)
    full_name: str = Field(..., min_length=1, max_length=255)
    phone_number: str = Field(..., min_length=1, max_length=20)
    email: Optional[str] = Field(None, max_length=255)
    street_address: str = Field(..., min_length=1)
    building_number: Optional[str] = Field(None, max_length=50)
    flat_number: Optional[str] = Field(None, max_length=50)
    city: str = Field(..., min_length=1, max_length=100)
    area: Optional[str] = Field(None, max_length=100)
    is_default: bool = False


class AddressCreate(AddressBase):
    """Schema for creating a new address."""
    pass


class AddressUpdate(BaseModel):
    """Schema for updating address information."""
    address_type: Optional[str] = Field(None, min_length=1, max_length=50)
    full_name: Optional[str] = Field(None, min_length=1, max_length=255)
    phone_number: Optional[str] = Field(None, min_length=1, max_length=20)
    email: Optional[str] = Field(None, max_length=255)
    street_address: Optional[str] = Field(None, min_length=1)
    building_number: Optional[str] = Field(None, max_length=50)
    flat_number: Optional[str] = Field(None, max_length=50)
    city: Optional[str] = Field(None, min_length=1, max_length=100)
    area: Optional[str] = Field(None, max_length=100)
    is_default: Optional[bool] = None


class AddressResponse(AddressBase, TimestampBase):
    """Schema for address response."""
    address_id: UUID4
    user_id: UUID4

    class Config:
        from_attributes = True
        populate_by_name = True


# ========================================
# PAYMENT METHOD SCHEMAS
# ========================================

class PaymentMethodBase(BaseModel):
    """Base payment method schema with common fields."""
    payment_type: PaymentTypeEnum
    card_holder_name: Optional[str] = Field(None, max_length=255)
    card_last_four: Optional[str] = Field(None, max_length=4)
    card_brand: Optional[str] = Field(None, max_length=50)
    expiry_month: Optional[int] = Field(None, ge=1, le=12)
    expiry_year: Optional[int] = Field(None, ge=2024)  # Minimum current year
    is_default: bool = False

    @validator('expiry_year')
    def validate_expiry_year(cls, v):
        if v and v < datetime.now().year:
            raise ValueError('Expiry year must be current year or later')
        return v


class PaymentMethodCreate(PaymentMethodBase):
    """Schema for creating a new payment method."""
    pass


class PaymentMethodUpdate(BaseModel):
    """Schema for updating payment method information."""
    payment_type: Optional[PaymentTypeEnum] = None
    card_holder_name: Optional[str] = Field(None, max_length=255)
    card_last_four: Optional[str] = Field(None, max_length=4)
    card_brand: Optional[str] = Field(None, max_length=50)
    expiry_month: Optional[int] = Field(None, ge=1, le=12)
    expiry_year: Optional[int] = Field(None, ge=2024)
    is_default: Optional[bool] = None


class PaymentMethodResponse(PaymentMethodBase, TimestampBase):
    """Schema for payment method response."""
    payment_method_id: UUID4
    user_id: UUID4

    class Config:
        from_attributes = True
        populate_by_name = True


# ========================================
# PROMOTION SCHEMAS
# ========================================

class PromotionBase(BaseModel):
    """Base promotion schema with common fields."""
    promotion_code: str = Field(..., min_length=1, max_length=50)
    promotion_name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    discount_type: DiscountTypeEnum
    discount_value: Decimal = Field(..., gt=0, decimal_places=2)
    minimum_order_amount: Decimal = Field(0, ge=0, decimal_places=2)
    maximum_discount_amount: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    usage_limit: Optional[int] = Field(None, gt=0)
    start_date: datetime
    end_date: datetime
    is_active: bool = True

    @validator('end_date')
    def validate_end_date(cls, v, values):
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError('End date must be after start date')
        return v


class PromotionCreate(PromotionBase):
    """Schema for creating a new promotion."""
    pass


class PromotionUpdate(BaseModel):
    """Schema for updating promotion information."""
    promotion_code: Optional[str] = Field(None, min_length=1, max_length=50)
    promotion_name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    discount_type: Optional[DiscountTypeEnum] = None
    discount_value: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    minimum_order_amount: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    maximum_discount_amount: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    usage_limit: Optional[int] = Field(None, gt=0)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_active: Optional[bool] = None


class PromotionResponse(PromotionBase, TimestampBase):
    """Schema for promotion response."""
    promotion_id: UUID4
    usage_count: int

    class Config:
        from_attributes = True
        populate_by_name = True


# ========================================
# ORDER ITEM SCHEMAS
# ========================================

class OrderItemBase(BaseModel):
    """Base order item schema with common fields."""
    quantity: int = Field(..., gt=0)
    unit_price: Decimal = Field(..., ge=0, decimal_places=2)
    total_price: Decimal = Field(..., ge=0, decimal_places=2)


class OrderItemCreate(OrderItemBase):
    """Schema for creating a new order item."""
    product_id: UUID4


class OrderItemResponse(OrderItemBase, TimestampBase):
    """Schema for order item response."""
    order_item_id: UUID4
    order_id: UUID4
    product_id: UUID4
    product: Optional[ProductResponse] = None

    class Config:
        from_attributes = True
        populate_by_name = True


# ========================================
# ORDER SCHEMAS
# ========================================

class OrderBase(BaseModel):
    """Base order schema with common fields."""
    order_number: str = Field(..., min_length=1, max_length=50)
    order_status: OrderStatusEnum = OrderStatusEnum.PENDING
    subtotal: Decimal = Field(..., ge=0, decimal_places=2)
    delivery_fee: Decimal = Field(..., ge=0, decimal_places=2)
    discount_amount: Decimal = Field(0, ge=0, decimal_places=2)
    points_used: int = Field(0, ge=0)
    points_earned: int = Field(0, ge=0)
    total_amount: Decimal = Field(..., ge=0, decimal_places=2)
    order_notes: Optional[str] = None
    estimated_delivery_time: Optional[datetime] = None
    delivered_at: Optional[datetime] = None


class OrderCreate(BaseModel):
    """Schema for creating a new order."""
    address_id: UUID4
    payment_method_id: UUID4
    promotion_id: Optional[UUID4] = None
    order_items: List[OrderItemCreate]
    order_notes: Optional[str] = None


class OrderUpdate(BaseModel):
    """Schema for updating order information."""
    order_status: Optional[OrderStatusEnum] = None
    estimated_delivery_time: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    order_notes: Optional[str] = None


class OrderResponse(OrderBase, TimestampBase):
    """Schema for order response."""
    order_id: UUID4
    user_id: UUID4
    address_id: UUID4
    payment_method_id: UUID4
    promotion_id: Optional[UUID4] = None
    address: Optional[AddressResponse] = None
    payment_method: Optional[PaymentMethodResponse] = None
    promotion: Optional[PromotionResponse] = None
    order_items: List[OrderItemResponse] = []

    class Config:
        from_attributes = True
        populate_by_name = True


class OrderDetails(OrderResponse):
    """Detailed order response with all related information."""
    user: UserResponse
    address: AddressResponse
    payment_method: PaymentMethodResponse
    promotion: Optional[PromotionResponse] = None
    order_items: List[OrderItemResponse] = []


# ========================================
# CART ITEM SCHEMAS
# ========================================

class CartItemBase(BaseModel):
    """Base cart item schema with common fields."""
    quantity: int = Field(..., gt=0)


class CartItemCreate(CartItemBase):
    """Schema for creating a new cart item."""
    product_id: UUID4


class CartItemUpdate(BaseModel):
    """Schema for updating cart item quantity."""
    quantity: int = Field(..., gt=0)


class CartItemResponse(CartItemBase, TimestampBase):
    """Schema for cart item response."""
    cart_item_id: UUID4
    user_id: UUID4
    product_id: UUID4
    product: Optional[ProductResponse] = None

    class Config:
        from_attributes = True
        populate_by_name = True


# ========================================
# ORDER STATUS HISTORY SCHEMAS
# ========================================

class OrderStatusHistoryBase(BaseModel):
    """Base order status history schema with common fields."""
    status: str = Field(..., min_length=1, max_length=50)
    notes: Optional[str] = None


class OrderStatusHistoryCreate(OrderStatusHistoryBase):
    """Schema for creating a new order status history entry."""
    pass


class OrderStatusHistoryResponse(OrderStatusHistoryBase, TimestampBase):
    """Schema for order status history response."""
    status_history_id: UUID4
    order_id: UUID4

    class Config:
        from_attributes = True
        populate_by_name = True


# ========================================
# PRODUCT OFFER SCHEMAS
# ========================================

class ProductOfferBase(BaseModel):
    """Base product offer schema with common fields."""
    offer_name: str = Field(..., min_length=1, max_length=255)
    discount_type: DiscountTypeEnum
    discount_value: Decimal = Field(..., gt=0, decimal_places=2)
    original_price: Decimal = Field(..., gt=0, decimal_places=2)
    sale_price: Decimal = Field(..., gt=0, decimal_places=2)
    start_date: datetime
    end_date: datetime
    is_active: bool = True

    @validator('end_date')
    def validate_end_date(cls, v, values):
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError('End date must be after start date')
        return v

    @validator('sale_price')
    def validate_sale_price(cls, v, values):
        if 'original_price' in values and v >= values['original_price']:
            raise ValueError('Sale price must be less than original price')
        return v


class ProductOfferCreate(ProductOfferBase):
    """Schema for creating a new product offer."""
    product_id: UUID4


class ProductOfferUpdate(BaseModel):
    """Schema for updating product offer information."""
    offer_name: Optional[str] = Field(None, min_length=1, max_length=255)
    discount_type: Optional[DiscountTypeEnum] = None
    discount_value: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    original_price: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    sale_price: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_active: Optional[bool] = None


class ProductOfferResponse(ProductOfferBase, TimestampBase):
    """Schema for product offer response."""
    offer_id: UUID4
    product_id: UUID4

    class Config:
        from_attributes = True
        populate_by_name = True


# ========================================
# COMPOSITE RESPONSE SCHEMAS
# ========================================

class UserWithDetails(UserResponse):
    """User response with addresses and payment methods."""
    addresses: List[AddressResponse] = []
    payment_methods: List[PaymentMethodResponse] = []


class CategoryWithProducts(CategoryResponse):
    """Category response with products."""
    products: List[ProductResponse] = []


class ProductWithOffers(ProductResponse):
    """Product response with active offers."""
    product_offers: List[ProductOfferResponse] = []


class CartSummary(BaseModel):
    """Shopping cart summary with items and totals."""
    items: List[CartItemResponse]
    total_items: int
    subtotal: Decimal
    delivery_fee: Decimal = Decimal('0')
    total_amount: Decimal

    class Config:
        from_attributes = True


# ========================================
# PAGINATION SCHEMAS
# ========================================

class PaginationParams(BaseModel):
    """Pagination parameters for list endpoints."""
    page: int = Field(1, ge=1)
    size: int = Field(20, ge=1, le=100)


class PaginatedResponse(BaseModel):
    """Generic paginated response wrapper."""
    items: List[dict]
    total: int
    page: int
    size: int
    pages: int

    class Config:
        from_attributes = True


# ========================================
# ERROR RESPONSE SCHEMAS
# ========================================

class ErrorResponse(BaseModel):
    """Standard error response format."""
    error: str
    message: str
    details: Optional[dict] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ValidationErrorResponse(BaseModel):
    """Validation error response format."""
    error: str = "Validation Error"
    message: str
    field_errors: List[dict]
    timestamp: datetime = Field(default_factory=datetime.utcnow)