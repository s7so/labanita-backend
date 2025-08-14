# Categories Package
# This package provides category management functionality for the Labanita backend

from .schemas import (
    CategoryResponse,
    CategoryListResponse,
    CategoryWithProductsResponse,
    ProductResponse,
    CategoryStatsResponse,
    CategoryHierarchyResponse,
    PaginationParams,
    PaginatedCategoriesResponse,
    PaginatedProductsResponse
)

from .services import CategoryService
from .routes import router as category_router

__all__ = [
    # Schemas
    "CategoryResponse",
    "CategoryListResponse", 
    "CategoryWithProductsResponse",
    "ProductResponse",
    "CategoryStatsResponse",
    "CategoryHierarchyResponse",
    "PaginationParams",
    "PaginatedCategoriesResponse",
    "PaginatedProductsResponse",
    
    # Services
    "CategoryService",
    
    # Routes
    "category_router"
]

__version__ = "1.0.0"
__author__ = "Labanita Team"
__description__ = "Category management system for Labanita backend"