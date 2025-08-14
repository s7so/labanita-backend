"""
Main FastAPI application for Labanita Egyptian Sweets Store API.
Provides REST API endpoints for products, categories, and core functionality.
"""

import uuid
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database import get_db, create_tables, check_database_connection, Base
from schemas import ProductResponse, CategoryResponse
from services import (
    get_products,
    get_product_by_id,
    get_categories,
    get_category_by_id,
    get_featured_products,
    get_new_arrivals,
    get_best_selling_products,
    search_products,
    get_products_count,
    get_categories_count
)


# ========================================
# FASTAPI APPLICATION SETUP
# ========================================

# Create FastAPI application instance
app = FastAPI(
    title="Labanita Egyptian Sweets Store API",
    description="A modern, scalable backend API for the Labanita Egyptian sweets delivery application",
    version="1.0.0",
    contact={
        "name": "Labanita Development Team",
        "email": "dev@labanita.com"
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT"
    }
)

# Add CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ========================================
# STARTUP EVENT HANDLER
# ========================================

@app.on_event("startup")
async def startup_event():
    """
    Startup event handler that runs when the application starts.
    Creates database tables and performs health checks.
    """
    try:
        # Create database tables if they don't exist
        create_tables()
        print("✅ Database tables created successfully")
        
        # Check database connection
        if check_database_connection():
            print("✅ Database connection verified")
        else:
            print("❌ Database connection failed")
            
    except Exception as e:
        print(f"❌ Startup error: {str(e)}")


# ========================================
# HEALTH CHECK ENDPOINT
# ========================================

@app.get("/", tags=["Health"])
async def root():
    """
    Root endpoint providing API information and health status.
    """
    return {
        "message": "Welcome to Labanita Egyptian Sweets Store API",
        "version": "1.0.0",
        "status": "healthy",
        "database": "connected" if check_database_connection() else "disconnected"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint for monitoring and load balancers.
    """
    db_status = check_database_connection()
    
    return {
        "status": "healthy" if db_status else "unhealthy",
        "database": "connected" if db_status else "disconnected",
        "timestamp": "2024-01-01T00:00:00Z"  # You can use datetime.utcnow() here
    }


# ========================================
# PRODUCT ENDPOINTS
# ========================================

@app.get(
    "/products/",
    response_model=List[ProductResponse],
    tags=["Products"],
    summary="Get all products",
    description="Retrieve a paginated list of products with optional filtering"
)
async def read_products(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    category_id: Optional[uuid.UUID] = Query(None, description="Filter by category ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    is_featured: Optional[bool] = Query(None, description="Filter by featured status"),
    is_new_arrival: Optional[bool] = Query(None, description="Filter by new arrival status"),
    is_best_selling: Optional[bool] = Query(None, description="Filter by best selling status"),
    db: Session = Depends(get_db)
):
    """
    Get a paginated list of products with optional filtering.
    
    - **skip**: Number of records to skip (for pagination)
    - **limit**: Maximum number of records to return (max 1000)
    - **category_id**: Filter by specific category
    - **is_active**: Filter by active status
    - **is_featured**: Filter by featured products
    - **is_new_arrival**: Filter by new arrivals
    - **is_best_selling**: Filter by best selling products
    """
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
    
    return products


@app.get(
    "/products/{product_id}",
    response_model=ProductResponse,
    tags=["Products"],
    summary="Get product by ID",
    description="Retrieve a specific product by its UUID"
)
async def read_product(
    product_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """
    Get a specific product by its ID.
    
    - **product_id**: The UUID of the product to retrieve
    """
    product = get_product_by_id(db=db, product_id=product_id)
    
    if product is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found"
        )
    
    return product


@app.get(
    "/products/featured/",
    response_model=List[ProductResponse],
    tags=["Products"],
    summary="Get featured products",
    description="Retrieve a list of featured products"
)
async def read_featured_products(
    limit: int = Query(10, ge=1, le=100, description="Maximum number of featured products to return"),
    db: Session = Depends(get_db)
):
    """
    Get a list of featured products.
    
    - **limit**: Maximum number of featured products to return
    """
    products = get_featured_products(db=db, limit=limit)
    return products


@app.get(
    "/products/new-arrivals/",
    response_model=List[ProductResponse],
    tags=["Products"],
    summary="Get new arrival products",
    description="Retrieve a list of new arrival products"
)
async def read_new_arrivals(
    limit: int = Query(10, ge=1, le=100, description="Maximum number of new arrival products to return"),
    db: Session = Depends(get_db)
):
    """
    Get a list of new arrival products.
    
    - **limit**: Maximum number of new arrival products to return
    """
    products = get_new_arrivals(db=db, limit=limit)
    return products


@app.get(
    "/products/best-selling/",
    response_model=List[ProductResponse],
    tags=["Products"],
    summary="Get best selling products",
    description="Retrieve a list of best selling products"
)
async def read_best_selling_products(
    limit: int = Query(10, ge=1, le=100, description="Maximum number of best selling products to return"),
    db: Session = Depends(get_db)
):
    """
    Get a list of best selling products.
    
    - **limit**: Maximum number of best selling products to return
    """
    products = get_best_selling_products(db=db, limit=limit)
    return products


@app.get(
    "/products/search/",
    response_model=List[ProductResponse],
    tags=["Products"],
    summary="Search products",
    description="Search products by name or description"
)
async def search_products_endpoint(
    q: str = Query(..., min_length=1, description="Search term"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(get_db)
):
    """
    Search products by name or description.
    
    - **q**: Search term (required)
    - **skip**: Number of records to skip (for pagination)
    - **limit**: Maximum number of records to return
    """
    products = search_products(db=db, search_term=q, skip=skip, limit=limit)
    return products


# ========================================
# CATEGORY ENDPOINTS
# ========================================

@app.get(
    "/categories/",
    response_model=List[CategoryResponse],
    tags=["Categories"],
    summary="Get all categories",
    description="Retrieve a paginated list of product categories"
)
async def read_categories(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of records to return"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db)
):
    """
    Get a paginated list of product categories.
    
    - **skip**: Number of records to skip (for pagination)
    - **limit**: Maximum number of records to return (max 100)
    - **is_active**: Filter by active status
    """
    categories = get_categories(db=db, skip=skip, limit=limit, is_active=is_active)
    return categories


@app.get(
    "/categories/{category_id}",
    response_model=CategoryResponse,
    tags=["Categories"],
    summary="Get category by ID",
    description="Retrieve a specific category by its UUID"
)
async def read_category(
    category_id: uuid.UUID,
    db: Session = Depends(get_db)
):
    """
    Get a specific category by its ID.
    
    - **category_id**: The UUID of the category to retrieve
    """
    category = get_category_by_id(db=db, category_id=category_id)
    
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with ID {category_id} not found"
        )
    
    return category


# ========================================
# STATISTICS ENDPOINTS
# ========================================

@app.get(
    "/stats/products/count",
    tags=["Statistics"],
    summary="Get products count",
    description="Get the total count of products with optional filtering"
)
async def get_products_count_endpoint(
    category_id: Optional[uuid.UUID] = Query(None, description="Filter by category ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db)
):
    """
    Get the total count of products with optional filtering.
    
    - **category_id**: Filter by specific category
    - **is_active**: Filter by active status
    """
    count = get_products_count(db=db, category_id=category_id, is_active=is_active)
    
    return {
        "count": count,
        "category_id": category_id,
        "is_active": is_active
    }


@app.get(
    "/stats/categories/count",
    tags=["Statistics"],
    summary="Get categories count",
    description="Get the total count of categories with optional filtering"
)
async def get_categories_count_endpoint(
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db)
):
    """
    Get the total count of categories with optional filtering.
    
    - **is_active**: Filter by active status
    """
    count = get_categories_count(db=db, is_active=is_active)
    
    return {
        "count": count,
        "is_active": is_active
    }


# ========================================
# ERROR HANDLERS
# ========================================

@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Handle 404 errors with consistent response format."""
    return {
        "error": "Not Found",
        "message": "The requested resource was not found",
        "path": str(request.url.path)
    }


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Handle 500 errors with consistent response format."""
    return {
        "error": "Internal Server Error",
        "message": "An unexpected error occurred",
        "path": str(request.url.path)
    }


# ========================================
# APPLICATION METADATA
# ========================================

if __name__ == "__main__":
    import uvicorn
    
    # Run the application with uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Enable auto-reload for development
        log_level="info"
    )