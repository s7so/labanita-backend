# Admin Package
# This package provides administrative functionality for the Labanita backend

from .schemas import (
    AdminProductResponse,
    AdminProductListResponse,
    AdminProductFilter,
    AdminProductCreateRequest,
    AdminProductUpdateRequest,
    AdminUserResponse,
    AdminUserListResponse,
    AdminDashboardStats,
    AdminActivityLog
)

from .services import AdminService
from .routes import router as admin_router

__all__ = [
    # Schemas
    "AdminProductResponse",
    "AdminProductListResponse",
    "AdminProductFilter",
    "AdminProductCreateRequest",
    "AdminProductUpdateRequest",
    "AdminUserResponse",
    "AdminUserListResponse",
    "AdminDashboardStats",
    "AdminActivityLog",
    
    # Services
    "AdminService",
    
    # Routes
    "admin_router"
]

__version__ = "1.0.0"
__author__ = "Labanita Team"
__description__ = "Administrative management system for Labanita backend"