from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path, Body
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from database import get_db
from core.responses import success_response, error_response
from core.exceptions import (
    NotFoundException, 
    ValidationException, 
    ConflictException
)
from orders.schemas import (
    OrderCalculationResponse, OrderCreateResponse, OrderListResponse,
    OrderResponse, OrderStatusResponse, OrderTrackingResponse,
    OrderCalculationRequest, OrderCreateRequest, OrderCancelRequest,
    OrderReorderRequest, OrderHistoryResponse, OrderHistoryFilter,
    OrderHistorySummary
)
from orders.services import OrderService

# Create router
router = APIRouter(prefix="/api/orders", tags=["Orders"])

# =============================================================================
# ORDER CALCULATION ENDPOINTS
# =============================================================================

@router.post("/calculate", response_model=OrderCalculationResponse)
async def calculate_order(
    request: OrderCalculationRequest = Body(...),
    db: Session = Depends(get_db)
):
    """
    Calculate order totals including taxes, shipping, and discounts
    
    Calculates comprehensive order pricing including:
    - Subtotal calculation
    - Promotion discounts
    - Tax calculations
    - Shipping costs
    - Final total amount
    
    The system will:
    - Validate all input parameters
    - Calculate item totals and discounts
    - Apply promotion calculations
    - Calculate shipping based on method and address
    - Calculate taxes based on shipping address
    - Provide available shipping options
    - Estimate delivery dates
    """
    try:
        order_service = OrderService(db)
        
        # Validate request parameters
        if not request.items:
            raise ValidationException("At least one item is required")
        
        if not request.shipping_address:
            raise ValidationException("Shipping address is required")
        
        if not request.user_id:
            raise ValidationException("User ID is required")
        
        # Calculate order
        calculation = order_service.calculate_order(
            items=request.items,
            shipping_address=request.shipping_address,
            billing_address=request.billing_address,
            shipping_method=request.shipping_method,
            applied_promotions=request.applied_promotions,
            user_id=request.user_id,
            currency=request.currency
        )
        
        return calculation
        
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to calculate order")

# =============================================================================
# ORDER CREATION ENDPOINTS
# =============================================================================

@router.post("/create", response_model=OrderCreateResponse)
async def create_order(
    request: OrderCreateRequest = Body(...),
    db: Session = Depends(get_db)
):
    """
    Create a new order
    
    Creates a complete order with all necessary information:
    - Validates user and payment method
    - Calculates order totals
    - Creates order and order items
    - Generates unique order number
    - Sets initial order status
    
    The system will:
    - Verify user exists and is valid
    - Validate payment method belongs to user
    - Calculate all pricing including taxes and shipping
    - Generate unique order number
    - Create order record with all details
    - Create order items with pricing
    - Set initial status as pending
    - Return complete order summary
    """
    try:
        order_service = OrderService(db)
        
        # Validate request parameters
        if not request.items:
            raise ValidationException("At least one item is required")
        
        if not request.shipping_address:
            raise ValidationException("Shipping address is required")
        
        if not request.payment_method_id:
            raise ValidationException("Payment method ID is required")
        
        if not request.user_id:
            raise ValidationException("User ID is required")
        
        # Create order
        order_result = order_service.create_order(
            items=request.items,
            shipping_address=request.shipping_address,
            billing_address=request.billing_address,
            shipping_method=request.shipping_method,
            payment_method_id=request.payment_method_id,
            applied_promotions=request.applied_promotions,
            order_notes=request.order_notes,
            user_id=request.user_id,
            currency=request.currency
        )
        
        return order_result
        
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create order")

# =============================================================================
# ORDER RETRIEVAL ENDPOINTS
# =============================================================================

@router.get("/", response_model=OrderListResponse)
async def get_orders(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    order_status: Optional[str] = Query(None, description="Filter by order status"),
    payment_status: Optional[str] = Query(None, description="Filter by payment status"),
    shipping_status: Optional[str] = Query(None, description="Filter by shipping status"),
    order_type: Optional[str] = Query(None, description="Filter by order type"),
    shipping_method: Optional[str] = Query(None, description="Filter by shipping method"),
    min_total: Optional[float] = Query(None, ge=0, description="Minimum order total"),
    max_total: Optional[float] = Query(None, ge=0, description="Maximum order total"),
    date_from: Optional[str] = Query(None, description="Orders from date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Orders to date (YYYY-MM-DD)"),
    has_promotions: Optional[bool] = Query(None, description="Whether order has promotions"),
    search: Optional[str] = Query(None, description="Search in order number, product names"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order (asc/desc)"),
    db: Session = Depends(get_db)
):
    """
    Get orders with pagination and filtering
    
    Returns a paginated list of orders with comprehensive filtering:
    - Filter by user, status, dates, amounts
    - Search in order numbers and notes
    - Sort by various fields
    - Pagination support
    
    The system will:
    - Apply all specified filters
    - Perform search across order fields
    - Sort results as requested
    - Apply pagination
    - Return orders with complete details
    - Include pagination metadata
    """
    try:
        order_service = OrderService(db)
        
        # Parse date filters
        parsed_date_from = None
        parsed_date_to = None
        
        if date_from:
            try:
                parsed_date_from = datetime.fromisoformat(date_from)
            except ValueError:
                raise ValidationException("Invalid date_from format. Use YYYY-MM-DD")
        
        if date_to:
            try:
                parsed_date_to = datetime.fromisoformat(date_to)
            except ValueError:
                raise ValidationException("Invalid date_to format. Use YYYY-MM-DD")
        
        # Create filter object
        from orders.schemas import OrderFilter
        filters = OrderFilter(
            user_id=user_id,
            order_status=order_status,
            payment_status=payment_status,
            shipping_status=shipping_status,
            order_type=order_type,
            shipping_method=shipping_method,
            min_total=min_total,
            max_total=max_total,
            date_from=parsed_date_from,
            date_to=parsed_date_to,
            has_promotions=has_promotions,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        # Get orders
        orders = order_service.get_orders(
            user_id=user_id,
            page=page,
            size=size,
            filters=filters
        )
        
        return orders
        
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get orders")

@router.get("/{order_id}", response_model=OrderResponse)
async def get_order_by_id(
    order_id: str = Path(..., description="ID of the order to retrieve"),
    user_id: Optional[str] = Query(None, description="User ID for access control"),
    db: Session = Depends(get_db)
):
    """
    Get a specific order by ID
    
    Returns complete order details including:
    - Order information and status
    - All order items with product details
    - Pricing breakdown and totals
    - Shipping and billing addresses
    - Payment method information
    - Applied promotions and discounts
    
    The system will:
    - Verify order exists
    - Check user access if user_id provided
    - Retrieve all order items
    - Build complete order response
    - Include all related information
    """
    try:
        order_service = OrderService(db)
        
        order = order_service.get_order_by_id(order_id, user_id)
        
        return order
        
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get order")

# =============================================================================
# ORDER STATUS MANAGEMENT ENDPOINTS
# =============================================================================

@router.put("/{order_id}/cancel", response_model=dict)
async def cancel_order(
    order_id: str = Path(..., description="ID of the order to cancel"),
    request: OrderCancelRequest = Body(...),
    db: Session = Depends(get_db)
):
    """
    Cancel an order
    
    Cancels an existing order with specified reason:
    - Validates order can be cancelled
    - Updates order status
    - Records cancellation reason
    - Updates timestamps
    
    The system will:
    - Verify order exists and belongs to user
    - Check if order can be cancelled
    - Update order status to cancelled
    - Record cancellation reason and timestamp
    - Create status history entry
    - Return cancellation confirmation
    """
    try:
        order_service = OrderService(db)
        
        # Validate request parameters
        if not request.reason:
            raise ValidationException("Cancellation reason is required")
        
        if len(request.reason) < 10:
            raise ValidationException("Cancellation reason must be at least 10 characters")
        
        if not request.user_id:
            raise ValidationException("User ID is required")
        
        # Cancel order
        cancellation_result = order_service.cancel_order(
            order_id=order_id,
            reason=request.reason,
            user_id=request.user_id
        )
        
        return cancellation_result
        
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to cancel order")

@router.get("/{order_id}/status", response_model=OrderStatusResponse)
async def get_order_status(
    order_id: str = Path(..., description="ID of the order to get status for"),
    user_id: Optional[str] = Query(None, description="User ID for access control"),
    db: Session = Depends(get_db)
):
    """
    Get order status and progress information
    
    Returns comprehensive order status including:
    - Current order status
    - Status history timeline
    - Progress percentage
    - Estimated delivery information
    - Next expected updates
    
    The system will:
    - Verify order exists
    - Check user access if user_id provided
    - Retrieve status history
    - Calculate progress percentage
    - Provide status descriptions and icons
    - Estimate next update times
    """
    try:
        order_service = OrderService(db)
        
        order_status = order_service.get_order_status(order_id, user_id)
        
        return order_status
        
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get order status")

# =============================================================================
# ORDER TRACKING ENDPOINTS
# =============================================================================

@router.get("/{order_id}/track", response_model=OrderTrackingResponse)
async def get_order_tracking(
    order_id: str = Path(..., description="ID of the order to track"),
    user_id: Optional[str] = Query(None, description="User ID for access control"),
    db: Session = Depends(get_db)
):
    """
    Get order tracking information
    
    Returns comprehensive tracking details including:
    - Tracking number and carrier
    - Current package location
    - Tracking events history
    - Estimated delivery date
    - Delivery attempts and notes
    
    The system will:
    - Verify order exists
    - Check user access if user_id provided
    - Retrieve tracking information
    - Get tracking events history
    - Calculate delivery statistics
    - Provide current status
    """
    try:
        order_service = OrderService(db)
        
        tracking_info = order_service.get_order_tracking(order_id, user_id)
        
        return tracking_info
        
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get order tracking")

# =============================================================================
# ORDER REORDERING ENDPOINTS
# =============================================================================

@router.post("/{order_id}/reorder", response_model=OrderCreateResponse)
async def reorder(
    order_id: str = Path(..., description="ID of the order to reorder"),
    request: OrderReorderRequest = Body(...),
    db: Session = Depends(get_db)
):
    """
    Create a new order based on an existing order
    
    Creates a new order with items from a previous order:
    - Can include all or selected items
    - Allows quantity updates
    - Can use new addresses and payment methods
    - Starts fresh with promotions
    
    The system will:
    - Verify original order exists
    - Prepare items for reorder
    - Allow quantity modifications
    - Use new or original addresses
    - Create new order with fresh calculations
    - Generate new order number
    - Apply current pricing and promotions
    """
    try:
        order_service = OrderService(db)
        
        # Validate request parameters
        if not request.user_id:
            raise ValidationException("User ID is required")
        
        # Perform reorder
        reorder_result = order_service.reorder(
            order_id=order_id,
            include_all_items=request.include_all_items,
            selected_items=request.selected_items,
            update_quantities=request.update_quantities,
            new_shipping_address=request.new_shipping_address,
            new_payment_method=request.new_payment_method,
            user_id=request.user_id
        )
        
        return reorder_result
        
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to reorder")

# =============================================================================
# ORDER UTILITY ENDPOINTS
# =============================================================================

@router.get("/{order_id}/summary", response_model=dict)
async def get_order_summary(
    order_id: str = Path(..., description="ID of the order to get summary for"),
    user_id: Optional[str] = Query(None, description="User ID for access control"),
    db: Session = Depends(get_db)
):
    """
    Get order summary information
    
    Returns a condensed summary of the order including:
    - Basic order information
    - Key totals and status
    - Item count and quantities
    - Delivery information
    
    Useful for quick order overview without full details.
    """
    try:
        order_service = OrderService(db)
        
        order = order_service.get_order_by_id(order_id, user_id)
        
        # Create summary
        summary = {
            "order_id": order.order_id,
            "order_number": order.order_number,
            "order_status": order.order_status,
            "payment_status": order.payment_status,
            "shipping_status": order.shipping_status,
            "total_amount": order.total_amount,
            "total_items": order.total_items,
            "total_quantity": order.total_quantity,
            "estimated_delivery": order.estimated_delivery,
            "created_at": order.created_at,
            "updated_at": order.updated_at
        }
        
        return summary
        
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get order summary")

@router.get("/{order_id}/invoice", response_model=dict)
async def get_order_invoice(
    order_id: str = Path(..., description="ID of the order to get invoice for"),
    user_id: Optional[str] = Query(None, description="User ID for access control"),
    format: str = Query("json", description="Invoice format (json, pdf, html)"),
    db: Session = Depends(get_db)
):
    """
    Get order invoice
    
    Returns invoice information for the order including:
    - Complete billing details
    - Itemized breakdown
    - Tax and shipping details
    - Payment information
    
    The system will:
    - Verify order exists and belongs to user
    - Generate invoice in requested format
    - Include all necessary billing information
    - Provide download or display options
    """
    try:
        order_service = OrderService(db)
        
        order = order_service.get_order_by_id(order_id, user_id)
        
        # Create invoice (placeholder - would typically generate actual invoice)
        invoice = {
            "invoice_number": f"INV-{order.order_number}",
            "order_id": order.order_id,
            "order_number": order.order_number,
            "invoice_date": datetime.utcnow(),
            "due_date": datetime.utcnow() + timedelta(days=30),
            "billing_address": order.billing_address,
            "shipping_address": order.shipping_address,
            "items": order.items,
            "subtotal": order.subtotal,
            "total_discount": order.total_discount,
            "total_tax": order.total_tax,
            "shipping_cost": order.shipping_cost,
            "total_amount": order.total_amount,
            "currency": order.currency,
            "format": format
        }
        
        return invoice
        
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get order invoice")

# =============================================================================
# ORDER ANALYTICS ENDPOINTS
# =============================================================================

@router.get("/analytics/overview", response_model=dict)
async def get_order_analytics(
    db: Session = Depends(get_db)
):
    """
    Get order analytics overview
    
    Returns comprehensive analytics for all orders including:
    - Order counts and revenue
    - Customer statistics
    - Performance metrics
    - Trend analysis
    
    The system will:
    - Calculate overall statistics
    - Analyze order patterns
    - Provide performance insights
    - Show revenue trends
    """
    try:
        order_service = OrderService(db)
        
        analytics = order_service.get_order_analytics()
        
        return analytics
        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get order analytics")

@router.get("/statistics/summary", response_model=dict)
async def get_order_statistics(
    db: Session = Depends(get_db)
):
    """
    Get order statistics summary
    
    Returns key order statistics including:
    - Total orders and revenue
    - Average order values
    - Status distribution
    - Conversion rates
    
    The system will:
    - Calculate key metrics
    - Provide status breakdowns
    - Show performance indicators
    - Include trend data
    """
    try:
        order_service = OrderService(db)
        
        statistics = order_service.get_order_statistics()
        
        return statistics
        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get order statistics")

# =============================================================================
# ORDER HISTORY ENDPOINTS
# =============================================================================

@router.get("/history", response_model=OrderHistoryResponse)
async def get_order_history(
    user_id: str = Query(..., description="User ID to get order history for"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    db: Session = Depends(get_db)
):
    """
    Get complete order history for a user
    
    Returns comprehensive order history including:
    - All orders with basic information
    - Pagination support
    - Basic summary statistics
    - Order status distribution
    
    The system will:
    - Retrieve all orders for the specified user
    - Apply pagination
    - Calculate summary statistics
    - Return formatted history items
    """
    try:
        order_service = OrderService(db)
        
        # Validate user_id
        if not user_id:
            raise ValidationException("User ID is required")
        
        # Create basic filter for pagination only
        from orders.schemas import OrderHistoryFilter
        filters = OrderHistoryFilter(
            page=page,
            size=size
        )
        
        # Get order history
        history = order_service.get_order_history(user_id, filters)
        
        return history
        
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get order history")

@router.get("/history/filter", response_model=OrderHistoryResponse)
async def get_filtered_order_history(
    user_id: str = Query(..., description="User ID to get order history for"),
    status: Optional[str] = Query(None, description="Filter by order status"),
    date_from: Optional[str] = Query(None, description="Orders from date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Orders to date (YYYY-MM-DD)"),
    min_amount: Optional[float] = Query(None, ge=0, description="Minimum order amount"),
    max_amount: Optional[float] = Query(None, ge=0, description="Maximum order amount"),
    shipping_method: Optional[str] = Query(None, description="Filter by shipping method"),
    has_promotions: Optional[bool] = Query(None, description="Whether order has promotions"),
    search: Optional[str] = Query(None, description="Search in order number, product names"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order (asc/desc)"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    db: Session = Depends(get_db)
):
    """
    Get filtered order history for a user
    
    Returns filtered order history with comprehensive filtering:
    - Filter by status, dates, amounts, shipping method
    - Search in order numbers and notes
    - Sort by various fields
    - Pagination support
    - Detailed summary statistics
    
    The system will:
    - Apply all specified filters
    - Perform search across order fields
    - Sort results as requested
    - Apply pagination
    - Calculate filtered summary statistics
    - Return filtered history with metadata
    """
    try:
        order_service = OrderService(db)
        
        # Validate user_id
        if not user_id:
            raise ValidationException("User ID is required")
        
        # Parse date filters
        parsed_date_from = None
        parsed_date_to = None
        
        if date_from:
            try:
                parsed_date_from = datetime.fromisoformat(date_from)
            except ValueError:
                raise ValidationException("Invalid date_from format. Use YYYY-MM-DD")
        
        if date_to:
            try:
                parsed_date_to = datetime.fromisoformat(date_to)
            except ValueError:
                raise ValidationException("Invalid date_to format. Use YYYY-MM-DD")
        
        # Validate amount filters
        if min_amount is not None and max_amount is not None:
            if min_amount > max_amount:
                raise ValidationException("min_amount cannot be greater than max_amount")
        
        # Create filter object
        filters = OrderHistoryFilter(
            status=status,
            date_from=parsed_date_from,
            date_to=parsed_date_to,
            min_amount=min_amount,
            max_amount=max_amount,
            shipping_method=shipping_method,
            has_promotions=has_promotions,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            size=size
        )
        
        # Get filtered order history
        history = order_service.get_order_history(user_id, filters)
        
        return history
        
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get filtered order history")

@router.get("/history/summary", response_model=OrderHistorySummary)
async def get_order_history_summary(
    user_id: str = Query(..., description="User ID to get summary for"),
    date_from: Optional[str] = Query(None, description="Summary from date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="Summary to date (YYYY-MM-DD)"),
    db: Session = Depends(get_db)
):
    """
    Get summary statistics for user's order history
    
    Returns comprehensive summary including:
    - Total orders and revenue
    - Average order values
    - Status distribution
    - Monthly breakdown
    - Shipping method preferences
    - Delivery success rates
    
    The system will:
    - Calculate overall statistics
    - Group orders by month
    - Analyze shipping preferences
    - Calculate success rates
    - Provide actionable insights
    """
    try:
        order_service = OrderService(db)
        
        # Validate user_id
        if not user_id:
            raise ValidationException("User ID is required")
        
        # Parse date filters
        parsed_date_from = None
        parsed_date_to = None
        
        if date_from:
            try:
                parsed_date_from = datetime.fromisoformat(date_from)
            except ValueError:
                raise ValidationException("Invalid date_from format. Use YYYY-MM-DD")
        
        if date_to:
            try:
                parsed_date_to = datetime.fromisoformat(date_to)
            except ValueError:
                raise ValidationException("Invalid date_to format. Use YYYY-MM-DD")
        
        # Get order history summary
        summary = order_service.get_order_history_summary(
            user_id=user_id,
            date_from=parsed_date_from,
            date_to=parsed_date_to
        )
        
        return summary
        
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get order history summary")

# =============================================================================
# HEALTH CHECK ENDPOINT
# =============================================================================

@router.get("/health/check", response_model=dict)
async def order_service_health_check():
    """
    Order service health check
    
    Check if the order management service is running properly.
    """
    return success_response(
        data={
            "service": "order-management",
            "status": "healthy",
            "endpoints": [
                "POST /api/orders/calculate",
                "POST /api/orders/create",
                "GET /api/orders",
                "GET /api/orders/{order_id}",
                "PUT /api/orders/{order_id}/cancel",
                "GET /api/orders/{order_id}/status",
                "GET /api/orders/{order_id}/track",
                "POST /api/orders/{order_id}/reorder",
                "GET /api/orders/{order_id}/summary",
                "GET /api/orders/{order_id}/invoice",
                "GET /api/orders/analytics/overview",
                "GET /api/orders/statistics/summary",
                "GET /api/orders/history",
                "GET /api/orders/history/filter",
                "GET /api/orders/history/summary"
            ],
            "features": [
                "Complete order management",
                "Order calculation and pricing",
                "Order creation and validation",
                "Order status tracking",
                "Order cancellation",
                "Order reordering",
                "Comprehensive filtering and search",
                "Pagination support",
                "Order analytics and statistics",
                "Invoice generation",
                "Shipping and tax calculations",
                "Promotion integration",
                "Order history management",
                "Advanced history filtering",
                "History summary and analytics"
            ]
        },
        message="Order service is running"
    )