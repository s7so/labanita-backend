from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, validator
from enum import Enum

# =============================================================================
# ENUMS
# =============================================================================

class AdminRole(str, Enum):
    """Admin role values"""
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    MODERATOR = "moderator"
    EDITOR = "editor"
    VIEWER = "viewer"

class ProductStatus(str, Enum):
    """Product status values for admin management"""
    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"
    PENDING_REVIEW = "pending_review"
    REJECTED = "rejected"
    OUT_OF_STOCK = "out_of_stock"
    DISCONTINUED = "discontinued"

class ApprovalStatus(str, Enum):
    """Approval status values"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    UNDER_REVIEW = "under_review"

# =============================================================================
# ADMIN PRODUCT MANAGEMENT SCHEMAS
# =============================================================================

class AdminProductCreateRequest(BaseModel):
    """Request schema for creating products (admin)"""
    product_name: str = Field(..., min_length=1, max_length=255, description="Product name")
    description: str = Field(..., min_length=10, description="Product description")
    short_description: Optional[str] = Field(None, max_length=500, description="Short product description")
    category_id: str = Field(..., description="Category ID")
    brand: Optional[str] = Field(None, max_length=100, description="Product brand")
    sku: str = Field(..., max_length=100, description="Stock Keeping Unit")
    barcode: Optional[str] = Field(None, max_length=100, description="Product barcode")
    price: float = Field(..., gt=0, description="Product price")
    compare_price: Optional[float] = Field(None, gt=0, description="Compare at price")
    cost_price: Optional[float] = Field(None, gt=0, description="Product cost price")
    weight: Optional[float] = Field(None, ge=0, description="Product weight in kg")
    dimensions: Optional[Dict[str, float]] = Field(None, description="Product dimensions")
    stock_quantity: int = Field(..., ge=0, description="Available stock quantity")
    min_stock_level: int = Field(0, ge=0, description="Minimum stock level for alerts")
    max_stock_level: Optional[int] = Field(None, ge=0, description="Maximum stock level")
    is_featured: bool = Field(False, description="Whether product is featured")
    is_active: bool = Field(True, description="Whether product is active")
    status: ProductStatus = Field(ProductStatus.DRAFT, description="Product status")
    tags: List[str] = Field(default_factory=list, description="Product tags")
    images: List[str] = Field(default_factory=list, description="Product image URLs")
    main_image: Optional[str] = Field(None, description="Main product image URL")
    seo_title: Optional[str] = Field(None, max_length=60, description="SEO title")
    seo_description: Optional[str] = Field(None, max_length=160, description="SEO description")
    seo_keywords: List[str] = Field(default_factory=list, description="SEO keywords")
    meta_data: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    notes: Optional[str] = Field(None, description="Admin notes")
    
    @validator('price', 'compare_price', 'cost_price')
    def validate_prices(cls, v, values):
        if v is not None:
            if v <= 0:
                raise ValueError('Price must be greater than 0')
        return v
    
    @validator('compare_price')
    def validate_compare_price(cls, v, values):
        if v is not None and 'price' in values:
            if v <= values['price']:
                raise ValueError('Compare price must be greater than regular price')
        return v

class AdminProductUpdateRequest(BaseModel):
    """Request schema for updating products (admin)"""
    product_name: Optional[str] = Field(None, min_length=1, max_length=255, description="Product name")
    description: Optional[str] = Field(None, min_length=10, description="Product description")
    short_description: Optional[str] = Field(None, max_length=500, description="Short product description")
    category_id: Optional[str] = Field(None, description="Category ID")
    brand: Optional[str] = Field(None, max_length=100, description="Product brand")
    sku: Optional[str] = Field(None, max_length=100, description="Stock Keeping Unit")
    barcode: Optional[str] = Field(None, max_length=100, description="Product barcode")
    price: Optional[float] = Field(None, gt=0, description="Product price")
    compare_price: Optional[float] = Field(None, gt=0, description="Compare at price")
    cost_price: Optional[float] = Field(None, gt=0, description="Product cost price")
    weight: Optional[float] = Field(None, ge=0, description="Product weight in kg")
    dimensions: Optional[Dict[str, float]] = Field(None, description="Product dimensions")
    stock_quantity: Optional[int] = Field(None, ge=0, description="Available stock quantity")
    min_stock_level: Optional[int] = Field(None, ge=0, description="Minimum stock level for alerts")
    max_stock_level: Optional[int] = Field(None, ge=0, description="Maximum stock level")
    is_featured: Optional[bool] = Field(None, description="Whether product is featured")
    is_active: Optional[bool] = Field(None, description="Whether product is active")
    status: Optional[ProductStatus] = Field(None, description="Product status")
    tags: Optional[List[str]] = Field(None, description="Product tags")
    images: Optional[List[str]] = Field(None, description="Product image URLs")
    main_image: Optional[str] = Field(None, description="Main product image URL")
    seo_title: Optional[str] = Field(None, max_length=60, description="SEO title")
    seo_description: Optional[str] = Field(None, max_length=160, description="SEO description")
    seo_keywords: Optional[List[str]] = Field(None, description="SEO keywords")
    meta_data: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    notes: Optional[str] = Field(None, description="Admin notes")

class AdminProductResponse(BaseModel):
    """Response schema for admin product management"""
    product_id: str = Field(..., description="Product unique identifier")
    product_name: str = Field(..., description="Product name")
    description: str = Field(..., description="Product description")
    short_description: Optional[str] = Field(None, description="Short product description")
    category_id: str = Field(..., description="Category ID")
    category_name: str = Field(..., description="Category name")
    brand: Optional[str] = Field(None, description="Product brand")
    sku: str = Field(..., description="Stock Keeping Unit")
    barcode: Optional[str] = Field(None, description="Product barcode")
    price: float = Field(..., description="Product price")
    compare_price: Optional[float] = Field(None, description="Compare at price")
    cost_price: Optional[float] = Field(None, description="Product cost price")
    weight: Optional[float] = Field(None, description="Product weight in kg")
    dimensions: Optional[Dict[str, float]] = Field(None, description="Product dimensions")
    stock_quantity: int = Field(..., description="Available stock quantity")
    min_stock_level: int = Field(..., description="Minimum stock level for alerts")
    max_stock_level: Optional[int] = Field(None, description="Maximum stock level")
    is_featured: bool = Field(..., description="Whether product is featured")
    is_active: bool = Field(..., description="Whether product is active")
    status: ProductStatus = Field(..., description="Product status")
    tags: List[str] = Field(..., description="Product tags")
    images: List[str] = Field(..., description="Product image URLs")
    main_image: Optional[str] = Field(None, description="Main product image URL")
    seo_title: Optional[str] = Field(None, description="SEO title")
    seo_description: Optional[str] = Field(None, description="SEO description")
    seo_keywords: List[str] = Field(..., description="SEO keywords")
    meta_data: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    notes: Optional[str] = Field(None, description="Admin notes")
    views_count: int = Field(..., description="Number of product views")
    sales_count: int = Field(..., description="Number of product sales")
    rating_average: float = Field(..., description="Average product rating")
    rating_count: int = Field(..., description="Number of product ratings")
    created_at: datetime = Field(..., description="When product was created")
    updated_at: datetime = Field(..., description="When product was last updated")
    created_by: str = Field(..., description="User ID who created the product")
    last_modified_by: str = Field(..., description="User ID who last modified the product")
    
    class Config:
        from_attributes = True

class AdminProductListResponse(BaseModel):
    """Response schema for admin product list"""
    products: List[AdminProductResponse] = Field(..., description="List of products")
    total_count: int = Field(..., description="Total number of products")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Page size")
    total_pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_prev: bool = Field(..., description="Whether there is a previous page")
    filters_applied: Dict[str, Any] = Field(..., description="Filters that were applied")
    summary: Dict[str, Any] = Field(..., description="Summary of filtered results")

class AdminProductFilter(BaseModel):
    """Filter schema for admin product management"""
    search: Optional[str] = Field(None, description="Search in product name, description, SKU")
    category_id: Optional[str] = Field(None, description="Filter by category ID")
    brand: Optional[str] = Field(None, description="Filter by brand")
    status: Optional[ProductStatus] = Field(None, description="Filter by product status")
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    is_featured: Optional[bool] = Field(None, description="Filter by featured status")
    price_min: Optional[float] = Field(None, ge=0, description="Minimum price")
    price_max: Optional[float] = Field(None, ge=0, description="Maximum price")
    stock_min: Optional[int] = Field(None, ge=0, description="Minimum stock quantity")
    stock_max: Optional[int] = Field(None, ge=0, description="Maximum stock quantity")
    created_date_from: Optional[datetime] = Field(None, description="Created from date")
    created_date_to: Optional[datetime] = Field(None, description="Created to date")
    updated_date_from: Optional[datetime] = Field(None, description="Updated from date")
    updated_date_to: Optional[datetime] = Field(None, description="Updated to date")
    sort_by: str = Field("created_at", description="Sort field")
    sort_order: str = Field("desc", description="Sort order (asc/desc)")
    page: int = Field(1, ge=1, description="Page number")
    size: int = Field(20, ge=1, le=100, description="Page size")

# =============================================================================
# ADMIN USER MANAGEMENT SCHEMAS
# =============================================================================

class AdminUserResponse(BaseModel):
    """Response schema for admin user management"""
    user_id: str = Field(..., description="User unique identifier")
    username: str = Field(..., description="Username")
    email: str = Field(..., description="Email address")
    first_name: str = Field(..., description="First name")
    last_name: str = Field(..., description="Last name")
    phone_number: Optional[str] = Field(None, description="Phone number")
    is_active: bool = Field(..., description="Whether user is active")
    is_verified: bool = Field(..., description="Whether user is verified")
    role: str = Field(..., description="User role")
    points_balance: int = Field(..., description="User points balance")
    total_orders: int = Field(..., description="Total number of orders")
    total_spent: float = Field(..., description="Total amount spent")
    last_login: Optional[datetime] = Field(None, description="Last login time")
    created_at: datetime = Field(..., description="When user was created")
    updated_at: datetime = Field(..., description="When user was last updated")
    
    class Config:
        from_attributes = True

class AdminUserListResponse(BaseModel):
    """Response schema for admin user list"""
    users: List[AdminUserResponse] = Field(..., description="List of users")
    total_count: int = Field(..., description="Total number of users")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Page size")
    total_pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_prev: bool = Field(None, description="Whether there is a previous page")

# =============================================================================
# ADMIN DASHBOARD SCHEMAS
# =============================================================================

class AdminDashboardStats(BaseModel):
    """Schema for admin dashboard statistics"""
    total_products: int = Field(..., description="Total number of products")
    active_products: int = Field(..., description="Number of active products")
    draft_products: int = Field(..., description="Number of draft products")
    out_of_stock_products: int = Field(..., description="Number of out of stock products")
    total_users: int = Field(..., description="Total number of users")
    active_users: int = Field(..., description="Number of active users")
    total_orders: int = Field(..., description="Total number of orders")
    pending_orders: int = Field(..., description="Number of pending orders")
    total_revenue: float = Field(..., description="Total revenue")
    monthly_revenue: float = Field(..., description="Monthly revenue")
    low_stock_alerts: int = Field(..., description="Number of low stock alerts")
    recent_activities: List[Dict[str, Any]] = Field(..., description="Recent system activities")

class AdminActivityLog(BaseModel):
    """Schema for admin activity log"""
    log_id: str = Field(..., description="Log unique identifier")
    user_id: str = Field(..., description="User ID who performed the action")
    username: str = Field(..., description="Username who performed the action")
    action: str = Field(..., description="Action performed")
    resource_type: str = Field(..., description="Type of resource affected")
    resource_id: str = Field(..., description="ID of resource affected")
    details: Dict[str, Any] = Field(..., description="Action details")
    ip_address: Optional[str] = Field(None, description="IP address of the action")
    user_agent: Optional[str] = Field(None, description="User agent of the action")
    created_at: datetime = Field(..., description="When action was performed")
    
    class Config:
        from_attributes = True

# =============================================================================
# INTERNAL SCHEMAS
# =============================================================================

class AdminProductCreate(BaseModel):
    """Internal schema for creating products"""
    product_name: str
    description: str
    short_description: Optional[str]
    category_id: str
    brand: Optional[str]
    sku: str
    barcode: Optional[str]
    price: float
    compare_price: Optional[float]
    cost_price: Optional[float]
    weight: Optional[float]
    dimensions: Optional[Dict[str, float]]
    stock_quantity: int
    min_stock_level: int
    max_stock_level: Optional[int]
    is_featured: bool
    is_active: bool
    status: ProductStatus
    tags: List[str]
    images: List[str]
    main_image: Optional[str]
    seo_title: Optional[str]
    seo_description: Optional[str]
    seo_keywords: List[str]
    meta_data: Optional[Dict[str, Any]]
    notes: Optional[str]
    created_by: str
    last_modified_by: str

class AdminProductUpdate(BaseModel):
    """Internal schema for updating products"""
    product_name: Optional[str]
    description: Optional[str]
    short_description: Optional[str]
    category_id: Optional[str]
    brand: Optional[str]
    sku: Optional[str]
    barcode: Optional[str]
    price: Optional[float]
    compare_price: Optional[float]
    cost_price: Optional[float]
    weight: Optional[float]
    dimensions: Optional[Dict[str, float]]
    stock_quantity: Optional[int]
    min_stock_level: Optional[int]
    max_stock_level: Optional[int]
    is_featured: Optional[bool]
    is_active: Optional[bool]
    status: Optional[ProductStatus]
    tags: Optional[List[str]]
    images: Optional[List[str]]
    main_image: Optional[str]
    seo_title: Optional[str]
    seo_description: Optional[str]
    seo_keywords: Optional[List[str]]
    meta_data: Optional[Dict[str, Any]]
    notes: Optional[str]
    last_modified_by: str

# =============================================================================
# ADMIN ORDER MANAGEMENT SCHEMAS
# =============================================================================

class AdminOrderResponse(BaseModel):
    """Response schema for admin order management"""
    order_id: str = Field(..., description="Order unique identifier")
    order_number: str = Field(..., description="Human-readable order number")
    user_id: str = Field(..., description="User ID who placed the order")
    username: str = Field(..., description="Username who placed the order")
    email: str = Field(..., description="User email")
    order_status: str = Field(..., description="Current order status")
    payment_status: str = Field(..., description="Current payment status")
    shipping_status: str = Field(..., description="Current shipping status")
    order_type: str = Field(..., description="Type of order")
    shipping_method: str = Field(..., description="Shipping method selected")
    subtotal: float = Field(..., description="Order subtotal")
    total_discount: float = Field(..., description="Total discount applied")
    total_tax: float = Field(..., description="Total tax amount")
    shipping_cost: float = Field(..., description="Shipping cost")
    total_amount: float = Field(..., description="Final total amount")
    applied_promotions: List[str] = Field(..., description="List of applied promotion IDs")
    items_count: int = Field(..., description="Number of items in order")
    total_quantity: int = Field(..., description="Total quantity of all items")
    estimated_delivery: Optional[datetime] = Field(None, description="Estimated delivery date")
    actual_delivery: Optional[datetime] = Field(None, description="Actual delivery date")
    notes: Optional[str] = Field(None, description="Order notes")
    admin_notes: Optional[str] = Field(None, description="Admin notes")
    created_at: datetime = Field(..., description="When order was created")
    updated_at: datetime = Field(..., description="When order was last updated")
    
    class Config:
        from_attributes = True

class AdminOrderListResponse(BaseModel):
    """Response schema for admin order list"""
    orders: List[AdminOrderResponse] = Field(..., description="List of orders")
    total_count: int = Field(..., description="Total number of orders")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Page size")
    total_pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_prev: bool = Field(..., description="Whether there is a previous page")
    filters_applied: Dict[str, Any] = Field(..., description="Filters that were applied")
    summary: Dict[str, Any] = Field(..., description="Summary of filtered results")

class AdminOrderFilter(BaseModel):
    """Filter schema for admin order management"""
    search: Optional[str] = Field(None, description="Search in order number, username, email")
    order_status: Optional[str] = Field(None, description="Filter by order status")
    payment_status: Optional[str] = Field(None, description="Filter by payment status")
    shipping_status: Optional[str] = Field(None, description="Filter by shipping status")
    order_type: Optional[str] = Field(None, description="Filter by order type")
    shipping_method: Optional[str] = Field(None, description="Filter by shipping method")
    amount_min: Optional[float] = Field(None, ge=0, description="Minimum order amount")
    amount_max: Optional[float] = Field(None, ge=0, description="Maximum order amount")
    created_date_from: Optional[datetime] = Field(None, description="Created from date")
    created_date_to: Optional[datetime] = Field(None, description="Created to date")
    delivery_date_from: Optional[datetime] = Field(None, description="Delivery from date")
    delivery_date_to: Optional[datetime] = Field(None, description="Delivery to date")
    has_promotions: Optional[bool] = Field(None, description="Whether order has promotions")
    sort_by: str = Field("created_at", description="Sort field")
    sort_order: str = Field("desc", description="Sort order (asc/desc)")
    page: int = Field(1, ge=1, description="Page number")
    size: int = Field(20, ge=1, le=100, description="Page size")

class AdminOrderStatusUpdate(BaseModel):
    """Request schema for updating order status"""
    order_status: str = Field(..., description="New order status")
    payment_status: Optional[str] = Field(None, description="New payment status")
    shipping_status: Optional[str] = Field(None, description="New shipping status")
    admin_notes: Optional[str] = Field(None, description="Admin notes for the status change")
    estimated_delivery: Optional[datetime] = Field(None, description="Updated estimated delivery date")
    actual_delivery: Optional[datetime] = Field(None, description="Actual delivery date if delivered")

class AdminOrderStats(BaseModel):
    """Schema for admin order statistics"""
    total_orders: int = Field(..., description="Total number of orders")
    total_revenue: float = Field(..., description="Total revenue from orders")
    monthly_revenue: float = Field(..., description="Monthly revenue")
    average_order_value: float = Field(..., description="Average order value")
    orders_by_status: Dict[str, int] = Field(..., description="Orders count by status")
    orders_by_payment_status: Dict[str, int] = Field(..., description="Orders count by payment status")
    orders_by_shipping_status: Dict[str, int] = Field(..., description="Orders count by shipping status")
    orders_by_month: List[Dict[str, Any]] = Field(..., description="Orders by month")
    top_products: List[Dict[str, Any]] = Field(..., description="Top selling products")
    top_categories: List[Dict[str, Any]] = Field(..., description="Top selling categories")
    delivery_performance: Dict[str, Any] = Field(..., description="Delivery performance metrics")

# =============================================================================
# ADMIN PROMOTION MANAGEMENT SCHEMAS
# =============================================================================

class AdminPromotionCreateRequest(BaseModel):
    """Request schema for creating promotions (admin)"""
    promotion_name: str = Field(..., min_length=1, max_length=255, description="Promotion name")
    description: str = Field(..., min_length=10, description="Promotion description")
    promotion_type: str = Field(..., description="Type of promotion")
    discount_type: str = Field(..., description="Type of discount")
    discount_value: float = Field(..., gt=0, description="Discount value")
    max_discount_amount: Optional[float] = Field(None, ge=0, description="Maximum discount amount")
    min_order_amount: Optional[float] = Field(None, ge=0, description="Minimum order amount required")
    max_order_amount: Optional[float] = Field(None, ge=0, description="Maximum order amount allowed")
    applicable_categories: List[str] = Field(default_factory=list, description="Categories this promotion applies to")
    applicable_products: List[str] = Field(default_factory=list, description="Specific products this promotion applies to")
    excluded_products: List[str] = Field(default_factory=list, description="Products excluded from this promotion")
    user_groups: List[str] = Field(default_factory=list, description="User groups eligible for this promotion")
    usage_limit_per_user: Optional[int] = Field(None, ge=1, description="Usage limit per user")
    total_usage_limit: Optional[int] = Field(None, ge=1, description="Total usage limit")
    current_usage: int = Field(0, ge=0, description="Current usage count")
    start_date: datetime = Field(..., description="Promotion start date")
    end_date: datetime = Field(..., description="Promotion end date")
    is_active: bool = Field(True, description="Whether promotion is active")
    priority: int = Field(1, ge=1, le=100, description="Promotion priority (1-100)")
    auto_apply: bool = Field(False, description="Whether promotion auto-applies to eligible orders")
    conditions: Dict[str, Any] = Field(default_factory=dict, description="Additional conditions")
    notes: Optional[str] = Field(None, description="Admin notes")
    
    @validator('end_date')
    def validate_end_date(cls, v, values):
        if 'start_date' in values and v <= values['start_date']:
            raise ValueError('End date must be after start date')
        return v
    
    @validator('discount_value')
    def validate_discount_value(cls, v, values):
        if 'discount_type' in values:
            if values['discount_type'] == 'percentage' and v > 100:
                raise ValueError('Percentage discount cannot exceed 100%')
        return v

class AdminPromotionUpdateRequest(BaseModel):
    """Request schema for updating promotions (admin)"""
    promotion_name: Optional[str] = Field(None, min_length=1, max_length=255, description="Promotion name")
    description: Optional[str] = Field(None, min_length=10, description="Promotion description")
    promotion_type: Optional[str] = Field(None, description="Type of promotion")
    discount_type: Optional[str] = Field(None, description="Type of discount")
    discount_value: Optional[float] = Field(None, gt=0, description="Discount value")
    max_discount_amount: Optional[float] = Field(None, ge=0, description="Maximum discount amount")
    min_order_amount: Optional[float] = Field(None, ge=0, description="Minimum order amount required")
    max_order_amount: Optional[float] = Field(None, ge=0, description="Maximum order amount allowed")
    applicable_categories: Optional[List[str]] = Field(None, description="Categories this promotion applies to")
    applicable_products: Optional[List[str]] = Field(None, description="Specific products this promotion applies to")
    excluded_products: Optional[List[str]] = Field(None, description="Products excluded from this promotion")
    user_groups: Optional[List[str]] = Field(None, description="User groups eligible for this promotion")
    usage_limit_per_user: Optional[int] = Field(None, ge=1, description="Usage limit per user")
    total_usage_limit: Optional[int] = Field(None, ge=1, description="Total usage limit")
    start_date: Optional[datetime] = Field(None, description="Promotion start date")
    end_date: Optional[datetime] = Field(None, description="Promotion end date")
    is_active: Optional[bool] = Field(None, description="Whether promotion is active")
    priority: Optional[int] = Field(None, ge=1, le=100, description="Promotion priority (1-100)")
    auto_apply: Optional[bool] = Field(None, description="Whether promotion auto-applies to eligible orders")
    conditions: Optional[Dict[str, Any]] = Field(None, description="Additional conditions")
    notes: Optional[str] = Field(None, description="Admin notes")

class AdminPromotionResponse(BaseModel):
    """Response schema for admin promotion management"""
    promotion_id: str = Field(..., description="Promotion unique identifier")
    promotion_name: str = Field(..., description="Promotion name")
    description: str = Field(..., description="Promotion description")
    promotion_type: str = Field(..., description="Type of promotion")
    discount_type: str = Field(..., description="Type of discount")
    discount_value: float = Field(..., description="Discount value")
    max_discount_amount: Optional[float] = Field(None, description="Maximum discount amount")
    min_order_amount: Optional[float] = Field(None, description="Minimum order amount required")
    max_order_amount: Optional[float] = Field(None, description="Maximum order amount allowed")
    applicable_categories: List[str] = Field(..., description="Categories this promotion applies to")
    applicable_products: List[str] = Field(..., description="Specific products this promotion applies to")
    excluded_products: List[str] = Field(..., description="Products excluded from this promotion")
    user_groups: List[str] = Field(..., description="User groups eligible for this promotion")
    usage_limit_per_user: Optional[int] = Field(None, description="Usage limit per user")
    total_usage_limit: Optional[int] = Field(None, description="Total usage limit")
    current_usage: int = Field(..., description="Current usage count")
    start_date: datetime = Field(..., description="Promotion start date")
    end_date: datetime = Field(..., description="Promotion end date")
    is_active: bool = Field(..., description="Whether promotion is active")
    priority: int = Field(..., description="Promotion priority")
    auto_apply: bool = Field(..., description="Whether promotion auto-applies")
    conditions: Dict[str, Any] = Field(..., description="Additional conditions")
    notes: Optional[str] = Field(None, description="Admin notes")
    total_revenue_generated: float = Field(..., description="Total revenue generated through this promotion")
    total_orders_affected: int = Field(..., description="Total orders affected by this promotion")
    average_discount_per_order: float = Field(..., description="Average discount per order")
    created_at: datetime = Field(..., description="When promotion was created")
    updated_at: datetime = Field(..., description="When promotion was last updated")
    created_by: str = Field(..., description="User ID who created the promotion")
    last_modified_by: str = Field(..., description="User ID who last modified the promotion")
    
    class Config:
        from_attributes = True

class AdminPromotionListResponse(BaseModel):
    """Response schema for admin promotion list"""
    promotions: List[AdminPromotionResponse] = Field(..., description="List of promotions")
    total_count: int = Field(..., description="Total number of promotions")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Page size")
    total_pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_prev: bool = Field(..., description="Whether there is a previous page")
    filters_applied: Dict[str, Any] = Field(..., description="Filters that were applied")
    summary: Dict[str, Any] = Field(..., description="Summary of filtered results")

class AdminPromotionFilter(BaseModel):
    """Filter schema for admin promotion management"""
    search: Optional[str] = Field(None, description="Search in promotion name, description")
    promotion_type: Optional[str] = Field(None, description="Filter by promotion type")
    discount_type: Optional[str] = Field(None, description="Filter by discount type")
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    auto_apply: Optional[bool] = Field(None, description="Filter by auto-apply status")
    start_date_from: Optional[datetime] = Field(None, description="Start date from")
    start_date_to: Optional[datetime] = Field(None, description="Start date to")
    end_date_from: Optional[datetime] = Field(None, description="End date from")
    end_date_to: Optional[datetime] = Field(None, description="End date to")
    min_discount_value: Optional[float] = Field(None, ge=0, description="Minimum discount value")
    max_discount_value: Optional[float] = Field(None, ge=0, description="Maximum discount value")
    sort_by: str = Field("created_at", description="Sort field")
    sort_order: str = Field("desc", description="Sort order (asc/desc)")
    page: int = Field(1, ge=1, description="Page number")
    size: int = Field(20, ge=1, le=100, description="Page size")