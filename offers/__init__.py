# Offers Package
# This package provides offer management functionality for the Labanita backend

from .schemas import (
    OfferResponse,
    ProductOfferResponse,
    ActiveOffersResponse,
    OfferListResponse,
    OfferDetailResponse,
    PaginatedOffersResponse,
    OfferStatsResponse,
    OfferAnalyticsResponse,
    OfferValidationResponse,
    OfferCreateRequest,
    OfferUpdateRequest,
    OfferFilter,
    PaginationParams
)

from .services import OfferService
from .routes import router as offer_router

__all__ = [
    # Schemas
    "OfferResponse",
    "ProductOfferResponse",
    "ActiveOffersResponse",
    "OfferListResponse",
    "OfferDetailResponse",
    "PaginatedOffersResponse",
    "OfferStatsResponse",
    "OfferAnalyticsResponse",
    "OfferValidationResponse",
    "OfferCreateRequest",
    "OfferUpdateRequest",
    "OfferFilter",
    "PaginationParams",
    
    # Services
    "OfferService",
    
    # Routes
    "offer_router"
]

__version__ = "1.0.0"
__author__ = "Labanita Team"
__description__ = "Offer management system for Labanita backend"