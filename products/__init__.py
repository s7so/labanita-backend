# Products Package
# This package provides product management functionality for the Labanita backend

from .schemas import (
    ProductResponse,
    ProductListResponse,
    ProductDetailResponse,
    FeaturedProductsResponse,
    NewArrivalsResponse,
    BestSellingProductsResponse,
    ProductSearchResponse,
    ProductFilterResponse,
    PaginatedProductsResponse,
    ProductStatsResponse,
    ProductAnalyticsResponse,
    RelatedProductsResponse,
    ProductFilter,
    ProductSearch,
    PaginationParams
)

from .services import ProductService
from .routes import router as product_router

__all__ = [
    # Schemas
    "ProductResponse",
    "ProductListResponse",
    "ProductDetailResponse",
    "FeaturedProductsResponse",
    "NewArrivalsResponse",
    "BestSellingProductsResponse",
    "ProductSearchResponse",
    "ProductFilterResponse",
    "PaginatedProductsResponse",
    "ProductStatsResponse",
    "ProductAnalyticsResponse",
    "RelatedProductsResponse",
    "ProductFilter",
    "ProductSearch",
    "PaginationParams",
    
    # Services
    "ProductService",
    
    # Routes
    "product_router"
]

__version__ = "1.0.0"
__author__ = "Labanita Team"
__description__ = "Product management system for Labanita backend"