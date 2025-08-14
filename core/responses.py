from typing import Optional, Any, Dict, List
from datetime import datetime
from pydantic import BaseModel, Field

class BaseResponse(BaseModel):
    """Base response model for all API endpoints"""
    success: bool = Field(..., description="Indicates if the operation was successful")
    message: str = Field(..., description="Human-readable message about the operation")
    data: Optional[Any] = Field(None, description="Response data payload")
    errors: Optional[List[Dict[str, str]]] = Field(None, description="List of validation errors")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    error_code: Optional[str] = Field(None, description="Error code for client handling")

class SuccessResponse(BaseResponse):
    """Success response model"""
    success: bool = True
    data: Any = Field(..., description="Response data payload")

class ErrorResponse(BaseResponse):
    """Error response model"""
    success: bool = False
    data: Optional[Any] = None
    errors: List[Dict[str, str]] = Field(..., description="List of validation errors")

class PaginatedResponse(BaseResponse):
    """Paginated response model"""
    success: bool = True
    data: List[Any] = Field(..., description="List of items")
    pagination: Dict[str, Any] = Field(..., description="Pagination information")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "Data retrieved successfully",
                "data": [],
                "pagination": {
                    "page": 1,
                    "size": 10,
                    "total": 100,
                    "pages": 10,
                    "has_next": True,
                    "has_prev": False
                },
                "timestamp": "2024-01-15T12:00:00Z"
            }
        }

class ValidationErrorResponse(ErrorResponse):
    """Validation error response model"""
    success: bool = False
    message: str = "Validation failed"
    errors: List[Dict[str, str]] = Field(..., description="List of field validation errors")
    
    class Config:
        schema_extra = {
            "example": {
                "success": False,
                "message": "Validation failed",
                "data": None,
                "errors": [
                    {
                        "field": "phone_number",
                        "message": "Invalid phone number format"
                    }
                ],
                "timestamp": "2024-01-15T12:00:00Z",
                "error_code": "VALIDATION_FAILED"
            }
        }

class AuthenticationErrorResponse(ErrorResponse):
    """Authentication error response model"""
    success: bool = False
    message: str = "Authentication failed"
    data: Optional[Any] = None
    errors: List[Dict[str, str]] = Field(default=[], description="Authentication errors")
    error_code: str = "AUTH_FAILED"
    
    class Config:
        schema_extra = {
            "example": {
                "success": False,
                "message": "Authentication failed",
                "data": None,
                "errors": [],
                "timestamp": "2024-01-15T12:00:00Z",
                "error_code": "AUTH_FAILED"
            }
        }

class NotFoundErrorResponse(ErrorResponse):
    """Not found error response model"""
    success: bool = False
    message: str = "Resource not found"
    data: Optional[Any] = None
    errors: List[Dict[str, str]] = Field(default=[], description="Not found errors")
    error_code: str = "NOT_FOUND"

# Response helper functions
def success_response(data: Any = None, message: str = "Operation completed successfully") -> SuccessResponse:
    """Create a success response"""
    return SuccessResponse(data=data, message=message)

def error_response(message: str, errors: Optional[List[Dict[str, str]]] = None, error_code: Optional[str] = None) -> ErrorResponse:
    """Create an error response"""
    return ErrorResponse(message=message, errors=errors or [], error_code=error_code)

def validation_error_response(errors: List[Dict[str, str]]) -> ValidationErrorResponse:
    """Create a validation error response"""
    return ValidationErrorResponse(errors=errors)

def authentication_error_response(message: str = "Authentication failed") -> AuthenticationErrorResponse:
    """Create an authentication error response"""
    return AuthenticationErrorResponse(message=message)

def not_found_error_response(message: str = "Resource not found") -> NotFoundErrorResponse:
    """Create a not found error response"""
    return NotFoundErrorResponse(message=message)