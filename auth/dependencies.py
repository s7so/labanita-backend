from typing import Optional
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from database import get_db
from core.security import security
from core.exceptions import AuthenticationException, AuthorizationException
from auth.models import User
from auth.services import AuthService

# HTTP Bearer token scheme
security_scheme = HTTPBearer(auto_error=False)

def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: Session = Depends(get_db)
) -> User:
    """
    Extract and validate current user from JWT token
    """
    if not credentials:
        raise AuthenticationException("Authentication required")
    
    try:
        # Verify access token
        payload = security.verify_token(credentials.credentials, "access")
        user_id = payload.get("sub")
        
        if not user_id:
            raise AuthenticationException("Invalid token payload")
        
        # Get user from database
        auth_service = AuthService(db)
        user = auth_service.get_user_by_id(user_id)
        
        if not user:
            raise AuthenticationException("User not found")
        
        if not user.is_active:
            raise AuthenticationException("User account is deactivated")
        
        return user
        
    except Exception as e:
        raise AuthenticationException("Invalid or expired token")

def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Ensure current user is active
    """
    if not current_user.is_active:
        raise AuthenticationException("User account is deactivated")
    
    return current_user

def get_current_verified_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Ensure current user is verified
    """
    if not current_user.is_verified:
        raise AuthenticationException("User account is not verified")
    
    return current_user

def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Extract current user if token is provided, otherwise return None
    Useful for endpoints that work with or without authentication
    """
    if not credentials:
        return None
    
    try:
        payload = security.verify_token(credentials.credentials, "access")
        user_id = payload.get("sub")
        
        if not user_id:
            return None
        
        auth_service = AuthService(db)
        user = auth_service.get_user_by_id(user_id)
        
        if not user or not user.is_active:
            return None
        
        return user
        
    except Exception:
        return None

def get_auth_service(
    db: Session = Depends(get_db)
) -> AuthService:
    """
    Get authentication service instance
    """
    return AuthService(db)

def get_user_from_token(
    token: str,
    db: Session = Depends(get_db)
) -> User:
    """
    Extract user from token string (for internal use)
    """
    try:
        payload = security.verify_token(token, "access")
        user_id = payload.get("sub")
        
        if not user_id:
            raise AuthenticationException("Invalid token payload")
        
        auth_service = AuthService(db)
        user = auth_service.get_user_by_id(user_id)
        
        if not user:
            raise AuthenticationException("User not found")
        
        return user
        
    except Exception as e:
        raise AuthenticationException("Invalid token")

def require_admin_role(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Ensure current user has admin role
    TODO: Implement role-based access control
    """
    # For now, we'll use a simple check
    # In the future, implement proper role system
    if not hasattr(current_user, 'is_admin') or not getattr(current_user, 'is_admin', False):
        raise AuthorizationException("Admin access required")
    
    return current_user

def require_phone_verification(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Ensure current user has verified phone number
    """
    if not current_user.is_verified:
        raise AuthenticationException("Phone number verification required")
    
    return current_user

def get_client_info(request: Request) -> dict:
    """
    Extract client information from request
    """
    return {
        "ip_address": request.client.host if request.client else None,
        "user_agent": request.headers.get("user-agent"),
        "device_info": request.headers.get("x-device-info"),
    }

# Rate limiting dependency (basic implementation)
def check_rate_limit(
    request: Request,
    current_user: Optional[User] = Depends(get_optional_user)
) -> bool:
    """
    Basic rate limiting check
    TODO: Implement proper rate limiting with Redis
    """
    # For now, just return True
    # In production, implement proper rate limiting
    return True

# Optional authentication for public endpoints
def get_public_user(
    request: Request,
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Get user if authenticated, otherwise return None
    Useful for public endpoints that can work with or without authentication
    """
    auth_header = request.headers.get("authorization")
    
    if not auth_header or not auth_header.startswith("Bearer "):
        return None
    
    token = auth_header.split(" ")[1]
    
    try:
        return get_user_from_token(token, db)
    except Exception:
        return None