from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from sqlalchemy.orm import Session

from database import get_db
from core.responses import success_response, error_response
from core.exceptions import (
    UserAlreadyExistsException, 
    InvalidCredentialsException, 
    OTPException,
    PhoneNumberException,
    NotFoundException
)
from auth.models import User
from auth.schemas import (
    PhoneNumberRequest, OTPVerificationRequest, UserRegistrationRequest,
    UserLoginRequest, PasswordResetRequest, UserProfileUpdateRequest,
    RefreshTokenRequest, SocialLoginRequest, UserProfileResponse,
    LoginResponse, RegistrationResponse, TokenResponse, OTPResponse
)
from auth.services import AuthService
from auth.dependencies import (
    get_current_user, get_current_active_user, get_current_verified_user,
    get_auth_service, get_client_info, require_phone_verification
)

# Create router
router = APIRouter(prefix="/api/auth", tags=["Authentication"])

# =============================================================================
# PHONE AUTHENTICATION ENDPOINTS
# =============================================================================

@router.post("/send-otp", response_model=OTPResponse)
async def send_otp(
    request: PhoneNumberRequest,
    otp_type: str = "REGISTRATION",  # REGISTRATION, LOGIN, RESET_PASSWORD
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """
    Send OTP to phone number for verification
    """
    try:
        auth_service = AuthService(db)
        result = auth_service.generate_and_send_otp(request.phone_number, otp_type)
        
        # Add cleanup task to background
        if background_tasks:
            background_tasks.add_task(auth_service.cleanup_expired_otps)
        
        return result
        
    except (PhoneNumberException, UserAlreadyExistsException, NotFoundException) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to send OTP")

@router.post("/resend-otp", response_model=OTPResponse)
async def resend_otp(
    request: PhoneNumberRequest,
    otp_type: str = "REGISTRATION",
    db: Session = Depends(get_db)
):
    """
    Resend OTP to phone number
    """
    try:
        auth_service = AuthService(db)
        result = auth_service.resend_otp(request.phone_number, otp_type)
        return result
        
    except OTPException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to resend OTP")

@router.post("/verify-otp", response_model=LoginResponse)
async def verify_otp(
    request: OTPVerificationRequest,
    db: Session = Depends(get_db)
):
    """
    Verify OTP and login/register user
    """
    try:
        auth_service = AuthService(db)
        
        # Verify OTP
        user = auth_service.verify_otp(
            request.phone_number, 
            request.otp_code, 
            request.otp_type
        )
        
        # Create user session
        tokens = auth_service.create_user_session(user)
        
        # Get user profile
        profile = auth_service.get_user_profile(str(user.user_id))
        
        return LoginResponse(
            user=profile,
            tokens=tokens,
            message="OTP verified successfully"
        )
        
    except OTPException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to verify OTP")

# =============================================================================
# USER REGISTRATION & LOGIN ENDPOINTS
# =============================================================================

@router.post("/register", response_model=RegistrationResponse)
async def register_user(
    request: UserRegistrationRequest,
    db: Session = Depends(get_db)
):
    """
    Register new user with phone number and optional password
    """
    try:
        auth_service = AuthService(db)
        
        # Hash password if provided
        password_hash = None
        if request.password:
            from core.security import security
            password_hash = security.get_password_hash(request.password)
        
        # Create user data
        user_data = request.dict()
        user_data["password_hash"] = password_hash
        
        # Register user
        user = auth_service.register_user(user_data)
        
        # Get user profile
        profile = auth_service.get_user_profile(str(user.user_id))
        
        return RegistrationResponse(
            user=profile,
            message="User registered successfully. Please verify your phone number."
        )
        
    except UserAlreadyExistsException as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to register user")

@router.post("/login", response_model=LoginResponse)
async def login_user(
    request: UserLoginRequest,
    req: Request,
    db: Session = Depends(get_db)
):
    """
    Login user with phone number and optional password
    """
    try:
        auth_service = AuthService(db)
        
        # Login user
        user = auth_service.login_user(request.phone_number, request.password)
        
        # Get client info
        client_info = get_client_info(req)
        
        # Create user session
        tokens = auth_service.create_user_session(
            user,
            device_info=client_info.get("device_info"),
            ip_address=client_info.get("ip_address"),
            user_agent=client_info.get("user_agent")
        )
        
        # Get user profile
        profile = auth_service.get_user_profile(str(user.user_id))
        
        return LoginResponse(
            user=profile,
            tokens=tokens,
            message="Login successful"
        )
        
    except InvalidCredentialsException as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to login")

# =============================================================================
# TOKEN MANAGEMENT ENDPOINTS
# =============================================================================

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token
    """
    try:
        auth_service = AuthService(db)
        result = auth_service.refresh_access_token(request.refresh_token)
        return result
        
    except InvalidCredentialsException as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to refresh token")

@router.post("/logout")
async def logout_user(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """
    Logout user by deactivating session
    """
    try:
        auth_service = AuthService(db)
        success = auth_service.logout_user(request.refresh_token)
        
        if success:
            return success_response(message="Logout successful")
        else:
            return error_response(message="Logout failed")
            
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to logout")

@router.post("/logout-all")
async def logout_all_sessions(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Logout user from all active sessions
    """
    try:
        auth_service = AuthService(db)
        success = auth_service.logout_all_sessions(str(current_user.user_id))
        
        if success:
            return success_response(message="Logged out from all sessions")
        else:
            return error_response(message="Logout failed")
            
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to logout")

# =============================================================================
# USER PROFILE ENDPOINTS
# =============================================================================

@router.get("/profile", response_model=UserProfileResponse)
async def get_profile(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get current user profile
    """
    try:
        auth_service = AuthService(db)
        profile = auth_service.get_user_profile(str(current_user.user_id))
        return profile
        
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get profile")

@router.put("/profile", response_model=UserProfileResponse)
async def update_profile(
    request: UserProfileUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update current user profile
    """
    try:
        auth_service = AuthService(db)
        
        # Hash password if provided
        update_data = request.dict(exclude_unset=True)
        if "password" in update_data:
            from core.security import security
            update_data["password_hash"] = security.get_password_hash(update_data.pop("password"))
        
        profile = auth_service.update_user_profile(str(current_user.user_id), update_data)
        return profile
        
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update profile")

@router.delete("/profile")
async def delete_account(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete current user account (soft delete)
    """
    try:
        auth_service = AuthService(db)
        success = auth_service.delete_user_account(str(current_user.user_id))
        
        if success:
            return success_response(message="Account deleted successfully")
        else:
            return error_response(message="Failed to delete account")
            
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete account")

# =============================================================================
# PASSWORD MANAGEMENT ENDPOINTS
# =============================================================================

@router.post("/password/reset")
async def reset_password(
    request: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """
    Reset user password using phone number
    """
    try:
        auth_service = AuthService(db)
        success = auth_service.reset_password(request.phone_number, request.new_password)
        
        if success:
            return success_response(message="Password reset successfully")
        else:
            return error_response(message="Failed to reset password")
            
    except NotFoundException as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to reset password")

@router.post("/password/change")
async def change_password(
    current_password: str,
    new_password: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Change current user password
    """
    try:
        auth_service = AuthService(db)
        success = auth_service.change_password(
            str(current_user.user_id), 
            current_password, 
            new_password
        )
        
        if success:
            return success_response(message="Password changed successfully")
        else:
            return error_response(message="Failed to change password")
            
    except InvalidCredentialsException as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to change password")

# =============================================================================
# SOCIAL LOGIN ENDPOINTS (TODO: Implement)
# =============================================================================

@router.post("/login/facebook")
async def facebook_login(
    request: SocialLoginRequest,
    db: Session = Depends(get_db)
):
    """
    Login with Facebook (TODO: Implement)
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, 
        detail="Facebook login not implemented yet"
    )

@router.post("/login/google")
async def google_login(
    request: SocialLoginRequest,
    db: Session = Depends(get_db)
):
    """
    Login with Google (TODO: Implement)
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, 
        detail="Google login not implemented yet"
    )

# =============================================================================
# UTILITY ENDPOINTS
# =============================================================================

@router.get("/sessions")
async def get_user_sessions(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get all active sessions for current user
    """
    try:
        auth_service = AuthService(db)
        sessions = auth_service.get_user_sessions(str(current_user.user_id))
        
        # Return session info (without sensitive data)
        session_info = []
        for session in sessions:
            session_info.append({
                "session_id": str(session.session_id),
                "device_info": session.device_info,
                "ip_address": session.ip_address,
                "created_at": session.created_at,
                "last_used_at": session.last_used_at,
                "expires_at": session.expires_at
            })
        
        return success_response(data=session_info, message="Sessions retrieved successfully")
        
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get sessions")

@router.get("/health")
async def auth_health_check():
    """
    Authentication service health check
    """
    return success_response(
        data={"status": "healthy", "service": "authentication"},
        message="Authentication service is running"
    )