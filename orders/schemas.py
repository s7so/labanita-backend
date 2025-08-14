from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from decimal import Decimal
from pydantic import BaseModel, Field, validator
from enum import Enum

# =============================================================================
# ENUMS
# =============================================================================

class OrderStatus(str, Enum):
    """Order status values"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"
    ON_HOLD = "on_hold"
    RETURNED = "returned"

class PaymentStatus(str, Enum):
    """Payment status values"""
    PENDING = "pending"
    AUTHORIZED = "authorized"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"
    CANCELLED = "cancelled"

class ShippingStatus(str, Enum):
    """Shipping status values"""
    PENDING = "pending"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    IN_TRANSIT = "in_transit"
    OUT_FOR_DELIVERY = "out_for_delivery"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETURNED = "returned"

class OrderType(str, Enum):
    """Order type values"""
    REGULAR = "regular"
    EXPRESS = "express"
    SAME_DAY = "same_day"
    NEXT_DAY = "next_day"
    SCHEDULED = "scheduled"
    SUBSCRIPTION = "subscription"
    PRE_ORDER = "pre_order"

class ShippingMethod(str, Enum):
    """Shipping method values"""
    STANDARD = "standard"
    EXPRESS = "express"
    PRIORITY = "priority"
    OVERNIGHT = "overnight"
    SAME_DAY = "same_day"
    PICKUP = "pickup"
    LOCAL_DELIVERY = "local_delivery"

# =============================================================================
# RESPONSE SCHEMAS
# =============================================================================

class OrderItemResponse(BaseModel):
    """Response schema for order item"""
    order_item_id: str = Field(..., description="Order item unique identifier")
    order_id: str = Field(..., description="Order ID this item belongs to")
    product_id: str = Field(..., description="Product ID")
    product_name: str = Field(..., description="Product name")
    product_image: Optional[str] = Field(None, description="Product image URL")
    category_id: str = Field(..., description="Product category ID")
    category_name: str = Field(..., description="Product category name")
    quantity: int = Field(..., description="Quantity ordered")
    unit_price: float = Field(..., description="Unit price at time of order")
    total_price: float = Field(..., description="Total price for this item")
    discount_amount: float = Field(..., description="Discount amount applied")
    discount_percentage: float = Field(..., description="Discount percentage applied")
    final_price: float = Field(..., description="Final price after discount")
    applied_promotions: List[str] = Field(..., description="List of applied promotion IDs")
    weight: Optional[float] = Field(None, description="Product weight")
    dimensions: Optional[Dict[str, float]] = Field(None, description="Product dimensions")
    created_at: datetime = Field(..., description="When order item was created")
    
    class Config:
        from_attributes = True

class OrderResponse(BaseModel):
    """Response schema for order"""
    order_id: str = Field(..., description="Order unique identifier")
    order_number: str = Field(..., description="Human-readable order number")
    user_id: str = Field(..., description="User ID who placed the order")
    order_status: OrderStatus = Field(..., description="Current order status")
    payment_status: PaymentStatus = Field(..., description="Current payment status")
    shipping_status: ShippingStatus = Field(..., description="Current shipping status")
    order_type: OrderType = Field(..., description="Type of order")
    shipping_method: ShippingMethod = Field(..., description="Shipping method selected")
    
    # Pricing information
    subtotal: float = Field(..., description="Subtotal before discounts and taxes")
    total_discount: float = Field(..., description="Total discount amount")
    total_tax: float = Field(..., description="Total tax amount")
    shipping_cost: float = Field(..., description="Shipping cost")
    total_amount: float = Field(..., description="Final total amount")
    
    # Applied promotions
    applied_promotions: List[Dict[str, Any]] = Field(..., description="Details of applied promotions")
    total_savings: float = Field(..., description="Total amount saved through promotions")
    
    # Shipping information
    shipping_address: Dict[str, Any] = Field(..., description="Shipping address details")
    billing_address: Dict[str, Any] = Field(..., description="Billing address details")
    estimated_delivery: Optional[datetime] = Field(None, description="Estimated delivery date")
    actual_delivery: Optional[datetime] = Field(None, description="Actual delivery date")
    
    # Payment information
    payment_method: Dict[str, Any] = Field(..., description="Payment method details")
    transaction_id: Optional[str] = Field(None, description="Payment transaction ID")
    
    # Order items
    items: List[OrderItemResponse] = Field(..., description="List of order items")
    total_items: int = Field(..., description="Total number of items")
    total_quantity: int = Field(..., description="Total quantity of all items")
    
    # Timestamps
    created_at: datetime = Field(..., description="When order was created")
    updated_at: datetime = Field(..., description="When order was last updated")
    cancelled_at: Optional[datetime] = Field(None, description="When order was cancelled")
    
    # Additional information
    notes: Optional[str] = Field(None, description="Order notes")
    tags: List[str] = Field(..., description="Order tags")
    priority: int = Field(..., description="Order priority")
    
    class Config:
        from_attributes = True

class OrderListResponse(BaseModel):
    """Response schema for list of orders"""
    orders: List[OrderResponse] = Field(..., description="List of orders")
    total_count: int = Field(..., description="Total number of orders")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Page size")
    total_pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_prev: bool = Field(..., description="Whether there is a previous page")

class OrderStatusResponse(BaseModel):
    """Response schema for order status"""
    order_id: str = Field(..., description="Order unique identifier")
    order_number: str = Field(..., description="Human-readable order number")
    current_status: OrderStatus = Field(..., description="Current order status")
    status_history: List[Dict[str, Any]] = Field(..., description="Order status history")
    estimated_delivery: Optional[datetime] = Field(None, description="Estimated delivery date")
    last_update: datetime = Field(..., description="Last status update")
    next_expected_update: Optional[datetime] = Field(None, description="Next expected update")
    status_description: str = Field(..., description="Human-readable status description")
    status_icon: str = Field(..., description="Status icon identifier")
    progress_percentage: int = Field(..., description="Order progress percentage")

class OrderTrackingResponse(BaseModel):
    """Response schema for order tracking"""
    order_id: str = Field(..., description="Order unique identifier")
    order_number: str = Field(..., description="Human-readable order number")
    tracking_number: Optional[str] = Field(None, description="Shipping tracking number")
    carrier: Optional[str] = Field(None, description="Shipping carrier")
    tracking_url: Optional[str] = Field(None, description="Tracking URL")
    current_location: Optional[str] = Field(None, description="Current package location")
    estimated_delivery: Optional[datetime] = Field(None, description="Estimated delivery date")
    tracking_events: List[Dict[str, Any]] = Field(..., description="Tracking events history")
    last_event: Optional[Dict[str, Any]] = Field(None, description="Last tracking event")
    delivery_attempts: int = Field(..., description="Number of delivery attempts")
    is_delivered: bool = Field(..., description="Whether order has been delivered")
    delivery_notes: Optional[str] = Field(None, description="Delivery notes")

class OrderCalculationResponse(BaseModel):
    """Response schema for order calculation"""
    subtotal: float = Field(..., description="Subtotal before discounts and taxes")
    total_discount: float = Field(..., description="Total discount amount")
    total_tax: float = Field(..., description="Total tax amount")
    shipping_cost: float = Field(..., description="Shipping cost")
    total_amount: float = Field(..., description="Final total amount")
    total_savings: float = Field(..., description="Total amount saved")
    applied_promotions: List[Dict[str, Any]] = Field(..., description="Applied promotions")
    available_promotions: List[Dict[str, Any]] = Field(..., description="Available promotions")
    tax_breakdown: Dict[str, float] = Field(..., description="Tax breakdown by type")
    shipping_options: List[Dict[str, Any]] = Field(..., description="Available shipping options")
    estimated_delivery: Dict[str, Any] = Field(..., description="Estimated delivery information")
    currency: str = Field(..., description="Currency used for calculations")

class OrderCreateResponse(BaseModel):
    """Response schema for order creation"""
    success: bool = Field(..., description="Whether order was created successfully")
    order_id: str = Field(..., description="Created order ID")
    order_number: str = Field(..., description="Created order number")
    message: str = Field(..., description="Creation result message")
    payment_required: bool = Field(..., description="Whether payment is required")
    payment_url: Optional[str] = Field(None, description="Payment URL if applicable")
    estimated_delivery: Optional[datetime] = Field(None, description="Estimated delivery date")
    order_summary: OrderResponse = Field(..., description="Created order summary")

# =============================================================================
# REQUEST SCHEMAS
# =============================================================================

class OrderCalculationRequest(BaseModel):
    """Request schema for order calculation"""
    items: List[Dict[str, Any]] = Field(..., description="Cart items for calculation")
    shipping_address: Dict[str, Any] = Field(..., description="Shipping address")
    billing_address: Optional[Dict[str, Any]] = Field(None, description="Billing address (optional)")
    shipping_method: ShippingMethod = Field(..., description="Selected shipping method")
    applied_promotions: List[str] = Field(..., description="List of promotion IDs to apply")
    user_id: str = Field(..., description="User ID for calculation")
    currency: str = Field("USD", description="Currency for calculation")
    
    @validator('items')
    def validate_items(cls, v):
        if not v:
            raise ValueError('At least one item is required')
        for item in v:
            if 'product_id' not in item or 'quantity' not in item or 'price' not in item:
                raise ValueError('Each item must have product_id, quantity, and price')
            if item['quantity'] < 1:
                raise ValueError('Quantity must be at least 1')
            if item['price'] < 0:
                raise ValueError('Price cannot be negative')
        return v

class OrderCreateRequest(BaseModel):
    """Request schema for creating an order"""
    items: List[Dict[str, Any]] = Field(..., description="Cart items for order")
    shipping_address: Dict[str, Any] = Field(..., description="Shipping address")
    billing_address: Optional[Dict[str, Any]] = Field(None, description="Billing address")
    shipping_method: ShippingMethod = Field(..., description="Selected shipping method")
    payment_method_id: str = Field(..., description="Payment method ID")
    applied_promotions: List[str] = Field(..., description="List of promotion IDs")
    order_notes: Optional[str] = Field(None, description="Order notes")
    user_id: str = Field(..., description="User ID placing the order")
    currency: str = Field("USD", description="Currency for order")
    
    @validator('items')
    def validate_items(cls, v):
        if not v:
            raise ValueError('At least one item is required')
        return v
    
    @validator('shipping_address')
    def validate_shipping_address(cls, v):
        required_fields = ['street', 'city', 'state', 'postal_code', 'country']
        for field in required_fields:
            if field not in v or not v[field]:
                raise ValueError(f'Shipping address {field} is required')
        return v

class OrderCancelRequest(BaseModel):
    """Request schema for cancelling an order"""
    reason: str = Field(..., min_length=10, max_length=500, description="Cancellation reason")
    refund_requested: bool = Field(False, description="Whether refund is requested")
    cancel_items: Optional[List[str]] = Field(None, description="Specific items to cancel")
    user_id: str = Field(..., description="User ID cancelling the order")

class OrderReorderRequest(BaseModel):
    """Request schema for reordering"""
    include_all_items: bool = Field(True, description="Whether to include all original items")
    selected_items: Optional[List[str]] = Field(None, description="Specific items to reorder")
    update_quantities: Optional[Dict[str, int]] = Field(None, description="Updated quantities")
    new_shipping_address: Optional[Dict[str, Any]] = Field(None, description="New shipping address")
    new_payment_method: Optional[str] = Field(None, description="New payment method ID")
    user_id: str = Field(..., description="User ID reordering")

# =============================================================================
# INTERNAL SCHEMAS
# =============================================================================

class OrderCreate(BaseModel):
    """Internal schema for creating order"""
    user_id: str
    order_type: OrderType
    shipping_method: ShippingMethod
    shipping_address: Dict[str, Any]
    billing_address: Dict[str, Any]
    payment_method_id: str
    applied_promotions: List[str]
    order_notes: Optional[str]
    currency: str
    items: List[Dict[str, Any]]

class OrderUpdate(BaseModel):
    """Internal schema for updating order"""
    order_status: Optional[OrderStatus] = None
    payment_status: Optional[PaymentStatus] = None
    shipping_status: Optional[ShippingStatus] = None
    estimated_delivery: Optional[datetime] = None
    actual_delivery: Optional[datetime] = None
    tracking_number: Optional[str] = None
    carrier: Optional[str] = None
    notes: Optional[str] = None
    tags: Optional[List[str]] = None
    priority: Optional[int] = None

class OrderItemCreate(BaseModel):
    """Internal schema for creating order item"""
    order_id: str
    product_id: str
    quantity: int
    unit_price: float
    total_price: float
    discount_amount: float
    discount_percentage: float
    final_price: float
    applied_promotions: List[str]
    weight: Optional[float]
    dimensions: Optional[Dict[str, float]]

# =============================================================================
# FILTER SCHEMAS
# =============================================================================

class OrderFilter(BaseModel):
    """Schema for filtering orders"""
    user_id: Optional[str] = Field(None, description="Filter by user ID")
    order_status: Optional[OrderStatus] = Field(None, description="Filter by order status")
    payment_status: Optional[PaymentStatus] = Field(None, description="Filter by payment status")
    shipping_status: Optional[ShippingStatus] = Field(None, description="Filter by shipping status")
    order_type: Optional[OrderType] = Field(None, description="Filter by order type")
    shipping_method: Optional[ShippingMethod] = Field(None, description="Filter by shipping method")
    min_total: Optional[float] = Field(None, ge=0, description="Minimum order total")
    max_total: Optional[float] = Field(None, ge=0, description="Maximum order total")
    date_from: Optional[datetime] = Field(None, description="Orders from date")
    date_to: Optional[datetime] = Field(None, description="Orders to date")
    has_promotions: Optional[bool] = Field(None, description="Whether order has promotions")
    search: Optional[str] = Field(None, description="Search in order number, product names")
    sort_by: str = Field("created_at", description="Sort field")
    sort_order: str = Field("desc", description="Sort order (asc/desc)")

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

class PaginatedOrdersResponse(BaseModel):
    """Paginated response for orders"""
    orders: List[OrderResponse] = Field(..., description="Orders in current page")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Page size")
    total: int = Field(..., description="Total number of orders")
    pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_prev: bool = Field(..., description="Whether there is a previous page")

# =============================================================================
# STATISTICS SCHEMAS
# =============================================================================

class OrderStatsResponse(BaseModel):
    """Response schema for order statistics"""
    total_orders: int = Field(..., description="Total number of orders")
    total_revenue: float = Field(..., description="Total revenue from orders")
    average_order_value: float = Field(..., description="Average order value")
    orders_by_status: Dict[str, int] = Field(..., description="Orders count by status")
    orders_by_month: List[Dict[str, Any]] = Field(..., description="Orders by month")
    top_products: List[Dict[str, Any]] = Field(..., description="Top selling products")
    conversion_rate: float = Field(..., description="Cart to order conversion rate")
    return_rate: float = Field(..., description="Order return rate")

class OrderAnalyticsResponse(BaseModel):
    """Response schema for order analytics"""
    total_orders: int = Field(..., description="Total number of orders")
    total_revenue: float = Field(..., description="Total revenue")
    total_customers: int = Field(..., description="Total unique customers")
    repeat_customer_rate: float = Field(..., description="Repeat customer rate")
    average_order_frequency: float = Field(..., description="Average orders per customer")
    top_customers: List[Dict[str, Any]] = Field(..., description="Top customers by order value")
    order_trends: List[Dict[str, Any]] = Field(..., description="Order trends over time")
    revenue_trends: List[Dict[str, Any]] = Field(..., description="Revenue trends over time")
    category_performance: List[Dict[str, Any]] = Field(..., description="Category performance")
    promotion_effectiveness: List[Dict[str, Any]] = Field(..., description="Promotion effectiveness")

# =============================================================================
# NOTIFICATION SCHEMAS
# =============================================================================

class OrderNotificationRequest(BaseModel):
    """Request schema for order notifications"""
    notification_type: str = Field(..., description="Type of notification")
    order_id: str = Field(..., description="Order ID for notification")
    user_id: str = Field(..., description="User ID to notify")
    message: str = Field(..., description="Notification message")
    priority: str = Field("normal", description="Notification priority")
    channel: str = Field("email", description="Notification channel")

class OrderNotificationResponse(BaseModel):
    """Response schema for order notifications"""
    notification_id: str = Field(..., description="Notification unique identifier")
    notification_type: str = Field(..., description="Type of notification")
    order_id: str = Field(..., description="Order ID")
    user_id: str = Field(..., description="User ID")
    message: str = Field(..., description="Notification message")
    priority: str = Field(..., description="Notification priority")
    channel: str = Field(..., description="Notification channel")
    created_at: datetime = Field(..., description="When notification was created")
    sent_at: Optional[datetime] = Field(None, description="When notification was sent")
    is_read: bool = Field(..., description="Whether notification has been read")
    status: str = Field(..., description="Notification status")

# =============================================================================
# ORDER HISTORY SCHEMAS
# =============================================================================

class OrderHistoryFilter(BaseModel):
    """Schema for filtering order history"""
    status: Optional[OrderStatus] = Field(None, description="Filter by order status")
    date_from: Optional[datetime] = Field(None, description="Orders from date")
    date_to: Optional[datetime] = Field(None, description="Orders to date")
    min_amount: Optional[float] = Field(None, ge=0, description="Minimum order amount")
    max_amount: Optional[float] = Field(None, ge=0, description="Maximum order amount")
    shipping_method: Optional[ShippingMethod] = Field(None, description="Filter by shipping method")
    has_promotions: Optional[bool] = Field(None, description="Whether order has promotions")
    search: Optional[str] = Field(None, description="Search in order number, product names")
    sort_by: str = Field("created_at", description="Sort field")
    sort_order: str = Field("desc", description="Sort order (asc/desc)")
    page: int = Field(1, ge=1, description="Page number")
    size: int = Field(20, ge=1, le=100, description="Page size")

class OrderHistoryItem(BaseModel):
    """Schema for order history item"""
    order_id: str = Field(..., description="Order unique identifier")
    order_number: str = Field(..., description="Human-readable order number")
    order_status: OrderStatus = Field(..., description="Current order status")
    payment_status: PaymentStatus = Field(..., description="Current payment status")
    shipping_status: ShippingStatus = Field(..., description="Current shipping status")
    total_amount: float = Field(..., description="Final total amount")
    total_items: int = Field(..., description="Total number of items")
    total_quantity: int = Field(..., description="Total quantity of all items")
    shipping_method: ShippingMethod = Field(..., description="Shipping method selected")
    applied_promotions: List[str] = Field(..., description="List of applied promotion IDs")
    total_savings: float = Field(..., description="Total amount saved through promotions")
    estimated_delivery: Optional[datetime] = Field(None, description="Estimated delivery date")
    actual_delivery: Optional[datetime] = Field(None, description="Actual delivery date")
    created_at: datetime = Field(..., description="When order was created")
    updated_at: datetime = Field(..., description="When order was last updated")
    cancelled_at: Optional[datetime] = Field(None, description="When order was cancelled")
    
    class Config:
        from_attributes = True

class OrderHistoryResponse(BaseModel):
    """Response schema for order history"""
    orders: List[OrderHistoryItem] = Field(..., description="List of orders in history")
    total_count: int = Field(..., description="Total number of orders")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Page size")
    total_pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_prev: bool = Field(..., description="Whether there is a previous page")
    filters_applied: Dict[str, Any] = Field(..., description="Filters that were applied")
    summary: Dict[str, Any] = Field(..., description="Summary of filtered results")

class OrderHistorySummary(BaseModel):
    """Schema for order history summary"""
    total_orders: int = Field(..., description="Total number of orders")
    total_revenue: float = Field(..., description="Total revenue from orders")
    average_order_value: float = Field(..., description="Average order value")
    orders_by_status: Dict[str, int] = Field(..., description="Orders count by status")
    orders_by_month: List[Dict[str, Any]] = Field(..., description="Orders by month")
    total_savings: float = Field(..., description="Total savings from promotions")
    most_used_shipping_method: str = Field(..., description="Most frequently used shipping method")
    delivery_success_rate: float = Field(..., description="Percentage of successful deliveries")