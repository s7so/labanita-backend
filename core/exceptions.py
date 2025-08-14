from fastapi import HTTPException, status
from typing import Optional, List, Dict, Any

class LabanitaException(HTTPException):
    """Base exception for Labanita API"""
    def __init__(
        self,
        status_code: int,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(status_code=status_code, detail=message)
        self.error_code = error_code
        self.details = details or {}

class AuthenticationException(LabanitaException):
    """Authentication related exceptions"""
    def __init__(self, message: str = "Authentication failed", error_code: str = "AUTH_FAILED"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, message=message, error_code=error_code)

class AuthorizationException(LabanitaException):
    """Authorization related exceptions"""
    def __init__(self, message: str = "Access denied", error_code: str = "ACCESS_DENIED"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, message=message, error_code=error_code)

class ValidationException(LabanitaException):
    """Validation related exceptions"""
    def __init__(self, message: str = "Validation failed", error_code: str = "VALIDATION_FAILED", details: Optional[Dict[str, Any]] = None):
        super().__init__(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, message=message, error_code=error_code, details=details)

class NotFoundException(LabanitaException):
    """Resource not found exceptions"""
    def __init__(self, message: str = "Resource not found", error_code: str = "NOT_FOUND"):
        super().__init__(status_code=status.HTTP_404_NOT_FOUND, message=message, error_code=error_code)

class ConflictException(LabanitaException):
    """Resource conflict exceptions"""
    def __init__(self, message: str = "Resource conflict", error_code: str = "CONFLICT"):
        super().__init__(status_code=status.HTTP_409_CONFLICT, message=message, error_code=error_code)

class RateLimitException(LabanitaException):
    """Rate limiting exceptions"""
    def __init__(self, message: str = "Rate limit exceeded", error_code: str = "RATE_LIMIT_EXCEEDED"):
        super().__init__(status_code=status.HTTP_429_TOO_MANY_REQUESTS, message=message, error_code=error_code)

class OTPException(LabanitaException):
    """OTP related exceptions"""
    def __init__(self, message: str = "OTP validation failed", error_code: str = "OTP_FAILED"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, message=message, error_code=error_code)

class PhoneNumberException(LabanitaException):
    """Phone number related exceptions"""
    def __init__(self, message: str = "Invalid phone number", error_code: str = "INVALID_PHONE"):
        super().__init__(status_code=status.HTTP_400_BAD_REQUEST, message=message, error_code=error_code)

class UserAlreadyExistsException(ConflictException):
    """User already exists exception"""
    def __init__(self, message: str = "User already exists", error_code: str = "USER_EXISTS"):
        super().__init__(message=message, error_code=error_code)

class InvalidCredentialsException(AuthenticationException):
    """Invalid credentials exception"""
    def __init__(self, message: str = "Invalid credentials", error_code: str = "INVALID_CREDENTIALS"):
        super().__init__(message=message, error_code=error_code)

class TokenExpiredException(AuthenticationException):
    """Token expired exception"""
    def __init__(self, message: str = "Token expired", error_code: str = "TOKEN_EXPIRED"):
        super().__init__(message=message, error_code=error_code)

class InvalidTokenException(AuthenticationException):
    """Invalid token exception"""
    def __init__(self, message: str = "Invalid token", error_code: str = "INVALID_TOKEN"):
        super().__init__(message=message, error_code=error_code)