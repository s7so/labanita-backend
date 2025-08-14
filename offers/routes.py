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
from offers.schemas import (
    OfferResponse, ProductOfferResponse, ActiveOffersResponse,
    OfferListResponse, OfferDetailResponse, PaginatedOffersResponse,
    OfferStatsResponse, OfferAnalyticsResponse, OfferValidationResponse,
    OfferCreateRequest, OfferUpdateRequest, OfferFilter, PaginationParams
)
from offers.services import OfferService

# Create router
router = APIRouter(prefix="/api/offers", tags=["Offers"])

# =============================================================================
# OFFER RETRIEVAL ENDPOINTS
# =============================================================================

@router.get("/", response_model=OfferListResponse)
async def get_all_offers(
    skip: int = Query(0, ge=0, description="Number of offers to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of offers to return"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    offer_type: Optional[str] = Query(None, description="Filter by offer type"),
    discount_type: Optional[str] = Query(None, description="Filter by discount type"),
    sort_by: str = Query("priority", description="Sort field (priority, created_at, discount_value)"),
    sort_order: str = Query("desc", description="Sort order (asc/desc)"),
    db: Session = Depends(get_db)
):
    """
    Get all offers with optional filtering and sorting
    
    Returns a list of all offers with optional filtering by:
    - Active status
    - Offer type
    - Discount type
    
    Supports sorting by various fields and pagination.
    """
    try:
        offer_service = OfferService(db)
        
        # Validate sort parameters
        valid_sort_fields = ["priority", "created_at", "discount_value", "start_date", "end_date"]
        if sort_by not in valid_sort_fields:
            raise ValidationException(f"Invalid sort field. Must be one of: {', '.join(valid_sort_fields)}")
        
        if sort_order.lower() not in ["asc", "desc"]:
            raise ValidationException("Sort order must be 'asc' or 'desc'")
        
        offers = offer_service.get_all_offers(
            skip=skip,
            limit=limit,
            is_active=is_active,
            offer_type=offer_type,
            discount_type=discount_type,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        return offers
        
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get offers")

@router.get("/{offer_id}", response_model=OfferResponse)
async def get_offer_by_id(
    offer_id: str = Path(..., description="ID of the offer to retrieve"),
    db: Session = Depends(get_db)
):
    """
    Get a specific offer by ID
    
    Returns detailed information about a single offer including:
    - Basic offer information
    - Applicable products and categories
    - Usage limits and dates
    - Offer status and priority
    """
    try:
        offer_service = OfferService(db)
        offer = offer_service.get_offer_by_id(offer_id)
        return offer
        
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get offer")

@router.get("/{offer_id}/detail", response_model=OfferDetailResponse)
async def get_offer_detail(
    offer_id: str = Path(..., description="ID of the offer to get detailed information for"),
    db: Session = Depends(get_db)
):
    """
    Get detailed offer information with related data
    
    Returns comprehensive offer information including:
    - Offer details
    - Applicable products details
    - Usage statistics
    - Performance metrics
    - Related offers
    """
    try:
        offer_service = OfferService(db)
        offer_detail = offer_service.get_offer_detail(offer_id)
        return offer_detail
        
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get offer detail")

# =============================================================================
# ACTIVE OFFERS ENDPOINTS
# =============================================================================

@router.get("/active", response_model=ActiveOffersResponse)
async def get_active_offers(
    category_id: Optional[str] = Query(None, description="Filter by category ID"),
    offer_type: Optional[str] = Query(None, description="Filter by offer type"),
    db: Session = Depends(get_db)
):
    """
    Get all currently active offers
    
    Returns offers that are currently active and valid:
    - Currently running offers
    - Within valid date range
    - Active status
    
    Can be filtered by category and offer type.
    """
    try:
        offer_service = OfferService(db)
        active_offers = offer_service.get_active_offers(
            category_id=category_id,
            offer_type=offer_type
        )
        return active_offers
        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get active offers")

# =============================================================================
# PRODUCT OFFERS ENDPOINTS
# =============================================================================

@router.get("/products/{product_id}/offers", response_model=List[ProductOfferResponse])
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
        offer_service = OfferService(db)
        product_offers = offer_service.get_product_offers(
            product_id=product_id,
            user_id=user_id
        )
        return product_offers
        
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get product offers")

@router.get("/products/with-offers", response_model=List[dict])
async def get_products_with_offers(
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
        offer_service = OfferService(db)
        products_with_offers = offer_service.get_products_with_offers()
        return products_with_offers
        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get products with offers")

# =============================================================================
# OFFER VALIDATION ENDPOINTS
# =============================================================================

@router.post("/validate", response_model=OfferValidationResponse)
async def validate_offers(
    product_ids: List[str] = Query(..., description="List of product IDs in cart"),
    category_ids: List[str] = Query(..., description="List of category IDs in cart"),
    cart_total: float = Query(..., ge=0, description="Total cart amount"),
    user_id: Optional[str] = Query(None, description="User ID for usage limit checking"),
    db: Session = Depends(get_db)
):
    """
    Validate which offers can be applied to a cart
    
    Validates offers against cart contents:
    - Checks offer applicability
    - Validates usage limits
    - Provides recommendations
    - Returns best offer suggestion
    
    Useful for cart validation and offer application.
    """
    try:
        offer_service = OfferService(db)
        
        # Validate input parameters
        if not product_ids and not category_ids:
            raise ValidationException("At least one product or category must be specified")
        
        if cart_total < 0:
            raise ValidationException("Cart total cannot be negative")
        
        validation_result = offer_service.validate_offers(
            product_ids=product_ids,
            category_ids=category_ids,
            cart_total=cart_total,
            user_id=user_id
        )
        
        return validation_result
        
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to validate offers")

# =============================================================================
# OFFER STATISTICS ENDPOINTS
# =============================================================================

@router.get("/{offer_id}/statistics", response_model=OfferStatsResponse)
async def get_offer_statistics(
    offer_id: str = Path(..., description="ID of the offer to get statistics for"),
    db: Session = Depends(get_db)
):
    """
    Get comprehensive statistics for an offer
    
    Returns detailed offer performance metrics:
    - Usage statistics
    - Revenue impact
    - Conversion rates
    - Performance score
    - User engagement data
    """
    try:
        offer_service = OfferService(db)
        stats = offer_service.get_offer_statistics(offer_id)
        return stats
        
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get offer statistics")

@router.get("/analytics/overview", response_model=OfferAnalyticsResponse)
async def get_offer_analytics(
    db: Session = Depends(get_db)
):
    """
    Get overall offer analytics
    
    Returns comprehensive analytics for all offers:
    - Offer counts and statuses
    - Performance metrics
    - Top performing offers
    - Category performance
    - Revenue impact analysis
    """
    try:
        offer_service = OfferService(db)
        analytics = offer_service.get_offer_analytics()
        return analytics
        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get offer analytics")

# =============================================================================
# PAGINATED OFFERS ENDPOINTS
# =============================================================================

@router.get("/paginated", response_model=PaginatedOffersResponse)
async def get_offers_paginated(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    offer_type: Optional[str] = Query(None, description="Filter by offer type"),
    discount_type: Optional[str] = Query(None, description="Filter by discount type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    status: Optional[str] = Query(None, description="Filter by offer status"),
    min_discount_value: Optional[float] = Query(None, ge=0, description="Minimum discount value"),
    max_discount_value: Optional[float] = Query(None, ge=0, description="Maximum discount value"),
    category_id: Optional[str] = Query(None, description="Filter by category"),
    product_id: Optional[str] = Query(None, description="Filter by product"),
    search: Optional[str] = Query(None, description="Search in offer name and description"),
    sort_by: str = Query("priority", description="Sort field for offers"),
    sort_order: str = Query("desc", description="Sort order for offers (asc/desc)"),
    db: Session = Depends(get_db)
):
    """
    Get paginated offers with optional filtering
    
    Returns paginated offers with comprehensive filtering:
    - Advanced filtering options
    - Search functionality
    - Sorting and pagination
    - Optimized for large offer catalogs
    """
    try:
        offer_service = OfferService(db)
        
        # Validate pagination parameters
        if page < 1:
            raise ValidationException("Page number must be greater than 0")
        
        if size < 1 or size > 100:
            raise ValidationException("Page size must be between 1 and 100")
        
        # Validate discount value filters
        if min_discount_value is not None and max_discount_value is not None:
            if min_discount_value > max_discount_value:
                raise ValidationException("Minimum discount value cannot be greater than maximum discount value")
        
        # Create filter object
        filters = OfferFilter(
            offer_type=offer_type,
            discount_type=discount_type,
            is_active=is_active,
            status=status,
            min_discount_value=min_discount_value,
            max_discount_value=max_discount_value,
            category_id=category_id,
            product_id=product_id,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        # Create pagination object
        pagination = PaginationParams(page=page, size=size)
        
        paginated_offers = offer_service.get_offers_paginated(pagination, filters)
        return paginated_offers
        
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get paginated offers")

# =============================================================================
# OFFER MANAGEMENT ENDPOINTS (ADMIN)
# =============================================================================

@router.post("/", response_model=OfferResponse)
async def create_offer(
    request: OfferCreateRequest,
    db: Session = Depends(get_db)
):
    """
    Create a new offer (Admin only)
    
    Creates a new promotional offer with:
    - Offer details and configuration
    - Applicable products and categories
    - Usage limits and date ranges
    - Priority and status settings
    """
    try:
        # This would typically require admin authentication
        # For now, we'll allow creation without auth check
        
        offer_service = OfferService(db)
        
        # Convert request to internal format
        offer_data = OfferCreate(
            offer_name=request.offer_name,
            description=request.description,
            offer_type=request.offer_type,
            discount_type=request.discount_type,
            discount_value=request.discount_value,
            min_purchase_amount=request.min_purchase_amount,
            max_discount_amount=request.max_discount_amount,
            buy_quantity=request.buy_quantity,
            get_quantity=request.get_quantity,
            applicable_products=request.applicable_products,
            applicable_categories=request.applicable_categories,
            excluded_products=request.excluded_products,
            excluded_categories=request.excluded_categories,
            usage_limit_per_user=request.usage_limit_per_user,
            total_usage_limit=request.total_usage_limit,
            start_date=request.start_date,
            end_date=request.end_date,
            priority=request.priority
        )
        
        # Create offer (this would need to be implemented in the service)
        # For now, return a placeholder response
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Offer creation will be implemented in a future version"
        )
        
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create offer")

@router.put("/{offer_id}", response_model=OfferResponse)
async def update_offer(
    offer_id: str = Path(..., description="ID of the offer to update"),
    request: OfferUpdateRequest,
    db: Session = Depends(get_db)
):
    """
    Update an existing offer (Admin only)
    
    Updates offer configuration and settings:
    - Modify offer details
    - Update applicable products/categories
    - Adjust usage limits and dates
    - Change priority and status
    """
    try:
        # This would typically require admin authentication
        # For now, we'll allow updates without auth check
        
        offer_service = OfferService(db)
        
        # Verify offer exists
        existing_offer = offer_service.get_offer_by_id(offer_id)
        
        # Update offer (this would need to be implemented in the service)
        # For now, return a placeholder response
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Offer updates will be implemented in a future version"
        )
        
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update offer")

@router.delete("/{offer_id}", response_model=dict)
async def delete_offer(
    offer_id: str = Path(..., description="ID of the offer to delete"),
    db: Session = Depends(get_db)
):
    """
    Delete an offer (Admin only)
    
    Soft deletes an offer:
    - Sets offer as inactive
    - Preserves historical data
    - Can be reactivated if needed
    """
    try:
        # This would typically require admin authentication
        # For now, we'll allow deletion without auth check
        
        offer_service = OfferService(db)
        
        # Verify offer exists
        existing_offer = offer_service.get_offer_by_id(offer_id)
        
        # Delete offer (this would need to be implemented in the service)
        # For now, return a placeholder response
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Offer deletion will be implemented in a future version"
        )
        
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete offer")

# =============================================================================
# UTILITY ENDPOINTS
# =============================================================================

@router.get("/types/available", response_model=List[str])
async def get_available_offer_types():
    """
    Get available offer types
    
    Returns list of all available offer types:
    - Percentage discounts
    - Fixed amount discounts
    - Buy one get one
    - Free shipping
    - Bundle discounts
    """
    return [
        "percentage_discount",
        "fixed_amount_discount",
        "buy_one_get_one",
        "buy_x_get_y",
        "free_shipping",
        "bundle_discount"
    ]

@router.get("/discount-types/available", response_model=List[str])
async def get_available_discount_types():
    """
    Get available discount types
    
    Returns list of all available discount types:
    - Percentage
    - Fixed amount
    - Free item
    - Free shipping
    """
    return [
        "percentage",
        "fixed_amount",
        "free_item",
        "free_shipping"
    ]

# =============================================================================
# HEALTH CHECK ENDPOINT
# =============================================================================

@router.get("/health/check", response_model=dict)
async def offer_service_health_check():
    """
    Offer service health check
    
    Check if the offer management service is running properly.
    """
    return success_response(
        data={
            "service": "offer-management",
            "status": "healthy",
            "endpoints": [
                "GET /api/offers",
                "GET /api/offers/{offer_id}",
                "GET /api/offers/{offer_id}/detail",
                "GET /api/offers/active",
                "GET /api/products/{product_id}/offers",
                "GET /api/products/with-offers",
                "POST /api/offers/validate",
                "GET /api/offers/{offer_id}/statistics",
                "GET /api/offers/analytics/overview",
                "GET /api/offers/paginated",
                "POST /api/offers",
                "PUT /api/offers/{offer_id}",
                "DELETE /api/offers/{offer_id}"
            ],
            "features": [
                "Offer listing with filtering and sorting",
                "Active offers management",
                "Product-specific offers",
                "Offer validation for carts",
                "Comprehensive offer statistics",
                "Offer analytics and performance",
                "Advanced filtering and pagination",
                "Admin offer management (future)"
            ]
        },
        message="Offer service is running"
    )