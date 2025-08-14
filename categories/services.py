import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, asc, and_, or_, text
from sqlalchemy.exc import IntegrityError

from core.exceptions import (
    NotFoundException, 
    ValidationException, 
    ConflictException
)
from models import Category, Product, OrderItem, Order
from categories.schemas import (
    CategoryResponse, CategoryListResponse, CategoryWithProductsResponse,
    ProductResponse, CategoryStatsResponse, CategoryHierarchyResponse,
    PaginationParams, PaginatedCategoriesResponse, PaginatedProductsResponse
)

class CategoryService:
    """Category service for category management and product retrieval"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # =============================================================================
    # CATEGORY RETRIEVAL
    # =============================================================================
    
    def get_all_categories(
        self, 
        is_active: Optional[bool] = None,
        parent_category_id: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: str = "sort_order",
        sort_order: str = "asc"
    ) -> CategoryListResponse:
        """Get all categories with optional filtering and sorting"""
        query = self.db.query(Category)
        
        # Apply filters
        if is_active is not None:
            query = query.filter(Category.is_active == is_active)
        
        if parent_category_id is not None:
            query = query.filter(Category.parent_category_id == parent_category_id)
        
        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                or_(
                    Category.category_name.ilike(search_filter),
                    Category.description.ilike(search_filter)
                )
            )
        
        # Apply sorting
        if hasattr(Category, sort_by):
            sort_column = getattr(Category, sort_by)
            if sort_order.lower() == "desc":
                query = query.order_by(desc(sort_column))
            else:
                query = query.order_by(asc(sort_column))
        else:
            # Default sorting
            query = query.order_by(asc(Category.sort_order))
        
        categories = query.all()
        
        # Convert to response format
        category_responses = []
        for category in categories:
            category_responses.append(CategoryResponse(
                category_id=str(category.category_id),
                category_name=category.category_name,
                description=category.description,
                image_url=category.image_url,
                parent_category_id=str(category.parent_category_id) if category.parent_category_id else None,
                is_active=category.is_active,
                sort_order=category.sort_order,
                created_at=category.created_at,
                updated_at=category.updated_at
            ))
        
        # Count active categories
        active_count = sum(1 for cat in categories if cat.is_active)
        
        return CategoryListResponse(
            categories=category_responses,
            total_count=len(categories),
            active_count=active_count
        )
    
    def get_category_by_id(self, category_id: str) -> CategoryResponse:
        """Get a specific category by ID"""
        category = self.db.query(Category).filter(Category.category_id == category_id).first()
        
        if not category:
            raise NotFoundException(f"Category with ID {category_id} not found")
        
        return CategoryResponse(
            category_id=str(category.category_id),
            category_name=category.category_name,
            description=category.description,
            image_url=category.image_url,
            parent_category_id=str(category.parent_category_id) if category.parent_category_id else None,
            is_active=category.is_active,
            sort_order=category.sort_order,
            created_at=category.created_at,
            updated_at=category.updated_at
        )
    
    def get_category_with_products(
        self, 
        category_id: str,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        in_stock: Optional[bool] = None,
        on_sale: Optional[bool] = None,
        min_rating: Optional[float] = None,
        search: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        page: int = 1,
        size: int = 20
    ) -> CategoryWithProductsResponse:
        """Get category with its products and optional filtering"""
        # Get category
        category = self.db.query(Category).filter(Category.category_id == category_id).first()
        if not category:
            raise NotFoundException(f"Category with ID {category_id} not found")
        
        # Build product query
        product_query = self.db.query(Product).filter(Product.category_id == category_id)
        
        # Apply product filters
        if min_price is not None:
            product_query = product_query.filter(Product.price >= min_price)
        
        if max_price is not None:
            product_query = product_query.filter(Product.price <= max_price)
        
        if in_stock is not None:
            if in_stock:
                product_query = product_query.filter(Product.stock_quantity > 0)
            else:
                product_query = product_query.filter(Product.stock_quantity <= 0)
        
        if on_sale is not None:
            if on_sale:
                product_query = product_query.filter(Product.sale_price.isnot(None))
            else:
                product_query = product_query.filter(Product.sale_price.is_(None))
        
        if min_rating is not None:
            product_query = product_query.filter(Product.rating >= min_rating)
        
        if search:
            search_filter = f"%{search}%"
            product_query = product_query.filter(
                or_(
                    Product.product_name.ilike(search_filter),
                    Product.description.ilike(search_filter)
                )
            )
        
        # Apply sorting
        if hasattr(Product, sort_by):
            sort_column = getattr(Product, sort_by)
            if sort_order.lower() == "desc":
                product_query = product_query.order_by(desc(sort_column))
            else:
                product_query = product_query.order_by(asc(sort_column))
        else:
            # Default sorting
            product_query = product_query.order_by(desc(Product.created_at))
        
        # Get total count before pagination
        total_products = product_query.count()
        
        # Apply pagination
        offset = (page - 1) * size
        products = product_query.offset(offset).limit(size).all()
        
        # Convert products to response format
        product_responses = []
        for product in products:
            product_responses.append(ProductResponse(
                product_id=str(product.product_id),
                product_name=product.product_name,
                description=product.description,
                price=float(product.price),
                sale_price=float(product.sale_price) if product.sale_price else None,
                image_url=product.image_url,
                is_active=product.is_active,
                stock_quantity=product.stock_quantity,
                rating=float(product.rating) if product.rating else None,
                review_count=product.review_count,
                created_at=product.created_at
            ))
        
        # Get subcategories
        subcategories = self.db.query(Category).filter(
            Category.parent_category_id == category_id,
            Category.is_active == True
        ).all()
        
        subcategory_responses = []
        for subcat in subcategories:
            subcategory_responses.append(CategoryResponse(
                category_id=str(subcat.category_id),
                category_name=subcat.category_name,
                description=subcat.description,
                image_url=subcat.image_url,
                parent_category_id=str(subcat.parent_category_id) if subcat.parent_category_id else None,
                is_active=subcat.is_active,
                sort_order=subcat.sort_order,
                created_at=subcat.created_at,
                updated_at=subcat.updated_at
            ))
        
        # Build category response
        category_response = CategoryResponse(
            category_id=str(category.category_id),
            category_name=category.category_name,
            description=category.description,
            image_url=category.image_url,
            parent_category_id=str(category.parent_category_id) if category.parent_category_id else None,
            is_active=category.is_active,
            sort_order=category.sort_order,
            created_at=category.created_at,
            updated_at=category.updated_at
        )
        
        return CategoryWithProductsResponse(
            category=category_response,
            products=product_responses,
            total_products=total_products,
            subcategories=subcategory_responses
        )
    
    def get_category_products_paginated(
        self,
        category_id: str,
        pagination: PaginationParams,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        in_stock: Optional[bool] = None,
        on_sale: Optional[bool] = None,
        min_rating: Optional[float] = None,
        search: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> PaginatedProductsResponse:
        """Get paginated products for a specific category"""
        # Verify category exists
        category = self.db.query(Category).filter(Category.category_id == category_id).first()
        if not category:
            raise NotFoundException(f"Category with ID {category_id} not found")
        
        # Build product query
        product_query = self.db.query(Product).filter(Product.category_id == category_id)
        
        # Apply filters
        if min_price is not None:
            product_query = product_query.filter(Product.price >= min_price)
        
        if max_price is not None:
            product_query = product_query.filter(Product.price <= max_price)
        
        if in_stock is not None:
            if in_stock:
                product_query = product_query.filter(Product.stock_quantity > 0)
            else:
                product_query = product_query.filter(Product.stock_quantity <= 0)
        
        if on_sale is not None:
            if on_sale:
                product_query = product_query.filter(Product.sale_price.isnot(None))
            else:
                product_query = product_query.filter(Product.sale_price.is_(None))
        
        if min_rating is not None:
            product_query = product_query.filter(Product.rating >= min_rating)
        
        if search:
            search_filter = f"%{search}%"
            product_query = product_query.filter(
                or_(
                    Product.product_name.ilike(search_filter),
                    Product.description.ilike(search_filter)
                )
            )
        
        # Apply sorting
        if hasattr(Product, sort_by):
            sort_column = getattr(Product, sort_by)
            if sort_order.lower() == "desc":
                product_query = product_query.order_by(desc(sort_column))
            else:
                product_query = product_query.order_by(asc(sort_column))
        else:
            # Default sorting
            product_query = product_query.order_by(desc(Product.created_at))
        
        # Get total count
        total = product_query.count()
        
        # Calculate pagination
        pages = (total + pagination.size - 1) // pagination.size
        has_next = pagination.page < pages
        has_prev = pagination.page > 1
        
        # Get products for current page
        products = product_query.offset(pagination.offset).limit(pagination.size).all()
        
        # Convert to response format
        product_responses = []
        for product in products:
            product_responses.append(ProductResponse(
                product_id=str(product.product_id),
                product_name=product.product_name,
                description=product.description,
                price=float(product.price),
                sale_price=float(product.sale_price) if product.sale_price else None,
                image_url=product.image_url,
                is_active=product.is_active,
                stock_quantity=product.stock_quantity,
                rating=float(product.rating) if product.rating else None,
                review_count=product.review_count,
                created_at=product.created_at
            ))
        
        return PaginatedProductsResponse(
            page=pagination.page,
            size=pagination.size,
            total=total,
            pages=pages,
            has_next=has_next,
            has_prev=has_prev,
            products=product_responses
        )
    
    # =============================================================================
    # CATEGORY STATISTICS
    # =============================================================================
    
    def get_category_statistics(self, category_id: str) -> CategoryStatsResponse:
        """Get comprehensive statistics for a category"""
        # Verify category exists
        category = self.db.query(Category).filter(Category.category_id == category_id).first()
        if not category:
            raise NotFoundException(f"Category with ID {category_id} not found")
        
        # Get product statistics
        products = self.db.query(Product).filter(Product.category_id == category_id).all()
        
        total_products = len(products)
        active_products = sum(1 for p in products if p.is_active)
        
        # Calculate average price
        if products:
            total_price = sum(float(p.price) for p in products)
            average_price = total_price / total_products
        else:
            average_price = 0.0
        
        # Calculate average rating
        rated_products = [p for p in products if p.rating is not None]
        if rated_products:
            total_rating = sum(float(p.rating) for p in rated_products)
            average_rating = total_rating / len(rated_products)
        else:
            average_rating = None
        
        # Get sales statistics
        sales_query = self.db.query(
            func.sum(OrderItem.quantity * OrderItem.unit_price).label('total_sales')
        ).join(Product, OrderItem.product_id == Product.product_id)\
         .join(Order, OrderItem.order_id == Order.order_id)\
         .filter(
            Product.category_id == category_id,
            Order.status == 'completed'
        )
        
        sales_result = sales_query.first()
        total_sales = float(sales_result.total_sales) if sales_result.total_sales else 0.0
        
        # Count subcategories
        subcategory_count = self.db.query(Category).filter(
            Category.parent_category_id == category_id
        ).count()
        
        # Get last product added
        last_product = self.db.query(Product).filter(
            Product.category_id == category_id
        ).order_by(desc(Product.created_at)).first()
        
        last_product_added = last_product.created_at if last_product else None
        
        return CategoryStatsResponse(
            category_id=str(category.category_id),
            category_name=category.category_name,
            total_products=total_products,
            active_products=active_products,
            total_sales=total_sales,
            average_price=average_price,
            average_rating=average_rating,
            subcategory_count=subcategory_count,
            last_product_added=last_product_added
        )
    
    # =============================================================================
    # CATEGORY HIERARCHY
    # =============================================================================
    
    def get_category_hierarchy(self, category_id: str) -> CategoryHierarchyResponse:
        """Get category hierarchy information"""
        # Verify category exists
        category = self.db.query(Category).filter(Category.category_id == category_id).first()
        if not category:
            raise NotFoundException(f"Category with ID {category_id} not found")
        
        # Get parent category
        parent = None
        if category.parent_category_id:
            parent = self.db.query(Category).filter(Category.category_id == category.parent_category_id).first()
            if parent:
                parent = CategoryResponse(
                    category_id=str(parent.category_id),
                    category_name=parent.category_name,
                    description=parent.description,
                    image_url=parent.image_url,
                    parent_category_id=str(parent.parent_category_id) if parent.parent_category_id else None,
                    is_active=parent.is_active,
                    sort_order=parent.sort_order,
                    created_at=parent.created_at,
                    updated_at=parent.updated_at
                )
        
        # Get child categories
        children = self.db.query(Category).filter(
            Category.parent_category_id == category_id,
            Category.is_active == True
        ).all()
        
        children_responses = []
        for child in children:
            children_responses.append(CategoryResponse(
                category_id=str(child.category_id),
                category_name=child.category_name,
                description=child.description,
                image_url=child.image_url,
                parent_category_id=str(child.parent_category_id) if child.parent_category_id else None,
                is_active=child.is_active,
                sort_order=child.sort_order,
                created_at=child.created_at,
                updated_at=child.updated_at
            ))
        
        # Get sibling categories (same parent)
        siblings = []
        if category.parent_category_id:
            siblings = self.db.query(Category).filter(
                Category.parent_category_id == category.parent_category_id,
                Category.category_id != category_id,
                Category.is_active == True
            ).all()
        else:
            # Root level categories
            siblings = self.db.query(Category).filter(
                Category.parent_category_id.is_(None),
                Category.category_id != category_id,
                Category.is_active == True
            ).all()
        
        siblings_responses = []
        for sibling in siblings:
            siblings_responses.append(CategoryResponse(
                category_id=str(sibling.category_id),
                category_name=sibling.category_name,
                description=sibling.description,
                image_url=sibling.image_url,
                parent_category_id=str(sibling.parent_category_id) if sibling.parent_category_id else None,
                is_active=sibling.is_active,
                sort_order=sibling.sort_order,
                created_at=sibling.created_at,
                updated_at=sibling.updated_at
            ))
        
        # Build breadcrumb
        breadcrumb = self._build_breadcrumb(category)
        
        # Build category response
        category_response = CategoryResponse(
            category_id=str(category.category_id),
            category_name=category.category_name,
            description=category.description,
            image_url=category.image_url,
            parent_category_id=str(category.parent_category_id) if category.parent_category_id else None,
            is_active=category.is_active,
            sort_order=category.sort_order,
            created_at=category.created_at,
            updated_at=category.updated_at
        )
        
        return CategoryHierarchyResponse(
            category=category_response,
            parent=parent,
            children=children_responses,
            siblings=siblings_responses,
            breadcrumb=breadcrumb
        )
    
    def _build_breadcrumb(self, category: Category) -> List[CategoryResponse]:
        """Build breadcrumb navigation for a category"""
        breadcrumb = []
        current = category
        
        while current:
            breadcrumb.insert(0, CategoryResponse(
                category_id=str(current.category_id),
                category_name=current.category_name,
                description=current.description,
                image_url=current.image_url,
                parent_category_id=str(current.parent_category_id) if current.parent_category_id else None,
                is_active=current.is_active,
                sort_order=current.sort_order,
                created_at=current.created_at,
                updated_at=current.updated_at
            ))
            
            if current.parent_category_id:
                current = self.db.query(Category).filter(Category.category_id == current.parent_category_id).first()
            else:
                break
        
        return breadcrumb
    
    # =============================================================================
    # CATEGORY MANAGEMENT (ADMIN FUNCTIONS)
    # =============================================================================
    
    def create_category(self, category_data: Dict[str, Any]) -> CategoryResponse:
        """Create a new category"""
        # Check if category name already exists
        existing = self.db.query(Category).filter(
            Category.category_name == category_data['category_name']
        ).first()
        
        if existing:
            raise ConflictException(f"Category with name '{category_data['category_name']}' already exists")
        
        # Create new category
        new_category = Category(
            category_name=category_data['category_name'],
            description=category_data.get('description'),
            image_url=category_data.get('image_url'),
            parent_category_id=category_data.get('parent_category_id'),
            is_active=category_data.get('is_active', True),
            sort_order=category_data.get('sort_order', 0)
        )
        
        self.db.add(new_category)
        self.db.commit()
        self.db.refresh(new_category)
        
        return self.get_category_by_id(str(new_category.category_id))
    
    def update_category(self, category_id: str, update_data: Dict[str, Any]) -> CategoryResponse:
        """Update an existing category"""
        category = self.db.query(Category).filter(Category.category_id == category_id).first()
        if not category:
            raise NotFoundException(f"Category with ID {category_id} not found")
        
        # Check if new name conflicts with existing
        if 'category_name' in update_data and update_data['category_name'] != category.category_name:
            existing = self.db.query(Category).filter(
                Category.category_name == update_data['category_name'],
                Category.category_id != category_id
            ).first()
            
            if existing:
                raise ConflictException(f"Category with name '{update_data['category_name']}' already exists")
        
        # Update fields
        for field, value in update_data.items():
            if hasattr(category, field):
                setattr(category, field, value)
        
        category.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(category)
        
        return self.get_category_by_id(category_id)
    
    def delete_category(self, category_id: str) -> bool:
        """Delete a category (soft delete)"""
        category = self.db.query(Category).filter(Category.category_id == category_id).first()
        if not category:
            raise NotFoundException(f"Category with ID {category_id} not found")
        
        # Check if category has products
        product_count = self.db.query(Product).filter(Product.category_id == category_id).count()
        if product_count > 0:
            raise ValidationException(f"Cannot delete category with {product_count} products. Move or delete products first.")
        
        # Check if category has subcategories
        subcategory_count = self.db.query(Category).filter(Category.parent_category_id == category_id).count()
        if subcategory_count > 0:
            raise ValidationException(f"Cannot delete category with {subcategory_count} subcategories. Move or delete subcategories first.")
        
        # Soft delete
        category.is_active = False
        category.updated_at = datetime.utcnow()
        
        self.db.commit()
        return True
    
    # =============================================================================
    # UTILITY FUNCTIONS
    # =============================================================================
    
    def get_root_categories(self) -> List[CategoryResponse]:
        """Get all root-level categories (no parent)"""
        root_categories = self.db.query(Category).filter(
            Category.parent_category_id.is_(None),
            Category.is_active == True
        ).order_by(Category.sort_order).all()
        
        return [
            CategoryResponse(
                category_id=str(cat.category_id),
                category_name=cat.category_name,
                description=cat.description,
                image_url=cat.image_url,
                parent_category_id=None,
                is_active=cat.is_active,
                sort_order=cat.sort_order,
                created_at=cat.created_at,
                updated_at=cat.updated_at
            )
            for cat in root_categories
        ]
    
    def get_category_tree(self) -> List[Dict[str, Any]]:
        """Get complete category tree structure"""
        def build_tree(parent_id=None):
            categories = self.db.query(Category).filter(
                Category.parent_category_id == parent_id,
                Category.is_active == True
            ).order_by(Category.sort_order).all()
            
            tree = []
            for cat in categories:
                node = {
                    'category_id': str(cat.category_id),
                    'category_name': cat.category_name,
                    'description': cat.description,
                    'image_url': cat.image_url,
                    'sort_order': cat.sort_order,
                    'children': build_tree(cat.category_id)
                }
                tree.append(node)
            
            return tree
        
        return build_tree()
    
    def search_categories(self, query: str, limit: int = 10) -> List[CategoryResponse]:
        """Search categories by name or description"""
        search_filter = f"%{query}%"
        
        categories = self.db.query(Category).filter(
            and_(
                Category.is_active == True,
                or_(
                    Category.category_name.ilike(search_filter),
                    Category.description.ilike(search_filter)
                )
            )
        ).limit(limit).all()
        
        return [
            CategoryResponse(
                category_id=str(cat.category_id),
                category_name=cat.category_name,
                description=cat.description,
                image_url=cat.image_url,
                parent_category_id=str(cat.parent_category_id) if cat.parent_category_id else None,
                is_active=cat.is_active,
                sort_order=cat.sort_order,
                created_at=cat.created_at,
                updated_at=cat.updated_at
            )
            for cat in categories
        ]