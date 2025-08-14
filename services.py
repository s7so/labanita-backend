"""
Business logic services for Labanita API.
Provides core functions for interacting with the database and implementing business logic.
"""

import uuid
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from models import Product, Category
from schemas import ProductResponse, CategoryResponse


# ========================================
# PRODUCT SERVICES
# ========================================

def get_products(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    category_id: Optional[uuid.UUID] = None,
    is_active: Optional[bool] = None,
    is_featured: Optional[bool] = None,
    is_new_arrival: Optional[bool] = None,
    is_best_selling: Optional[bool] = None
) -> List[Product]:
    """
    Fetch products from the database with optional filtering and pagination.
    
    Args:
        db: Database session
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        category_id: Filter by specific category ID
        is_active: Filter by active status
        is_featured: Filter by featured status
        is_new_arrival: Filter by new arrival status
        is_best_selling: Filter by best selling status
    
    Returns:
        List of Product objects matching the criteria
    """
    # Build query with filters
    query = db.query(Product)
    
    # Apply filters if provided
    filters = []
    
    if category_id is not None:
        filters.append(Product.category_id == category_id)
    
    if is_active is not None:
        filters.append(Product.is_active == is_active)
    
    if is_featured is not None:
        filters.append(Product.is_featured == is_featured)
    
    if is_new_arrival is not None:
        filters.append(Product.is_new_arrival == is_new_arrival)
    
    if is_best_selling is not None:
        filters.append(Product.is_best_selling == is_best_selling)
    
    # Apply filters if any exist
    if filters:
        query = query.filter(and_(*filters))
    
    # Apply ordering and pagination
    return query.order_by(Product.sort_order.asc(), Product.product_name.asc()).offset(skip).limit(limit).all()


def get_product_by_id(db: Session, product_id: uuid.UUID) -> Optional[Product]:
    """
    Fetch a single product by its ID.
    
    Args:
        db: Database session
        product_id: UUID of the product to fetch
    
    Returns:
        Product object if found, None otherwise
    """
    return db.query(Product).filter(Product.product_id == product_id).first()


def get_product_by_slug(db: Session, product_slug: str) -> Optional[Product]:
    """
    Fetch a single product by its slug.
    
    Args:
        db: Database session
        product_slug: Slug of the product to fetch
    
    Returns:
        Product object if found, None otherwise
    """
    return db.query(Product).filter(Product.product_slug == product_slug).first()


def get_featured_products(db: Session, limit: int = 10) -> List[Product]:
    """
    Fetch featured products from the database.
    
    Args:
        db: Database session
        limit: Maximum number of featured products to return
    
    Returns:
        List of featured Product objects
    """
    return db.query(Product).filter(
        and_(Product.is_featured == True, Product.is_active == True)
    ).order_by(Product.sort_order.asc(), Product.product_name.asc()).limit(limit).all()


def get_new_arrivals(db: Session, limit: int = 10) -> List[Product]:
    """
    Fetch new arrival products from the database.
    
    Args:
        db: Database session
        limit: Maximum number of new arrival products to return
    
    Returns:
        List of new arrival Product objects
    """
    return db.query(Product).filter(
        and_(Product.is_new_arrival == True, Product.is_active == True)
    ).order_by(Product.created_at.desc()).limit(limit).all()


def get_best_selling_products(db: Session, limit: int = 10) -> List[Product]:
    """
    Fetch best selling products from the database.
    
    Args:
        db: Database session
        limit: Maximum number of best selling products to return
    
    Returns:
        List of best selling Product objects
    """
    return db.query(Product).filter(
        and_(Product.is_best_selling == True, Product.is_active == True)
    ).order_by(Product.sort_order.asc(), Product.product_name.asc()).limit(limit).all()


def search_products(
    db: Session, 
    search_term: str, 
    skip: int = 0, 
    limit: int = 100
) -> List[Product]:
    """
    Search products by name or description.
    
    Args:
        db: Database session
        search_term: Text to search for in product names and descriptions
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
    
    Returns:
        List of Product objects matching the search criteria
    """
    search_pattern = f"%{search_term}%"
    
    return db.query(Product).filter(
        and_(
            Product.is_active == True,
            (
                Product.product_name.ilike(search_pattern) |
                Product.description.ilike(search_pattern)
            )
        )
    ).order_by(Product.sort_order.asc(), Product.product_name.asc()).offset(skip).limit(limit).all()


# ========================================
# CATEGORY SERVICES
# ========================================

def get_categories(
    db: Session, 
    skip: int = 0, 
    limit: int = 10,
    is_active: Optional[bool] = None
) -> List[Category]:
    """
    Fetch categories from the database with optional filtering and pagination.
    
    Args:
        db: Database session
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return
        is_active: Filter by active status
    
    Returns:
        List of Category objects matching the criteria
    """
    query = db.query(Category)
    
    # Apply active filter if provided
    if is_active is not None:
        query = query.filter(Category.is_active == is_active)
    
    # Apply ordering and pagination
    return query.order_by(Category.sort_order.asc(), Category.category_name.asc()).offset(skip).limit(limit).all()


def get_category_by_id(db: Session, category_id: uuid.UUID) -> Optional[Category]:
    """
    Fetch a single category by its ID.
    
    Args:
        db: Database session
        category_id: UUID of the category to fetch
    
    Returns:
        Category object if found, None otherwise
    """
    return db.query(Category).filter(Category.category_id == category_id).first()


def get_category_by_slug(db: Session, category_slug: str) -> Optional[Category]:
    """
    Fetch a single category by its slug.
    
    Args:
        db: Database session
        category_slug: Slug of the category to fetch
    
    Returns:
        Category object if found, None otherwise
    """
    return db.query(Category).filter(Category.category_slug == category_slug).first()


def get_active_categories(db: Session) -> List[Category]:
    """
    Fetch all active categories from the database.
    
    Args:
        db: Database session
    
    Returns:
        List of active Category objects
    """
    return db.query(Category).filter(Category.is_active == True).order_by(
        Category.sort_order.asc(), Category.category_name.asc()
    ).all()


def get_category_with_products(
    db: Session, 
    category_id: uuid.UUID,
    skip: int = 0,
    limit: int = 100
) -> Optional[Category]:
    """
    Fetch a category with its associated products.
    
    Args:
        db: Database session
        category_id: UUID of the category to fetch
        skip: Number of product records to skip (for pagination)
        limit: Maximum number of product records to return
    
    Returns:
        Category object with products if found, None otherwise
    """
    category = db.query(Category).filter(Category.category_id == category_id).first()
    
    if category:
        # Load products for this category with pagination
        products = db.query(Product).filter(
            and_(Product.category_id == category_id, Product.is_active == True)
        ).order_by(Product.sort_order.asc(), Product.product_name.asc()).offset(skip).limit(limit).all()
        
        # Set the products on the category object
        category.products = products
    
    return category


# ========================================
# UTILITY SERVICES
# ========================================

def get_products_count(
    db: Session,
    category_id: Optional[uuid.UUID] = None,
    is_active: Optional[bool] = None
) -> int:
    """
    Get the total count of products matching the given criteria.
    
    Args:
        db: Database session
        category_id: Filter by specific category ID
        is_active: Filter by active status
    
    Returns:
        Total count of products matching the criteria
    """
    query = db.query(Product)
    
    filters = []
    
    if category_id is not None:
        filters.append(Product.category_id == category_id)
    
    if is_active is not None:
        filters.append(Product.is_active == is_active)
    
    if filters:
        query = query.filter(and_(*filters))
    
    return query.count()


def get_categories_count(db: Session, is_active: Optional[bool] = None) -> int:
    """
    Get the total count of categories matching the given criteria.
    
    Args:
        db: Database session
        is_active: Filter by active status
    
    Returns:
        Total count of categories matching the criteria
    """
    query = db.query(Category)
    
    if is_active is not None:
        query = query.filter(Category.is_active == is_active)
    
    return query.count()