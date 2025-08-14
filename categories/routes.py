from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.orm import Session

from database import get_db
from core.responses import success_response, error_response
from core.exceptions import (
    NotFoundException, 
    ValidationException, 
    ConflictException
)
from categories.schemas import (
    CategoryResponse, CategoryListResponse, CategoryWithProductsResponse,
    ProductResponse, CategoryStatsResponse, CategoryHierarchyResponse,
    PaginationParams, PaginatedProductsResponse
)
from categories.services import CategoryService

# Create router
router = APIRouter(prefix="/api/categories", tags=["Categories"])

# =============================================================================
# CATEGORY RETRIEVAL ENDPOINTS
# =============================================================================

@router.get("/", response_model=CategoryListResponse)
async def get_all_categories(
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    parent_category_id: Optional[str] = Query(None, description="Filter by parent category ID"),
    search: Optional[str] = Query(None, description="Search in category name and description"),
    sort_by: str = Query("sort_order", description="Sort field (category_name, sort_order, created_at)"),
    sort_order: str = Query("asc", description="Sort order (asc/desc)"),
    db: Session = Depends(get_db)
):
    """
    Get all categories with optional filtering and sorting
    
    Returns a list of all categories with optional filtering by:
    - Active status
    - Parent category
    - Search query in name/description
    
    Supports sorting by various fields and pagination.
    """
    try:
        category_service = CategoryService(db)
        
        # Validate sort parameters
        valid_sort_fields = ["category_name", "sort_order", "created_at", "updated_at"]
        if sort_by not in valid_sort_fields:
            raise ValidationException(f"Invalid sort field. Must be one of: {', '.join(valid_sort_fields)}")
        
        if sort_order.lower() not in ["asc", "desc"]:
            raise ValidationException("Sort order must be 'asc' or 'desc'")
        
        categories = category_service.get_all_categories(
            is_active=is_active,
            parent_category_id=parent_category_id,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        return categories
        
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get categories")

@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category_by_id(
    category_id: str = Path(..., description="ID of the category to retrieve"),
    db: Session = Depends(get_db)
):
    """
    Get a specific category by ID
    
    Returns detailed information about a single category including:
    - Basic category information
    - Parent/child relationships
    - Active status and metadata
    """
    try:
        category_service = CategoryService(db)
        category = category_service.get_category_by_id(category_id)
        return category
        
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get category")

@router.get("/{category_id}/products", response_model=CategoryWithProductsResponse)
async def get_category_products(
    category_id: str = Path(..., description="ID of the category to get products for"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price filter"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price filter"),
    in_stock: Optional[bool] = Query(None, description="Filter by stock availability"),
    on_sale: Optional[bool] = Query(None, description="Filter by sale status"),
    min_rating: Optional[float] = Query(None, ge=0, le=5, description="Minimum rating filter"),
    search: Optional[str] = Query(None, description="Search in product name and description"),
    sort_by: str = Query("created_at", description="Sort field for products"),
    sort_order: str = Query("desc", description="Sort order for products (asc/desc)"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    db: Session = Depends(get_db)
):
    """
    Get products for a specific category with filtering and pagination
    
    Returns all products in the specified category with optional filtering by:
    - Price range (min/max)
    - Stock availability
    - Sale status
    - Rating
    - Search query
    
    Includes category information and subcategories.
    """
    try:
        category_service = CategoryService(db)
        
        # Validate sort parameters
        valid_sort_fields = ["product_name", "price", "created_at", "rating", "stock_quantity"]
        if sort_by not in valid_sort_fields:
            raise ValidationException(f"Invalid sort field. Must be one of: {', '.join(valid_sort_fields)}")
        
        if sort_order.lower() not in ["asc", "desc"]:
            raise ValidationException("Sort order must be 'asc' or 'desc'")
        
        # Validate price filters
        if min_price is not None and max_price is not None and min_price > max_price:
            raise ValidationException("Minimum price cannot be greater than maximum price")
        
        products = category_service.get_category_with_products(
            category_id=category_id,
            min_price=min_price,
            max_price=max_price,
            in_stock=in_stock,
            on_sale=on_sale,
            min_rating=min_rating,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            size=size
        )
        
        return products
        
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get category products")

@router.get("/{category_id}/products/paginated", response_model=PaginatedProductsResponse)
async def get_category_products_paginated(
    category_id: str = Path(..., description="ID of the category to get products for"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    min_price: Optional[float] = Query(None, ge=0, description="Minimum price filter"),
    max_price: Optional[float] = Query(None, ge=0, description="Maximum price filter"),
    in_stock: Optional[bool] = Query(None, description="Filter by stock availability"),
    on_sale: Optional[bool] = Query(None, description="Filter by sale status"),
    min_rating: Optional[float] = Query(None, ge=0, le=5, description="Minimum rating filter"),
    search: Optional[str] = Query(None, description="Search in product name and description"),
    sort_by: str = Query("created_at", description="Sort field for products"),
    sort_order: str = Query("desc", description="Sort order for products (asc/desc)"),
    db: Session = Depends(get_db)
):
    """
    Get paginated products for a specific category with filtering
    
    Returns paginated products in the specified category with comprehensive filtering options.
    This endpoint is optimized for large product catalogs with proper pagination metadata.
    """
    try:
        category_service = CategoryService(db)
        
        # Validate pagination parameters
        if page < 1:
            raise ValidationException("Page number must be greater than 0")
        
        if size < 1 or size > 100:
            raise ValidationException("Page size must be between 1 and 100")
        
        # Validate sort parameters
        valid_sort_fields = ["product_name", "price", "created_at", "rating", "stock_quantity"]
        if sort_by not in valid_sort_fields:
            raise ValidationException(f"Invalid sort field. Must be one of: {', '.join(valid_sort_fields)}")
        
        if sort_order.lower() not in ["asc", "desc"]:
            raise ValidationException("Sort order must be 'asc' or 'desc'")
        
        # Validate price filters
        if min_price is not None and max_price is not None and min_price > max_price:
            raise ValidationException("Minimum price cannot be greater than maximum price")
        
        # Create pagination object
        pagination = PaginationParams(page=page, size=size)
        
        products = category_service.get_category_products_paginated(
            category_id=category_id,
            pagination=pagination,
            min_price=min_price,
            max_price=max_price,
            in_stock=in_stock,
            on_sale=on_sale,
            min_rating=min_rating,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        return products
        
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get paginated category products")

# =============================================================================
# CATEGORY STATISTICS ENDPOINTS
# =============================================================================

@router.get("/{category_id}/statistics", response_model=CategoryStatsResponse)
async def get_category_statistics(
    category_id: str = Path(..., description="ID of the category to get statistics for"),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive statistics for a category
    
    Returns detailed statistics including:
    - Product counts (total, active)
    - Sales information
    - Average pricing and ratings
    - Subcategory information
    - Last activity timestamps
    """
    try:
        category_service = CategoryService(db)
        stats = category_service.get_category_statistics(category_id)
        return stats
        
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get category statistics")

# =============================================================================
# CATEGORY HIERARCHY ENDPOINTS
# =============================================================================

@router.get("/{category_id}/hierarchy", response_model=CategoryHierarchyResponse)
async def get_category_hierarchy(
    category_id: str = Path(..., description="ID of the category to get hierarchy for"),
    db: Session = Depends(get_db)
):
    """
    Get category hierarchy information
    
    Returns complete hierarchy information including:
    - Parent category (if any)
    - Child categories (subcategories)
    - Sibling categories at the same level
    - Breadcrumb navigation path
    """
    try:
        category_service = CategoryService(db)
        hierarchy = category_service.get_category_hierarchy(category_id)
        return hierarchy
        
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get category hierarchy")

# =============================================================================
# UTILITY ENDPOINTS
# =============================================================================

@router.get("/root/list", response_model=List[CategoryResponse])
async def get_root_categories(
    db: Session = Depends(get_db)
):
    """
    Get all root-level categories (no parent)
    
    Returns only top-level categories that don't have a parent category.
    Useful for building main navigation menus.
    """
    try:
        category_service = CategoryService(db)
        root_categories = category_service.get_root_categories()
        return root_categories
        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get root categories")

@router.get("/tree/structure", response_model=List[dict])
async def get_category_tree(
    db: Session = Depends(get_db)
):
    """
    Get complete category tree structure
    
    Returns a hierarchical tree structure of all categories.
    Useful for building category navigation menus and breadcrumbs.
    """
    try:
        category_service = CategoryService(db)
        tree = category_service.get_category_tree()
        return tree
        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get category tree")

@router.get("/search/query", response_model=List[CategoryResponse])
async def search_categories(
    query: str = Query(..., min_length=2, description="Search query for categories"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of results to return"),
    db: Session = Depends(get_db)
):
    """
    Search categories by name or description
    
    Performs a text search across category names and descriptions.
    Returns matching categories ordered by relevance.
    """
    try:
        if len(query.strip()) < 2:
            raise ValidationException("Search query must be at least 2 characters long")
        
        category_service = CategoryService(db)
        results = category_service.search_categories(query, limit)
        return results
        
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to search categories")

# =============================================================================
# HEALTH CHECK ENDPOINT
# =============================================================================

@router.get("/health/check", response_model=dict)
async def category_service_health_check():
    """
    Category service health check
    
    Check if the category management service is running properly.
    """
    return success_response(
        data={
            "service": "category-management",
            "status": "healthy",
            "endpoints": [
                "GET /api/categories",
                "GET /api/categories/{category_id}",
                "GET /api/categories/{category_id}/products",
                "GET /api/categories/{category_id}/products/paginated",
                "GET /api/categories/{category_id}/statistics",
                "GET /api/categories/{category_id}/hierarchy",
                "GET /api/categories/root/list",
                "GET /api/categories/tree/structure",
                "GET /api/categories/search/query"
            ],
            "features": [
                "Category listing with filtering and sorting",
                "Product retrieval by category",
                "Advanced product filtering (price, stock, rating, etc.)",
                "Pagination support",
                "Category hierarchy and navigation",
                "Statistics and analytics",
                "Search functionality"
            ]
        },
        message="Category service is running"
    )