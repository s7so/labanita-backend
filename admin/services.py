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
from models import Product, Category, User, Order, OrderItem, Promotion
from admin.schemas import (
    AdminProductResponse, AdminProductListResponse, AdminProductFilter,
    AdminProductCreate, AdminProductUpdate, AdminProductCreateRequest,
    AdminProductUpdateRequest, AdminUserResponse, AdminUserListResponse,
    AdminDashboardStats, AdminActivityLog, AdminOrderResponse, AdminOrderListResponse,
    AdminOrderFilter, AdminOrderStatusUpdate, AdminOrderStats, AdminPromotionResponse,
    AdminPromotionListResponse, AdminPromotionFilter, AdminPromotionCreateRequest,
    AdminPromotionUpdateRequest
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
    # ADMIN ORDER MANAGEMENT
    # =============================================================================
    
    def get_admin_orders(
        self,
        filters: Optional[AdminOrderFilter] = None
    ) -> AdminOrderListResponse:
        """Get orders for admin management with filtering and pagination"""
        try:
            query = self.db.query(Order).join(User, Order.user_id == User.user_id)
            
            # Apply filters
            if filters:
                if filters.search:
                    search_term = f"%{filters.search}%"
                    query = query.filter(
                        or_(
                            Order.order_number.ilike(search_term),
                            User.username.ilike(search_term),
                            User.email.ilike(search_term)
                        )
                    )
                
                if filters.order_status:
                    query = query.filter(Order.order_status == filters.order_status)
                
                if filters.payment_status:
                    query = query.filter(Order.payment_status == filters.payment_status)
                
                if filters.shipping_status:
                    query = query.filter(Order.shipping_status == filters.shipping_status)
                
                if filters.order_type:
                    query = query.filter(Order.order_type == filters.order_type)
                
                if filters.shipping_method:
                    query = query.filter(Order.shipping_method == filters.shipping_method)
                
                if filters.amount_min:
                    query = query.filter(Order.total_amount >= filters.amount_min)
                
                if filters.amount_max:
                    query = query.filter(Order.total_amount <= filters.amount_max)
                
                if filters.created_date_from:
                    query = query.filter(Order.created_at >= filters.created_date_from)
                
                if filters.created_date_to:
                    query = query.filter(Order.created_at <= filters.created_date_to)
                
                if filters.delivery_date_from:
                    query = query.filter(Order.estimated_delivery >= filters.delivery_date_from)
                
                if filters.delivery_date_to:
                    query = query.filter(Order.estimated_delivery <= filters.delivery_date_to)
                
                if filters.has_promotions is not None:
                    if filters.has_promotions:
                        query = query.filter(Order.applied_promotions != [])
                    else:
                        query = query.filter(Order.applied_promotions == [])
            
            # Get total count
            total = query.count()
            
            # Apply sorting
            if filters and filters.sort_by:
                sort_field = getattr(Order, filters.sort_by, Order.created_at)
                if filters.sort_order == "asc":
                    query = query.order_by(asc(sort_field))
                else:
                    query = query.order_by(desc(sort_field))
            else:
                query = query.order_by(desc(Order.created_at))
            
            # Apply pagination
            page = filters.page if filters else 1
            size = filters.size if filters else 20
            orders = query.offset((page - 1) * size).limit(size).all()
            
            # Build order responses
            order_responses = []
            for order in orders:
                order_responses.append(self._build_admin_order_response(order))
            
            # Calculate pagination info
            total_pages = (total + size - 1) // size
            has_next = page < total_pages
            has_prev = page > 1
            
            # Build filters applied
            filters_applied = {}
            if filters:
                if filters.search:
                    filters_applied["search"] = filters.search
                if filters.order_status:
                    filters_applied["order_status"] = filters.order_status
                if filters.payment_status:
                    filters_applied["payment_status"] = filters.payment_status
                if filters.shipping_status:
                    filters_applied["shipping_status"] = filters.shipping_status
                if filters.order_type:
                    filters_applied["order_type"] = filters.order_type
                if filters.shipping_method:
                    filters_applied["shipping_method"] = filters.shipping_method
                if filters.amount_min:
                    filters_applied["amount_min"] = filters.amount_min
                if filters.amount_max:
                    filters_applied["amount_max"] = filters.amount_max
            
            # Build summary
            summary = self._build_admin_orders_summary(orders)
            
            return AdminOrderListResponse(
                orders=order_responses,
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
            raise ValidationException(f"Failed to get admin orders: {str(e)}")
    
    def update_admin_order_status(
        self,
        order_id: str,
        status_update: AdminOrderStatusUpdate,
        admin_user_id: str
    ) -> AdminOrderResponse:
        """Update order status (admin)"""
        try:
            # Get existing order
            order = self.db.query(Order).filter(Order.order_id == order_id).first()
            if not order:
                raise NotFoundException(f"Order with ID {order_id} not found")
            
            # Update status fields
            if status_update.order_status:
                order.order_status = status_update.order_status
            
            if status_update.payment_status:
                order.payment_status = status_update.payment_status
            
            if status_update.shipping_status:
                order.shipping_status = status_update.shipping_status
            
            if status_update.admin_notes:
                order.admin_notes = status_update.admin_notes
            
            if status_update.estimated_delivery:
                order.estimated_delivery = status_update.estimated_delivery
            
            if status_update.actual_delivery:
                order.actual_delivery = status_update.actual_delivery
            
            order.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(order)
            
            # Log admin activity
            self._log_admin_activity(
                user_id=admin_user_id,
                action="update_order_status",
                resource_type="order",
                resource_id=order_id,
                details={
                    "new_order_status": status_update.order_status,
                    "new_payment_status": status_update.payment_status,
                    "new_shipping_status": status_update.shipping_status
                }
            )
            
            return self._build_admin_order_response(order)
            
        except NotFoundException:
            raise
        except Exception as e:
            self.db.rollback()
            raise ValidationException(f"Failed to update order status: {str(e)}")
    
    def get_admin_order_stats(self) -> AdminOrderStats:
        """Get admin order statistics"""
        try:
            # Basic order statistics
            total_orders = self.db.query(Order).count()
            total_revenue = self.db.query(func.sum(Order.total_amount)).scalar() or 0.0
            
            # Monthly revenue (mock data for now)
            monthly_revenue = 8500.00
            
            # Calculate average order value
            average_order_value = total_revenue / total_orders if total_orders > 0 else 0.0
            
            # Orders by status
            orders_by_status = {}
            status_counts = self.db.query(
                Order.order_status, func.count(Order.order_id)
            ).group_by(Order.order_status).all()
            
            for status, count in status_counts:
                orders_by_status[status] = count
            
            # Orders by payment status
            orders_by_payment_status = {}
            payment_counts = self.db.query(
                Order.payment_status, func.count(Order.order_id)
            ).group_by(Order.payment_status).all()
            
            for status, count in payment_counts:
                orders_by_payment_status[status] = count
            
            # Orders by shipping status
            orders_by_shipping_status = {}
            shipping_counts = self.db.query(
                Order.shipping_status, func.count(Order.order_id)
            ).group_by(Order.shipping_status).all()
            
            for status, count in shipping_counts:
                orders_by_shipping_status[status] = count
            
            # Mock data for other statistics
            orders_by_month = [
                {"month": "2024-01", "count": 45, "revenue": 12500.00},
                {"month": "2024-02", "count": 52, "revenue": 14800.00},
                {"month": "2024-03", "count": 48, "revenue": 13200.00}
            ]
            
            top_products = [
                {"product_id": "PROD_001", "name": "iPhone 15 Pro", "sales": 25, "revenue": 24999.75},
                {"product_id": "PROD_002", "name": "MacBook Air", "sales": 18, "revenue": 17999.82},
                {"product_id": "PROD_003", "name": "AirPods Pro", "sales": 32, "revenue": 7999.68}
            ]
            
            top_categories = [
                {"category_id": "CAT_001", "name": "Electronics", "orders": 85, "revenue": 50999.25},
                {"category_id": "CAT_002", "name": "Clothing", "orders": 45, "revenue": 8999.55},
                {"category_id": "CAT_003", "name": "Home & Garden", "orders": 28, "revenue": 3999.72}
            ]
            
            delivery_performance = {
                "on_time_delivery": 92.5,
                "average_delivery_time": "2.3 days",
                "delivery_success_rate": 98.7,
                "return_rate": 1.3
            }
            
            return AdminOrderStats(
                total_orders=total_orders,
                total_revenue=total_revenue,
                monthly_revenue=monthly_revenue,
                average_order_value=average_order_value,
                orders_by_status=orders_by_status,
                orders_by_payment_status=orders_by_payment_status,
                orders_by_shipping_status=orders_by_shipping_status,
                orders_by_month=orders_by_month,
                top_products=top_products,
                top_categories=top_categories,
                delivery_performance=delivery_performance
            )
            
        except Exception as e:
            raise ValidationException(f"Failed to get admin order stats: {str(e)}")
    
    # =============================================================================
    # ADMIN PROMOTION MANAGEMENT
    # =============================================================================
    
    def get_admin_promotions(
        self,
        filters: Optional[AdminPromotionFilter] = None
    ) -> AdminPromotionListResponse:
        """Get promotions for admin management with filtering and pagination"""
        try:
            query = self.db.query(Promotion)
            
            # Apply filters
            if filters:
                if filters.search:
                    search_term = f"%{filters.search}%"
                    query = query.filter(
                        or_(
                            Promotion.promotion_name.ilike(search_term),
                            Promotion.description.ilike(search_term)
                        )
                    )
                
                if filters.promotion_type:
                    query = query.filter(Promotion.promotion_type == filters.promotion_type)
                
                if filters.discount_type:
                    query = query.filter(Promotion.discount_type == filters.discount_type)
                
                if filters.is_active is not None:
                    query = query.filter(Promotion.is_active == filters.is_active)
                
                if filters.auto_apply is not None:
                    query = query.filter(Promotion.auto_apply == filters.auto_apply)
                
                if filters.start_date_from:
                    query = query.filter(Promotion.start_date >= filters.start_date_from)
                
                if filters.start_date_to:
                    query = query.filter(Promotion.start_date <= filters.start_date_to)
                
                if filters.end_date_from:
                    query = query.filter(Promotion.end_date >= filters.end_date_from)
                
                if filters.end_date_to:
                    query = query.filter(Promotion.end_date <= filters.end_date_to)
                
                if filters.min_discount_value:
                    query = query.filter(Promotion.discount_value >= filters.min_discount_value)
                
                if filters.max_discount_value:
                    query = query.filter(Promotion.discount_value <= filters.max_discount_value)
            
            # Get total count
            total = query.count()
            
            # Apply sorting
            if filters and filters.sort_by:
                sort_field = getattr(Promotion, filters.sort_by, Promotion.created_at)
                if filters.sort_order == "asc":
                    query = query.order_by(asc(sort_field))
                else:
                    query = query.order_by(desc(sort_field))
            else:
                query = query.order_by(desc(Promotion.created_at))
            
            # Apply pagination
            page = filters.page if filters else 1
            size = filters.size if filters else 20
            promotions = query.offset((page - 1) * size).limit(size).all()
            
            # Build promotion responses
            promotion_responses = []
            for promotion in promotions:
                promotion_responses.append(self._build_admin_promotion_response(promotion))
            
            # Calculate pagination info
            total_pages = (total + size - 1) // size
            has_next = page < total_pages
            has_prev = page > 1
            
            # Build filters applied
            filters_applied = {}
            if filters:
                if filters.search:
                    filters_applied["search"] = filters.search
                if filters.promotion_type:
                    filters_applied["promotion_type"] = filters.promotion_type
                if filters.discount_type:
                    filters_applied["discount_type"] = filters.discount_type
                if filters.is_active is not None:
                    filters_applied["is_active"] = filters.is_active
                if filters.auto_apply is not None:
                    filters_applied["auto_apply"] = filters.auto_apply
            
            # Build summary
            summary = self._build_admin_promotions_summary(promotions)
            
            return AdminPromotionListResponse(
                promotions=promotion_responses,
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
            raise ValidationException(f"Failed to get admin promotions: {str(e)}")
    
    def create_admin_promotion(
        self,
        promotion_data: AdminPromotionCreateRequest,
        admin_user_id: str
    ) -> AdminPromotionResponse:
        """Create new promotion (admin)"""
        try:
            # Create promotion
            new_promotion = Promotion(
                promotion_id=str(uuid.uuid4()),
                promotion_name=promotion_data.promotion_name,
                description=promotion_data.description,
                promotion_type=promotion_data.promotion_type,
                discount_type=promotion_data.discount_type,
                discount_value=promotion_data.discount_value,
                max_discount_amount=promotion_data.max_discount_amount,
                min_order_amount=promotion_data.min_order_amount,
                max_order_amount=promotion_data.max_order_amount,
                applicable_categories=promotion_data.applicable_categories,
                applicable_products=promotion_data.applicable_products,
                excluded_products=promotion_data.excluded_products,
                user_groups=promotion_data.user_groups,
                usage_limit_per_user=promotion_data.usage_limit_per_user,
                total_usage_limit=promotion_data.total_usage_limit,
                current_usage=promotion_data.current_usage,
                start_date=promotion_data.start_date,
                end_date=promotion_data.end_date,
                is_active=promotion_data.is_active,
                priority=promotion_data.priority,
                auto_apply=promotion_data.auto_apply,
                conditions=promotion_data.conditions,
                notes=promotion_data.notes,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            self.db.add(new_promotion)
            self.db.commit()
            self.db.refresh(new_promotion)
            
            # Log admin activity
            self._log_admin_activity(
                user_id=admin_user_id,
                action="create_promotion",
                resource_type="promotion",
                resource_id=new_promotion.promotion_id,
                details={"promotion_name": new_promotion.promotion_name}
            )
            
            return self._build_admin_promotion_response(new_promotion)
            
        except IntegrityError:
            self.db.rollback()
            raise ConflictException("Promotion creation failed due to database constraint")
        except Exception as e:
            self.db.rollback()
            raise ValidationException(f"Failed to create promotion: {str(e)}")
    
    def update_admin_promotion(
        self,
        promotion_id: str,
        promotion_data: AdminPromotionUpdateRequest,
        admin_user_id: str
    ) -> AdminPromotionResponse:
        """Update existing promotion (admin)"""
        try:
            # Get existing promotion
            promotion = self.db.query(Promotion).filter(Promotion.promotion_id == promotion_id).first()
            if not promotion:
                raise NotFoundException(f"Promotion with ID {promotion_id} not found")
            
            # Update fields
            update_fields = promotion_data.dict(exclude_unset=True)
            for field, value in update_fields.items():
                if hasattr(promotion, field):
                    setattr(promotion, field, value)
            
            promotion.updated_at = datetime.utcnow()
            
            self.db.commit()
            self.db.refresh(promotion)
            
            # Log admin activity
            self._log_admin_activity(
                user_id=admin_user_id,
                action="update_promotion",
                resource_type="promotion",
                resource_id=promotion_id,
                details={"updated_fields": list(update_fields.keys())}
            )
            
            return self._build_admin_promotion_response(promotion)
            
        except NotFoundException:
            raise
        except IntegrityError:
            self.db.rollback()
            raise ConflictException("Promotion update failed due to database constraint")
        except Exception as e:
            self.db.rollback()
            raise ValidationException(f"Failed to update promotion: {str(e)}")
    
    def delete_admin_promotion(self, promotion_id: str, admin_user_id: str) -> bool:
        """Delete promotion (admin)"""
        try:
            # Get existing promotion
            promotion = self.db.query(Promotion).filter(Promotion.promotion_id == promotion_id).first()
            if not promotion:
                raise NotFoundException(f"Promotion with ID {promotion_id} not found")
            
            # Check if promotion is currently active
            if promotion.is_active and promotion.start_date <= datetime.utcnow() <= promotion.end_date:
                raise ConflictException("Cannot delete currently active promotion. Consider deactivating instead.")
            
            # Log admin activity before deletion
            self._log_admin_activity(
                user_id=admin_user_id,
                action="delete_promotion",
                resource_type="promotion",
                resource_id=promotion_id,
                details={"promotion_name": promotion.promotion_name}
            )
            
            # Delete promotion
            self.db.delete(promotion)
            self.db.commit()
            
            return True
            
        except NotFoundException:
            raise
        except IntegrityError:
            self.db.rollback()
            raise ConflictException("Promotion deletion failed due to database constraint")
        except Exception as e:
            self.db.rollback()
            raise ValidationException(f"Failed to delete promotion: {str(e)}")
    
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
    
    def _build_admin_order_response(self, order: Order) -> AdminOrderResponse:
        """Build admin order response from database model"""
        # Get user information
        username = "Unknown"
        email = "Unknown"
        if hasattr(order, 'user') and order.user:
            username = order.user.username
            email = order.user.email
        
        # Get order items count and total quantity
        items_count = 0
        total_quantity = 0
        if hasattr(order, 'items') and order.items:
            items_count = len(order.items)
            total_quantity = sum(item.quantity for item in order.items)
        
        return AdminOrderResponse(
            order_id=str(order.order_id),
            order_number=order.order_number,
            user_id=str(order.user_id),
            username=username,
            email=email,
            order_status=order.order_status,
            payment_status=order.payment_status,
            shipping_status=order.shipping_status,
            order_type=getattr(order, 'order_type', 'regular'),
            shipping_method=order.shipping_method,
            subtotal=order.subtotal,
            total_discount=order.total_discount,
            total_tax=order.total_tax,
            shipping_cost=order.shipping_cost,
            total_amount=order.total_amount,
            applied_promotions=order.applied_promotions or [],
            items_count=items_count,
            total_quantity=total_quantity,
            estimated_delivery=order.estimated_delivery,
            actual_delivery=order.actual_delivery,
            notes=getattr(order, 'notes', None),
            admin_notes=getattr(order, 'admin_notes', None),
            created_at=order.created_at,
            updated_at=order.updated_at
        )
    
    def _build_admin_promotion_response(self, promotion: Promotion) -> AdminPromotionResponse:
        """Build admin promotion response from database model"""
        # Mock data for analytics (in real implementation, these would come from analytics)
        total_revenue_generated = getattr(promotion, 'total_revenue_generated', 0.0)
        total_orders_affected = getattr(promotion, 'total_orders_affected', 0)
        average_discount_per_order = getattr(promotion, 'average_discount_per_order', 0.0)
        
        return AdminPromotionResponse(
            promotion_id=str(promotion.promotion_id),
            promotion_name=promotion.promotion_name,
            description=promotion.description,
            promotion_type=promotion.promotion_type,
            discount_type=promotion.discount_type,
            discount_value=promotion.discount_value,
            max_discount_amount=getattr(promotion, 'max_discount_amount', None),
            min_order_amount=getattr(promotion, 'min_order_amount', None),
            max_order_amount=getattr(promotion, 'max_order_amount', None),
            applicable_categories=promotion.applicable_categories or [],
            applicable_products=promotion.applicable_products or [],
            excluded_products=promotion.excluded_products or [],
            user_groups=promotion.user_groups or [],
            usage_limit_per_user=getattr(promotion, 'usage_limit_per_user', None),
            total_usage_limit=getattr(promotion, 'total_usage_limit', None),
            current_usage=getattr(promotion, 'current_usage', 0),
            start_date=promotion.start_date,
            end_date=promotion.end_date,
            is_active=promotion.is_active,
            priority=getattr(promotion, 'priority', 1),
            auto_apply=getattr(promotion, 'auto_apply', False),
            conditions=getattr(promotion, 'conditions', {}),
            notes=getattr(promotion, 'notes', None),
            total_revenue_generated=total_revenue_generated,
            total_orders_affected=total_orders_affected,
            average_discount_per_order=average_discount_per_order,
            created_at=promotion.created_at,
            updated_at=promotion.updated_at,
            created_by=getattr(promotion, 'created_by', 'system'),
            last_modified_by=getattr(promotion, 'last_modified_by', 'system')
        )
    
    def _build_admin_orders_summary(self, orders: List[Order]) -> Dict[str, Any]:
        """Build summary for admin orders"""
        if not orders:
            return {
                "total_orders": 0,
                "total_revenue": 0.0,
                "average_order_value": 0.0,
                "status_distribution": {},
                "payment_status_distribution": {},
                "shipping_status_distribution": {}
            }
        
        total_orders = len(orders)
        total_revenue = sum(order.total_amount for order in orders)
        average_order_value = total_revenue / total_orders if total_orders > 0 else 0.0
        
        # Status distributions
        status_distribution = {}
        payment_status_distribution = {}
        shipping_status_distribution = {}
        
        for order in orders:
            # Order status
            status = order.order_status
            status_distribution[status] = status_distribution.get(status, 0) + 1
            
            # Payment status
            payment_status = order.payment_status
            payment_status_distribution[payment_status] = payment_status_distribution.get(payment_status, 0) + 1
            
            # Shipping status
            shipping_status = order.shipping_status
            shipping_status_distribution[shipping_status] = shipping_status_distribution.get(shipping_status, 0) + 1
        
        return {
            "total_orders": total_orders,
            "total_revenue": total_revenue,
            "average_order_value": average_order_value,
            "status_distribution": status_distribution,
            "payment_status_distribution": payment_status_distribution,
            "shipping_status_distribution": shipping_status_distribution
        }
    
    def _build_admin_promotions_summary(self, promotions: List[Promotion]) -> Dict[str, Any]:
        """Build summary for admin promotions"""
        if not promotions:
            return {
                "total_promotions": 0,
                "active_promotions": 0,
                "expired_promotions": 0,
                "type_distribution": {},
                "discount_type_distribution": {}
            }
        
        total_promotions = len(promotions)
        active_promotions = len([p for p in promotions if p.is_active])
        expired_promotions = len([p for p in promotions if p.end_date < datetime.utcnow()])
        
        # Type distributions
        type_distribution = {}
        discount_type_distribution = {}
        
        for promotion in promotions:
            # Promotion type
            promo_type = promotion.promotion_type
            type_distribution[promo_type] = type_distribution.get(promo_type, 0) + 1
            
            # Discount type
            discount_type = promotion.discount_type
            discount_type_distribution[discount_type] = discount_type_distribution.get(discount_type, 0) + 1
        
        return {
            "total_promotions": total_promotions,
            "active_promotions": active_promotions,
            "expired_promotions": expired_promotions,
            "type_distribution": type_distribution,
            "discount_type_distribution": discount_type_distribution
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