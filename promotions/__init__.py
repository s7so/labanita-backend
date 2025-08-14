# Promotions Package
# This package provides promotion management functionality for the Labanita backend

from .schemas import (
    PromotionResponse,
    ActivePromotionsResponse,
    PromotionValidationResponse,
    PromotionApplicationResponse,
    PromotionRemovalResponse,
    PromotionValidationRequest,
    PromotionApplicationRequest,
    PromotionRemovalRequest,
    UserPromotionResponse,
    UserPromotionsResponse,
    PromotionCreateRequest,
    PromotionUpdateRequest,
    PromotionFilter,
    PaginationParams,
    PaginatedPromotionsResponse,
    PromotionStatsResponse,
    PromotionAnalyticsResponse
)

from .services import PromotionService
from .routes import router as promotion_router

__all__ = [
    # Schemas
    "PromotionResponse",
    "ActivePromotionsResponse",
    "PromotionValidationResponse",
    "PromotionApplicationResponse",
    "PromotionRemovalResponse",
    "PromotionValidationRequest",
    "PromotionApplicationRequest",
    "PromotionRemovalRequest",
    "UserPromotionResponse",
    "UserPromotionsResponse",
    "PromotionCreateRequest",
    "PromotionUpdateRequest",
    "PromotionFilter",
    "PaginationParams",
    "PaginatedPromotionsResponse",
    "PromotionStatsResponse",
    "PromotionAnalyticsResponse",
    
    # Services
    "PromotionService",
    
    # Routes
    "promotion_router"
]

__version__ = "1.0.0"
__author__ = "Labanita Team"
__description__ = "Promotion management system for Labanita backend"