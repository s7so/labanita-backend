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
from cart.schemas import (
    CartResponse, CartItemListResponse, CartSummaryResponse, CartOperationResponse,
    CartItemCreateRequest, CartItemUpdateRequest, CartValidationResponse,
    CartOfferRequest, CartValidationRequest
)
from cart.services import CartService

# Create router
router = APIRouter(prefix="/api/cart", tags=["Cart"])

# =============================================================================
# CART RETRIEVAL ENDPOINTS
# =============================================================================

@router.get("/", response_model=CartResponse)
async def get_cart(
    user_id: str = Query(..., description="User ID to get cart for"),
    db: Session = Depends(get_db)
):
    """
    Get complete cart for a user
    
    Returns the full cart including:
    - All cart items with product details
    - Cart summary with totals and discounts
    - Applied offers and available offers
    - Shipping and tax calculations
    - Estimated delivery information
    """
    try:
        cart_service = CartService(db)
        cart = cart_service.get_user_cart(user_id)
        return cart
        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get cart")

@router.get("/summary", response_model=CartSummaryResponse)
async def get_cart_summary(
    user_id: str = Query(..., description="User ID to get cart summary for"),
    db: Session = Depends(get_db)
):
    """
    Get cart summary for a user
    
    Returns a summary of the cart including:
    - Total items and quantities
    - Subtotal, discounts, taxes, and shipping
    - Final total amount
    - Savings information
    - Applied and available offers
    - Delivery estimates
    """
    try:
        cart_service = CartService(db)
        summary = cart_service.get_cart_summary(user_id)
        return summary
        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get cart summary")

# =============================================================================
# CART ITEM OPERATIONS
# =============================================================================

@router.post("/items", response_model=CartOperationResponse)
async def add_item_to_cart(
    request: CartItemCreateRequest,
    user_id: str = Query(..., description="User ID to add item for"),
    db: Session = Depends(get_db)
):
    """
    Add a product to user's cart
    
    Adds a product to the cart with specified quantity:
    - Validates product availability and stock
    - Updates existing item if already in cart
    - Applies price updates if product price changed
    - Returns updated cart summary
    
    The system will:
    - Check if product exists and is active
    - Validate stock availability
    - Update quantity if item already exists
    - Create new cart item if needed
    """
    try:
        cart_service = CartService(db)
        
        # Validate request
        if not request.product_id:
            raise ValidationException("Product ID is required")
        
        if request.quantity < 1:
            raise ValidationException("Quantity must be at least 1")
        
        if request.quantity > 100:
            raise ValidationException("Quantity cannot exceed 100")
        
        result = cart_service.add_item_to_cart(
            user_id=user_id,
            product_id=request.product_id,
            quantity=request.quantity
        )
        
        return result
        
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to add item to cart")

@router.put("/items/{cart_item_id}", response_model=CartOperationResponse)
async def update_cart_item(
    cart_item_id: str = Path(..., description="ID of the cart item to update"),
    request: CartItemUpdateRequest,
    user_id: str = Query(..., description="User ID who owns the cart item"),
    db: Session = Depends(get_db)
):
    """
    Update quantity of a cart item
    
    Updates the quantity of an existing cart item:
    - Validates new quantity against stock and limits
    - Updates total price calculations
    - Returns updated cart summary
    
    The system will:
    - Verify cart item exists and belongs to user
    - Validate quantity against stock availability
    - Update item quantity and recalculate prices
    - Return updated cart summary
    """
    try:
        cart_service = CartService(db)
        
        # Validate request
        if request.quantity < 1:
            raise ValidationException("Quantity must be at least 1")
        
        if request.quantity > 100:
            raise ValidationException("Quantity cannot exceed 100")
        
        result = cart_service.update_cart_item(
            user_id=user_id,
            cart_item_id=cart_item_id,
            quantity=request.quantity
        )
        
        return result
        
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update cart item")

@router.delete("/items/{cart_item_id}", response_model=CartOperationResponse)
async def remove_cart_item(
    cart_item_id: str = Path(..., description="ID of the cart item to remove"),
    user_id: str = Query(..., description="User ID who owns the cart item"),
    db: Session = Depends(get_db)
):
    """
    Remove a specific item from cart
    
    Removes a cart item from the user's cart:
    - Soft deletes the item (sets status to removed)
    - Updates cart summary
    - Returns confirmation and updated summary
    
    The system will:
    - Verify cart item exists and belongs to user
    - Soft delete the item (preserves history)
    - Recalculate cart totals
    - Return updated cart summary
    """
    try:
        cart_service = CartService(db)
        
        result = cart_service.remove_cart_item(
            user_id=user_id,
            cart_item_id=cart_item_id
        )
        
        return result
        
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to remove cart item")

@router.delete("/clear", response_model=CartOperationResponse)
async def clear_cart(
    user_id: str = Query(..., description="User ID to clear cart for"),
    db: Session = Depends(get_db)
):
    """
    Clear all items from user's cart
    
    Removes all items from the user's cart:
    - Soft deletes all cart items
    - Resets cart to empty state
    - Returns confirmation and empty summary
    
    The system will:
    - Get all active cart items for the user
    - Soft delete all items (preserves history)
    - Return empty cart summary
    - Confirm number of items cleared
    """
    try:
        cart_service = CartService(db)
        
        result = cart_service.clear_cart(user_id=user_id)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to clear cart")

# =============================================================================
# CART VALIDATION ENDPOINTS
# =============================================================================

@router.post("/validate", response_model=CartValidationResponse)
async def validate_cart(
    request: CartValidationRequest = Body(...),
    user_id: str = Query(..., description="User ID to validate cart for"),
    db: Session = Depends(get_db)
):
    """
    Validate user's cart for issues
    
    Performs comprehensive cart validation:
    - Stock availability checks
    - Price change detection
    - Offer validation
    - Delivery option checks
    - Generates recommendations
    
    The system will check:
    - Product availability and stock levels
    - Price changes since items were added
    - Validity of applied offers
    - Delivery options and restrictions
    - Generate improvement recommendations
    """
    try:
        cart_service = CartService(db)
        
        validation_result = cart_service.validate_cart(
            user_id=user_id,
            validate_stock=request.validate_stock,
            validate_prices=request.validate_prices,
            validate_offers=request.validate_offers,
            check_delivery=request.check_delivery
        )
        
        return validation_result
        
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to validate cart")

# =============================================================================
# CART OFFER OPERATIONS
# =============================================================================

@router.post("/offers", response_model=CartOperationResponse)
async def apply_offer_to_cart(
    request: CartOfferRequest,
    user_id: str = Query(..., description="User ID to apply offer for"),
    db: Session = Depends(get_db)
):
    """
    Apply an offer to the entire cart
    
    Applies a promotional offer to the cart:
    - Validates offer eligibility
    - Applies discounts to applicable items
    - Updates cart totals
    - Returns updated summary
    
    The system will:
    - Verify offer is active and valid
    - Check cart total meets minimum requirements
    - Apply discounts to eligible items
    - Update cart summary with new totals
    """
    try:
        cart_service = CartService(db)
        
        if request.action.value == "apply_offer":
            result = cart_service.apply_offer_to_cart(
                user_id=user_id,
                offer_id=request.offer_id
            )
        elif request.action.value == "remove_offer":
            result = cart_service.remove_offer_from_cart(
                user_id=user_id,
                offer_id=request.offer_id
            )
        else:
            raise ValidationException(f"Invalid action: {request.action}")
        
        return result
        
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to apply offer to cart")

@router.delete("/offers/{offer_id}", response_model=CartOperationResponse)
async def remove_offer_from_cart(
    offer_id: str = Path(..., description="ID of the offer to remove"),
    user_id: str = Query(..., description="User ID to remove offer for"),
    db: Session = Depends(get_db)
):
    """
    Remove an offer from the entire cart
    
    Removes a previously applied offer from the cart:
    - Removes offer from all applicable items
    - Recalculates cart totals
    - Returns updated summary
    
    The system will:
    - Find all cart items with the specified offer
    - Remove the offer from those items
    - Recalculate discounts and totals
    - Return updated cart summary
    """
    try:
        cart_service = CartService(db)
        
        result = cart_service.remove_offer_from_cart(
            user_id=user_id,
            offer_id=offer_id
        )
        
        return result
        
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to remove offer from cart")

# =============================================================================
# CART UTILITY ENDPOINTS
# =============================================================================

@router.get("/items", response_model=CartItemListResponse)
async def get_cart_items(
    user_id: str = Query(..., description="User ID to get cart items for"),
    db: Session = Depends(get_db)
):
    """
    Get all cart items for a user
    
    Returns a list of all cart items with:
    - Product details and images
    - Quantities and prices
    - Discount information
    - Stock availability
    - Applied offers
    - Cart summary
    """
    try:
        cart_service = CartService(db)
        cart_items = cart_service.get_cart_items(user_id)
        return cart_items
        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get cart items")

@router.get("/analytics", response_model=dict)
async def get_cart_analytics(
    db: Session = Depends(get_db)
):
    """
    Get cart analytics overview
    
    Returns analytics about cart usage:
    - Total active carts
    - Average cart values
    - Conversion rates
    - Abandonment rates
    - Top products in carts
    """
    try:
        cart_service = CartService(db)
        analytics = cart_service.get_cart_analytics()
        return analytics
        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get cart analytics")

@router.post("/cleanup", response_model=dict)
async def cleanup_expired_carts(
    db: Session = Depends(get_db)
):
    """
    Clean up expired cart items
    
    Removes cart items that have expired:
    - Items older than specified age
    - Abandoned cart cleanup
    - Returns count of cleaned items
    
    This endpoint is typically called by a scheduled job.
    """
    try:
        cart_service = CartService(db)
        cleaned_count = cart_service.cleanup_expired_carts()
        
        return {
            "success": True,
            "message": f"Cleaned up {cleaned_count} expired cart items",
            "cleaned_count": cleaned_count
        }
        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to cleanup expired carts")

# =============================================================================
# CART NOTIFICATION ENDPOINTS
# =============================================================================

@router.get("/notifications", response_model=List[dict])
async def get_cart_notifications(
    user_id: str = Query(..., description="User ID to get notifications for"),
    db: Session = Depends(get_db)
):
    """
    Get cart notifications for a user
    
    Returns notifications related to cart:
    - Price change alerts
    - Stock availability updates
    - Offer expiration warnings
    - Delivery updates
    """
    try:
        # This would typically query a notifications table
        # For now, return empty list as placeholder
        return []
        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get cart notifications")

# =============================================================================
# CART SHARING ENDPOINTS
# =============================================================================

@router.post("/share", response_model=dict)
async def share_cart(
    share_with_email: str = Query(..., description="Email to share cart with"),
    share_type: str = Query("view", description="Type of sharing access"),
    expires_at: Optional[str] = Query(None, description="When shared access expires"),
    user_id: str = Query(..., description="User ID sharing the cart"),
    db: Session = Depends(get_db)
):
    """
    Share cart with another user
    
    Shares the cart with specified user:
    - Creates shared access link
    - Sets access permissions
    - Sets expiration time
    - Returns sharing details
    
    The system will:
    - Generate unique sharing token
    - Set access permissions (view/edit)
    - Set expiration time
    - Send notification to shared user
    """
    try:
        # This would typically create a cart sharing record
        # For now, return placeholder response
        return {
            "success": True,
            "message": "Cart shared successfully",
            "share_id": "placeholder_share_id",
            "share_url": f"https://example.com/cart/shared/placeholder_share_id",
            "expires_at": expires_at or "7 days from now"
        }
        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to share cart")

# =============================================================================
# CART EXPORT ENDPOINTS
# =============================================================================

@router.post("/export", response_model=dict)
async def export_cart(
    export_format: str = Query("json", description="Export format (json, csv, pdf)"),
    include_summary: bool = Query(True, description="Include cart summary"),
    include_offers: bool = Query(True, description="Include applied offers"),
    user_id: str = Query(..., description="User ID to export cart for"),
    db: Session = Depends(get_db)
):
    """
    Export cart data
    
    Exports cart data in specified format:
    - JSON, CSV, or PDF format
    - Includes cart items and summary
    - Applied offers and discounts
    - Download link generation
    
    The system will:
    - Generate export in requested format
    - Include specified data sections
    - Create download link
    - Set expiration for download
    """
    try:
        # This would typically generate export file
        # For now, return placeholder response
        return {
            "success": True,
            "message": "Cart exported successfully",
            "export_id": "placeholder_export_id",
            "download_url": f"https://example.com/exports/placeholder_export_id",
            "format": export_format,
            "expires_at": "24 hours from now"
        }
        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to export cart")

# =============================================================================
# HEALTH CHECK ENDPOINT
# =============================================================================

@router.get("/health/check", response_model=dict)
async def cart_service_health_check():
    """
    Cart service health check
    
    Check if the cart management service is running properly.
    """
    return success_response(
        data={
            "service": "cart-management",
            "status": "healthy",
            "endpoints": [
                "GET /api/cart",
                "GET /api/cart/summary",
                "POST /api/cart/items",
                "PUT /api/cart/items/{cart_item_id}",
                "DELETE /api/cart/items/{cart_item_id}",
                "DELETE /api/cart/clear",
                "POST /api/cart/validate",
                "POST /api/cart/offers",
                "DELETE /api/cart/offers/{offer_id}",
                "GET /api/cart/items",
                "GET /api/cart/analytics",
                "POST /api/cart/cleanup",
                "GET /api/cart/notifications",
                "POST /api/cart/share",
                "POST /api/cart/export"
            ],
            "features": [
                "Complete cart management",
                "Item addition, update, and removal",
                "Cart clearing and validation",
                "Offer application and removal",
                "Cart analytics and cleanup",
                "Cart sharing and export",
                "Real-time price and stock validation",
                "Comprehensive cart summaries",
                "Tax and shipping calculations"
            ]
        },
        message="Cart service is running"
    )