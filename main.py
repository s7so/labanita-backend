"""
Main FastAPI application for Labanita Egyptian Sweets Store API.
Provides REST API endpoints for products, categories, and core functionality.
"""

import uuid
from typing import List, Optional
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from database import get_db, create_tables, check_database_connection, Base
from core.config import settings
from core.responses import success_response, error_response
from core.exceptions import LabanitaException
from schemas import ProductResponse, CategoryResponse
from services import (
    get_products, get_product_by_id, get_categories, get_category_by_id,
    get_featured_products, get_new_arrivals, get_best_selling_products,
    search_products, get_products_count, get_categories_count
)
from auth.routes import router as auth_router
from user.routes import router as user_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    try:
        # Create database tables
        create_tables()
        print("✅ Database tables created successfully")
        
        # Check database connection
        if check_database_connection():
            print("✅ Database connection verified")
        else:
            print("❌ Database connection failed")
            
    except Exception as e:
        print(f"❌ Startup error: {str(e)}")
    
    yield
    
    print("🔄 Shutting down Labanita API...")

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    description="A modern, scalable backend API for the Labanita Egyptian sweets delivery application",
    version=settings.APP_VERSION,
    contact={"name": "Labanita Development Team", "email": "dev@labanita.com"},
    license_info={"name": "MIT License", "url": "https://opensource.org/licenses/MIT"},
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# Include authentication routes
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])

# Include user management routes
app.include_router(user_router, prefix="/api/user", tags=["User Management"])

# Global exception handler for custom exceptions
@app.exception_handler(LabanitaException)
async def labanita_exception_handler(request, exc: LabanitaException):
    """Handle custom Labanita exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response(
            message=exc.detail,
            error_code=exc.error_code,
            errors=exc.details
        ).dict()
    )

# =============================================================================
# HEALTH CHECK ENDPOINTS
# =============================================================================

@app.get("/health", tags=["Health"])
async def health_check():
    """Basic health check endpoint"""
    return success_response(
        data={
            "status": "healthy",
            "service": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT
        },
        message="Labanita API is running"
    )

@app.get("/api/health", tags=["Health"])
async def api_health_check():
    """API health check endpoint"""
    return success_response(
        data={
            "status": "healthy",
            "service": "Labanita API",
            "version": settings.APP_VERSION,
            "database": "connected" if check_database_connection() else "disconnected"
        },
        message="API is healthy"
    )

# =============================================================================
# PRODUCT ENDPOINTS
# =============================================================================

@app.get("/api/products/", response_model=List[ProductResponse], tags=["Products"])
async def read_products(
    skip: int = Query(0, ge=0, description="Number of products to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of products to return"),
    category_id: Optional[uuid.UUID] = Query(None, description="Filter by category ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    is_featured: Optional[bool] = Query(None, description="Filter by featured status"),
    is_new_arrival: Optional[bool] = Query(None, description="Filter by new arrival status"),
    is_best_selling: Optional[bool] = Query(None, description="Filter by best selling status"),
    db: Session = Depends(get_db)
):
    """Get list of products with optional filtering"""
    try:
        products = get_products(
            db=db,
            skip=skip,
            limit=limit,
            category_id=category_id,
            is_active=is_active,
            is_featured=is_featured,
            is_new_arrival=is_new_arrival,
            is_best_selling=is_best_selling
        )
        
        return [ProductResponse.from_orm(product) for product in products]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve products: {str(e)}")

@app.get("/api/products/{product_id}", response_model=ProductResponse, tags=["Products"])
async def read_product(product_id: uuid.UUID, db: Session = Depends(get_db)):
    """Get a specific product by ID"""
    try:
        product = get_product_by_id(db=db, product_id=product_id)
        if product is None:
            raise HTTPException(status_code=404, detail="Product not found")
        
        return ProductResponse.from_orm(product)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve product: {str(e)}")

@app.get("/api/products/featured", response_model=List[ProductResponse], tags=["Products"])
async def read_featured_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get featured products"""
    try:
        products = get_featured_products(db=db, skip=skip, limit=limit)
        return [ProductResponse.from_orm(product) for product in products]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve featured products: {str(e)}")

@app.get("/api/products/new-arrivals", response_model=List[ProductResponse], tags=["Products"])
async def read_new_arrivals(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get new arrival products"""
    try:
        products = get_new_arrivals(db=db, skip=skip, limit=limit)
        return [ProductResponse.from_orm(product) for product in products]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve new arrivals: {str(e)}")

@app.get("/api/products/best-selling", response_model=List[ProductResponse], tags=["Products"])
async def read_best_selling_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get best selling products"""
    try:
        products = get_best_selling_products(db=db, skip=skip, limit=limit)
        return [ProductResponse.from_orm(product) for product in products]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve best selling products: {str(e)}")

@app.get("/api/products/search", response_model=List[ProductResponse], tags=["Products"])
async def search_products_endpoint(
    q: str = Query(..., min_length=2, description="Search query"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Search products by name or description"""
    try:
        products = search_products(db=db, query=q, skip=skip, limit=limit)
        return [ProductResponse.from_orm(product) for product in products]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search products: {str(e)}")

@app.get("/api/products/count", tags=["Products"])
async def get_products_count_endpoint(
    category_id: Optional[uuid.UUID] = Query(None),
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db)
):
    """Get total count of products"""
    try:
        count = get_products_count(db=db, category_id=category_id, is_active=is_active)
        return success_response(data={"count": count}, message="Products count retrieved successfully")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get products count: {str(e)}")

# =============================================================================
# CATEGORY ENDPOINTS
# =============================================================================

@app.get("/api/categories/", response_model=List[CategoryResponse], tags=["Categories"])
async def read_categories(
    skip: int = Query(0, ge=0, description="Number of categories to skip"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of categories to return"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db)
):
    """Get list of categories with optional filtering"""
    try:
        categories = get_categories(db=db, skip=skip, limit=limit, is_active=is_active)
        return [CategoryResponse.from_orm(category) for category in categories]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve categories: {str(e)}")

@app.get("/api/categories/{category_id}", response_model=CategoryResponse, tags=["Categories"])
async def read_category(category_id: uuid.UUID, db: Session = Depends(get_db)):
    """Get a specific category by ID"""
    try:
        category = get_category_by_id(db=db, category_id=category_id)
        if category is None:
            raise HTTPException(status_code=404, detail="Category not found")
        
        return CategoryResponse.from_orm(category)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve category: {str(e)}")

@app.get("/api/categories/{category_id}/products", response_model=List[ProductResponse], tags=["Categories"])
async def read_category_products(
    category_id: uuid.UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get products by category ID"""
    try:
        products = get_products(db=db, skip=skip, limit=limit, category_id=category_id)
        return [ProductResponse.from_orm(product) for product in products]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve category products: {str(e)}")

@app.get("/api/categories/count", tags=["Categories"])
async def get_categories_count_endpoint(
    is_active: Optional[bool] = Query(None),
    db: Session = Depends(get_db)
):
    """Get total count of categories"""
    try:
        count = get_categories_count(db=db, is_active=is_active)
        return success_response(data={"count": count}, message="Categories count retrieved successfully")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get categories count: {str(e)}")

# =============================================================================
# ROOT ENDPOINT
# =============================================================================

@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information"""
    return success_response(
        data={
            "app_name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
            "docs_url": "/api/docs",
            "health_check": "/health",
            "available_modules": [
                "Authentication (/api/auth/*)",
                "User Management (/api/user/*)",
                "Products (/api/products/*)",
                "Categories (/api/categories/*)"
            ]
        },
        message="Welcome to Labanita API"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )