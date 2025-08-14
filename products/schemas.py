from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, validator
from enum import Enum

# =============================================================================
# ENUMS
# =============================================================================

class ProductSortField(str, Enum):
    """Product sorting fields"""
    NAME = "product_name"
    PRICE = "price"
    CREATED_AT = "created_at"
    RATING = "rating"
    STOCK_QUANTITY = "stock_quantity"
    SALES_COUNT = "sales_count"
    REVIEW_COUNT = "review_count"

class ProductSortOrder(str, Enum):
    """Product sorting orders"""
    ASC = "asc"
    DESC = "desc"

class ProductStatus(str, Enum):
    """Product status values"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    OUT_OF_STOCK = "out_of_stock"
    DISCONTINUED = "discontinued"

# =============================================================================
# RESPONSE SCHEMAS
# =============================================================================

class ProductResponse(BaseModel):
    """Response schema for product"""
    product_id: str = Field(..., description="Product unique identifier")
    product_name: str = Field(..., description="Product name")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., description="Product price")
    sale_price: Optional[float] = Field(None, description="Sale price if on discount")
    cost_price: Optional[float] = Field(None, description="Product cost price")
    sku: Optional[str] = Field(None, description="Stock keeping unit")
    barcode: Optional[str] = Field(None, description="Product barcode")
    weight: Optional[float] = Field(None, description="Product weight in grams")
    dimensions: Optional[str] = Field(None, description="Product dimensions (LxWxH)")
    image_url: Optional[str] = Field(None, description="Main product image URL")
    gallery_images: Optional[List[str]] = Field(None, description="Additional product images")
    category_id: str = Field(..., description="Category ID")
    category_name: str = Field(..., description="Category name")
    is_active: bool = Field(..., description="Whether product is active")
    is_featured: bool = Field(..., description="Whether product is featured")
    is_new_arrival: bool = Field(..., description="Whether product is new arrival")
    is_best_selling: bool = Field(..., description="Whether product is best selling")
    stock_quantity: int = Field(..., description="Available stock quantity")
    min_stock_threshold: int = Field(..., description="Minimum stock threshold")
    max_stock_threshold: int = Field(..., description="Maximum stock threshold")
    rating: Optional[float] = Field(None, description="Average product rating")
    review_count: int = Field(..., description="Number of reviews")
    sales_count: int = Field(..., description="Total sales count")
    view_count: int = Field(..., description="Product view count")
    tags: Optional[List[str]] = Field(None, description="Product tags")
    allergens: Optional[List[str]] = Field(None, description="Allergen information")
    nutritional_info: Optional[Dict[str, Any]] = Field(None, description="Nutritional information")
    ingredients: Optional[List[str]] = Field(None, description="Product ingredients")
    storage_instructions: Optional[str] = Field(None, description="Storage instructions")
    expiry_date: Optional[datetime] = Field(None, description="Product expiry date")
    created_at: datetime = Field(..., description="When product was created")
    updated_at: datetime = Field(..., description="When product was last updated")
    
    class Config:
        from_attributes = True

class ProductListResponse(BaseModel):
    """Response schema for list of products"""
    products: List[ProductResponse] = Field(..., description="List of products")
    total_count: int = Field(..., description="Total number of products")
    active_count: int = Field(..., description="Number of active products")
    featured_count: int = Field(..., description="Number of featured products")
    new_arrivals_count: int = Field(..., description="Number of new arrivals")
    best_selling_count: int = Field(..., description="Number of best selling products")

class ProductDetailResponse(BaseModel):
    """Response schema for detailed product information"""
    product: ProductResponse = Field(..., description="Product information")
    related_products: List[ProductResponse] = Field(..., description="Related products")
    category_path: List[Dict[str, str]] = Field(..., description="Category navigation path")
    stock_status: str = Field(..., description="Current stock status")
    discount_percentage: Optional[float] = Field(None, description="Discount percentage if on sale")
    is_low_stock: bool = Field(..., description="Whether product is low on stock")
    estimated_delivery: Optional[str] = Field(None, description="Estimated delivery time")

class FeaturedProductsResponse(BaseModel):
    """Response schema for featured products"""
    products: List[ProductResponse] = Field(..., description="Featured products")
    total_count: int = Field(..., description="Total number of featured products")
    category_breakdown: Dict[str, int] = Field(..., description="Featured products by category")

class NewArrivalsResponse(BaseModel):
    """Response schema for new arrival products"""
    products: List[ProductResponse] = Field(..., description="New arrival products")
    total_count: int = Field(..., description="Total number of new arrivals")
    arrival_period: str = Field(..., description="New arrival period (e.g., 'Last 30 days')")

class BestSellingProductsResponse(BaseModel):
    """Response schema for best selling products"""
    products: List[ProductResponse] = Field(..., description="Best selling products")
    total_count: int = Field(..., description="Total number of best selling products")
    sales_period: str = Field(..., description="Sales period for ranking (e.g., 'Last 90 days')")
    sales_ranking: List[Dict[str, Any]] = Field(..., description="Sales ranking information")

class ProductSearchResponse(BaseModel):
    """Response schema for product search results"""
    products: List[ProductResponse] = Field(..., description="Search results")
    total_count: int = Field(..., description="Total number of matching products")
    search_query: str = Field(..., description="Original search query")
    search_suggestions: List[str] = Field(..., description="Search suggestions")
    category_filters: List[Dict[str, Any]] = Field(..., description="Available category filters")
    price_range: Dict[str, float] = Field(..., description="Price range of results")

class ProductFilterResponse(BaseModel):
    """Response schema for filtered products"""
    products: List[ProductResponse] = Field(..., description="Filtered products")
    total_count: int = Field(..., description="Total number of matching products")
    applied_filters: Dict[str, Any] = Field(..., description="Applied filters")
    available_filters: Dict[str, Any] = Field(..., description="Available filter options")
    filter_summary: Dict[str, Any] = Field(..., description="Filter summary")

# =============================================================================
# FILTER SCHEMAS
# =============================================================================

class ProductFilter(BaseModel):
    """Schema for product filtering"""
    category_id: Optional[str] = Field(None, description="Filter by category ID")
    category_name: Optional[str] = Field(None, description="Filter by category name")
    price_min: Optional[float] = Field(None, ge=0, description="Minimum price filter")
    price_max: Optional[float] = Field(None, ge=0, description="Maximum price filter")
    in_stock: Optional[bool] = Field(None, description="Filter by stock availability")
    on_sale: Optional[bool] = Field(None, description="Filter by sale status")
    min_rating: Optional[float] = Field(None, ge=0, le=5, description="Minimum rating filter")
    is_featured: Optional[bool] = Field(None, description="Filter by featured status")
    is_new_arrival: Optional[bool] = Field(None, description="Filter by new arrival status")
    is_best_selling: Optional[bool] = Field(None, description="Filter by best selling status")
    tags: Optional[List[str]] = Field(None, description="Filter by tags")
    allergens: Optional[List[str]] = Field(None, description="Filter by allergens")
    weight_min: Optional[float] = Field(None, ge=0, description="Minimum weight filter")
    weight_max: Optional[float] = Field(None, ge=0, description="Maximum weight filter")
    
    @validator('price_max')
    def validate_price_range(cls, v, values):
        if v is not None and 'price_min' in values and values['price_min'] is not None:
            if v < values['price_min']:
                raise ValueError('Maximum price cannot be less than minimum price')
        return v
    
    @validator('weight_max')
    def validate_weight_range(cls, v, values):
        if v is not None and 'weight_min' in values and values['weight_min'] is not None:
            if v < values['weight_min']:
                raise ValueError('Maximum weight cannot be less than minimum weight')
        return v

class ProductSearch(BaseModel):
    """Schema for product search"""
    query: str = Field(..., min_length=2, description="Search query")
    category_id: Optional[str] = Field(None, description="Limit search to specific category")
    price_min: Optional[float] = Field(None, ge=0, description="Minimum price filter")
    price_max: Optional[float] = Field(None, ge=0, description="Maximum price filter")
    in_stock: Optional[bool] = Field(None, description="Filter by stock availability")
    min_rating: Optional[float] = Field(None, ge=0, le=5, description="Minimum rating filter")
    sort_by: ProductSortField = Field(ProductSortField.CREATED_AT, description="Sort field")
    sort_order: ProductSortOrder = Field(ProductSortOrder.DESC, description="Sort order")
    
    @validator('query')
    def validate_query(cls, v):
        if len(v.strip()) < 2:
            raise ValueError('Search query must be at least 2 characters long')
        return v.strip()

class ProductSort(BaseModel):
    """Schema for product sorting"""
    sort_by: ProductSortField = Field(ProductSortField.CREATED_AT, description="Sort field")
    sort_order: ProductSortOrder = Field(ProductSortOrder.DESC, description="Sort order")

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

class PaginatedProductsResponse(BaseModel):
    """Paginated response for products"""
    products: List[ProductResponse] = Field(..., description="Products in current page")
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Page size")
    total: int = Field(..., description="Total number of products")
    pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_prev: bool = Field(..., description="Whether there is a previous page")

# =============================================================================
# INTERNAL SCHEMAS
# =============================================================================

class ProductCreate(BaseModel):
    """Internal schema for creating product"""
    product_name: str
    description: Optional[str] = None
    price: float
    sale_price: Optional[float] = None
    cost_price: Optional[float] = None
    sku: Optional[str] = None
    barcode: Optional[str] = None
    weight: Optional[float] = None
    dimensions: Optional[str] = None
    image_url: Optional[str] = None
    gallery_images: Optional[List[str]] = None
    category_id: str
    is_active: bool = True
    is_featured: bool = False
    is_new_arrival: bool = False
    is_best_selling: bool = False
    stock_quantity: int = 0
    min_stock_threshold: int = 5
    max_stock_threshold: int = 1000
    tags: Optional[List[str]] = None
    allergens: Optional[List[str]] = None
    nutritional_info: Optional[Dict[str, Any]] = None
    ingredients: Optional[List[str]] = None
    storage_instructions: Optional[str] = None
    expiry_date: Optional[datetime] = None

class ProductUpdate(BaseModel):
    """Internal schema for updating product"""
    product_name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    sale_price: Optional[float] = None
    cost_price: Optional[float] = None
    sku: Optional[str] = None
    barcode: Optional[str] = None
    weight: Optional[float] = None
    dimensions: Optional[str] = None
    image_url: Optional[str] = None
    gallery_images: Optional[List[str]] = None
    category_id: Optional[str] = None
    is_active: Optional[bool] = None
    is_featured: Optional[bool] = None
    is_new_arrival: Optional[bool] = None
    is_best_selling: Optional[bool] = None
    stock_quantity: Optional[int] = None
    min_stock_threshold: Optional[int] = None
    max_stock_threshold: Optional[int] = None
    tags: Optional[List[str]] = None
    allergens: Optional[List[str]] = None
    nutritional_info: Optional[Dict[str, Any]] = None
    ingredients: Optional[List[str]] = None
    storage_instructions: Optional[str] = None
    expiry_date: Optional[datetime] = None

# =============================================================================
# STATISTICS SCHEMAS
# =============================================================================

class ProductStatsResponse(BaseModel):
    """Response schema for product statistics"""
    product_id: str = Field(..., description="Product unique identifier")
    product_name: str = Field(..., description="Product name")
    total_sales: float = Field(..., description="Total sales amount")
    total_quantity_sold: int = Field(..., description="Total quantity sold")
    average_order_value: float = Field(..., description="Average order value")
    view_count: int = Field(..., description="Product view count")
    conversion_rate: float = Field(..., description="View to purchase conversion rate")
    stock_turnover: float = Field(..., description="Stock turnover rate")
    profit_margin: Optional[float] = Field(None, description="Profit margin percentage")
    last_sale_date: Optional[datetime] = Field(None, description="Date of last sale")
    sales_trend: List[Dict[str, Any]] = Field(..., description="Sales trend data")

class ProductAnalyticsResponse(BaseModel):
    """Response schema for product analytics"""
    total_products: int = Field(..., description="Total number of products")
    active_products: int = Field(..., description="Number of active products")
    out_of_stock_products: int = Field(..., description="Number of out of stock products")
    low_stock_products: int = Field(..., description="Number of low stock products")
    featured_products: int = Field(..., description="Number of featured products")
    new_arrivals: int = Field(..., description="Number of new arrivals")
    best_selling_products: int = Field(..., description="Number of best selling products")
    total_stock_value: float = Field(..., description="Total stock value")
    average_price: float = Field(..., description="Average product price")
    average_rating: Optional[float] = Field(None, description="Average product rating")
    top_categories: List[Dict[str, Any]] = Field(..., description="Top product categories")
    sales_performance: List[Dict[str, Any]] = Field(..., description="Sales performance data")

# =============================================================================
# RELATED PRODUCTS SCHEMAS
# =============================================================================

class RelatedProductsResponse(BaseModel):
    """Response schema for related products"""
    product_id: str = Field(..., description="Original product ID")
    related_products: List[ProductResponse] = Field(..., description="Related products")
    relationship_type: str = Field(..., description="Type of relationship")
    total_count: int = Field(..., description="Total number of related products")
    categories: List[str] = Field(..., description="Categories of related products")

class ProductRecommendationsResponse(BaseModel):
    """Response schema for product recommendations"""
    user_id: Optional[str] = Field(None, description="User ID if personalized")
    recommendations: List[ProductResponse] = Field(..., description="Recommended products")
    recommendation_type: str = Field(..., description="Type of recommendation")
    confidence_score: float = Field(..., description="Recommendation confidence score")
    total_count: int = Field(..., description="Total number of recommendations")