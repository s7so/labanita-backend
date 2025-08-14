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
from admin.schemas import (
    AdminProductResponse, AdminProductListResponse, AdminProductFilter,
    AdminProductCreateRequest, AdminProductUpdateRequest, AdminOrderResponse,
    AdminOrderListResponse, AdminOrderFilter, AdminOrderStatusUpdate,
    AdminPromotionResponse, AdminPromotionListResponse, AdminPromotionFilter,
    AdminPromotionCreateRequest, AdminPromotionUpdateRequest
)
from admin.services import AdminService

# Create router
router = APIRouter(prefix="/api/admin", tags=["Admin"])

# =============================================================================
# ADMIN PRODUCT MANAGEMENT ENDPOINTS
# =============================================================================

@router.get("/products", response_model=AdminProductListResponse)
async def get_admin_products(
    search: Optional[str] = Query(None, description="Search in product name, description, SKU"),
    category_id: Optional[str] = Query(None, description="Filter by category ID"),
    brand: Optional[str] = Query(None, description="Filter by brand"),
    status: Optional[str] = Query(None, description="Filter by product status"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    is_featured: Optional[bool] = Query(None, description="Filter by featured status"),
    price_min: Optional[float] = Query(None, ge=0, description="Minimum price"),
    price_max: Optional[float] = Query(None, ge=0, description="Maximum price"),
    stock_min: Optional[int] = Query(None, ge=0, description="Minimum stock quantity"),
    stock_max: Optional[int] = Query(None, ge=0, description="Maximum stock quantity"),
    created_date_from: Optional[str] = Query(None, description="Created from date (YYYY-MM-DD)"),
    created_date_to: Optional[str] = Query(None, description="Created to date (YYYY-MM-DD)"),
    updated_date_from: Optional[str] = Query(None, description="Updated from date (YYYY-MM-DD)"),
    updated_date_to: Optional[str] = Query(None, description="Updated to date (YYYY-MM-DD)"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order (asc/desc)"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    db: Session = Depends(get_db)
):
    """
    Get products for admin management
    
    Returns comprehensive product list with advanced filtering:
    - Search across product fields
    - Filter by category, brand, status, price, stock
    - Date range filtering
    - Sorting and pagination
    - Summary statistics
    
    The system will:
    - Apply all specified filters
    - Perform search across product fields
    - Sort results as requested
    - Apply pagination
    - Calculate filtered summary statistics
    - Return products with admin-specific details
    """
    try:
        admin_service = AdminService(db)
        
        # Parse date filters
        parsed_created_date_from = None
        parsed_created_date_to = None
        parsed_updated_date_from = None
        parsed_updated_date_to = None
        
        if created_date_from:
            try:
                from datetime import datetime
                parsed_created_date_from = datetime.fromisoformat(created_date_from)
            except ValueError:
                raise ValidationException("Invalid created_date_from format. Use YYYY-MM-DD")
        
        if created_date_to:
            try:
                from datetime import datetime
                parsed_created_date_to = datetime.fromisoformat(created_date_to)
            except ValueError:
                raise ValidationException("Invalid created_date_to format. Use YYYY-MM-DD")
        
        if updated_date_from:
            try:
                from datetime import datetime
                parsed_updated_date_from = datetime.fromisoformat(updated_date_from)
            except ValueError:
                raise ValidationException("Invalid updated_date_from format. Use YYYY-MM-DD")
        
        if updated_date_to:
            try:
                from datetime import datetime
                parsed_updated_date_to = datetime.fromisoformat(updated_date_to)
            except ValueError:
                raise ValidationException("Invalid updated_date_to format. Use YYYY-MM-DD")
        
        # Validate price filters
        if price_min is not None and price_max is not None:
            if price_min > price_max:
                raise ValidationException("price_min cannot be greater than price_max")
        
        # Validate stock filters
        if stock_min is not None and stock_max is not None:
            if stock_min > stock_max:
                raise ValidationException("stock_min cannot be greater than stock_max")
        
        # Create filter object
        filters = AdminProductFilter(
            search=search,
            category_id=category_id,
            brand=brand,
            status=status,
            is_active=is_active,
            is_featured=is_featured,
            price_min=price_min,
            price_max=price_max,
            stock_min=stock_min,
            stock_max=stock_max,
            created_date_from=parsed_created_date_from,
            created_date_to=parsed_created_date_to,
            updated_date_from=parsed_updated_date_from,
            updated_date_to=parsed_updated_date_to,
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            size=size
        )
        
        # Get admin products
        products = admin_service.get_admin_products(filters)
        return products
        
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get admin products")

@router.post("/products", response_model=AdminProductResponse)
async def create_admin_product(
    product_data: AdminProductCreateRequest = Body(...),
    admin_user_id: str = Query(..., description="Admin user ID creating the product"),
    db: Session = Depends(get_db)
):
    """
    Create new product (admin only)
    
    Creates a new product with comprehensive details:
    - Product information and description
    - Pricing and inventory details
    - SEO and metadata
    - Admin notes and status
    
    The system will:
    - Validate all input parameters
    - Check SKU uniqueness
    - Validate category exists
    - Create product record
    - Log admin activity
    - Return created product details
    """
    try:
        admin_service = AdminService(db)
        
        # Validate admin_user_id
        if not admin_user_id:
            raise ValidationException("Admin user ID is required")
        
        # Create product
        new_product = admin_service.create_admin_product(product_data, admin_user_id)
        return new_product
        
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except ConflictException as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create product")

@router.get("/products/{product_id}", response_model=AdminProductResponse)
async def get_admin_product_by_id(
    product_id: str = Path(..., description="Product ID to retrieve"),
    db: Session = Depends(get_db)
):
    """
    Get product by ID for admin management
    
    Returns detailed product information including:
    - Complete product details
    - Admin-specific fields
    - Performance metrics
    - Audit information
    
    The system will:
    - Find product by ID
    - Return admin-specific details
    - Include category information
    - Provide performance metrics
    """
    try:
        admin_service = AdminService(db)
        product = admin_service.get_admin_product_by_id(product_id)
        return product
        
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get admin product")

@router.put("/products/{product_id}", response_model=AdminProductResponse)
async def update_admin_product(
    product_id: str = Path(..., description="Product ID to update"),
    product_data: AdminProductUpdateRequest = Body(...),
    admin_user_id: str = Query(..., description="Admin user ID updating the product"),
    db: Session = Depends(get_db)
):
    """
    Update existing product (admin only)
    
    Updates product with comprehensive details:
    - Modify any product field
    - Update pricing and inventory
    - Change status and visibility
    - Update SEO and metadata
    
    The system will:
    - Validate product exists
    - Check SKU uniqueness if changing
    - Validate category if changing
    - Update specified fields
    - Log admin activity
    - Return updated product details
    """
    try:
        admin_service = AdminService(db)
        
        # Validate admin_user_id
        if not admin_user_id:
            raise ValidationException("Admin user ID is required")
        
        # Update product
        updated_product = admin_service.update_admin_product(product_id, product_data, admin_user_id)
        return updated_product
        
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except ConflictException as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update product")

@router.delete("/products/{product_id}", response_model=dict)
async def delete_admin_product(
    product_id: str = Path(..., description="Product ID to delete"),
    admin_user_id: str = Query(..., description="Admin user ID deleting the product"),
    db: Session = Depends(get_db)
):
    """
    Delete product (admin only)
    
    Permanently removes a product from the system:
    - Complete product deletion
    - Validation of deletion constraints
    - Activity logging
    
    The system will:
    - Validate product exists
    - Check for order dependencies
    - Prevent deletion if constraints exist
    - Log admin activity
    - Return deletion confirmation
    """
    try:
        admin_service = AdminService(db)
        
        # Validate admin_user_id
        if not admin_user_id:
            raise ValidationException("Admin user ID is required")
        
        # Delete product
        success = admin_service.delete_admin_product(product_id, admin_user_id)
        
        if success:
            return success_response(
                data={"product_id": product_id},
                message="Product deleted successfully"
            )
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete product")
        
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except ConflictException as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete product")

# =============================================================================
# ADMIN BULK OPERATIONS ENDPOINTS
# =============================================================================

@router.put("/products/bulk/status", response_model=dict)
async def bulk_update_product_status(
    product_ids: List[str] = Body(..., description="List of product IDs to update"),
    status: str = Body(..., description="New status to apply"),
    admin_user_id: str = Query(..., description="Admin user ID performing the bulk update"),
    db: Session = Depends(get_db)
):
    """
    Bulk update product status (admin only)
    
    Updates multiple products to a new status:
    - Mass status changes
    - Validation of status values
    - Activity logging for bulk operations
    
    The system will:
    - Validate all product IDs
    - Check status validity
    - Update multiple products
    - Log bulk activity
    - Return update summary
    """
    try:
        admin_service = AdminService(db)
        
        # Validate admin_user_id
        if not admin_user_id:
            raise ValidationException("Admin user ID is required")
        
        # Validate product_ids
        if not product_ids:
            raise ValidationException("Product IDs list cannot be empty")
        
        # Bulk update status
        result = admin_service.bulk_update_product_status(product_ids, status, admin_user_id)
        return success_response(
            data=result,
            message="Bulk status update completed successfully"
        )
        
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to bulk update product status")

# =============================================================================
# ADMIN ORDER MANAGEMENT ENDPOINTS
# =============================================================================

@router.get("/orders", response_model=AdminOrderListResponse)
async def get_admin_orders(
    search: Optional[str] = Query(None, description="Search in order number, username, email"),
    order_status: Optional[str] = Query(None, description="Filter by order status"),
    payment_status: Optional[str] = Query(None, description="Filter by payment status"),
    shipping_status: Optional[str] = Query(None, description="Filter by shipping status"),
    order_type: Optional[str] = Query(None, description="Filter by order type"),
    shipping_method: Optional[str] = Query(None, description="Filter by shipping method"),
    amount_min: Optional[float] = Query(None, ge=0, description="Minimum order amount"),
    amount_max: Optional[float] = Query(None, ge=0, description="Maximum order amount"),
    created_date_from: Optional[str] = Query(None, description="Created from date (YYYY-MM-DD)"),
    created_date_to: Optional[str] = Query(None, description="Created to date (YYYY-MM-DD)"),
    delivery_date_from: Optional[str] = Query(None, description="Delivery from date (YYYY-MM-DD)"),
    delivery_date_to: Optional[str] = Query(None, description="Delivery to date (YYYY-MM-DD)"),
    has_promotions: Optional[bool] = Query(None, description="Whether order has promotions"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order (asc/desc)"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    db: Session = Depends(get_db)
):
    """
    Get orders for admin management
    
    Returns comprehensive order list with advanced filtering:
    - Search across order fields
    - Filter by status, payment, shipping, type
    - Amount and date range filtering
    - Promotion filtering
    - Sorting and pagination
    - Summary statistics
    
    The system will:
    - Apply all specified filters
    - Perform search across order fields
    - Sort results as requested
    - Apply pagination
    - Calculate filtered summary statistics
    - Return orders with admin-specific details
    """
    try:
        admin_service = AdminService(db)
        
        # Parse date filters
        parsed_created_date_from = None
        parsed_created_date_to = None
        parsed_delivery_date_from = None
        parsed_delivery_date_to = None
        
        if created_date_from:
            try:
                from datetime import datetime
                parsed_created_date_from = datetime.fromisoformat(created_date_from)
            except ValueError:
                raise ValidationException("Invalid created_date_from format. Use YYYY-MM-DD")
        
        if created_date_to:
            try:
                from datetime import datetime
                parsed_created_date_to = datetime.fromisoformat(created_date_to)
            except ValueError:
                raise ValidationException("Invalid created_date_to format. Use YYYY-MM-DD")
        
        if delivery_date_from:
            try:
                from datetime import datetime
                parsed_delivery_date_from = datetime.fromisoformat(delivery_date_from)
            except ValueError:
                raise ValidationException("Invalid delivery_date_from format. Use YYYY-MM-DD")
        
        if delivery_date_to:
            try:
                from datetime import datetime
                parsed_delivery_date_to = datetime.fromisoformat(delivery_date_to)
            except ValueError:
                raise ValidationException("Invalid delivery_date_to format. Use YYYY-MM-DD")
        
        # Validate amount filters
        if amount_min is not None and amount_max is not None:
            if amount_min > amount_max:
                raise ValidationException("amount_min cannot be greater than amount_max")
        
        # Create filter object
        filters = AdminOrderFilter(
            search=search,
            order_status=order_status,
            payment_status=payment_status,
            shipping_status=shipping_status,
            order_type=order_type,
            shipping_method=shipping_method,
            amount_min=amount_min,
            amount_max=amount_max,
            created_date_from=parsed_created_date_from,
            created_date_to=parsed_created_date_to,
            delivery_date_from=parsed_delivery_date_from,
            delivery_date_to=parsed_delivery_date_to,
            has_promotions=has_promotions,
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            size=size
        )
        
        # Get admin orders
        orders = admin_service.get_admin_orders(filters)
        return orders
        
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get admin orders")

@router.put("/orders/{order_id}/status", response_model=AdminOrderResponse)
async def update_admin_order_status(
    order_id: str = Path(..., description="Order ID to update status for"),
    status_update: AdminOrderStatusUpdate = Body(...),
    admin_user_id: str = Query(..., description="Admin user ID updating the order status"),
    db: Session = Depends(get_db)
):
    """
    Update order status (admin only)
    
    Updates order status, payment status, and shipping status:
    - Change order workflow status
    - Update payment processing status
    - Modify shipping and delivery status
    - Add admin notes and delivery dates
    
    The system will:
    - Validate order exists
    - Update specified status fields
    - Log admin activity
    - Return updated order details
    """
    try:
        admin_service = AdminService(db)
        
        # Validate admin_user_id
        if not admin_user_id:
            raise ValidationException("Admin user ID is required")
        
        # Update order status
        updated_order = admin_service.update_admin_order_status(order_id, status_update, admin_user_id)
        return updated_order
        
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update order status")

@router.get("/orders/stats", response_model=dict)
async def get_admin_order_stats(
    db: Session = Depends(get_db)
):
    """
    Get admin order statistics
    
    Returns comprehensive order analytics:
    - Total orders and revenue
    - Status distributions
    - Performance metrics
    - Top products and categories
    - Delivery performance
    
    The system will:
    - Calculate real-time statistics
    - Provide performance metrics
    - Show business insights
    - Return actionable data
    """
    try:
        admin_service = AdminService(db)
        stats = admin_service.get_admin_order_stats()
        return success_response(
            data=stats,
            message="Admin order statistics retrieved successfully"
        )
        
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get admin order stats")

# =============================================================================
# ADMIN PROMOTION MANAGEMENT ENDPOINTS
# =============================================================================

@router.get("/promotions", response_model=AdminPromotionListResponse)
async def get_admin_promotions(
    search: Optional[str] = Query(None, description="Search in promotion name, description"),
    promotion_type: Optional[str] = Query(None, description="Filter by promotion type"),
    discount_type: Optional[str] = Query(None, description="Filter by discount type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    auto_apply: Optional[bool] = Query(None, description="Filter by auto-apply status"),
    start_date_from: Optional[str] = Query(None, description="Start date from (YYYY-MM-DD)"),
    start_date_to: Optional[str] = Query(None, description="Start date to (YYYY-MM-DD)"),
    end_date_from: Optional[str] = Query(None, description="End date from (YYYY-MM-DD)"),
    end_date_to: Optional[str] = Query(None, description="End date to (YYYY-MM-DD)"),
    min_discount_value: Optional[float] = Query(None, ge=0, description="Minimum discount value"),
    max_discount_value: Optional[float] = Query(None, ge=0, description="Maximum discount value"),
    sort_by: str = Query("created_at", description="Sort field"),
    sort_order: str = Query("desc", description="Sort order (asc/desc)"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    db: Session = Depends(get_db)
):
    """
    Get promotions for admin management
    
    Returns comprehensive promotion list with advanced filtering:
    - Search across promotion fields
    - Filter by type, discount type, status
    - Date range filtering
    - Discount value filtering
    - Sorting and pagination
    - Summary statistics
    
    The system will:
    - Apply all specified filters
    - Perform search across promotion fields
    - Sort results as requested
    - Apply pagination
    - Calculate filtered summary statistics
    - Return promotions with admin-specific details
    """
    try:
        admin_service = AdminService(db)
        
        # Parse date filters
        parsed_start_date_from = None
        parsed_start_date_to = None
        parsed_end_date_from = None
        parsed_end_date_to = None
        
        if start_date_from:
            try:
                from datetime import datetime
                parsed_start_date_from = datetime.fromisoformat(start_date_from)
            except ValueError:
                raise ValidationException("Invalid start_date_from format. Use YYYY-MM-DD")
        
        if start_date_to:
            try:
                from datetime import datetime
                parsed_start_date_to = datetime.fromisoformat(start_date_to)
            except ValueError:
                raise ValidationException("Invalid start_date_to format. Use YYYY-MM-DD")
        
        if end_date_from:
            try:
                from datetime import datetime
                parsed_end_date_from = datetime.fromisoformat(end_date_from)
            except ValueError:
                raise ValidationException("Invalid end_date_from format. Use YYYY-MM-DD")
        
        if end_date_to:
            try:
                from datetime import datetime
                parsed_end_date_to = datetime.fromisoformat(end_date_to)
            except ValueError:
                raise ValidationException("Invalid end_date_to format. Use YYYY-MM-DD")
        
        # Validate discount value filters
        if min_discount_value is not None and max_discount_value is not None:
            if min_discount_value > max_discount_value:
                raise ValidationException("min_discount_value cannot be greater than max_discount_value")
        
        # Create filter object
        filters = AdminPromotionFilter(
            search=search,
            promotion_type=promotion_type,
            discount_type=discount_type,
            is_active=is_active,
            auto_apply=auto_apply,
            start_date_from=parsed_start_date_from,
            start_date_to=parsed_start_date_to,
            end_date_from=parsed_end_date_from,
            end_date_to=parsed_end_date_to,
            min_discount_value=min_discount_value,
            max_discount_value=max_discount_value,
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            size=size
        )
        
        # Get admin promotions
        promotions = admin_service.get_admin_promotions(filters)
        return promotions
        
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get admin promotions")

@router.post("/promotions", response_model=AdminPromotionResponse)
async def create_admin_promotion(
    promotion_data: AdminPromotionCreateRequest = Body(...),
    admin_user_id: str = Query(..., description="Admin user ID creating the promotion"),
    db: Session = Depends(get_db)
):
    """
    Create new promotion (admin only)
    
    Creates a new promotion with comprehensive details:
    - Promotion configuration and rules
    - Discount settings and limits
    - Applicability and conditions
    - Scheduling and priority
    
    The system will:
    - Validate all input parameters
    - Create promotion record
    - Log admin activity
    - Return created promotion details
    """
    try:
        admin_service = AdminService(db)
        
        # Validate admin_user_id
        if not admin_user_id:
            raise ValidationException("Admin user ID is required")
        
        # Create promotion
        new_promotion = admin_service.create_admin_promotion(promotion_data, admin_user_id)
        return new_promotion
        
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except ConflictException as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create promotion")

@router.put("/promotions/{promotion_id}", response_model=AdminPromotionResponse)
async def update_admin_promotion(
    promotion_id: str = Path(..., description="Promotion ID to update"),
    promotion_data: AdminPromotionUpdateRequest = Body(...),
    admin_user_id: str = Query(..., description="Admin user ID updating the promotion"),
    db: Session = Depends(get_db)
):
    """
    Update existing promotion (admin only)
    
    Updates promotion with comprehensive details:
    - Modify promotion configuration
    - Update discount settings
    - Change applicability rules
    - Adjust scheduling and priority
    
    The system will:
    - Validate promotion exists
    - Update specified fields
    - Log admin activity
    - Return updated promotion details
    """
    try:
        admin_service = AdminService(db)
        
        # Validate admin_user_id
        if not admin_user_id:
            raise ValidationException("Admin user ID is required")
        
        # Update promotion
        updated_promotion = admin_service.update_admin_promotion(promotion_id, promotion_data, admin_user_id)
        return updated_promotion
        
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except ConflictException as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update promotion")

@router.delete("/promotions/{promotion_id}", response_model=dict)
async def delete_admin_promotion(
    promotion_id: str = Path(..., description="Promotion ID to delete"),
    admin_user_id: str = Query(..., description="Admin user ID deleting the promotion"),
    db: Session = Depends(get_db)
):
    """
    Delete promotion (admin only)
    
    Permanently removes a promotion from the system:
    - Complete promotion deletion
    - Validation of deletion constraints
    - Activity logging
    
    The system will:
    - Validate promotion exists
    - Check for active status
    - Prevent deletion if constraints exist
    - Log admin activity
    - Return deletion confirmation
    """
    try:
        admin_service = AdminService(db)
        
        # Validate admin_user_id
        if not admin_user_id:
            raise ValidationException("Admin user ID is required")
        
        # Delete promotion
        success = admin_service.delete_admin_promotion(promotion_id, admin_user_id)
        
        if success:
            return success_response(
                data={"promotion_id": promotion_id},
                message="Promotion deleted successfully"
            )
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete promotion")
        
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except ConflictException as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete promotion")

# =============================================================================
# ADMIN DASHBOARD ENDPOINTS
# =============================================================================

@router.get("/dashboard/stats", response_model=dict)
async def get_admin_dashboard_stats(
    db: Session = Depends(get_db)
):
    """
    Get admin dashboard statistics
    
    Returns comprehensive dashboard metrics:
    - Product statistics
    - User statistics
    - Order statistics
    - Revenue information
    - System alerts
    
    The system will:
    - Calculate real-time statistics
    - Provide performance metrics
    - Show system health indicators
    - Return actionable insights
    """
    try:
        admin_service = AdminService(db)
        stats = admin_service.get_admin_dashboard_stats()
        return success_response(
            data=stats,
            message="Admin dashboard statistics retrieved successfully"
        )
        
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get admin dashboard stats")

# =============================================================================
# ADMIN USER MANAGEMENT ENDPOINTS
# =============================================================================

@router.get("/users", response_model=AdminUserListResponse)
async def get_admin_users(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    search: Optional[str] = Query(None, description="Search in username, email, names"),
    role: Optional[str] = Query(None, description="Filter by user role"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db)
):
    """
    Get users for admin management
    
    Returns user list with filtering:
    - User information and status
    - Role and permissions
    - Activity metrics
    - Account statistics
    
    The system will:
    - Apply search and filters
    - Provide pagination
    - Return user details
    - Include activity metrics
    """
    try:
        admin_service = AdminService(db)
        users = admin_service.get_admin_users(page, size, search, role, is_active)
        return users
        
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get admin users")

# =============================================================================
# HEALTH CHECK ENDPOINT
# =============================================================================

@router.get("/health/check", response_model=dict)
async def admin_service_health_check():
    """
    Admin service health check
    
    Check if the admin management service is running properly.
    """
    return success_response(
        data={
            "service": "admin-management",
            "status": "healthy",
            "endpoints": [
                "GET /api/admin/products",
                "POST /api/admin/products",
                "GET /api/admin/products/{product_id}",
                "PUT /api/admin/products/{product_id}",
                "DELETE /api/admin/products/{product_id}",
                "PUT /api/admin/products/bulk/status",
                "GET /api/admin/orders",
                "PUT /api/admin/orders/{order_id}/status",
                "GET /api/admin/orders/stats",
                "GET /api/admin/promotions",
                "POST /api/admin/promotions",
                "PUT /api/admin/promotions/{promotion_id}",
                "DELETE /api/admin/promotions/{promotion_id}",
                "GET /api/admin/dashboard/stats",
                "GET /api/admin/users"
            ],
            "features": [
                "Complete product management",
                "Advanced filtering and search",
                "Bulk operations",
                "Admin activity logging",
                "Dashboard statistics",
                "User management",
                "Product lifecycle management",
                "Inventory control",
                "SEO management",
                "Performance analytics",
                "Order management and tracking",
                "Status updates and workflow",
                "Order analytics and insights",
                "Promotion creation and management",
                "Promotion rules and conditions",
                "Promotion performance tracking"
            ]
        },
        message="Admin service is running"
    )