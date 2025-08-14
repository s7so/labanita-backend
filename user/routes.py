from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.orm import Session

from database import get_db
from core.responses import success_response, error_response
from core.exceptions import (
    NotFoundException, 
    ValidationException, 
    ConflictException,
    InvalidCredentialsException
)
from auth.dependencies import get_current_active_user, get_current_verified_user
from auth.models import User
from user.schemas import (
    UserProfileUpdateRequest, PasswordChangeRequest, AccountDeletionRequest,
    UserProfileResponse, UserPointsResponse, UserPointsHistoryResponse, UserStatsResponse,
    AddressCreateRequest, AddressUpdateRequest, AddressResponse, AddressListResponse
)
from user.services import UserService

# Create router
router = APIRouter(prefix="/api/user", tags=["User Management"])

# =============================================================================
# PROFILE MANAGEMENT ENDPOINTS
# =============================================================================

@router.get("/profile", response_model=UserProfileResponse)
async def get_user_profile(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get current user profile
    
    Returns the complete profile information for the authenticated user.
    """
    try:
        user_service = UserService(db)
        profile = user_service.get_user_profile(str(current_user.user_id))
        return profile
        
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get profile")

@router.put("/profile", response_model=UserProfileResponse)
async def update_user_profile(
    request: UserProfileUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update current user profile
    
    Update user information including name, email, and phone number.
    Email and phone number must be unique across all users.
    """
    try:
        user_service = UserService(db)
        
        # Convert request to internal format
        update_data = request.dict(exclude_unset=True)
        
        profile = user_service.update_user_profile(str(current_user.user_id), update_data)
        return profile
        
    except ConflictException as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update profile")

@router.post("/profile/password", response_model=dict)
async def change_password(
    request: PasswordChangeRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Change user password
    
    Change the current user's password. Requires current password verification.
    """
    try:
        user_service = UserService(db)
        
        success = user_service.change_user_password(
            str(current_user.user_id),
            request.current_password,
            request.new_password
        )
        
        if success:
            return success_response(
                message="Password changed successfully",
                data={"user_id": str(current_user.user_id)}
            )
        else:
            return error_response(message="Failed to change password")
            
    except InvalidCredentialsException as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to change password")

# =============================================================================
# ADDRESS MANAGEMENT ENDPOINTS
# =============================================================================

@router.get("/addresses", response_model=AddressListResponse)
async def get_user_addresses(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get all addresses for the current user
    
    Returns a list of all addresses associated with the authenticated user,
    including which one is set as default.
    """
    try:
        user_service = UserService(db)
        addresses = user_service.get_user_addresses(str(current_user.user_id))
        return addresses
        
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get addresses")

@router.post("/addresses", response_model=AddressResponse)
async def create_user_address(
    request: AddressCreateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Create a new address for the current user
    
    Creates a new delivery address. If set as default, it will automatically
    unset any existing default address.
    """
    try:
        user_service = UserService(db)
        
        # Convert request to internal format
        address_data = AddressCreate(
            user_id=str(current_user.user_id),
            address_type=request.address_type,
            full_name=request.full_name,
            phone_number=request.phone_number,
            email=request.email,
            street_address=request.street_address,
            building_number=request.building_number,
            flat_number=request.flat_number,
            city=request.city,
            area=request.area,
            is_default=request.is_default
        )
        
        address = user_service.create_user_address(str(current_user.user_id), address_data)
        return address
        
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to create address")

@router.put("/addresses/{address_id}", response_model=AddressResponse)
async def update_user_address(
    address_id: str = Path(..., description="ID of the address to update"),
    request: AddressUpdateRequest = None,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update an existing address for the current user
    
    Updates the specified address with new information.
    Only fields provided in the request will be updated.
    """
    try:
        user_service = UserService(db)
        
        # Convert request to internal format
        update_data = AddressUpdate(**request.dict(exclude_unset=True)) if request else AddressUpdate()
        
        address = user_service.update_user_address(str(current_user.user_id), address_id, update_data)
        return address
        
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update address")

@router.delete("/addresses/{address_id}", response_model=dict)
async def delete_user_address(
    address_id: str = Path(..., description="ID of the address to delete"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete an address for the current user
    
    Deletes the specified address. If it's the default address,
    another address will automatically be set as default.
    Cannot delete the only address.
    """
    try:
        user_service = UserService(db)
        
        success = user_service.delete_user_address(str(current_user.user_id), address_id)
        
        if success:
            return success_response(
                message="Address deleted successfully",
                data={"address_id": address_id}
            )
        else:
            return error_response(message="Failed to delete address")
            
    except ValidationException as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete address")

@router.put("/addresses/{address_id}/set-default", response_model=AddressResponse)
async def set_default_address(
    address_id: str = Path(..., description="ID of the address to set as default"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Set an address as the default for the current user
    
    Sets the specified address as the default delivery address.
    Any previously default address will be unset.
    """
    try:
        user_service = UserService(db)
        
        address = user_service.set_default_address(str(current_user.user_id), address_id)
        return address
        
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to set default address")

@router.get("/addresses/default", response_model=AddressResponse)
async def get_default_address(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get the default address for the current user
    
    Returns the address marked as default for delivery.
    """
    try:
        user_service = UserService(db)
        
        address = user_service.get_default_address(str(current_user.user_id))
        if not address:
            raise NotFoundException("No default address found")
        
        return address
        
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get default address")

# =============================================================================
# ACCOUNT MANAGEMENT ENDPOINTS
# =============================================================================

@router.delete("/account", response_model=dict)
async def delete_user_account(
    request: AccountDeletionRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete user account
    
    Permanently deactivate the user account. This is a soft delete operation.
    User data is retained but the account becomes inactive.
    
    **Warning:** This action cannot be undone immediately.
    """
    try:
        user_service = UserService(db)
        
        success = user_service.delete_user_account(
            str(current_user.user_id),
            request.reason
        )
        
        if success:
            return success_response(
                message="Account deleted successfully",
                data={
                    "user_id": str(current_user.user_id),
                    "deletion_date": "now",
                    "data_retention_period": 30,
                    "reactivation_deadline": "30 days from now"
                }
            )
        else:
            return error_response(message="Failed to delete account")
            
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete account")

@router.post("/account/reactivate", response_model=dict)
async def reactivate_user_account(
    current_user: User = Depends(get_current_user),  # Allow inactive users
    db: Session = Depends(get_db)
):
    """
    Reactivate deleted user account
    
    Reactivate a previously deleted user account.
    """
    try:
        user_service = UserService(db)
        
        success = user_service.reactivate_user_account(str(current_user.user_id))
        
        if success:
            return success_response(
                message="Account reactivated successfully",
                data={"user_id": str(current_user.user_id)}
            )
        else:
            return error_response(message="Failed to reactivate account")
            
    except ConflictException as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to reactivate account")

# =============================================================================
# POINTS MANAGEMENT ENDPOINTS
# =============================================================================

@router.get("/points", response_model=UserPointsResponse)
async def get_user_points(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get user points information
    
    Returns current points balance, expiry information, and points statistics.
    """
    try:
        user_service = UserService(db)
        points = user_service.get_user_points(str(current_user.user_id))
        return points
        
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get points")

@router.get("/points/history", response_model=List[UserPointsHistoryResponse])
async def get_user_points_history(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of records to return"),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get user points history
    
    Returns a paginated list of points transactions including earned, used, and expired points.
    """
    try:
        user_service = UserService(db)
        history = user_service.get_user_points_history(
            str(current_user.user_id),
            skip=skip,
            limit=limit
        )
        return history
        
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get points history")

# =============================================================================
# USER STATISTICS ENDPOINTS
# =============================================================================

@router.get("/statistics", response_model=UserStatsResponse)
async def get_user_statistics(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get user statistics and analytics
    
    Returns comprehensive user statistics including order history, spending patterns,
    and favorite categories.
    """
    try:
        user_service = UserService(db)
        stats = user_service.get_user_statistics(str(current_user.user_id))
        return stats
        
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get statistics")

# =============================================================================
# ADDITIONAL USER ENDPOINTS
# =============================================================================

@router.get("/profile/verification-status", response_model=dict)
async def get_verification_status(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get user verification status
    
    Returns detailed verification information for the user account.
    """
    try:
        return success_response(
            data={
                "user_id": str(current_user.user_id),
                "phone_verified": current_user.is_verified,
                "email_verified": current_user.email is not None,
                "facebook_connected": current_user.facebook_id is not None,
                "google_connected": current_user.google_id is not None,
                "verification_level": "full" if current_user.is_verified else "basic"
            },
            message="Verification status retrieved successfully"
        )
        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get verification status")

@router.get("/profile/security", response_model=dict)
async def get_security_info(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get user security information
    
    Returns security-related information for the user account.
    """
    try:
        return success_response(
            data={
                "user_id": str(current_user.user_id),
                "has_password": current_user.password_hash is not None,
                "last_password_change": "unknown",  # TODO: Add to user model
                "two_factor_enabled": False,  # TODO: Implement 2FA
                "login_history": "available",  # TODO: Implement login history
                "security_score": 85  # TODO: Calculate based on security measures
            },
            message="Security information retrieved successfully"
        )
        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get security information")

@router.post("/profile/export", response_model=dict)
async def export_user_data(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Export user data
    
    Request export of all user data in a structured format.
    This is typically an asynchronous operation.
    """
    try:
        # TODO: Implement actual data export functionality
        return success_response(
            data={
                "user_id": str(current_user.user_id),
                "export_requested": True,
                "export_id": "exp_12345",
                "estimated_completion": "24 hours",
                "download_url": None,
                "status": "pending"
            },
            message="Data export requested successfully"
        )
        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to request data export")

# =============================================================================
# UTILITY ENDPOINTS
# =============================================================================

@router.get("/health", response_model=dict)
async def user_service_health_check():
    """
    User service health check
    
    Check if the user management service is running properly.
    """
    return success_response(
        data={
            "service": "user-management",
            "status": "healthy",
            "endpoints": [
                "GET /api/user/profile",
                "PUT /api/user/profile",
                "DELETE /api/user/account",
                "GET /api/user/points",
                "GET /api/user/statistics",
                "GET /api/user/addresses",
                "POST /api/user/addresses",
                "PUT /api/user/addresses/{address_id}",
                "DELETE /api/user/addresses/{address_id}",
                "PUT /api/user/addresses/{address_id}/set-default"
            ]
        },
        message="User service is running"
    )