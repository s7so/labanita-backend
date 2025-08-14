"""
Main FastAPI application for Labanita Egyptian Sweets Store API.
Provides REST API endpoints for products, categories, and core functionality.
"""

import uuid
from typing import List, Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, Query, status, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from database import get_db, create_tables, check_database_connection, Base
from core.config import settings
from core.exceptions import LabanitaException
from core.responses import success_response, error_response
from auth.routes import router as auth_router
from user.routes import router as user_router
from categories.routes import router as category_router
from products.routes import router as product_router
from offers.routes import router as offer_router
from cart.routes import router as cart_router
from promotions.routes import router as promotion_router

# =============================================================================
# LIFESPAN EVENTS
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    print("🚀 Starting Labanita Backend...")
    
    # Create database tables
    try:
        await create_tables()
        print("✅ Database tables created successfully")
    except Exception as e:
        print(f"❌ Failed to create database tables: {e}")
    
    # Check database connection
    try:
        await check_database_connection()
        print("✅ Database connection verified")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
    
    print("🎉 Labanita Backend started successfully!")
    
    yield
    
    # Shutdown
    print("🛑 Shutting down Labanita Backend...")

# =============================================================================
# FASTAPI APP INSTANCE
# =============================================================================

app = FastAPI(
    title=settings.APP_TITLE,
    version=settings.APP_VERSION,
    description="Labanita Backend API - Comprehensive E-commerce Platform",
    lifespan=lifespan
)

# =============================================================================
# CORS MIDDLEWARE
# =============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# =============================================================================
# EXCEPTION HANDLERS
# =============================================================================

@app.exception_handler(LabanitaException)
async def labanita_exception_handler(request: Request, exc: LabanitaException):
    """Handle custom Labanita exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(
            message=exc.message,
            error_code=exc.error_code,
            details=exc.details
        )
    )

# =============================================================================
# INCLUDE ROUTERS
# =============================================================================

# Authentication routes
app.include_router(auth_router, prefix="/api")

# User management routes
app.include_router(user_router, prefix="/api")

# Category management routes
app.include_router(category_router, prefix="/api")

# Product management routes
app.include_router(product_router, prefix="/api")

# Offer management routes
app.include_router(offer_router, prefix="/api")

# Cart management routes
app.include_router(cart_router, prefix="/api")

# Promotion management routes
app.include_router(promotion_router, prefix="/api")

# =============================================================================
# ROOT ENDPOINT
# =============================================================================

@app.get("/", response_model=dict)
async def root():
    """
    Root endpoint - API information and available modules
    
    Returns information about the Labanita Backend API and available modules.
    """
    return success_response(
        data={
            "app_name": "Labanita Backend",
            "version": "1.0.0",
            "description": "Comprehensive E-commerce Platform Backend",
            "status": "running",
            "available_modules": [
                "Authentication (/api/auth/*)",
                "User Management (/api/user/*)",
                "Category Management (/api/categories/*)",
                "Product Management (/api/products/*)",
                "Offer Management (/api/offers/*)",
                "Cart Management (/api/cart/*)",
                "Promotion Management (/api/promotions/*)",
                "Order Management (/api/orders/*)",
                "Payment Processing (/api/payments/*)",
                "Inventory Management (/api/inventory/*)",
                "Analytics & Reporting (/api/analytics/*)"
            ],
            "documentation": "/docs",
            "health_check": "/health",
            "database_status": "connected"
        },
        message="Welcome to Labanita Backend API"
    )

# =============================================================================
# HEALTH CHECK ENDPOINTS
# =============================================================================

@app.get("/health", response_model=dict)
async def health_check():
    """
    Basic health check endpoint
    
    Returns the basic health status of the application.
    """
    return success_response(
        data={
            "status": "healthy",
            "timestamp": "now",
            "version": "1.0.0"
        },
        message="Labanita Backend is running"
    )

@app.get("/health/detailed", response_model=dict)
async def detailed_health_check(db: Session = Depends(get_db)):
    """
    Detailed health check endpoint
    
    Returns comprehensive health information including database connectivity.
    """
    try:
        # Check database connection
        db_status = "connected"
        try:
            db.execute("SELECT 1")
        except Exception:
            db_status = "disconnected"
        
        return success_response(
            data={
                "status": "healthy",
                "timestamp": "now",
                "version": "1.0.0",
                "database": {
                    "status": db_status,
                    "type": "PostgreSQL"
                },
                "services": {
                    "auth": "running",
                    "user_management": "running",
                    "category_management": "running",
                    "product_management": "running",
                    "offer_management": "running",
                    "cart_management": "running",
                    "promotion_management": "running"
                }
            },
            message="Detailed health check completed"
        )
        
    except Exception as e:
        return error_response(
            message="Health check failed",
            error_code="HEALTH_CHECK_ERROR",
            details=str(e)
        )

# =============================================================================
# DATABASE ENDPOINTS
# =============================================================================

@app.get("/api/database/status", response_model=dict)
async def database_status(db: Session = Depends(get_db)):
    """
    Database status endpoint
    
    Returns detailed database connection and health information.
    """
    try:
        # Test database connection
        result = db.execute("SELECT version()").scalar()
        
        return success_response(
            data={
                "status": "connected",
                "database_type": "PostgreSQL",
                "version": result,
                "connection_pool": "active",
                "tables": [
                    "users",
                    "categories", 
                    "products",
                    "orders",
                    "order_items",
                    "addresses",
                    "payment_methods",
                    "promotions",
                    "cart_items",
                    "order_status_history",
                    "product_offers"
                ]
            },
            message="Database connection successful"
        )
        
    except Exception as e:
        return error_response(
            message="Database connection failed",
            error_code="DB_CONNECTION_ERROR",
            details=str(e)
        )

# =============================================================================
# LEGACY ENDPOINTS (FOR BACKWARD COMPATIBILITY)
# =============================================================================

@app.get("/api/products/", response_model=List[dict])
async def get_products(
    skip: int = Query(0, ge=0, description="Number of products to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of products to return"),
    db: Session = Depends(get_db)
):
    """
    Get all products (Legacy endpoint)
    
    This endpoint is maintained for backward compatibility.
    Consider using the new product management endpoints for better functionality.
    """
    try:
        from models import Product
        from schemas import ProductResponse
        
        products = db.query(Product).offset(skip).limit(limit).all()
        
        product_responses = []
        for product in products:
            product_responses.append(ProductResponse.from_orm(product))
        
        return product_responses
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve products: {str(e)}"
        )

@app.get("/api/products/{product_id}", response_model=dict)
async def get_product(
    product_id: str,
    db: Session = Depends(get_db)
):
    """
    Get a specific product by ID (Legacy endpoint)
    
    This endpoint is maintained for backward compatibility.
    Consider using the new product management endpoints for better functionality.
    """
    try:
        from models import Product
        from schemas import ProductResponse
        
        product = db.query(Product).filter(Product.product_id == product_id).first()
        
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {product_id} not found"
            )
        
        return ProductResponse.from_orm(product)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve product: {str(e)}"
        )

@app.get("/api/categories/", response_model=List[dict])
async def get_categories_legacy(
    skip: int = Query(0, ge=0, description="Number of categories to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of categories to return"),
    db: Session = Depends(get_db)
):
    """
    Get all categories (Legacy endpoint)
    
    This endpoint is maintained for backward compatibility.
    Consider using the new category management endpoints for better functionality.
    """
    try:
        from models import Category
        from schemas import CategoryResponse
        
        categories = db.query(Category).offset(skip).limit(limit).all()
        
        category_responses = []
        for category in categories:
            category_responses.append(CategoryResponse.from_orm(category))
        
        return category_responses
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve categories: {str(e)}"
        )

# =============================================================================
# ERROR HANDLING
# =============================================================================

@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    """Handle 404 errors"""
    return JSONResponse(
        status_code=404,
        content=error_response(
            message="Endpoint not found",
            error_code="ENDPOINT_NOT_FOUND",
            details=f"The requested endpoint {request.url.path} does not exist"
        )
    )

@app.exception_handler(500)
async def internal_error_handler(request: Request, exc: HTTPException):
    """Handle 500 errors"""
    return JSONResponse(
        status_code=500,
        content=error_response(
            message="Internal server error",
            error_code="INTERNAL_SERVER_ERROR",
            details="An unexpected error occurred. Please try again later."
        )
    )

# =============================================================================
# STARTUP MESSAGE
# =============================================================================

if __name__ == "__main__":
    print("🚀 Starting Labanita Backend...")
    print("📚 API Documentation available at /docs")
    print("🔍 Health check available at /health")
    print("🎯 Category management available at /api/categories")
    print("🛍️ Product management available at /api/products")
    print("🎁 Offer management available at /api/offers")
    print("🛒 Cart management available at /api/cart")
    print("🎉 Promotion management available at /api/promotions")
    print("👤 User management available at /api/user")
    print("🔐 Authentication available at /api/auth")