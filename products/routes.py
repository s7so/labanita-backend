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
from products.schemas import (
    ProductResponse, ProductListResponse, ProductDetailResponse,
    FeaturedProductsResponse, NewArrivalsResponse, BestSellingProductsResponse,
    ProductSearchResponse, ProductFilterResponse, PaginatedProductsResponse,
    ProductStatsResponse, ProductAnalyticsResponse, RelatedProductsResponse,
    ProductFilter, ProductSearch, PaginationParams
)
from products.services import ProductService

# Create router
router = APIRouter(prefix="/api/products", tags=["Products"])

# =============================================================================
# PRODUCT RETRIEVAL ENDPOINTS
# =============================================================================

@router.get("/", response_model=ProductListResponse)
async def get_all_products(
    skip: int = Query(0, ge=0, description="Number of products to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of products to return"),
    category_id: Optional[str] = Query(None, description="Filter by category ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    is_featured: Optional[bool] = Query(None, description="Filter by featured status"),
    is_new_arrival: Optional[bool] = Query(None, description="Filter by new arrival status"),
    is_best_selling: Optional[bool] = Query(None, description="Filter by best selling status"),
    sort_by: str = Query("created_at", description="Sort field (product_name, price, created_at, rating, stock_quantity)"),
    sort_order: str = Query("desc", description="Sort order (asc/desc)"),
    db: Session = Depends(get_db)
):
    """
    Get all products with optional filtering and sorting
    
    Returns a list of all products with optional filtering by:
    - Category
    - Active status
    - Featured status
    - New arrival status
    - Best selling status
    
    Supports sorting by various fields and pagination.
    """
    try:
        product_service = ProductService(db)
        
        # Validate sort parameters
        valid_sort_fields = ["product_name", "price", "created_at", "rating", "stock_quantity", "sales_count", "review_count"]
        if sort_by not in valid_sort_fields:
            raise ValidationException(f"Invalid sort field. Must be one of: {', '.join(valid_sort_fields)}")
        
        if sort_order.lower() not in ["asc", "desc"]:
            raise ValidationException("Sort order must be 'asc' or 'desc'")
        
        products = product_service.get_all_products(
            skip=skip,
            limit=limit,
            category_id=category_id,
            is_active=is_active,
            is_featured=is_featured,
            is_new_arrival=is_new_arrival,
            is_best_selling=is_best_selling,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        return products
        
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get products")

@router.get("/{product_id}", response_model=ProductResponse)
async def get_product_by_id(
    product_id: str = Path(..., description="ID of the product to retrieve"),
    db: Session = Depends(get_db)
):
    """
    Get a specific product by ID
    
    Returns detailed information about a single product including:
    - Basic product information
    - Category information
    - Stock and pricing details
    - Product metadata
    """
    try:
        product_service = ProductService(db)
        product = product_service.get_product_by_id(product_id)
        return product
        
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get product")

@router.get("/{product_id}/detail", response_model=ProductDetailResponse)
async def get_product_detail(
    product_id: str = Path(..., description="ID of the product to get detailed information for"),
    db: Session = Depends(get_db)
):
    """
    Get detailed product information with related data
    
    Returns comprehensive product information including:
    - Product details
    - Related products
    - Category navigation path
    - Stock status and delivery estimates
    - Discount information
    """
    try:
        product_service = ProductService(db)
        product_detail = product_service.get_product_detail(product_id)
        return product_detail
        
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get product detail")

# =============================================================================
# FEATURED PRODUCTS ENDPOINTS
# =============================================================================

@router.get("/featured", response_model=FeaturedProductsResponse)
async def get_featured_products(
    limit: int = Query(20, ge=1, le=100, description="Maximum number of featured products to return"),
    category_id: Optional[str] = Query(None, description="Filter by category ID"),
    db: Session = Depends(get_db)
):
    """
    Get featured products
    
    Returns a list of featured products that are highlighted for promotion.
    Products are ordered by rating and sales performance.
    """
    try:
        product_service = ProductService(db)
        featured_products = product_service.get_featured_products(
            limit=limit,
            category_id=category_id
        )
        return featured_products
        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get featured products")

# =============================================================================
# NEW ARRIVALS ENDPOINTS
# =============================================================================

@router.get("/new-arrivals", response_model=NewArrivalsResponse)
async def get_new_arrivals(
    limit: int = Query(20, ge=1, le=100, description="Maximum number of new arrivals to return"),
    days: int = Query(30, ge=1, le=365, description="Number of days to consider for new arrivals"),
    db: Session = Depends(get_db)
):
    """
    Get new arrival products
    
    Returns products marked as new arrivals within the specified time period.
    Products are ordered by creation date (newest first).
    """
    try:
        product_service = ProductService(db)
        new_arrivals = product_service.get_new_arrivals(
            limit=limit,
            days=days
        )
        return new_arrivals
        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get new arrivals")

# =============================================================================
# BEST SELLING PRODUCTS ENDPOINTS
# =============================================================================

@router.get("/best-selling", response_model=BestSellingProductsResponse)
async def get_best_selling_products(
    limit: int = Query(20, ge=1, le=100, description="Maximum number of best selling products to return"),
    days: int = Query(90, ge=1, le=365, description="Number of days to consider for sales ranking"),
    db: Session = Depends(get_db)
):
    """
    Get best selling products
    
    Returns products marked as best sellers based on sales performance.
    Products are ordered by sales count and include sales ranking information.
    """
    try:
        product_service = ProductService(db)
        best_selling = product_service.get_best_selling_products(
            limit=limit,
            days=days
        )
        return best_selling
        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get best selling products")

# =============================================================================
# PRODUCT OFFERS ENDPOINTS
# =============================================================================

@router.get("/offers", response_model=List[dict])
async def get_products_with_offers(
    limit: int = Query(50, ge=1, le=200, description="Maximum number of products to return"),
    category_id: Optional[str] = Query(None, description="Filter by category ID"),
    db: Session = Depends(get_db)
):
    """
    Get all products that have active offers
    
    Returns products that currently have active offers:
    - Product information
    - Number of offers available
    - Best offer details
    - Useful for showcasing discounted products
    """
    try:
        # Import offer service
        from offers.services import OfferService
        
        offer_service = OfferService(db)
        products_with_offers = offer_service.get_products_with_offers()
        
        # Apply category filter if specified
        if category_id:
            products_with_offers = [
                product for product in products_with_offers
                if any(cat_id == category_id for cat_id in product.get('category_ids', []))
            ]
        
        # Apply limit
        if limit:
            products_with_offers = products_with_offers[:limit]
        
        return products_with_offers
        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get products with offers")

@router.get("/{product_id}/offers", response_model=List[dict])
async def get_product_offers(
    product_id: str = Path(..., description="ID of the product to get offers for"),
    user_id: Optional[str] = Query(None, description="User ID for usage limit checking"),
    db: Session = Depends(get_db)
):
    """
    Get all offers applicable to a specific product
    
    Returns offers that can be applied to the specified product:
    - Product-specific offers
    - Category-based offers
    - Excludes offers that exclude this product
    - Includes user-specific usage information
    """
    try:
        # Import offer service
        from offers.services import OfferService
        
        offer_service = OfferService(db)
        product_offers = offer_service.get_product_offers(
            product_id=product_id,
            user_id=user_id
        )
        
        # Convert to simple dict format for consistency
        offers_list = []
        for offer in product_offers:
            offers_list.append({
                "offer_id": offer.offer_id,
                "offer_name": offer.offer_name,
                "description": offer.description,
                "offer_type": offer.offer_type,
                "discount_type": offer.discount_type,
                "discount_value": offer.discount_value,
                "original_price": offer.original_price,
                "discounted_price": offer.discounted_price,
                "savings_amount": offer.savings_amount,
                "savings_percentage": offer.savings_percentage,
                "min_purchase_amount": offer.min_purchase_amount,
                "max_discount_amount": offer.max_discount_amount,
                "usage_limit_per_user": offer.usage_limit_per_user,
                "remaining_usage": offer.remaining_usage,
                "start_date": offer.start_date,
                "end_date": offer.end_date,
                "is_active": offer.is_active,
                "priority": offer.priority
            })
        
        return offers_list
        
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get product offers")

# =============================================================================
# PRODUCT SEARCH ENDPOINTS
# =============================================================================

@router.get("/search", response_model=ProductSearchResponse)
async def search_products(
    q: str = Query(..., min_length=2, description="Search query"),
    category_id: Optional[str] = Query(None, description="Limit search to specific category"),
    price_min: Optional[float] = Query(None, ge=0, description="Minimum price filter"),
    price_max: Optional[float] = Query(None, ge=0, description="Maximum price filter"),
    in_stock: Optional[bool] = Query(None, description="Filter by stock availability"),
    min_rating: Optional[float] = Query(None, ge=0, le=5, description="Minimum rating filter"),
    sort_by: str = Query("created_at", description="Sort field for search results"),
    sort_order: str = Query("desc", description="Sort order for search results (asc/desc)"),
    db: Session = Depends(get_db)
):
    """
    Search products by query with filters
    
    Performs a comprehensive search across product names, descriptions, and tags.
    Supports additional filtering by category, price, stock, and rating.
    """
    try:
        product_service = ProductService(db)
        
        # Validate sort parameters
        valid_sort_fields = ["product_name", "price", "created_at", "rating", "stock_quantity"]
        if sort_by not in valid_sort_fields:
            raise ValidationException(f"Invalid sort field. Must be one of: {', '.join(valid_sort_fields)}")
        
        if sort_order.lower() not in ["asc", "desc"]:
            raise ValidationException("Sort order must be 'asc' or 'desc'")
        
        # Validate price filters
        if price_min is not None and price_max is not None and price_min > price_max:
            raise ValidationException("Minimum price cannot be greater than maximum price")
        
        # Create search query object
        search_query = ProductSearch(
            query=q,
            category_id=category_id,
            price_min=price_min,
            price_max=price_max,
            in_stock=in_stock,
            min_rating=min_rating,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        search_results = product_service.search_products(search_query)
        return search_results
        
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to search products")

# =============================================================================
# PRODUCT FILTERING ENDPOINTS
# =============================================================================

@router.get("/filter", response_model=ProductFilterResponse)
async def filter_products(
    category: Optional[str] = Query(None, description="Filter by category name"),
    price_min: Optional[float] = Query(None, ge=0, description="Minimum price filter"),
    price_max: Optional[float] = Query(None, ge=0, description="Maximum price filter"),
    in_stock: Optional[bool] = Query(None, description="Filter by stock availability"),
    on_sale: Optional[bool] = Query(None, description="Filter by sale status"),
    min_rating: Optional[float] = Query(None, ge=0, le=5, description="Minimum rating filter"),
    is_featured: Optional[bool] = Query(None, description="Filter by featured status"),
    is_new_arrival: Optional[bool] = Query(None, description="Filter by new arrival status"),
    is_best_selling: Optional[bool] = Query(None, description="Filter by best selling status"),
    tags: Optional[str] = Query(None, description="Comma-separated list of tags to filter by"),
    allergens: Optional[str] = Query(None, description="Comma-separated list of allergens to filter by"),
    weight_min: Optional[float] = Query(None, ge=0, description="Minimum weight filter"),
    weight_max: Optional[float] = Query(None, ge=0, description="Maximum weight filter"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    db: Session = Depends(get_db)
):
    """
    Filter products based on multiple criteria
    
    Advanced product filtering with support for:
    - Category and pricing
    - Stock availability and sale status
    - Ratings and special flags
    - Tags and allergens
    - Weight and dimensions
    - Pagination
    """
    try:
        product_service = ProductService(db)
        
        # Validate pagination parameters
        if page < 1:
            raise ValidationException("Page number must be greater than 0")
        
        if size < 1 or size > 100:
            raise ValidationException("Page size must be between 1 and 100")
        
        # Validate price filters
        if price_min is not None and price_max is not None and price_min > price_max:
            raise ValidationException("Minimum price cannot be greater than maximum price")
        
        # Validate weight filters
        if weight_min is not None and weight_max is not None and weight_min > weight_max:
            raise ValidationException("Minimum weight cannot be greater than maximum weight")
        
        # Parse comma-separated values
        tag_list = [tag.strip() for tag in tags.split(",")] if tags else None
        allergen_list = [allergen.strip() for allergen in allergens.split(",")] if allergens else None
        
        # Create filter object
        filters = ProductFilter(
            category_name=category,
            price_min=price_min,
            price_max=price_max,
            in_stock=in_stock,
            on_sale=on_sale,
            min_rating=min_rating,
            is_featured=is_featured,
            is_new_arrival=is_new_arrival,
            is_best_selling=is_best_selling,
            tags=tag_list,
            allergens=allergen_list,
            weight_min=weight_min,
            weight_max=weight_max
        )
        
        # Create pagination object
        pagination = PaginationParams(page=page, size=size)
        
        filtered_products = product_service.filter_products(filters, pagination)
        return filtered_products
        
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to filter products")

# =============================================================================
# PAGINATED PRODUCTS ENDPOINTS
# =============================================================================

@router.get("/paginated", response_model=PaginatedProductsResponse)
async def get_products_paginated(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    category_id: Optional[str] = Query(None, description="Filter by category ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    sort_by: str = Query("created_at", description="Sort field for products"),
    sort_order: str = Query("desc", description="Sort order for products (asc/desc)"),
    db: Session = Depends(get_db)
):
    """
    Get paginated products with optional filtering
    
    Returns paginated products with comprehensive pagination metadata.
    This endpoint is optimized for large product catalogs.
    """
    try:
        product_service = ProductService(db)
        
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
        
        # Create pagination object
        pagination = PaginationParams(page=page, size=size)
        
        paginated_products = product_service.get_products_paginated(
            pagination=pagination,
            category_id=category_id,
            is_active=is_active,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        return paginated_products
        
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get paginated products")

# =============================================================================
# PRODUCT STATISTICS ENDPOINTS
# =============================================================================

@router.get("/{product_id}/statistics", response_model=ProductStatsResponse)
async def get_product_statistics(
    product_id: str = Path(..., description="ID of the product to get statistics for"),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive statistics for a product
    
    Returns detailed product statistics including:
    - Sales performance
    - Conversion rates
    - Stock turnover
    - Profit margins
    - Sales trends
    """
    try:
        product_service = ProductService(db)
        stats = product_service.get_product_statistics(product_id)
        return stats
        
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get product statistics")

@router.get("/analytics/overview", response_model=ProductAnalyticsResponse)
async def get_product_analytics(
    db: Session = Depends(get_db)
):
    """
    Get overall product analytics
    
    Returns comprehensive analytics for all products including:
    - Product counts and statuses
    - Stock value and pricing
    - Category performance
    - Sales trends
    """
    try:
        product_service = ProductService(db)
        analytics = product_service.get_product_analytics()
        return analytics
        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get product analytics")

# =============================================================================
# RELATED PRODUCTS ENDPOINTS
# =============================================================================

@router.get("/{product_id}/related", response_model=RelatedProductsResponse)
async def get_related_products(
    product_id: str = Path(..., description="ID of the product to get related products for"),
    limit: int = Query(6, ge=1, le=20, description="Maximum number of related products to return"),
    db: Session = Depends(get_db)
):
    """
    Get related products for a specific product
    
    Returns products that are related based on:
    - Same category
    - Similar tags
    - Complementary products
    
    Useful for cross-selling and product discovery.
    """
    try:
        product_service = ProductService(db)
        related_products = product_service.get_related_products(product_id, limit)
        return related_products
        
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get related products")

# =============================================================================
# UTILITY ENDPOINTS
# =============================================================================

@router.get("/categories/{category_id}/products", response_model=List[ProductResponse])
async def get_products_by_category(
    category_id: str = Path(..., description="ID of the category to get products for"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of products to return"),
    db: Session = Depends(get_db)
):
    """
    Get products by category ID
    
    Returns all products in a specific category.
    Useful for category browsing and navigation.
    """
    try:
        product_service = ProductService(db)
        products = product_service.get_all_products(
            limit=limit,
            category_id=category_id,
            is_active=True
        )
        return products.products
        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get products by category")

@router.get("/tags/{tag}/list", response_model=List[ProductResponse])
async def get_products_by_tag(
    tag: str = Path(..., description="Tag to filter products by"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of products to return"),
    db: Session = Depends(get_db)
):
    """
    Get products by tag
    
    Returns all products that have a specific tag.
    Useful for tag-based browsing and discovery.
    """
    try:
        # This would need to be implemented in the service
        # For now, we'll use the filter endpoint
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Tag-based filtering will be implemented in a future version"
        )
        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get products by tag")

# =============================================================================
# HEALTH CHECK ENDPOINT
# =============================================================================

@router.get("/health/check", response_model=dict)
async def product_service_health_check():
    """
    Product service health check
    
    Check if the product management service is running properly.
    """
    return success_response(
        data={
            "service": "product-management",
            "status": "healthy",
            "endpoints": [
                "GET /api/products",
                "GET /api/products/{product_id}",
                "GET /api/products/{product_id}/detail",
                "GET /api/products/featured",
                "GET /api/products/new-arrivals",
                "GET /api/products/best-selling",
                "GET /api/products/offers",
                "GET /api/products/{product_id}/offers",
                "GET /api/products/search",
                "GET /api/products/filter",
                "GET /api/products/paginated",
                "GET /api/products/{product_id}/statistics",
                "GET /api/products/analytics/overview",
                "GET /api/products/{product_id}/related",
                "GET /api/products/categories/{category_id}/products"
            ],
            "features": [
                "Product listing with filtering and sorting",
                "Featured, new arrivals, and best selling products",
                "Product offers and discounts",
                "Advanced search functionality",
                "Comprehensive filtering options",
                "Pagination support",
                "Product statistics and analytics",
                "Related products discovery",
                "Category-based product browsing"
            ]
        },
        message="Product service is running"
    )