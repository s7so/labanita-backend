from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field

# =============================================================================
# RESPONSE SCHEMAS
# =============================================================================

class CategoryResponse(BaseModel):
    """Response schema for category"""
    category_id: str = Field(..., description="Category unique identifier")
    category_name: str = Field(..., description="Category name")
    description: Optional[str] = Field(None, description="Category description")
    image_url: Optional[str] = Field(None, description="Category image URL")
    parent_category_id: Optional[str] = Field(None, description="Parent category ID if this is a subcategory")
    is_active: bool = Field(..., description="Whether category is active")
    sort_order: int = Field(..., description="Sort order for display")
    created_at: datetime = Field(..., description="When category was created")
    updated_at: datetime = Field(..., description="When category was last updated")
    
    class Config:
        from_attributes = True

class CategoryListResponse(BaseModel):
    """Response schema for list of categories"""
    categories: List[CategoryResponse] = Field(..., description="List of categories")
    total_count: int = Field(..., description="Total number of categories")
    active_count: int = Field(..., description="Number of active categories")

class CategoryWithProductsResponse(BaseModel):
    """Response schema for category with its products"""
    category: CategoryResponse = Field(..., description="Category information")
    products: List['ProductResponse'] = Field(..., description="Products in this category")
    total_products: int = Field(..., description="Total number of products in category")
    subcategories: List[CategoryResponse] = Field(..., description="Subcategories if any")

class ProductResponse(BaseModel):
    """Response schema for product in category"""
    product_id: str = Field(..., description="Product unique identifier")
    product_name: str = Field(..., description="Product name")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., description="Product price")
    sale_price: Optional[float] = Field(None, description="Sale price if on discount")
    image_url: Optional[str] = Field(None, description="Product image URL")
    is_active: bool = Field(..., description="Whether product is active")
    stock_quantity: int = Field(..., description="Available stock quantity")
    rating: Optional[float] = Field(None, description="Average product rating")
    review_count: int = Field(..., description="Number of reviews")
    created_at: datetime = Field(..., description="When product was created")
    
    class Config:
        from_attributes = True

# =============================================================================
# INTERNAL SCHEMAS
# =============================================================================

class CategoryCreate(BaseModel):
    """Internal schema for creating category"""
    category_name: str
    description: Optional[str] = None
    image_url: Optional[str] = None
    parent_category_id: Optional[str] = None
    is_active: bool = True
    sort_order: int = 0

class CategoryUpdate(BaseModel):
    """Internal schema for updating category"""
    category_name: Optional[str] = None
    description: Optional[str] = None
    image_url: Optional[str] = None
    parent_category_id: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None

# =============================================================================
# FILTER SCHEMAS
# =============================================================================

class CategoryFilter(BaseModel):
    """Schema for filtering categories"""
    is_active: Optional[bool] = Field(None, description="Filter by active status")
    parent_category_id: Optional[str] = Field(None, description="Filter by parent category")
    search: Optional[str] = Field(None, description="Search in category name and description")
    sort_by: str = Field("sort_order", description="Sort field")
    sort_order: str = Field("asc", description="Sort order (asc/desc)")

class ProductFilter(BaseModel):
    """Schema for filtering products in category"""
    min_price: Optional[float] = Field(None, description="Minimum price filter")
    max_price: Optional[float] = Field(None, description="Maximum price filter")
    in_stock: Optional[bool] = Field(None, description="Filter by stock availability")
    on_sale: Optional[bool] = Field(None, description="Filter by sale status")
    min_rating: Optional[float] = Field(None, description="Minimum rating filter")
    search: Optional[str] = Field(None, description="Search in product name and description")
    sort_by: str = Field("created_at", description="Sort field")
    sort_order: str = Field("desc", description="Sort order (asc/desc)")

# =============================================================================
# STATISTICS SCHEMAS
# =============================================================================

class CategoryStatsResponse(BaseModel):
    """Response schema for category statistics"""
    category_id: str = Field(..., description="Category unique identifier")
    category_name: str = Field(..., description="Category name")
    total_products: int = Field(..., description="Total number of products")
    active_products: int = Field(..., description="Number of active products")
    total_sales: float = Field(..., description="Total sales amount")
    average_price: float = Field(..., description="Average product price")
    average_rating: Optional[float] = Field(None, description="Average product rating")
    subcategory_count: int = Field(..., description="Number of subcategories")
    last_product_added: Optional[datetime] = Field(None, description="When last product was added")

# =============================================================================
# HIERARCHY SCHEMAS
# =============================================================================

class CategoryHierarchyResponse(BaseModel):
    """Response schema for category hierarchy"""
    category: CategoryResponse = Field(..., description="Current category")
    parent: Optional[CategoryResponse] = Field(None, description="Parent category if exists")
    children: List[CategoryResponse] = Field(..., description="Child categories if any")
    siblings: List[CategoryResponse] = Field(..., description="Sibling categories at same level")
    breadcrumb: List[CategoryResponse] = Field(..., description="Breadcrumb navigation path")

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

class PaginatedResponse(BaseModel):
    """Base schema for paginated responses"""
    page: int = Field(..., description="Current page number")
    size: int = Field(..., description="Page size")
    total: int = Field(..., description="Total number of items")
    pages: int = Field(..., description="Total number of pages")
    has_next: bool = Field(..., description="Whether there is a next page")
    has_prev: bool = Field(..., description="Whether there is a previous page")

class PaginatedCategoriesResponse(PaginatedResponse):
    """Paginated response for categories"""
    categories: List[CategoryResponse] = Field(..., description="Categories in current page")

class PaginatedProductsResponse(PaginatedResponse):
    """Paginated response for products"""
    products: List[ProductResponse] = Field(..., description="Products in current page")