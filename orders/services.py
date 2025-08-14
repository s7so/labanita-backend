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
from models import Order, OrderItem, Product, Category, User, Address, PaymentMethod, Promotion
from orders.schemas import (
    OrderResponse, OrderListResponse, OrderStatusResponse, OrderTrackingResponse,
    OrderCalculationResponse, OrderCreateResponse, OrderCreate, OrderUpdate,
    OrderItemCreate, OrderFilter, PaginationParams, PaginatedOrdersResponse,
    OrderStatsResponse, OrderAnalyticsResponse, OrderHistoryFilter, OrderHistoryResponse,
    OrderHistoryItem, OrderHistorySummary
)

class OrderService:
    """Order service for order management, calculation, creation, and tracking"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # =============================================================================
    # ORDER CALCULATION
    # =============================================================================
    
    def calculate_order(
        self,
        items: List[Dict[str, Any]],
        shipping_address: Dict[str, Any],
        billing_address: Optional[Dict[str, Any]],
        shipping_method: str,
        applied_promotions: List[str],
        user_id: str,
        currency: str = "USD"
    ) -> OrderCalculationResponse:
        """Calculate order totals including taxes, shipping, and discounts"""
        try:
            # Calculate subtotal
            subtotal = sum(item.get('price', 0) * item.get('quantity', 1) for item in items)
            
            # Calculate discounts from promotions
            total_discount = 0.0
            promotion_details = []
            
            for promotion_id in applied_promotions:
                promotion = self.db.query(Promotion).filter(
                    and_(
                        Promotion.promotion_id == promotion_id,
                        Promotion.is_active == True,
                        Promotion.start_date <= datetime.utcnow(),
                        Promotion.end_date >= datetime.utcnow()
                    )
                ).first()
                
                if promotion:
                    # Calculate promotion discount
                    if promotion.discount_type == "percentage":
                        discount_amount = (subtotal * promotion.discount_value) / 100
                        if promotion.max_discount_amount:
                            discount_amount = min(discount_amount, promotion.max_discount_amount)
                    elif promotion.discount_type == "fixed_amount":
                        discount_amount = min(promotion.discount_value, subtotal)
                    else:
                        discount_amount = 0.0
                    
                    total_discount += discount_amount
                    promotion_details.append({
                        "promotion_id": str(promotion.promotion_id),
                        "promotion_name": promotion.promotion_name,
                        "discount_type": promotion.discount_type,
                        "discount_value": promotion.discount_value,
                        "discount_amount": discount_amount
                    })
            
            # Calculate shipping cost
            shipping_cost = self._calculate_shipping_cost(
                items, shipping_address, shipping_method
            )
            
            # Calculate taxes
            total_tax, tax_breakdown = self._calculate_taxes(
                subtotal - total_discount, shipping_address, currency
            )
            
            # Calculate final total
            final_total = subtotal - total_discount + total_tax + shipping_cost
            
            # Get available promotions
            available_promotions = self._get_available_promotions(items, user_id)
            
            # Get shipping options
            shipping_options = self._get_shipping_options(items, shipping_address)
            
            # Calculate estimated delivery
            estimated_delivery = self._calculate_estimated_delivery(
                shipping_method, shipping_address
            )
            
            return OrderCalculationResponse(
                subtotal=subtotal,
                total_discount=total_discount,
                total_tax=total_tax,
                shipping_cost=shipping_cost,
                total_amount=final_total,
                total_savings=total_discount,
                applied_promotions=promotion_details,
                available_promotions=available_promotions,
                tax_breakdown=tax_breakdown,
                shipping_options=shipping_options,
                estimated_delivery=estimated_delivery,
                currency=currency
            )
            
        except Exception as e:
            raise ValidationException(f"Failed to calculate order: {str(e)}")
    
    # =============================================================================
    # ORDER CREATION
    # =============================================================================
    
    def create_order(
        self,
        items: List[Dict[str, Any]],
        shipping_address: Dict[str, Any],
        billing_address: Optional[Dict[str, Any]],
        shipping_method: str,
        payment_method_id: str,
        applied_promotions: List[str],
        order_notes: Optional[str],
        user_id: str,
        currency: str = "USD"
    ) -> OrderCreateResponse:
        """Create a new order"""
        try:
            # Validate user exists
            user = self.db.query(User).filter(User.user_id == user_id).first()
            if not user:
                raise ValidationException(f"User with ID {user_id} not found")
            
            # Validate payment method
            payment_method = self.db.query(PaymentMethod).filter(
                and_(
                    PaymentMethod.payment_method_id == payment_method_id,
                    PaymentMethod.user_id == user_id
                )
            ).first()
            if not payment_method:
                raise ValidationException(f"Payment method with ID {payment_method_id} not found")
            
            # Calculate order totals
            calculation = self.calculate_order(
                items=items,
                shipping_address=shipping_address,
                billing_address=billing_address,
                shipping_method=shipping_method,
                applied_promotions=applied_promotions,
                user_id=user_id,
                currency=currency
            )
            
            # Generate order number
            order_number = self._generate_order_number()
            
            # Create order
            order_data = OrderCreate(
                user_id=user_id,
                order_type="regular",
                shipping_method=shipping_method,
                shipping_address=shipping_address,
                billing_address=billing_address or shipping_address,
                payment_method_id=payment_method_id,
                applied_promotions=applied_promotions,
                order_notes=order_notes,
                currency=currency,
                items=items
            )
            
            new_order = Order(
                order_id=uuid.uuid4(),
                order_number=order_number,
                user_id=order_data.user_id,
                order_status="pending",
                payment_status="pending",
                shipping_status="pending",
                order_type=order_data.order_type,
                shipping_method=order_data.shipping_method,
                subtotal=calculation.subtotal,
                total_discount=calculation.total_discount,
                total_tax=calculation.total_tax,
                shipping_cost=calculation.shipping_cost,
                total_amount=calculation.total_amount,
                applied_promotions=order_data.applied_promotions,
                total_savings=calculation.total_savings,
                shipping_address=order_data.shipping_address,
                billing_address=order_data.billing_address,
                payment_method_id=order_data.payment_method_id,
                notes=order_data.order_notes,
                currency=order_data.currency,
                priority=1,
                tags=[],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            self.db.add(new_order)
            self.db.flush()  # Get the order ID
            
            # Create order items
            order_items = []
            for item in items:
                product = self.db.query(Product).filter(Product.product_id == item['product_id']).first()
                if not product:
                    raise ValidationException(f"Product with ID {item['product_id']} not found")
                
                # Calculate item totals
                item_total = item['price'] * item['quantity']
                item_discount = (item_total * calculation.total_discount / calculation.subtotal) if calculation.subtotal > 0 else 0
                item_final_price = item_total - item_discount
                
                order_item = OrderItem(
                    order_item_id=uuid.uuid4(),
                    order_id=new_order.order_id,
                    product_id=item['product_id'],
                    quantity=item['quantity'],
                    unit_price=item['price'],
                    total_price=item_total,
                    discount_amount=item_discount,
                    discount_percentage=(item_discount / item_total * 100) if item_total > 0 else 0,
                    final_price=item_final_price,
                    applied_promotions=applied_promotions,
                    weight=product.weight,
                    dimensions={
                        "length": product.length,
                        "width": product.width,
                        "height": product.height
                    } if product.length and product.width and product.height else None,
                    created_at=datetime.utcnow()
                )
                
                self.db.add(order_item)
                order_items.append(order_item)
            
            # Create order status history
            self._create_order_status_history(new_order.order_id, "pending", "Order created")
            
            self.db.commit()
            
            # Build order response
            order_response = self._build_order_response(new_order, order_items)
            
            return OrderCreateResponse(
                success=True,
                order_id=str(new_order.order_id),
                order_number=order_number,
                message="Order created successfully",
                payment_required=True,
                payment_url=None,  # Would be generated by payment service
                estimated_delivery=calculation.estimated_delivery.get('estimated_date'),
                order_summary=order_response
            )
            
        except ValidationException:
            raise
        except Exception as e:
            self.db.rollback()
            raise ValidationException(f"Failed to create order: {str(e)}")
    
    # =============================================================================
    # ORDER RETRIEVAL
    # =============================================================================
    
    def get_orders(
        self,
        user_id: Optional[str] = None,
        page: int = 1,
        size: int = 20,
        filters: Optional[OrderFilter] = None
    ) -> PaginatedOrdersResponse:
        """Get orders with pagination and filtering"""
        try:
            query = self.db.query(Order)
            
            # Apply filters
            if user_id:
                query = query.filter(Order.user_id == user_id)
            
            if filters:
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
                if filters.min_total:
                    query = query.filter(Order.total_amount >= filters.min_total)
                if filters.max_total:
                    query = query.filter(Order.total_amount <= filters.max_total)
                if filters.date_from:
                    query = query.filter(Order.created_at >= filters.date_from)
                if filters.date_to:
                    query = query.filter(Order.created_at <= filters.date_to)
                if filters.has_promotions:
                    if filters.has_promotions:
                        query = query.filter(Order.applied_promotions != [])
                    else:
                        query = query.filter(Order.applied_promotions == [])
                if filters.search:
                    search_term = f"%{filters.search}%"
                    query = query.filter(
                        or_(
                            Order.order_number.ilike(search_term),
                            Order.notes.ilike(search_term)
                        )
                    )
            
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
            orders = query.offset((page - 1) * size).limit(size).all()
            
            # Build responses
            order_responses = []
            for order in orders:
                order_items = self.db.query(OrderItem).filter(OrderItem.order_id == order.order_id).all()
                order_responses.append(self._build_order_response(order, order_items))
            
            # Calculate pagination info
            total_pages = (total + size - 1) // size
            has_next = page < total_pages
            has_prev = page > 1
            
            return PaginatedOrdersResponse(
                orders=order_responses,
                page=page,
                size=size,
                total=total,
                pages=total_pages,
                has_next=has_next,
                has_prev=has_prev
            )
            
        except Exception as e:
            raise ValidationException(f"Failed to get orders: {str(e)}")
    
    def get_order_by_id(self, order_id: str, user_id: Optional[str] = None) -> OrderResponse:
        """Get a specific order by ID"""
        try:
            query = self.db.query(Order).filter(Order.order_id == order_id)
            
            if user_id:
                query = query.filter(Order.user_id == user_id)
            
            order = query.first()
            
            if not order:
                raise NotFoundException(f"Order with ID {order_id} not found")
            
            order_items = self.db.query(OrderItem).filter(OrderItem.order_id == order.order_id).all()
            
            return self._build_order_response(order, order_items)
            
        except NotFoundException:
            raise
        except Exception as e:
            raise ValidationException(f"Failed to get order: {str(e)}")
    
    # =============================================================================
    # ORDER STATUS MANAGEMENT
    # =============================================================================
    
    def get_order_status(self, order_id: str, user_id: Optional[str] = None) -> OrderStatusResponse:
        """Get order status and history"""
        try:
            order = self.get_order_by_id(order_id, user_id)
            
            # Get status history
            status_history = self._get_order_status_history(order_id)
            
            # Calculate progress percentage
            progress_percentage = self._calculate_order_progress(order.order_status)
            
            # Get status description and icon
            status_description, status_icon = self._get_status_info(order.order_status)
            
            # Calculate next expected update
            next_expected_update = self._calculate_next_update(order.order_status, order.created_at)
            
            return OrderStatusResponse(
                order_id=str(order.order_id),
                order_number=order.order_number,
                current_status=order.order_status,
                status_history=status_history,
                estimated_delivery=order.estimated_delivery,
                last_update=order.updated_at,
                next_expected_update=next_expected_update,
                status_description=status_description,
                status_icon=status_icon,
                progress_percentage=progress_percentage
            )
            
        except NotFoundException:
            raise
        except Exception as e:
            raise ValidationException(f"Failed to get order status: {str(e)}")
    
    def cancel_order(self, order_id: str, reason: str, user_id: str) -> Dict[str, Any]:
        """Cancel an order"""
        try:
            order = self.db.query(Order).filter(
                and_(
                    Order.order_id == order_id,
                    Order.user_id == user_id
                )
            ).first()
            
            if not order:
                raise NotFoundException(f"Order with ID {order_id} not found")
            
            # Check if order can be cancelled
            if order.order_status in ["shipped", "delivered", "cancelled"]:
                raise ValidationException(f"Order cannot be cancelled in current status: {order.order_status}")
            
            # Update order status
            order.order_status = "cancelled"
            order.payment_status = "cancelled"
            order.cancelled_at = datetime.utcnow()
            order.updated_at = datetime.utcnow()
            
            # Create status history entry
            self._create_order_status_history(order_id, "cancelled", f"Order cancelled: {reason}")
            
            self.db.commit()
            
            return {
                "success": True,
                "message": "Order cancelled successfully",
                "order_id": str(order.order_id),
                "order_number": order.order_number,
                "cancelled_at": order.cancelled_at,
                "reason": reason
            }
            
        except (NotFoundException, ValidationException):
            raise
        except Exception as e:
            self.db.rollback()
            raise ValidationException(f"Failed to cancel order: {str(e)}")
    
    # =============================================================================
    # ORDER TRACKING
    # =============================================================================
    
    def get_order_tracking(self, order_id: str, user_id: Optional[str] = None) -> OrderTrackingResponse:
        """Get order tracking information"""
        try:
            order = self.get_order_by_id(order_id, user_id)
            
            # Get tracking events (placeholder - would typically come from shipping service)
            tracking_events = self._get_tracking_events(order_id)
            
            # Get last event
            last_event = tracking_events[-1] if tracking_events else None
            
            # Calculate delivery attempts
            delivery_attempts = len([e for e in tracking_events if e.get('event_type') == 'delivery_attempt'])
            
            # Check if delivered
            is_delivered = order.order_status == "delivered"
            
            return OrderTrackingResponse(
                order_id=str(order.order_id),
                order_number=order.order_number,
                tracking_number=order.tracking_number,
                carrier=order.carrier,
                tracking_url=order.tracking_url if hasattr(order, 'tracking_url') else None,
                current_location=last_event.get('location') if last_event else None,
                estimated_delivery=order.estimated_delivery,
                tracking_events=tracking_events,
                last_event=last_event,
                delivery_attempts=delivery_attempts,
                is_delivered=is_delivered,
                delivery_notes=order.notes if order.order_status == "delivered" else None
            )
            
        except NotFoundException:
            raise
        except Exception as e:
            raise ValidationException(f"Failed to get order tracking: {str(e)}")
    
    # =============================================================================
    # ORDER REORDERING
    # =============================================================================
    
    def reorder(
        self,
        order_id: str,
        include_all_items: bool,
        selected_items: Optional[List[str]] = None,
        update_quantities: Optional[Dict[str, int]] = None,
        new_shipping_address: Optional[Dict[str, Any]] = None,
        new_payment_method: Optional[str] = None,
        user_id: str = None
    ) -> OrderCreateResponse:
        """Create a new order based on an existing order"""
        try:
            # Get original order
            original_order = self.get_order_by_id(order_id, user_id)
            
            # Prepare items for reorder
            if include_all_items:
                reorder_items = []
                for item in original_order.items:
                    quantity = update_quantities.get(str(item.order_item_id), item.quantity) if update_quantities else item.quantity
                    reorder_items.append({
                        "product_id": item.product_id,
                        "quantity": quantity,
                        "price": item.unit_price
                    })
            else:
                if not selected_items:
                    raise ValidationException("Selected items must be specified when not including all items")
                
                reorder_items = []
                for item in original_order.items:
                    if str(item.order_item_id) in selected_items:
                        quantity = update_quantities.get(str(item.order_item_id), item.quantity) if update_quantities else item.quantity
                        reorder_items.append({
                            "product_id": item.product_id,
                            "quantity": quantity,
                            "price": item.unit_price
                        })
            
            if not reorder_items:
                raise ValidationException("No items selected for reorder")
            
            # Use new or original addresses and payment method
            shipping_address = new_shipping_address or original_order.shipping_address
            billing_address = new_shipping_address or original_order.billing_address
            payment_method_id = new_payment_method or original_order.payment_method.get('payment_method_id')
            
            # Create new order
            return self.create_order(
                items=reorder_items,
                shipping_address=shipping_address,
                billing_address=billing_address,
                shipping_method=original_order.shipping_method,
                payment_method_id=payment_method_id,
                applied_promotions=[],  # Start fresh with promotions
                order_notes=f"Reorder of order {original_order.order_number}",
                user_id=user_id or original_order.user_id,
                currency=original_order.currency
            )
            
        except (NotFoundException, ValidationException):
            raise
        except Exception as e:
            raise ValidationException(f"Failed to reorder: {str(e)}")
    
    # =============================================================================
    # ORDER HISTORY MANAGEMENT
    # =============================================================================
    
    def get_order_history(
        self,
        user_id: str,
        filters: Optional[OrderHistoryFilter] = None
    ) -> OrderHistoryResponse:
        """Get order history for a user with filtering and pagination"""
        try:
            query = self.db.query(Order).filter(Order.user_id == user_id)
            
            # Apply filters
            if filters:
                if filters.status:
                    query = query.filter(Order.order_status == filters.status)
                
                if filters.date_from:
                    query = query.filter(Order.created_at >= filters.date_from)
                
                if filters.date_to:
                    query = query.filter(Order.created_at <= filters.date_to)
                
                if filters.min_amount:
                    query = query.filter(Order.total_amount >= filters.min_amount)
                
                if filters.max_amount:
                    query = query.filter(Order.total_amount <= filters.max_amount)
                
                if filters.shipping_method:
                    query = query.filter(Order.shipping_method == filters.shipping_method)
                
                if filters.has_promotions is not None:
                    if filters.has_promotions:
                        query = query.filter(Order.applied_promotions != [])
                    else:
                        query = query.filter(Order.applied_promotions == [])
                
                if filters.search:
                    search_term = f"%{filters.search}%"
                    query = query.filter(
                        or_(
                            Order.order_number.ilike(search_term),
                            Order.notes.ilike(search_term)
                        )
                    )
            
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
            
            # Build history items
            history_items = []
            for order in orders:
                history_items.append(self._build_order_history_item(order))
            
            # Calculate pagination info
            total_pages = (total + size - 1) // size
            has_next = page < total_pages
            has_prev = page > 1
            
            # Build filters applied
            filters_applied = {}
            if filters:
                if filters.status:
                    filters_applied["status"] = filters.status
                if filters.date_from:
                    filters_applied["date_from"] = filters.date_from.isoformat()
                if filters.date_to:
                    filters_applied["date_to"] = filters.date_to.isoformat()
                if filters.min_amount:
                    filters_applied["min_amount"] = filters.min_amount
                if filters.max_amount:
                    filters_applied["max_amount"] = filters.max_amount
                if filters.shipping_method:
                    filters_applied["shipping_method"] = filters.shipping_method
                if filters.has_promotions is not None:
                    filters_applied["has_promotions"] = filters.has_promotions
                if filters.search:
                    filters_applied["search"] = filters.search
            
            # Build summary
            summary = self._build_order_history_summary(orders)
            
            return OrderHistoryResponse(
                orders=history_items,
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
            raise ValidationException(f"Failed to get order history: {str(e)}")
    
    def get_order_history_summary(
        self,
        user_id: str,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> OrderHistorySummary:
        """Get summary statistics for user's order history"""
        try:
            query = self.db.query(Order).filter(Order.user_id == user_id)
            
            # Apply date filters if provided
            if date_from:
                query = query.filter(Order.created_at >= date_from)
            if date_to:
                query = query.filter(Order.created_at <= date_to)
            
            orders = query.all()
            
            if not orders:
                return OrderHistorySummary(
                    total_orders=0,
                    total_revenue=0.0,
                    average_order_value=0.0,
                    orders_by_status={},
                    orders_by_month=[],
                    total_savings=0.0,
                    most_used_shipping_method="none",
                    delivery_success_rate=0.0
                )
            
            # Calculate basic statistics
            total_orders = len(orders)
            total_revenue = sum(order.total_amount for order in orders)
            average_order_value = total_revenue / total_orders if total_orders > 0 else 0.0
            total_savings = sum(order.total_savings for order in orders)
            
            # Calculate orders by status
            orders_by_status = {}
            for order in orders:
                status = order.order_status
                orders_by_status[status] = orders_by_status.get(status, 0) + 1
            
            # Calculate orders by month
            orders_by_month = self._calculate_orders_by_month(orders)
            
            # Calculate most used shipping method
            shipping_methods = {}
            for order in orders:
                method = order.shipping_method
                shipping_methods[method] = shipping_methods.get(method, 0) + 1
            
            most_used_shipping_method = max(shipping_methods.items(), key=lambda x: x[1])[0] if shipping_methods else "none"
            
            # Calculate delivery success rate
            successful_deliveries = len([o for o in orders if o.order_status == "delivered"])
            delivery_success_rate = (successful_deliveries / total_orders * 100) if total_orders > 0 else 0.0
            
            return OrderHistorySummary(
                total_orders=total_orders,
                total_revenue=total_revenue,
                average_order_value=average_order_value,
                orders_by_status=orders_by_status,
                orders_by_month=orders_by_month,
                total_savings=total_savings,
                most_used_shipping_method=most_used_shipping_method,
                delivery_success_rate=delivery_success_rate
            )
            
        except Exception as e:
            raise ValidationException(f"Failed to get order history summary: {str(e)}")
    
    # =============================================================================
    # HELPER METHODS
    # =============================================================================
    
    def _build_order_response(self, order: Order, order_items: List[OrderItem]) -> OrderResponse:
        """Build order response from database model"""
        # Build order items responses
        item_responses = []
        for item in order_items:
            product = self.db.query(Product).filter(Product.product_id == item.product_id).first()
            category = self.db.query(Category).filter(Category.category_id == product.category_id).first() if product else None
            
            item_responses.append({
                "order_item_id": str(item.order_item_id),
                "order_id": str(item.order_id),
                "product_id": str(item.product_id),
                "product_name": product.product_name if product else "Unknown Product",
                "product_image": product.image_url if product else None,
                "category_id": str(product.category_id) if product else None,
                "category_name": category.category_name if category else "Unknown Category",
                "quantity": item.quantity,
                "unit_price": item.unit_price,
                "total_price": item.total_price,
                "discount_amount": item.discount_amount,
                "discount_percentage": item.discount_percentage,
                "final_price": item.final_price,
                "applied_promotions": item.applied_promotions or [],
                "weight": item.weight,
                "dimensions": item.dimensions,
                "created_at": item.created_at
            })
        
        # Get payment method details
        payment_method = self.db.query(PaymentMethod).filter(
            PaymentMethod.payment_method_id == order.payment_method_id
        ).first()
        
        payment_method_details = {
            "payment_method_id": str(payment_method.payment_method_id),
            "payment_type": payment_method.payment_type,
            "card_last_four": payment_method.card_last_four,
            "expiry_month": payment_method.expiry_month,
            "expiry_year": payment_method.expiry_year
        } if payment_method else {}
        
        return OrderResponse(
            order_id=str(order.order_id),
            order_number=order.order_number,
            user_id=str(order.user_id),
            order_status=order.order_status,
            payment_status=order.payment_status,
            shipping_status=order.shipping_status,
            order_type=order.order_type,
            shipping_method=order.shipping_method,
            subtotal=order.subtotal,
            total_discount=order.total_discount,
            total_tax=order.total_tax,
            shipping_cost=order.shipping_cost,
            total_amount=order.total_amount,
            applied_promotions=order.applied_promotions or [],
            total_savings=order.total_savings,
            shipping_address=order.shipping_address,
            billing_address=order.billing_address,
            estimated_delivery=order.estimated_delivery,
            actual_delivery=order.actual_delivery,
            payment_method=payment_method_details,
            transaction_id=order.transaction_id,
            items=item_responses,
            total_items=len(item_responses),
            total_quantity=sum(item['quantity'] for item in item_responses),
            created_at=order.created_at,
            updated_at=order.updated_at,
            cancelled_at=order.cancelled_at,
            notes=order.notes,
            tags=order.tags or [],
            priority=order.priority
        )
    
    def _build_order_history_item(self, order: Order) -> OrderHistoryItem:
        """Build order history item from database model"""
        return OrderHistoryItem(
            order_id=str(order.order_id),
            order_number=order.order_number,
            order_status=order.order_status,
            payment_status=order.payment_status,
            shipping_status=order.shipping_status,
            total_amount=order.total_amount,
            total_items=len(order.items) if hasattr(order, 'items') else 0,
            total_quantity=sum(item.quantity for item in order.items) if hasattr(order, 'items') else 0,
            shipping_method=order.shipping_method,
            applied_promotions=order.applied_promotions or [],
            total_savings=order.total_savings,
            estimated_delivery=order.estimated_delivery,
            actual_delivery=order.actual_delivery,
            created_at=order.created_at,
            updated_at=order.updated_at,
            cancelled_at=order.cancelled_at
        )
    
    def _build_order_history_summary(self, orders: List[Order]) -> Dict[str, Any]:
        """Build summary for order history"""
        if not orders:
            return {
                "total_orders": 0,
                "total_revenue": 0.0,
                "average_order_value": 0.0,
                "total_savings": 0.0,
                "status_distribution": {},
                "shipping_methods": {}
            }
        
        total_orders = len(orders)
        total_revenue = sum(order.total_amount for order in orders)
        average_order_value = total_revenue / total_orders
        total_savings = sum(order.total_savings for order in orders)
        
        # Status distribution
        status_distribution = {}
        for order in orders:
            status = order.order_status
            status_distribution[status] = status_distribution.get(status, 0) + 1
        
        # Shipping methods
        shipping_methods = {}
        for order in orders:
            method = order.shipping_method
            shipping_methods[method] = shipping_methods.get(method, 0) + 1
        
        return {
            "total_orders": total_orders,
            "total_revenue": total_revenue,
            "average_order_value": average_order_value,
            "total_savings": total_savings,
            "status_distribution": status_distribution,
            "shipping_methods": shipping_methods
        }
    
    def _calculate_orders_by_month(self, orders: List[Order]) -> List[Dict[str, Any]]:
        """Calculate orders grouped by month"""
        monthly_orders = {}
        
        for order in orders:
            month_key = order.created_at.strftime("%Y-%m")
            if month_key not in monthly_orders:
                monthly_orders[month_key] = {
                    "month": month_key,
                    "count": 0,
                    "revenue": 0.0,
                    "savings": 0.0
                }
            
            monthly_orders[month_key]["count"] += 1
            monthly_orders[month_key]["revenue"] += order.total_amount
            monthly_orders[month_key]["savings"] += order.total_savings
        
        # Convert to list and sort by month
        result = list(monthly_orders.values())
        result.sort(key=lambda x: x["month"], reverse=True)
        
        return result
    
    def _calculate_shipping_cost(
        self,
        items: List[Dict[str, Any]],
        shipping_address: Dict[str, Any],
        shipping_method: str
    ) -> float:
        """Calculate shipping cost based on items and method"""
        # This would typically integrate with a shipping service
        # For now, return placeholder calculations
        
        total_weight = sum(
            item.get('weight', 0.5) * item.get('quantity', 1) for item in items
        )
        
        base_shipping = 5.99
        
        if shipping_method == "express":
            return base_shipping * 2
        elif shipping_method == "priority":
            return base_shipping * 1.5
        elif shipping_method == "overnight":
            return base_shipping * 3
        elif shipping_method == "same_day":
            return base_shipping * 4
        elif shipping_method == "pickup":
            return 0.0
        else:  # standard
            return base_shipping
    
    def _calculate_taxes(
        self,
        subtotal: float,
        shipping_address: Dict[str, Any],
        currency: str
    ) -> tuple[float, Dict[str, float]]:
        """Calculate taxes based on address and subtotal"""
        # This would typically integrate with a tax service
        # For now, return placeholder calculations
        
        country = shipping_address.get('country', 'US')
        state = shipping_address.get('state', 'CA')
        
        # Placeholder tax rates
        if country == 'US':
            if state == 'CA':
                tax_rate = 0.085
            elif state == 'NY':
                tax_rate = 0.08875
            else:
                tax_rate = 0.07
        else:
            tax_rate = 0.05
        
        total_tax = subtotal * tax_rate
        
        tax_breakdown = {
            "sales_tax": total_tax,
            "local_tax": 0.0,
            "state_tax": total_tax * 0.8,
            "federal_tax": 0.0
        }
        
        return total_tax, tax_breakdown
    
    def _get_available_promotions(
        self,
        items: List[Dict[str, Any]],
        user_id: str
    ) -> List[Dict[str, Any]]:
        """Get available promotions for the order"""
        # This would typically query active promotions
        # For now, return empty list as placeholder
        return []
    
    def _get_shipping_options(
        self,
        items: List[Dict[str, Any]],
        shipping_address: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Get available shipping options"""
        # This would typically integrate with a shipping service
        # For now, return placeholder options
        
        return [
            {
                "method": "standard",
                "name": "Standard Shipping",
                "cost": 5.99,
                "estimated_days": "3-5 business days"
            },
            {
                "method": "express",
                "name": "Express Shipping",
                "cost": 11.98,
                "estimated_days": "2-3 business days"
            },
            {
                "method": "priority",
                "name": "Priority Shipping",
                "cost": 8.99,
                "estimated_days": "1-2 business days"
            }
        ]
    
    def _calculate_estimated_delivery(
        self,
        shipping_method: str,
        shipping_address: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate estimated delivery date"""
        # This would typically integrate with a shipping service
        # For now, return placeholder calculations
        
        base_days = 3
        
        if shipping_method == "express":
            base_days = 2
        elif shipping_method == "priority":
            base_days = 1
        elif shipping_method == "overnight":
            base_days = 1
        elif shipping_method == "same_day":
            base_days = 0
        
        estimated_date = datetime.utcnow() + timedelta(days=base_days)
        
        return {
            "estimated_date": estimated_date,
            "estimated_days": base_days,
            "shipping_method": shipping_method
        }
    
    def _generate_order_number(self) -> str:
        """Generate unique order number"""
        # This would typically use a sequence or pattern
        # For now, generate a simple timestamp-based number
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        random_suffix = str(uuid.uuid4())[:8].upper()
        return f"ORD-{timestamp}-{random_suffix}"
    
    def _create_order_status_history(
        self,
        order_id: str,
        status: str,
        notes: str
    ):
        """Create order status history entry"""
        # This would typically create a status history record
        # For now, just log the action
        print(f"Order {order_id} status changed to {status}: {notes}")
    
    def _get_order_status_history(self, order_id: str) -> List[Dict[str, Any]]:
        """Get order status history"""
        # This would typically query a status history table
        # For now, return placeholder data
        return [
            {
                "status": "pending",
                "timestamp": datetime.utcnow(),
                "notes": "Order created"
            }
        ]
    
    def _calculate_order_progress(self, status: str) -> int:
        """Calculate order progress percentage"""
        progress_map = {
            "pending": 10,
            "confirmed": 20,
            "processing": 40,
            "shipped": 70,
            "in_transit": 80,
            "out_for_delivery": 90,
            "delivered": 100,
            "cancelled": 0,
            "refunded": 0,
            "returned": 0
        }
        return progress_map.get(status, 0)
    
    def _get_status_info(self, status: str) -> tuple[str, str]:
        """Get status description and icon"""
        status_info = {
            "pending": ("Order received and being processed", "📋"),
            "confirmed": ("Order confirmed and payment verified", "✅"),
            "processing": ("Order is being prepared for shipping", "⚙️"),
            "shipped": ("Order has been shipped", "📦"),
            "in_transit": ("Order is in transit", "🚚"),
            "out_for_delivery": ("Order is out for delivery", "🚛"),
            "delivered": ("Order has been delivered", "🎉"),
            "cancelled": ("Order has been cancelled", "❌"),
            "refunded": ("Order has been refunded", "💰"),
            "returned": ("Order has been returned", "📤")
        }
        return status_info.get(status, ("Unknown status", "❓"))
    
    def _calculate_next_update(self, status: str, created_at: datetime) -> Optional[datetime]:
        """Calculate next expected update time"""
        if status in ["delivered", "cancelled", "refunded", "returned"]:
            return None
        
        # This would typically use business logic
        # For now, return placeholder calculations
        if status == "pending":
            return created_at + timedelta(hours=2)
        elif status == "confirmed":
            return created_at + timedelta(hours=4)
        elif status == "processing":
            return created_at + timedelta(hours=8)
        elif status == "shipped":
            return created_at + timedelta(days=1)
        else:
            return created_at + timedelta(days=1)
    
    def _get_tracking_events(self, order_id: str) -> List[Dict[str, Any]]:
        """Get tracking events for an order"""
        # This would typically integrate with a shipping service
        # For now, return placeholder events
        return [
            {
                "event_type": "order_created",
                "timestamp": datetime.utcnow(),
                "location": "Warehouse",
                "description": "Order has been created and is being processed"
            }
        ]
    
    def get_order_statistics(self) -> OrderStatsResponse:
        """Get order statistics (placeholder implementation)"""
        # This would typically calculate from order data
        return OrderStatsResponse(
            total_orders=0,
            total_revenue=0.0,
            average_order_value=0.0,
            orders_by_status={},
            orders_by_month=[],
            top_products=[],
            conversion_rate=0.0,
            return_rate=0.0
        )
    
    def get_order_analytics(self) -> OrderAnalyticsResponse:
        """Get order analytics (placeholder implementation)"""
        # This would typically calculate from order data
        return OrderAnalyticsResponse(
            total_orders=0,
            total_revenue=0.0,
            total_customers=0,
            repeat_customer_rate=0.0,
            average_order_frequency=0.0,
            top_customers=[],
            order_trends=[],
            revenue_trends=[],
            category_performance=[],
            promotion_effectiveness=[]
        )