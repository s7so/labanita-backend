import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, asc, and_, or_, text, case
from sqlalchemy.exc import IntegrityError

from core.exceptions import (
    NotFoundException, 
    ValidationException, 
    ConflictException
)
from models import Product, Category, User, Order, OrderItem
from admin.schemas import (
    AdminProductResponse, AdminProductListResponse, AdminProductFilter,
    AdminProductCreate, AdminProductUpdate, AdminProductCreateRequest,
    AdminProductUpdateRequest, AdminUserResponse, AdminUserListResponse,
    AdminDashboardStats, AdminActivityLog
)

class AdminService:
    """Admin service for administrative functions and product management"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # =============================================================================
    # ADMIN PRODUCT MANAGEMENT
    # =============================================================================
    
    def get_admin_products(
        self,
        filters: Optional[AdminProductFilter] = None
    ) -> AdminProductListResponse:
        """Get products for admin management with filtering and pagination"""
        try:
            query = self.db.query(Product).join(Category, Product.category_id == Category.category_id)
            
            # Apply filters
            if filters:
                if filters.search:
                    search_term = f"%{filters.search}%"
                    query = query.filter(
                        or_(
                            Product.product_name.ilike(search_term),
                            Product.description.ilike(search_term),
                            Product.sku.ilike(search_term)
                        )
                    )
                
                if filters.category_id:
                    query = query.filter(Product.category_id == filters.category_id)
                
                if filters.brand:
                    query = query.filter(Product.brand == filters.brand)
                
                if filters.status:
                    query = query.filter(Product.status == filters.status)
                
                if filters.is_active is not None:
                    query = query.filter(Product.is_active == filters.is_active)
                
                if filters.is_featured is not None:
                    query = query.filter(Product.is_featured == filters.is_featured)
                
                if filters.price_min:
                    query = query.filter(Product.price >= filters.price_min)
                
                if filters.price_max:
                    query = query.filter(Product.price <= filters.price_max)
                
                if filters.stock_min:
                    query = query.filter(Product.stock_quantity >= filters.stock_min)
                
                if filters.stock_max:
                    query = query.filter(Product.stock_quantity <= filters.stock_max)
                
                if filters.created_date_from:
                    query = query.filter(Product.created_at >= filters.created_date_from)
                
                if filters.created_date_to:
                    query = query.filter(Product.created_at <= filters.created_date_to)
                
                if filters.updated_date_from:
                    query = query.filter(Product.updated_at >= filters.updated_date_from)
                
                if filters.updated_date_to:
                    query = query.filter(Product.updated_at <= filters.updated_date_to)
            
            # Get total count
            total = query.count()
            
            # Apply sorting
            if filters and filters.sort_by:
                sort_field = getattr(Product, filters.sort_by, Product.created_at)
                if filters.sort_order == "asc":
                    query = query.order_by(asc(sort_field))
                else:
                    query = query.order_by(desc(sort_field))
            else:
                query = query.order_by(desc(Product.created_at))
            
            # Apply pagination
            page = filters.page if filters else 1
            size = filters.size if filters else 20
            products = query.offset((page - 1) * size).limit(size).all()
            
            # Build product responses
            product_responses = []
            for product in products:
                product_responses.append(self._build_admin_product_response(product))
            
            # Calculate pagination info
            total_pages = (total + size - 1) // size
            has_next = page < total_pages
            has_prev = page > 1
            
            # Build filters applied
            filters_applied = {}
            if filters:
                if filters.search:
                    filters_applied["search"] = filters.search
                if filters.category_id:
                    filters_applied["category_id"] = filters.category_id
                if filters.brand:
                    filters_applied["brand"] = filters.brand
                if filters.status:
                    filters_applied["status"] = filters.status
                if filters.is_active is not None:
                    filters_applied["is_active"] = filters.is_active
                if filters.is_featured is not None:
                    filters_applied["is_featured"] = filters.is_featured
                if filters.price_min:
                    filters_applied["price_min"] = filters.price_min
                if filters.price_max:
                    filters_applied["price_max"] = filters.price_max
                if filters.stock_min:
                    filters_applied["stock_min"] = filters.stock_min
                if filters.stock_max:
                    filters_applied["stock_max"] = filters.stock_max
            
            # Build summary
            summary = self._build_admin_products_summary(products)
            
            return AdminProductListResponse(
                products=product_responses,
                total_count=total,
                page=page,
                size=size,
                total_pages=total_pages,
                has_next=has_next,
                has_prev=has_prev,
                filters_applied=filters_applied,
                summary=summary
            )
            
        except Exception as e:
            raise ValidationException(f"Failed to get admin products: {str(e)}")
    
    def get_admin_product_by_id(self, product_id: str) -> AdminProductResponse:
        """Get product by ID for admin management"""
        try:
            product = self.db.query(Product).join(
                Category, Product.category_id == Category.category_id
            ).filter(Product.product_id == product_id).first()
            
            if not product:
                raise NotFoundException(f"Product with ID {product_id} not found")
            
            return self._build_admin_product_response(product)
            
        except NotFoundException:
            raise
        except Exception as e:
            raise ValidationException(f"Failed to get admin product: {str(e)}")
    
    def create_admin_product(
        self,
        product_data: AdminProductCreateRequest,
        admin_user_id: str
    ) -> AdminProductResponse:
        """Create new product (admin)"""
        try:
            # Validate SKU uniqueness
            existing_sku = self.db.query(Product).filter(Product.sku == product_data.sku).first()
            if existing_sku:
                raise ConflictException(f"Product with SKU {product_data.sku} already exists")
            
            # Validate category exists
            category = self.db.query(Category).filter(Category.category_id == product_data.category_id).first()
            if not category:
                raise ValidationException(f"Category with ID {product_data.category_id} not found")
            
            # Create product
            new_product = Product(
                product_id=str(uuid.uuid4()),
                product_name=product_data.product_name,
                description=product_data.description,
                short_description=product_data.short_description,
                category_id=product_data.category_id,
                brand=product_data.brand,
                sku=product_data.sku,
                barcode=product_data.barcode,
                price=product_data.price,
                compare_price=product_data.compare_price,
                cost_price=product_data.cost_price,
                weight=product_data.weight,
                dimensions=product_data.dimensions,
                stock_quantity=product_data.stock_quantity,
                min_stock_level=product_data.min_stock_level,
                max_stock_level=product_data.max_stock_level,
                is_featured=product_data.is_featured,
                is_active=product_data.is_active,
                status=product_data.status.value,
                tags=product_data.tags,
                images=product_data.images,
                main_image=product_data.main_image,
                seo_title=product_data.seo_title,
                seo_description=product_data.seo_description,
                seo_keywords=product_data.seo_keywords,
                meta_data=product_data.meta_data,
                notes=product_data.notes,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            self.db.add(new_product)
            self.db.commit()
            self.db.refresh(new_product)
            
            # Log admin activity
            self._log_admin_activity(
                user_id=admin_user_id,
                action="create_product",
                resource_type="product",
                resource_id=new_product.product_id,
                details={"product_name": new_product.product_name}
            )
            
            return self._build_admin_product_response(new_product)
            
        except IntegrityError:
            self.db.rollback()
            raise ConflictException("Product creation failed due to database constraint")
        except Exception as e:
            self.db.rollback()
            raise ValidationException(f"Failed to create product: {str(e)}")
    
    def update_admin_product(
        self,
        product_id: str,
        product_data: AdminProductUpdateRequest,
        admin_user_id: str
    ) -> AdminProductResponse:
        """Update existing product (admin)"""
        try:
            # Get existing product
            product = self.db.query(Product).filter(Product.product_id == product_id).first()
            if not product:
                raise NotFoundException(f"Product with ID {product_id} not found")
            
            # Check SKU uniqueness if changing
            if product_data.sku and product_data.sku != product.sku:
                existing_sku = self.db.query(Product).filter(
                    and_(
                        Product.sku == product_data.sku,
                        Product.product_id != product_id
                    )
                ).first()
                if existing_sku:
                    raise ConflictException(f"Product with SKU {product_data.sku} already exists")
            
            # Validate category if changing
            if product_data.category_id and product_data.category_id != product.category_id:
                category = self.db.query(Category).filter(Category.category_id == product_data.category_id).first()
                if not category:
                    raise ValidationException(f"Category with ID {product_data.category_id} not found")
            
            # Update fields
            update_fields = product_data.dict(exclude_unset=True)
            for field, value in update_fields.items():
                if hasattr(product, field):
                    setattr(product, field, value)
            
            product.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(product)
            
            # Log admin activity
            self._log_admin_activity(
                user_id=admin_user_id,
                action="update_product",
                resource_type="product",
                resource_id=product_id,
                details={"updated_fields": list(update_fields.keys())}
            )
            
            return self._build_admin_product_response(product)
            
        except IntegrityError:
            self.db.rollback()
            raise ConflictException("Product update failed due to database constraint")
        except Exception as e:
            self.db.rollback()
            raise ValidationException(f"Failed to update product: {str(e)}")
    
    def delete_admin_product(self, product_id: str, admin_user_id: str) -> bool:
        """Delete product (admin)"""
        try:
            # Get existing product
            product = self.db.query(Product).filter(Product.product_id == product_id).first()
            if not product:
                raise NotFoundException(f"Product with ID {product_id} not found")
            
            # Check if product has orders
            order_items = self.db.query(OrderItem).filter(OrderItem.product_id == product_id).first()
            if order_items:
                raise ConflictException("Cannot delete product with existing orders. Consider archiving instead.")
            
            # Log admin activity before deletion
            self._log_admin_activity(
                user_id=admin_user_id,
                action="delete_product",
                resource_type="product",
                resource_id=product_id,
                details={"product_name": product.product_name}
            )
            
            # Delete product
            self.db.delete(product)
            self.db.commit()
            
            return True
            
        except IntegrityError:
            self.db.rollback()
            raise ConflictException("Product deletion failed due to database constraint")
        except Exception as e:
            self.db.rollback()
            raise ValidationException(f"Failed to delete product: {str(e)}")
    
    def bulk_update_product_status(
        self,
        product_ids: List[str],
        status: str,
        admin_user_id: str
    ) -> Dict[str, Any]:
        """Bulk update product status"""
        try:
            # Validate status
            valid_statuses = ["active", "inactive", "archived", "draft"]
            if status not in valid_statuses:
                raise ValidationException(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
            
            # Update products
            updated_count = self.db.query(Product).filter(
                Product.product_id.in_(product_ids)
            ).update({
                "status": status,
                "updated_at": datetime.utcnow()
            }, synchronize_session=False)
            
            self.db.commit()
            
            # Log admin activity
            self._log_admin_activity(
                user_id=admin_user_id,
                action="bulk_update_product_status",
                resource_type="product",
                resource_id="multiple",
                details={
                    "product_ids": product_ids,
                    "new_status": status,
                    "updated_count": updated_count
                }
            )
            
            return {
                "message": f"Successfully updated {updated_count} products to status: {status}",
                "updated_count": updated_count,
                "status": status
            }
            
        except Exception as e:
            self.db.rollback()
            raise ValidationException(f"Failed to bulk update product status: {str(e)}")
    
    # =============================================================================
    # ADMIN USER MANAGEMENT
    # =============================================================================
    
    def get_admin_users(
        self,
        page: int = 1,
        size: int = 20,
        search: Optional[str] = None,
        role: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> AdminUserListResponse:
        """Get users for admin management"""
        try:
            query = self.db.query(User)
            
            # Apply filters
            if search:
                search_term = f"%{search}%"
                query = query.filter(
                    or_(
                        User.username.ilike(search_term),
                        User.email.ilike(search_term),
                        User.first_name.ilike(search_term),
                        User.last_name.ilike(search_term)
                    )
                )
            
            if role:
                query = query.filter(User.role == role)
            
            if is_active is not None:
                query = query.filter(User.is_active == is_active)
            
            # Get total count
            total = query.count()
            
            # Apply pagination
            users = query.offset((page - 1) * size).limit(size).all()
            
            # Build user responses
            user_responses = []
            for user in users:
                user_responses.append(self._build_admin_user_response(user))
            
            # Calculate pagination info
            total_pages = (total + size - 1) // size
            has_next = page < total_pages
            has_prev = page > 1
            
            return AdminUserListResponse(
                users=user_responses,
                total_count=total,
                page=page,
                size=size,
                total_pages=total_pages,
                has_next=has_next,
                has_prev=has_prev
            )
            
        except Exception as e:
            raise ValidationException(f"Failed to get admin users: {str(e)}")
    
    # =============================================================================
    # ADMIN DASHBOARD
    # =============================================================================
    
    def get_admin_dashboard_stats(self) -> AdminDashboardStats:
        """Get admin dashboard statistics"""
        try:
            # Product statistics
            total_products = self.db.query(Product).count()
            active_products = self.db.query(Product).filter(Product.is_active == True).count()
            draft_products = self.db.query(Product).filter(Product.status == "draft").count()
            out_of_stock_products = self.db.query(Product).filter(Product.stock_quantity == 0).count()
            
            # User statistics
            total_users = self.db.query(User).count()
            active_users = self.db.query(User).filter(User.is_active == True).count()
            
            # Order statistics
            total_orders = self.db.query(Order).count()
            pending_orders = self.db.query(Order).filter(Order.order_status == "pending").count()
            
            # Revenue statistics (mock data for now)
            total_revenue = 50000.00
            monthly_revenue = 8500.00
            
            # Low stock alerts
            low_stock_products = self.db.query(Product).filter(
                and_(
                    Product.stock_quantity <= Product.min_stock_level,
                    Product.stock_quantity > 0
                )
            ).count()
            
            # Recent activities (mock data for now)
            recent_activities = [
                {
                    "action": "Product created",
                    "resource": "iPhone 15 Pro",
                    "user": "admin@labanita.com",
                    "timestamp": datetime.utcnow().isoformat()
                },
                {
                    "action": "Order status updated",
                    "resource": "ORD-2024-001",
                    "user": "moderator@labanita.com",
                    "timestamp": (datetime.utcnow() - timedelta(hours=2)).isoformat()
                }
            ]
            
            return AdminDashboardStats(
                total_products=total_products,
                active_products=active_products,
                draft_products=draft_products,
                out_of_stock_products=out_of_stock_products,
                total_users=total_users,
                active_users=active_users,
                total_orders=total_orders,
                pending_orders=pending_orders,
                total_revenue=total_revenue,
                monthly_revenue=monthly_revenue,
                low_stock_alerts=low_stock_products,
                recent_activities=recent_activities
            )
            
        except Exception as e:
            raise ValidationException(f"Failed to get admin dashboard stats: {str(e)}")
    
    # =============================================================================
    # HELPER METHODS
    # =============================================================================
    
    def _build_admin_product_response(self, product: Product) -> AdminProductResponse:
        """Build admin product response from database model"""
        # Get category name
        category_name = "Unknown"
        if hasattr(product, 'category') and product.category:
            category_name = product.category.category_name
        
        # Mock data for views, sales, ratings (in real implementation, these would come from analytics)
        views_count = getattr(product, 'views_count', 0)
        sales_count = getattr(product, 'sales_count', 0)
        rating_average = getattr(product, 'rating_average', 0.0)
        rating_count = getattr(product, 'rating_count', 0)
        
        return AdminProductResponse(
            product_id=str(product.product_id),
            product_name=product.product_name,
            description=product.description,
            short_description=getattr(product, 'short_description', None),
            category_id=str(product.category_id),
            category_name=category_name,
            brand=getattr(product, 'brand', None),
            sku=product.sku,
            barcode=getattr(product, 'barcode', None),
            price=product.price,
            compare_price=getattr(product, 'compare_price', None),
            cost_price=getattr(product, 'cost_price', None),
            weight=getattr(product, 'weight', None),
            dimensions=getattr(product, 'dimensions', None),
            stock_quantity=product.stock_quantity,
            min_stock_level=getattr(product, 'min_stock_level', 0),
            max_stock_level=getattr(product, 'max_stock_level', None),
            is_featured=product.is_featured,
            is_active=product.is_active,
            status=product.status,
            tags=getattr(product, 'tags', []),
            images=getattr(product, 'images', []),
            main_image=getattr(product, 'main_image', None),
            seo_title=getattr(product, 'seo_title', None),
            seo_description=getattr(product, 'seo_description', None),
            seo_keywords=getattr(product, 'seo_keywords', []),
            meta_data=getattr(product, 'meta_data', None),
            notes=getattr(product, 'notes', None),
            views_count=views_count,
            sales_count=sales_count,
            rating_average=rating_average,
            rating_count=rating_count,
            created_at=product.created_at,
            updated_at=product.updated_at,
            created_by=getattr(product, 'created_by', 'system'),
            last_modified_by=getattr(product, 'last_modified_by', 'system')
        )
    
    def _build_admin_user_response(self, user: User) -> AdminUserResponse:
        """Build admin user response from database model"""
        # Mock data for orders and spending (in real implementation, these would come from analytics)
        total_orders = getattr(user, 'total_orders', 0)
        total_spent = getattr(user, 'total_spent', 0.0)
        
        return AdminUserResponse(
            user_id=str(user.user_id),
            username=user.username,
            email=user.email,
            first_name=user.first_name,
            last_name=user.last_name,
            phone_number=getattr(user, 'phone_number', None),
            is_active=user.is_active,
            is_verified=getattr(user, 'is_verified', False),
            role=getattr(user, 'role', 'user'),
            points_balance=getattr(user, 'points_balance', 0),
            total_orders=total_orders,
            total_spent=total_spent,
            last_login=getattr(user, 'last_login', None),
            created_at=user.created_at,
            updated_at=user.updated_at
        )
    
    def _build_admin_products_summary(self, products: List[Product]) -> Dict[str, Any]:
        """Build summary for admin products"""
        if not products:
            return {
                "total_products": 0,
                "active_products": 0,
                "draft_products": 0,
                "out_of_stock_products": 0,
                "total_value": 0.0,
                "average_price": 0.0,
                "status_distribution": {},
                "category_distribution": {}
            }
        
        total_products = len(products)
        active_products = len([p for p in products if p.is_active])
        draft_products = len([p for p in products if p.status == "draft"])
        out_of_stock_products = len([p for p in products if p.stock_quantity == 0])
        
        total_value = sum(p.price * p.stock_quantity for p in products)
        average_price = sum(p.price for p in products) / total_products if total_products > 0 else 0.0
        
        # Status distribution
        status_distribution = {}
        for product in products:
            status = product.status
            status_distribution[status] = status_distribution.get(status, 0) + 1
        
        # Category distribution
        category_distribution = {}
        for product in products:
            category_id = str(product.category_id)
            category_distribution[category_id] = category_distribution.get(category_id, 0) + 1
        
        return {
            "total_products": total_products,
            "active_products": active_products,
            "draft_products": draft_products,
            "out_of_stock_products": out_of_stock_products,
            "total_value": total_value,
            "average_price": average_price,
            "status_distribution": status_distribution,
            "category_distribution": category_distribution
        }
    
    def _log_admin_activity(
        self,
        user_id: str,
        action: str,
        resource_type: str,
        resource_id: str,
        details: Dict[str, Any]
    ):
        """Log admin activity (mock implementation)"""
        # In a real implementation, this would save to an activity log table
        # For now, we'll just pass through
        pass