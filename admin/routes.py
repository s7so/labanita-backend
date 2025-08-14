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
    AdminProductCreateRequest, AdminProductUpdateRequest
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
                "Performance analytics"
            ]
        },
        message="Admin service is running"
    )