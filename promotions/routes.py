from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, Body
from sqlalchemy.orm import Session

from database import get_db
from core.responses import success_response, error_response
from core.exceptions import (
    NotFoundException, 
    ValidationException, 
    ConflictException
)
from promotions.schemas import (
    ActivePromotionsResponse, PromotionValidationResponse,
    PromotionApplicationResponse, PromotionRemovalResponse,
    PromotionValidationRequest, PromotionApplicationRequest,
    PromotionRemovalRequest
)
from promotions.services import PromotionService

# Create router
router = APIRouter(prefix="/api/promotions", tags=["Promotions"])

# =============================================================================
# PROMOTION RETRIEVAL ENDPOINTS
# =============================================================================

@router.get("/active", response_model=ActivePromotionsResponse)
async def get_active_promotions(
    user_id: Optional[str] = Query(None, description="User ID to get user-specific promotions"),
    category_id: Optional[str] = Query(None, description="Filter by category ID"),
    promotion_type: Optional[str] = Query(None, description="Filter by promotion type"),
    db: Session = Depends(get_db)
):
    """
    Get all currently active promotions
    
    Returns promotions that are currently active and valid:
    - Currently running promotions
    - Within valid date range
    - Active status
    
    Can be filtered by category and promotion type.
    If user_id is provided, returns user-specific promotions.
    """
    try:
        promotion_service = PromotionService(db)
        active_promotions = promotion_service.get_active_promotions(
            user_id=user_id,
            category_id=category_id,
            promotion_type=promotion_type
        )
        return active_promotions
        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get active promotions")

# =============================================================================
# PROMOTION VALIDATION ENDPOINTS
# =============================================================================

@router.post("/validate", response_model=PromotionValidationResponse)
async def validate_promotion(
    request: PromotionValidationRequest = Body(...),
    db: Session = Depends(get_db)
):
    """
    Validate if a promotion can be applied
    
    Validates promotion applicability based on:
    - Promotion status and dates
    - User eligibility
    - Cart contents and total
    - Usage limits
    - Product/category restrictions
    
    Returns detailed validation results including:
    - Whether promotion is valid
    - Calculated discount amounts
    - Any validation errors
    - Terms and conditions
    - Recommendations
    """
    try:
        promotion_service = PromotionService(db)
        
        # Validate request parameters
        if not request.product_ids and not request.category_ids:
            raise ValidationException("At least one product or category must be specified")
        
        if request.cart_total < 0:
            raise ValidationException("Cart total cannot be negative")
        
        if not request.user_id:
            raise ValidationException("User ID is required")
        
        # If promotion_code is provided, get promotion by code
        if request.promotion_code:
            promotion = promotion_service.get_promotion_by_code(request.promotion_code)
            promotion_id = promotion.promotion_id
        else:
            raise ValidationException("Promotion ID or code is required")
        
        validation_result = promotion_service.validate_promotion(
            promotion_id=promotion_id,
            product_ids=request.product_ids,
            category_ids=request.category_ids,
            cart_total=request.cart_total,
            user_id=request.user_id,
            user_groups=request.user_groups or [],
            purchase_history=request.purchase_history or {}
        )
        
        return validation_result
        
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to validate promotion")

# =============================================================================
# PROMOTION APPLICATION ENDPOINTS
# =============================================================================

@router.post("/apply", response_model=PromotionApplicationResponse)
async def apply_promotion(
    request: PromotionApplicationRequest = Body(...),
    db: Session = Depends(get_db)
):
    """
    Apply a promotion to cart items
    
    Applies a validated promotion to the specified cart:
    - Validates promotion can be applied
    - Applies discounts to eligible items
    - Updates promotion usage counts
    - Returns detailed application results
    
    The system will:
    - Verify promotion exists and is valid
    - Check user eligibility and usage limits
    - Apply discounts to applicable cart items
    - Update promotion usage statistics
    - Return updated cart totals and savings
    """
    try:
        promotion_service = PromotionService(db)
        
        # Validate request parameters
        if not request.promotion_id:
            raise ValidationException("Promotion ID is required")
        
        if not request.user_id:
            raise ValidationException("User ID is required")
        
        if not request.cart_items:
            raise ValidationException("Cart items are required")
        
        if request.cart_total < 0:
            raise ValidationException("Cart total cannot be negative")
        
        # Apply promotion
        application_result = promotion_service.apply_promotion(
            promotion_id=request.promotion_id,
            user_id=request.user_id,
            cart_items=request.cart_items,
            cart_total=request.cart_total,
            session_id=request.session_id
        )
        
        return application_result
        
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to apply promotion")

# =============================================================================
# PROMOTION REMOVAL ENDPOINTS
# =============================================================================

@router.delete("/remove", response_model=PromotionRemovalResponse)
async def remove_promotion(
    request: PromotionRemovalRequest = Body(...),
    db: Session = Depends(get_db)
):
    """
    Remove a promotion from cart items
    
    Removes a previously applied promotion from the cart:
    - Removes discounts from affected items
    - Recalculates cart totals
    - Returns removal confirmation
    
    The system will:
    - Verify promotion exists
    - Remove applied discounts from cart items
    - Recalculate cart totals
    - Return updated cart information
    """
    try:
        promotion_service = PromotionService(db)
        
        # Validate request parameters
        if not request.promotion_id:
            raise ValidationException("Promotion ID is required")
        
        if not request.user_id:
            raise ValidationException("User ID is required")
        
        if not request.cart_items:
            raise ValidationException("Cart items are required")
        
        # Remove promotion
        removal_result = promotion_service.remove_promotion(
            promotion_id=request.promotion_id,
            user_id=request.user_id,
            cart_items=request.cart_items,
            reason=request.reason
        )
        
        return removal_result
        
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to remove promotion")

# =============================================================================
# PROMOTION MANAGEMENT ENDPOINTS
# =============================================================================

@router.get("/{promotion_id}", response_model=dict)
async def get_promotion_by_id(
    promotion_id: str = Path(..., description="ID of the promotion to retrieve"),
    db: Session = Depends(get_db)
):
    """
    Get a specific promotion by ID
    
    Returns detailed information about a single promotion including:
    - Basic promotion information
    - Applicable products and categories
    - Usage limits and dates
    - Promotion status and priority
    """
    try:
        promotion_service = PromotionService(db)
        promotion = promotion_service.get_promotion_by_id(promotion_id)
        return promotion
        
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get promotion")

@router.get("/code/{promotion_code}", response_model=dict)
async def get_promotion_by_code(
    promotion_code: str = Path(..., description="Code of the promotion to retrieve"),
    db: Session = Depends(get_db)
):
    """
    Get a promotion by its code
    
    Returns promotion information using the promotion code:
    - Useful for code-based promotion lookup
    - Returns same information as ID-based lookup
    """
    try:
        promotion_service = PromotionService(db)
        promotion = promotion_service.get_promotion_by_code(promotion_code)
        return promotion
        
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get promotion by code")

# =============================================================================
# USER PROMOTIONS ENDPOINTS
# =============================================================================

@router.get("/user/{user_id}/available", response_model=dict)
async def get_user_available_promotions(
    user_id: str = Path(..., description="User ID to get promotions for"),
    db: Session = Depends(get_db)
):
    """
    Get all promotions available to a specific user
    
    Returns promotions that the user is eligible for:
    - User-specific eligibility checks
    - Usage limit information
    - Estimated savings
    - Expired promotions history
    
    The system will:
    - Check user eligibility for each promotion
    - Calculate remaining usage limits
    - Estimate potential savings
    - Include promotion history
    """
    try:
        promotion_service = PromotionService(db)
        user_promotions = promotion_service.get_user_promotions(user_id)
        return user_promotions
        
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get user promotions")

# =============================================================================
# PROMOTION ANALYTICS ENDPOINTS
# =============================================================================

@router.get("/analytics/overview", response_model=dict)
async def get_promotion_analytics(
    db: Session = Depends(get_db)
):
    """
    Get overall promotion analytics
    
    Returns comprehensive analytics for all promotions including:
    - Promotion counts and statuses
    - Performance metrics
    - Top performing promotions
    - Category performance
    - Revenue impact analysis
    """
    try:
        promotion_service = PromotionService(db)
        analytics = promotion_service.get_promotion_analytics()
        return analytics
        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get promotion analytics")

# =============================================================================
# PROMOTION UTILITY ENDPOINTS
# =============================================================================

@router.get("/types/available", response_model=List[str])
async def get_available_promotion_types():
    """
    Get available promotion types
    
    Returns list of all available promotion types:
    - Percentage discounts
    - Fixed amount discounts
    - Buy one get one
    - Free shipping
    - Bundle discounts
    - Cashback offers
    - Loyalty points
    - First time purchase
    - Birthday offers
    - Seasonal sales
    - Flash sales
    """
    return [
        "percentage_discount",
        "fixed_amount_discount",
        "buy_one_get_one",
        "buy_x_get_y",
        "free_shipping",
        "bundle_discount",
        "cashback",
        "loyalty_points",
        "first_time_purchase",
        "birthday_offer",
        "seasonal_sale",
        "flash_sale"
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
    - Cashback
    - Points
    """
    return [
        "percentage",
        "fixed_amount",
        "free_item",
        "free_shipping",
        "cashback",
        "points"
    ]

@router.get("/trigger-types/available", response_model=List[str])
async def get_available_trigger_types():
    """
    Get available promotion trigger types
    
    Returns list of all available trigger types:
    - Manual
    - Automatic
    - Scheduled
    - Event-based
    - User action
    - System generated
    """
    return [
        "manual",
        "automatic",
        "scheduled",
        "event_based",
        "user_action",
        "system_generated"
    ]

# =============================================================================
# PROMOTION VALIDATION UTILITIES
# =============================================================================

@router.post("/validate/cart", response_model=dict)
async def validate_cart_for_promotions(
    product_ids: List[str] = Query(..., description="Product IDs in cart"),
    category_ids: List[str] = Query(..., description="Category IDs in cart"),
    cart_total: float = Query(..., ge=0, description="Cart total amount"),
    user_id: str = Query(..., description="User ID for validation"),
    db: Session = Depends(get_db)
):
    """
    Validate cart contents for available promotions
    
    Checks which promotions can be applied to the current cart:
    - Returns list of applicable promotions
    - Shows potential savings
    - Indicates eligibility requirements
    - Provides recommendations
    
    Useful for showing users available promotions before checkout.
    """
    try:
        promotion_service = PromotionService(db)
        
        # Get all active promotions
        active_promotions = promotion_service.get_active_promotions(user_id=user_id)
        
        applicable_promotions = []
        total_potential_savings = 0.0
        
        for promotion in active_promotions.promotions:
            # Validate each promotion
            validation_result = promotion_service.validate_promotion(
                promotion_id=promotion.promotion_id,
                product_ids=product_ids,
                category_ids=category_ids,
                cart_total=cart_total,
                user_id=user_id
            )
            
            if validation_result.is_valid:
                applicable_promotions.append({
                    "promotion": promotion,
                    "discount_amount": validation_result.discount_amount,
                    "discount_percentage": validation_result.discount_percentage,
                    "final_price": validation_result.final_price,
                    "savings_amount": validation_result.savings_amount,
                    "terms_and_conditions": validation_result.terms_and_conditions
                })
                total_potential_savings += validation_result.savings_amount
        
        return {
            "applicable_promotions": applicable_promotions,
            "total_potential_savings": total_potential_savings,
            "cart_total": cart_total,
            "user_id": user_id,
            "recommendations": [
                "Apply highest discount promotion first",
                "Check for bundle discounts if buying multiple items",
                "Consider free shipping promotions for large orders"
            ]
        }
        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to validate cart for promotions")

# =============================================================================
# HEALTH CHECK ENDPOINT
# =============================================================================

@router.get("/health/check", response_model=dict)
async def promotion_service_health_check():
    """
    Promotion service health check
    
    Check if the promotion management service is running properly.
    """
    return success_response(
        data={
            "service": "promotion-management",
            "status": "healthy",
            "endpoints": [
                "GET /api/promotions/active",
                "POST /api/promotions/validate",
                "POST /api/promotions/apply",
                "DELETE /api/promotions/remove",
                "GET /api/promotions/{promotion_id}",
                "GET /api/promotions/code/{promotion_code}",
                "GET /api/promotions/user/{user_id}/available",
                "GET /api/promotions/analytics/overview",
                "GET /api/promotions/types/available",
                "GET /api/promotions/discount-types/available",
                "GET /api/promotions/trigger-types/available",
                "POST /api/promotions/validate/cart"
            ],
            "features": [
                "Active promotions management",
                "Promotion validation and eligibility",
                "Promotion application and removal",
                "User-specific promotion access",
                "Comprehensive promotion analytics",
                "Cart validation for promotions",
                "Multiple promotion types support",
                "Advanced eligibility rules",
                "Usage limit management",
                "Real-time validation"
            ]
        },
        message="Promotion service is running"
    )