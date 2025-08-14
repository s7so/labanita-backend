from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, validator
from enum import Enum

# =============================================================================
# ENUMS
# =============================================================================

class CartItemStatus(str, Enum):
    """Cart item status values"""
    ACTIVE = "active"
    OUT_OF_STOCK = "out_of_stock"
    PRICE_CHANGED = "price_changed"
    PRODUCT_UNAVAILABLE = "product_unavailable"
    REMOVED = "removed"

class CartAction(str, Enum):
    """Cart action values"""
    ADD = "add"
    UPDATE = "update"
    REMOVE = "remove"
    CLEAR = "clear"
    APPLY_OFFER = "apply_offer"
    REMOVE_OFFER = "remove_offer"

# =============================================================================
# RESPONSE SCHEMAS
# =============================================================================

class CartItemResponse(BaseModel):
    """Response schema for cart item"""
    cart_item_id: str = Field(..., description="Cart item unique identifier")
    user_id: str = Field(..., description="User ID who owns this cart item")
    product_id: str = Field(..., description="Product ID in cart")
    product_name: str = Field(..., description="Product name")
    product_image: Optional[str] = Field(None, description="Product image URL")
    category_id: str = Field(..., description="Product category ID")
    category_name: str = Field(..., description="Product category name")
    quantity: int = Field(..., description="Quantity of product in cart")
    unit_price: float = Field(..., description="Current unit price")
    original_unit_price: float = Field(..., description="Original unit price when added")
    total_price: float = Field(..., description="Total price for this item (quantity * unit_price)")
    original_total_price: float = Field(..., description="Original total price when added")
    discount_amount: float = Field(..., description="Discount amount applied to this item")
    discount_percentage: float = Field(..., description="Discount percentage applied to this item")
    applied_offers: List[str] = Field(..., description="List of offer IDs applied to this item")
    stock_quantity: int = Field(..., description="Available stock quantity")
    max_quantity_allowed: int = Field(..., description="Maximum quantity allowed per order")
    is_available: bool = Field(..., description="Whether product is currently available")
    status: CartItemStatus = Field(..., description="Current status of cart item")
    added_at: datetime = Field(..., description="When item was added to cart")
    updated_at: datetime = Field(..., description="When item was last updated")
    
    class Config:
        from_attributes = True

class CartSummaryResponse(BaseModel):
    """Response schema for cart summary"""
    user_id: str = Field(..., description="User ID who owns this cart")
    total_items: int = Field(..., description="Total number of items in cart")
    total_quantity: int = Field(..., description="Total quantity of all items")
    subtotal: float = Field(..., description="Subtotal before discounts and taxes")
    total_discount: float = Field(..., description="Total discount amount applied")
    total_tax: float = Field(..., description="Total tax amount")
    shipping_cost: float = Field(..., description="Shipping cost")
    total_amount: float = Field(..., description="Final total amount")
    savings_amount: float = Field(..., description="Total amount saved through discounts")
    savings_percentage: float = Field(..., description="Percentage of total savings")
    applied_offers: List[Dict[str, Any]] = Field(..., description="Details of applied offers")
    available_offers: List[Dict[str, Any]] = Field(..., description="Offers that could be applied")
    estimated_delivery: Optional[str] = Field(None, description="Estimated delivery date")
    free_shipping_threshold: Optional[float] = Field(None, description="Amount needed for free shipping")
    items: List[CartItemResponse] = Field(..., description="List of cart items")
    
    class Config:
        from_attributes = True

class CartResponse(BaseModel):
    """Response schema for full cart"""
    cart_id: str = Field(..., description="Cart unique identifier")
    user_id: str = Field(..., description="User ID who owns this cart")
    summary: CartSummaryResponse = Field(..., description="Cart summary information")
    created_at: datetime = Field(..., description="When cart was created")
    updated_at: datetime = Field(..., description="When cart was last updated")
    expires_at: Optional[datetime] = Field(None, description="When cart expires")
    
    class Config:
        from_attributes = True

class CartItemListResponse(BaseModel):
    """Response schema for list of cart items"""
    cart_items: List[CartItemResponse] = Field(..., description="List of cart items")
    total_count: int = Field(..., description="Total number of cart items")
    summary: CartSummaryResponse = Field(..., description="Cart summary information")

# =============================================================================
# REQUEST SCHEMAS
# =============================================================================

class CartItemCreateRequest(BaseModel):
    """Request schema for adding item to cart"""
    product_id: str = Field(..., description="Product ID to add to cart")
    quantity: int = Field(..., ge=1, le=100, description="Quantity to add")
    
    @validator('quantity')
    def validate_quantity(cls, v):
        if v < 1:
            raise ValueError('Quantity must be at least 1')
        if v > 100:
            raise ValueError('Quantity cannot exceed 100')
        return v

class CartItemUpdateRequest(BaseModel):
    """Request schema for updating cart item"""
    quantity: int = Field(..., ge=1, le=100, description="New quantity for cart item")
    
    @validator('quantity')
    def validate_quantity(cls, v):
        if v < 1:
            raise ValueError('Quantity must be at least 1')
        if v > 100:
            raise ValueError('Quantity cannot exceed 100')
        return v

class CartOfferRequest(BaseModel):
    """Request schema for applying/removing offers to cart"""
    offer_id: str = Field(..., description="Offer ID to apply or remove")
    action: CartAction = Field(..., description="Action to perform (apply_offer or remove_offer)")

class CartValidationRequest(BaseModel):
    """Request schema for cart validation"""
    validate_stock: bool = Field(True, description="Whether to validate stock availability")
    validate_prices: bool = Field(True, description="Whether to validate current prices")
    validate_offers: bool = Field(True, description="Whether to validate applied offers")
    check_delivery: bool = Field(False, description="Whether to check delivery options")

# =============================================================================
# INTERNAL SCHEMAS
# =============================================================================

class CartItemCreate(BaseModel):
    """Internal schema for creating cart item"""
    user_id: str
    product_id: str
    quantity: int
    unit_price: float
    original_unit_price: float
    category_id: str
    max_quantity_allowed: int

class CartItemUpdate(BaseModel):
    """Internal schema for updating cart item"""
    quantity: Optional[int] = None
    unit_price: Optional[float] = None
    status: Optional[CartItemStatus] = None
    applied_offers: Optional[List[str]] = None

class CartSummary(BaseModel):
    """Internal schema for cart summary calculations"""
    total_items: int
    total_quantity: int
    subtotal: float
    total_discount: float
    total_tax: float
    shipping_cost: float
    total_amount: float
    savings_amount: float
    savings_percentage: float

# =============================================================================
# CART OPERATION SCHEMAS
# =============================================================================

class CartOperationResponse(BaseModel):
    """Response schema for cart operations"""
    success: bool = Field(..., description="Whether operation was successful")
    message: str = Field(..., description="Operation result message")
    cart_item_id: Optional[str] = Field(None, description="Cart item ID if applicable")
    updated_summary: Optional[CartSummaryResponse] = Field(None, description="Updated cart summary")
    validation_errors: List[str] = Field(..., description="Any validation errors encountered")
    warnings: List[str] = Field(..., description="Any warnings about the operation")

class CartValidationResponse(BaseModel):
    """Response schema for cart validation results"""
    is_valid: bool = Field(..., description="Whether cart is valid")
    validation_errors: List[str] = Field(..., description="List of validation errors")
    warnings: List[str] = Field(..., description="List of warnings")
    price_changes: List[Dict[str, Any]] = Field(..., description="Products with price changes")
    stock_issues: List[Dict[str, Any]] = Field(..., description="Products with stock issues")
    offer_issues: List[Dict[str, Any]] = Field(..., description="Issues with applied offers")
    recommendations: List[str] = Field(..., description="Recommendations for cart improvement")

# =============================================================================
# CART ANALYTICS SCHEMAS
# =============================================================================

class CartAnalyticsResponse(BaseModel):
    """Response schema for cart analytics"""
    total_carts: int = Field(..., description="Total number of active carts")
    average_cart_value: float = Field(..., description="Average cart value")
    average_items_per_cart: float = Field(..., description="Average number of items per cart")
    cart_abandonment_rate: float = Field(..., description="Cart abandonment rate percentage")
    top_products_in_carts: List[Dict[str, Any]] = Field(..., description="Most common products in carts")
    cart_conversion_rate: float = Field(..., description="Cart to order conversion rate")
    average_cart_lifetime: float = Field(..., description="Average cart lifetime in hours")

class CartItemAnalytics(BaseModel):
    """Response schema for cart item analytics"""
    product_id: str = Field(..., description="Product ID")
    product_name: str = Field(..., description="Product name")
    total_added_to_cart: int = Field(..., description="Total times added to cart")
    total_removed_from_cart: int = Field(..., description="Total times removed from cart")
    average_quantity: float = Field(..., description="Average quantity when added")
    cart_to_order_rate: float = Field(..., description="Rate of cart items converted to orders")
    average_cart_lifetime: float = Field(..., description="Average time in cart before order")

# =============================================================================
# CART NOTIFICATION SCHEMAS
# =============================================================================

class CartNotificationRequest(BaseModel):
    """Request schema for cart notifications"""
    notification_type: str = Field(..., description="Type of notification")
    message: str = Field(..., description="Notification message")
    priority: str = Field("normal", description="Notification priority")
    expires_at: Optional[datetime] = Field(None, description="When notification expires")

class CartNotificationResponse(BaseModel):
    """Response schema for cart notifications"""
    notification_id: str = Field(..., description="Notification unique identifier")
    notification_type: str = Field(..., description="Type of notification")
    message: str = Field(..., description="Notification message")
    priority: str = Field(..., description="Notification priority")
    created_at: datetime = Field(..., description="When notification was created")
    expires_at: Optional[datetime] = Field(None, description="When notification expires")
    is_read: bool = Field(..., description="Whether notification has been read")

# =============================================================================
# CART SHARING SCHEMAS
# =============================================================================

class CartShareRequest(BaseModel):
    """Request schema for sharing cart"""
    share_with_email: Optional[str] = Field(None, description="Email to share cart with")
    share_with_user_id: Optional[str] = Field(None, description="User ID to share cart with")
    share_type: str = Field("view", description="Type of sharing (view, edit, collaborate)")
    expires_at: Optional[datetime] = Field(None, description="When shared access expires")

class CartShareResponse(BaseModel):
    """Response schema for shared cart access"""
    share_id: str = Field(..., description="Share unique identifier")
    cart_id: str = Field(..., description="Cart ID being shared")
    shared_by: str = Field(..., description="User ID who shared the cart")
    shared_with: str = Field(..., description="User ID or email shared with")
    share_type: str = Field(..., description="Type of sharing access")
    created_at: datetime = Field(..., description="When cart was shared")
    expires_at: Optional[datetime] = Field(None, description="When shared access expires")
    is_active: bool = Field(..., description="Whether shared access is still active")

# =============================================================================
# CART MERGE SCHEMAS
# =============================================================================

class CartMergeRequest(BaseModel):
    """Request schema for merging carts"""
    source_cart_id: str = Field(..., description="Source cart ID to merge from")
    target_cart_id: str = Field(..., description="Target cart ID to merge into")
    merge_strategy: str = Field("prefer_target", description="Merge strategy (prefer_target, prefer_source, combine)")
    handle_conflicts: str = Field("ask", description="How to handle conflicts (ask, auto_resolve, skip)")

class CartMergeResponse(BaseModel):
    """Response schema for cart merge results"""
    success: bool = Field(..., description="Whether merge was successful")
    merged_items: int = Field(..., description="Number of items merged")
    skipped_items: int = Field(..., description="Number of items skipped")
    conflicts_resolved: int = Field(..., description="Number of conflicts resolved")
    final_cart_id: str = Field(..., description="Final cart ID after merge")
    merge_summary: CartSummaryResponse = Field(..., description="Summary of merged cart")
    warnings: List[str] = Field(..., description="Any warnings during merge")

# =============================================================================
# CART EXPORT SCHEMAS
# =============================================================================

class CartExportRequest(BaseModel):
    """Request schema for exporting cart"""
    export_format: str = Field("json", description="Export format (json, csv, pdf)")
    include_summary: bool = Field(True, description="Whether to include cart summary")
    include_offers: bool = Field(True, description="Whether to include applied offers")
    include_product_details: bool = Field(True, description="Whether to include detailed product information")

class CartExportResponse(BaseModel):
    """Response schema for cart export"""
    export_id: str = Field(..., description="Export unique identifier")
    export_format: str = Field(..., description="Format of exported data")
    download_url: str = Field(..., description="URL to download exported data")
    file_size: int = Field(..., description="Size of exported file in bytes")
    expires_at: datetime = Field(..., description="When export download expires")
    created_at: datetime = Field(..., description="When export was created")