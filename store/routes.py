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
from store.schemas import (
    StoreInfoResponse, DeliveryAreasResponse, DeliveryAreaResponse,
    DeliveryFeeResponse, OperatingHoursResponse, DeliveryFeeRequest
)
from store.services import StoreService

# Create router
router = APIRouter(prefix="/api/store", tags=["Store"])

# =============================================================================
# STORE INFO ENDPOINTS
# =============================================================================

@router.get("/info", response_model=StoreInfoResponse)
async def get_store_info(
    store_id: str = Query("main", description="Store ID to get info for"),
    db: Session = Depends(get_db)
):
    """
    Get store information
    
    Returns comprehensive store information including:
    - Store details and description
    - Contact information and social media
    - Physical location and coordinates
    - Store features and amenities
    - Store policies and terms
    
    The system will:
    - Retrieve store information by ID
    - Return contact details and location
    - Provide store features and policies
    - Include store status and branding
    """
    try:
        store_service = StoreService(db)
        store_info = store_service.get_store_info(store_id)
        return store_info
        
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get store info")

# =============================================================================
# DELIVERY AREA ENDPOINTS
# =============================================================================

@router.get("/delivery-areas", response_model=DeliveryAreasResponse)
async def get_delivery_areas(
    db: Session = Depends(get_db)
):
    """
    Get all delivery areas
    
    Returns comprehensive delivery area information including:
    - All available delivery areas
    - Area types and coverage
    - Cities and postal codes covered
    - Estimated delivery times
    - Active/inactive status
    
    The system will:
    - Retrieve all delivery areas
    - Calculate coverage summary
    - Provide area statistics
    - Return detailed area information
    """
    try:
        store_service = StoreService(db)
        delivery_areas = store_service.get_delivery_areas()
        return delivery_areas
        
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get delivery areas")

@router.get("/delivery-areas/{area_id}", response_model=DeliveryAreaResponse)
async def get_delivery_area_by_id(
    area_id: str = Path(..., description="Delivery area ID"),
    db: Session = Depends(get_db)
):
    """
    Get specific delivery area by ID
    
    Returns detailed information for a specific delivery area:
    - Area details and description
    - Coverage information
    - Delivery time estimates
    - Active status
    
    The system will:
    - Find delivery area by ID
    - Return detailed area information
    - Validate area exists
    """
    try:
        store_service = StoreService(db)
        delivery_area = store_service.get_delivery_area_by_id(area_id)
        return delivery_area
        
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get delivery area")

# =============================================================================
# DELIVERY FEE ENDPOINTS
# =============================================================================

@router.get("/delivery-fee/{area_id}", response_model=DeliveryFeeResponse)
async def get_delivery_fee(
    area_id: str = Path(..., description="Delivery area ID"),
    order_amount: float = Query(..., ge=0, description="Order subtotal amount"),
    order_weight: Optional[float] = Query(None, ge=0, description="Order total weight in kg"),
    delivery_date: Optional[str] = Query(None, description="Preferred delivery date (YYYY-MM-DD)"),
    is_express: bool = Query(False, description="Whether express delivery is requested"),
    db: Session = Depends(get_db)
):
    """
    Calculate delivery fee for a specific area and order
    
    Returns comprehensive delivery fee calculation including:
    - Base delivery fee
    - Final calculated fee
    - Fee calculation breakdown
    - Free delivery eligibility
    - Applied discounts and surcharges
    
    The system will:
    - Validate delivery area exists
    - Calculate base delivery fee
    - Apply order amount discounts
    - Add express delivery surcharges
    - Calculate weight-based fees
    - Determine free delivery eligibility
    - Provide detailed calculation breakdown
    """
    try:
        store_service = StoreService(db)
        
        # Parse delivery date if provided
        parsed_delivery_date = None
        if delivery_date:
            try:
                from datetime import datetime
                parsed_delivery_date = datetime.fromisoformat(delivery_date)
            except ValueError:
                raise ValidationException("Invalid delivery_date format. Use YYYY-MM-DD")
        
        # Create delivery fee request
        delivery_fee_request = DeliveryFeeRequest(
            area_id=area_id,
            order_amount=order_amount,
            order_weight=order_weight,
            delivery_date=parsed_delivery_date,
            is_express=is_express
        )
        
        # Calculate delivery fee
        delivery_fee = store_service.calculate_delivery_fee(delivery_fee_request)
        return delivery_fee
        
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to calculate delivery fee")

@router.post("/delivery-fee/calculate", response_model=DeliveryFeeResponse)
async def calculate_delivery_fee_post(
    request: DeliveryFeeRequest = Body(...),
    db: Session = Depends(get_db)
):
    """
    Calculate delivery fee using POST method
    
    Alternative endpoint for delivery fee calculation using POST body:
    - More flexible parameter handling
    - Better for complex calculations
    - Supports larger parameter sets
    
    The system will:
    - Validate request parameters
    - Calculate delivery fee
    - Return detailed fee breakdown
    """
    try:
        store_service = StoreService(db)
        delivery_fee = store_service.calculate_delivery_fee(request)
        return delivery_fee
        
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to calculate delivery fee")

# =============================================================================
# OPERATING HOURS ENDPOINTS
# =============================================================================

@router.get("/operating-hours", response_model=OperatingHoursResponse)
async def get_operating_hours(
    store_id: str = Query("main", description="Store ID to get operating hours for"),
    db: Session = Depends(get_db)
):
    """
    Get store operating hours
    
    Returns comprehensive operating hours information including:
    - Weekly operating schedule
    - Current open/closed status
    - Next open time
    - Special hours and holidays
    - Timezone information
    
    The system will:
    - Retrieve operating schedule
    - Determine current status
    - Calculate next open time
    - Include special hours
    - Provide holiday information
    """
    try:
        store_service = StoreService(db)
        operating_hours = store_service.get_operating_hours(store_id)
        return operating_hours
        
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get operating hours")

@router.get("/operating-hours/current-status", response_model=dict)
async def get_current_store_status(
    store_id: str = Query("main", description="Store ID to get status for"),
    db: Session = Depends(get_db)
):
    """
    Get current store status
    
    Returns current store status summary including:
    - Whether store is currently open
    - Next open time
    - Current store status
    - Delivery area information
    
    The system will:
    - Check current operating status
    - Calculate next open time
    - Provide status summary
    - Include delivery information
    """
    try:
        store_service = StoreService(db)
        store_status = store_service.get_store_status()
        return success_response(
            data=store_status,
            message="Store status retrieved successfully"
        )
        
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get store status")

# =============================================================================
# STORE STATUS ENDPOINTS
# =============================================================================

@router.get("/status", response_model=dict)
async def get_store_overview(
    db: Session = Depends(get_db)
):
    """
    Get comprehensive store overview
    
    Returns store overview including:
    - Store information summary
    - Current operating status
    - Delivery area summary
    - Quick status indicators
    
    The system will:
    - Retrieve store overview
    - Provide status summary
    - Include key metrics
    """
    try:
        store_service = StoreService(db)
        
        # Get all store information
        store_info = store_service.get_store_info()
        operating_hours = store_service.get_operating_hours()
        delivery_areas = store_service.get_delivery_areas()
        
        overview = {
            "store": {
                "name": store_info.store_name,
                "status": store_info.store_status,
                "description": store_info.store_description
            },
            "operating": {
                "is_open": operating_hours.is_currently_open,
                "next_open": operating_hours.next_open_time,
                "timezone": operating_hours.timezone
            },
            "delivery": {
                "total_areas": delivery_areas.total_count,
                "active_areas": delivery_areas.active_areas,
                "coverage": delivery_areas.coverage_summary
            },
            "last_updated": operating_hours.last_updated
        }
        
        return success_response(
            data=overview,
            message="Store overview retrieved successfully"
        )
        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get store overview")

# =============================================================================
# HEALTH CHECK ENDPOINT
# =============================================================================

@router.get("/health/check", response_model=dict)
async def store_service_health_check():
    """
    Store service health check
    
    Check if the store management service is running properly.
    """
    return success_response(
        data={
            "service": "store-management",
            "status": "healthy",
            "endpoints": [
                "GET /api/store/info",
                "GET /api/store/delivery-areas",
                "GET /api/store/delivery-areas/{area_id}",
                "GET /api/store/delivery-fee/{area_id}",
                "POST /api/store/delivery-fee/calculate",
                "GET /api/store/operating-hours",
                "GET /api/store/operating-hours/current-status",
                "GET /api/store/status"
            ],
            "features": [
                "Store information management",
                "Delivery area management",
                "Delivery fee calculation",
                "Operating hours management",
                "Store status monitoring",
                "Holiday and special hours",
                "Multi-area delivery support",
                "Flexible fee calculation",
                "Real-time status updates",
                "Timezone support"
            ]
        },
        message="Store service is running"
    )