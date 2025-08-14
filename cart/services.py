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
from models import CartItem, Product, Category, ProductOffer
from cart.schemas import (
    CartItemResponse, CartSummaryResponse, CartResponse, CartItemListResponse,
    CartItemCreate, CartItemUpdate, CartSummary, CartOperationResponse,
    CartValidationResponse, CartItemStatus
)

class CartService:
    """Cart service for cart management, validation, and operations"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # =============================================================================
    # CART RETRIEVAL
    # =============================================================================
    
    def get_user_cart(self, user_id: str) -> CartResponse:
        """Get complete cart for a user"""
        # Get all cart items for user
        cart_items = self.db.query(CartItem).filter(
            and_(
                CartItem.user_id == user_id,
                CartItem.status != CartItemStatus.REMOVED
            )
        ).all()
        
        if not cart_items:
            # Create empty cart response
            empty_summary = CartSummaryResponse(
                user_id=user_id,
                total_items=0,
                total_quantity=0,
                subtotal=0.0,
                total_discount=0.0,
                total_tax=0.0,
                shipping_cost=0.0,
                total_amount=0.0,
                savings_amount=0.0,
                savings_percentage=0.0,
                applied_offers=[],
                available_offers=[],
                estimated_delivery=None,
                free_shipping_threshold=None,
                items=[]
            )
            
            return CartResponse(
                cart_id=str(uuid.uuid4()),
                user_id=user_id,
                summary=empty_summary,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(days=30)
            )
        
        # Build cart items responses
        cart_item_responses = []
        for item in cart_items:
            cart_item_responses.append(self._build_cart_item_response(item))
        
        # Calculate cart summary
        summary = self._calculate_cart_summary(cart_items, user_id)
        summary.items = cart_item_responses
        
        # Get or create cart ID (using first item's creation time as cart creation time)
        cart_creation_time = min(item.created_at for item in cart_items)
        cart_update_time = max(item.updated_at for item in cart_items)
        
        return CartResponse(
            cart_id=str(uuid.uuid4()),  # In a real system, this would be stored
            user_id=user_id,
            summary=summary,
            created_at=cart_creation_time,
            updated_at=cart_update_time,
            expires_at=datetime.utcnow() + timedelta(days=30)
        )
    
    def get_cart_items(self, user_id: str) -> CartItemListResponse:
        """Get all cart items for a user"""
        cart_items = self.db.query(CartItem).filter(
            and_(
                CartItem.user_id == user_id,
                CartItem.status != CartItemStatus.REMOVED
            )
        ).all()
        
        cart_item_responses = []
        for item in cart_items:
            cart_item_responses.append(self._build_cart_item_response(item))
        
        summary = self._calculate_cart_summary(cart_items, user_id)
        
        return CartItemListResponse(
            cart_items=cart_item_responses,
            total_count=len(cart_items),
            summary=summary
        )
    
    def get_cart_summary(self, user_id: str) -> CartSummaryResponse:
        """Get cart summary for a user"""
        cart_items = self.db.query(CartItem).filter(
            and_(
                CartItem.user_id == user_id,
                CartItem.status != CartItemStatus.REMOVED
            )
        ).all()
        
        summary = self._calculate_cart_summary(cart_items, user_id)
        
        # Add cart items to summary
        cart_item_responses = []
        for item in cart_items:
            cart_item_responses.append(self._build_cart_item_response(item))
        summary.items = cart_item_responses
        
        return summary
    
    # =============================================================================
    # CART ITEM OPERATIONS
    # =============================================================================
    
    def add_item_to_cart(
        self,
        user_id: str,
        product_id: str,
        quantity: int
    ) -> CartOperationResponse:
        """Add a product to user's cart"""
        try:
            # Validate product exists and is active
            product = self.db.query(Product).filter(
                and_(
                    Product.product_id == product_id,
                    Product.is_active == True
                )
            ).first()
            
            if not product:
                raise ValidationException(f"Product with ID {product_id} not found or inactive")
            
            # Check stock availability
            if product.stock_quantity < quantity:
                raise ValidationException(f"Insufficient stock. Available: {product.stock_quantity}, Requested: {quantity}")
            
            # Check if item already exists in cart
            existing_item = self.db.query(CartItem).filter(
                and_(
                    CartItem.user_id == user_id,
                    CartItem.product_id == product_id,
                    CartItem.status != CartItemStatus.REMOVED
                )
            ).first()
            
            if existing_item:
                # Update existing item quantity
                new_quantity = existing_item.quantity + quantity
                if new_quantity > product.stock_quantity:
                    raise ValidationException(f"Total quantity ({new_quantity}) exceeds available stock ({product.stock_quantity})")
                
                existing_item.quantity = new_quantity
                existing_item.updated_at = datetime.utcnow()
                
                # Update price if it has changed
                if existing_item.unit_price != float(product.price):
                    existing_item.unit_price = float(product.price)
                    existing_item.original_unit_price = float(product.price)
                
                self.db.commit()
                
                # Get updated summary
                updated_summary = self.get_cart_summary(user_id)
                
                return CartOperationResponse(
                    success=True,
                    message=f"Updated quantity for {product.product_name} in cart",
                    cart_item_id=str(existing_item.cart_item_id),
                    updated_summary=updated_summary,
                    validation_errors=[],
                    warnings=[]
                )
            else:
                # Create new cart item
                cart_item_data = CartItemCreate(
                    user_id=user_id,
                    product_id=product_id,
                    quantity=quantity,
                    unit_price=float(product.price),
                    original_unit_price=float(product.price),
                    category_id=str(product.category_id),
                    max_quantity_allowed=product.max_quantity_per_order or 100
                )
                
                new_cart_item = CartItem(
                    cart_item_id=uuid.uuid4(),
                    user_id=cart_item_data.user_id,
                    product_id=cart_item_data.product_id,
                    quantity=cart_item_data.quantity,
                    unit_price=cart_item_data.unit_price,
                    original_unit_price=cart_item_data.original_unit_price,
                    category_id=cart_item_data.category_id,
                    max_quantity_allowed=cart_item_data.max_quantity_allowed,
                    status=CartItemStatus.ACTIVE,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow()
                )
                
                self.db.add(new_cart_item)
                self.db.commit()
                
                # Get updated summary
                updated_summary = self.get_cart_summary(user_id)
                
                return CartOperationResponse(
                    success=True,
                    message=f"Added {product.product_name} to cart",
                    cart_item_id=str(new_cart_item.cart_item_id),
                    updated_summary=updated_summary,
                    validation_errors=[],
                    warnings=[]
                )
                
        except ValidationException:
            raise
        except Exception as e:
            self.db.rollback()
            raise ValidationException(f"Failed to add item to cart: {str(e)}")
    
    def update_cart_item(
        self,
        user_id: str,
        cart_item_id: str,
        quantity: int
    ) -> CartOperationResponse:
        """Update quantity of a cart item"""
        try:
            # Get cart item
            cart_item = self.db.query(CartItem).filter(
                and_(
                    CartItem.cart_item_id == cart_item_id,
                    CartItem.user_id == user_id,
                    CartItem.status != CartItemStatus.REMOVED
                )
            ).first()
            
            if not cart_item:
                raise NotFoundException(f"Cart item with ID {cart_item_id} not found")
            
            # Validate quantity
            if quantity < 1:
                raise ValidationException("Quantity must be at least 1")
            
            if quantity > cart_item.max_quantity_allowed:
                raise ValidationException(f"Quantity cannot exceed {cart_item.max_quantity_allowed}")
            
            # Check stock availability
            product = self.db.query(Product).filter(Product.product_id == cart_item.product_id).first()
            if product and product.stock_quantity < quantity:
                raise ValidationException(f"Insufficient stock. Available: {product.stock_quantity}, Requested: {quantity}")
            
            # Update quantity
            cart_item.quantity = quantity
            cart_item.updated_at = datetime.utcnow()
            
            # Update total price
            cart_item.total_price = quantity * cart_item.unit_price
            cart_item.original_total_price = quantity * cart_item.original_unit_price
            
            self.db.commit()
            
            # Get updated summary
            updated_summary = self.get_cart_summary(user_id)
            
            return CartOperationResponse(
                success=True,
                message=f"Updated quantity for cart item",
                cart_item_id=str(cart_item.cart_item_id),
                updated_summary=updated_summary,
                validation_errors=[],
                warnings=[]
            )
            
        except (NotFoundException, ValidationException):
            raise
        except Exception as e:
            self.db.rollback()
            raise ValidationException(f"Failed to update cart item: {str(e)}")
    
    def remove_cart_item(
        self,
        user_id: str,
        cart_item_id: str
    ) -> CartOperationResponse:
        """Remove a specific item from cart"""
        try:
            # Get cart item
            cart_item = self.db.query(CartItem).filter(
                and_(
                    CartItem.cart_item_id == cart_item_id,
                    CartItem.user_id == user_id,
                    CartItem.status != CartItemStatus.REMOVED
                )
            ).first()
            
            if not cart_item:
                raise NotFoundException(f"Cart item with ID {cart_item_id} not found")
            
            # Soft delete by setting status to REMOVED
            cart_item.status = CartItemStatus.REMOVED
            cart_item.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            # Get updated summary
            updated_summary = self.get_cart_summary(user_id)
            
            return CartOperationResponse(
                success=True,
                message=f"Removed item from cart",
                cart_item_id=str(cart_item.cart_item_id),
                updated_summary=updated_summary,
                validation_errors=[],
                warnings=[]
            )
            
        except NotFoundException:
            raise
        except Exception as e:
            self.db.rollback()
            raise ValidationException(f"Failed to remove cart item: {str(e)}")
    
    def clear_cart(self, user_id: str) -> CartOperationResponse:
        """Clear all items from user's cart"""
        try:
            # Get all active cart items
            cart_items = self.db.query(CartItem).filter(
                and_(
                    CartItem.user_id == user_id,
                    CartItem.status != CartItemStatus.REMOVED
                )
            ).all()
            
            if not cart_items:
                return CartOperationResponse(
                    success=True,
                    message="Cart is already empty",
                    cart_item_id=None,
                    updated_summary=self.get_cart_summary(user_id),
                    validation_errors=[],
                    warnings=[]
                )
            
            # Soft delete all items
            for item in cart_items:
                item.status = CartItemStatus.REMOVED
                item.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            # Get updated summary
            updated_summary = self.get_cart_summary(user_id)
            
            return CartOperationResponse(
                success=True,
                message=f"Cleared {len(cart_items)} items from cart",
                cart_item_id=None,
                updated_summary=updated_summary,
                validation_errors=[],
                warnings=[]
            )
            
        except Exception as e:
            self.db.rollback()
            raise ValidationException(f"Failed to clear cart: {str(e)}")
    
    # =============================================================================
    # CART VALIDATION
    # =============================================================================
    
    def validate_cart(
        self,
        user_id: str,
        validate_stock: bool = True,
        validate_prices: bool = True,
        validate_offers: bool = True,
        check_delivery: bool = False
    ) -> CartValidationResponse:
        """Validate user's cart for issues"""
        try:
            cart_items = self.db.query(CartItem).filter(
                and_(
                    CartItem.user_id == user_id,
                    CartItem.status != CartItemStatus.REMOVED
                )
            ).all()
            
            if not cart_items:
                return CartValidationResponse(
                    is_valid=True,
                    validation_errors=[],
                    warnings=["Cart is empty"],
                    price_changes=[],
                    stock_issues=[],
                    offer_issues=[],
                    recommendations=[]
                )
            
            validation_errors = []
            warnings = []
            price_changes = []
            stock_issues = []
            offer_issues = []
            recommendations = []
            
            for item in cart_items:
                product = self.db.query(Product).filter(Product.product_id == item.product_id).first()
                
                if not product:
                    validation_errors.append(f"Product {item.product_id} no longer exists")
                    continue
                
                if not product.is_active:
                    validation_errors.append(f"Product {product.product_name} is no longer available")
                    continue
                
                # Validate stock
                if validate_stock:
                    if product.stock_quantity < item.quantity:
                        stock_issues.append({
                            "product_id": str(product.product_id),
                            "product_name": product.product_name,
                            "requested_quantity": item.quantity,
                            "available_quantity": product.stock_quantity,
                            "shortage": item.quantity - product.stock_quantity
                        })
                        validation_errors.append(f"Insufficient stock for {product.product_name}")
                
                # Validate prices
                if validate_prices:
                    current_price = float(product.price)
                    if current_price != item.unit_price:
                        price_changes.append({
                            "product_id": str(product.product_id),
                            "product_name": product.product_name,
                            "old_price": item.unit_price,
                            "new_price": current_price,
                            "price_difference": current_price - item.unit_price
                        })
                        warnings.append(f"Price changed for {product.product_name}")
                
                # Validate offers
                if validate_offers and item.applied_offers:
                    # This would typically validate each applied offer
                    # For now, we'll just check if offers are still active
                    pass
                
                # Check delivery options
                if check_delivery:
                    # This would typically check delivery availability
                    # For now, we'll just add a placeholder
                    pass
            
            # Generate recommendations
            if stock_issues:
                recommendations.append("Consider reducing quantities for out-of-stock items")
            
            if price_changes:
                recommendations.append("Review price changes before checkout")
            
            if len(cart_items) == 1:
                recommendations.append("Add more items to qualify for free shipping")
            
            # Check if cart is valid
            is_valid = len(validation_errors) == 0
            
            return CartValidationResponse(
                is_valid=is_valid,
                validation_errors=validation_errors,
                warnings=warnings,
                price_changes=price_changes,
                stock_issues=stock_issues,
                offer_issues=offer_issues,
                recommendations=recommendations
            )
            
        except Exception as e:
            raise ValidationException(f"Failed to validate cart: {str(e)}")
    
    # =============================================================================
    # CART OFFERS
    # =============================================================================
    
    def apply_offer_to_cart(
        self,
        user_id: str,
        offer_id: str
    ) -> CartOperationResponse:
        """Apply an offer to the entire cart"""
        try:
            # Get offer
            offer = self.db.query(ProductOffer).filter(
                and_(
                    ProductOffer.offer_id == offer_id,
                    ProductOffer.is_active == True,
                    ProductOffer.start_date <= datetime.utcnow(),
                    ProductOffer.end_date >= datetime.utcnow()
                )
            ).first()
            
            if not offer:
                raise ValidationException(f"Offer {offer_id} not found or not active")
            
            # Get cart items
            cart_items = self.db.query(CartItem).filter(
                and_(
                    CartItem.user_id == user_id,
                    CartItem.status != CartItemStatus.REMOVED
                )
            ).all()
            
            if not cart_items:
                raise ValidationException("Cart is empty")
            
            # Check if offer is applicable to cart
            cart_total = sum(item.total_price for item in cart_items)
            if offer.min_purchase_amount and cart_total < offer.min_purchase_amount:
                raise ValidationException(f"Cart total (${cart_total:.2f}) is below minimum requirement (${offer.min_purchase_amount:.2f})")
            
            # Apply offer to applicable items
            items_updated = 0
            for item in cart_items:
                if self._is_item_eligible_for_offer(item, offer):
                    # Apply discount
                    if offer.discount_type == "percentage":
                        discount_amount = (item.total_price * offer.discount_value) / 100
                        if offer.max_discount_amount:
                            discount_amount = min(discount_amount, offer.max_discount_amount)
                    elif offer.discount_type == "fixed_amount":
                        discount_amount = min(offer.discount_value, item.total_price)
                    else:
                        discount_amount = 0
                    
                    # Update item with offer
                    if item.applied_offers is None:
                        item.applied_offers = []
                    
                    if offer_id not in item.applied_offers:
                        item.applied_offers.append(offer_id)
                        items_updated += 1
                    
                    item.updated_at = datetime.utcnow()
            
            if items_updated == 0:
                raise ValidationException("No items in cart are eligible for this offer")
            
            self.db.commit()
            
            # Get updated summary
            updated_summary = self.get_cart_summary(user_id)
            
            return CartOperationResponse(
                success=True,
                message=f"Applied offer to {items_updated} items in cart",
                cart_item_id=None,
                updated_summary=updated_summary,
                validation_errors=[],
                warnings=[]
            )
            
        except ValidationException:
            raise
        except Exception as e:
            self.db.rollback()
            raise ValidationException(f"Failed to apply offer: {str(e)}")
    
    def remove_offer_from_cart(
        self,
        user_id: str,
        offer_id: str
    ) -> CartOperationResponse:
        """Remove an offer from the entire cart"""
        try:
            # Get cart items with this offer
            cart_items = self.db.query(CartItem).filter(
                and_(
                    CartItem.user_id == user_id,
                    CartItem.status != CartItemStatus.REMOVED,
                    CartItem.applied_offers.contains([offer_id])
                )
            ).all()
            
            if not cart_items:
                raise ValidationException(f"Offer {offer_id} is not applied to any items in cart")
            
            # Remove offer from items
            items_updated = 0
            for item in cart_items:
                if item.applied_offers and offer_id in item.applied_offers:
                    item.applied_offers.remove(offer_id)
                    items_updated += 1
                    item.updated_at = datetime.utcnow()
            
            self.db.commit()
            
            # Get updated summary
            updated_summary = self.get_cart_summary(user_id)
            
            return CartOperationResponse(
                success=True,
                message=f"Removed offer from {items_updated} items in cart",
                cart_item_id=None,
                updated_summary=updated_summary,
                validation_errors=[],
                warnings=[]
            )
            
        except ValidationException:
            raise
        except Exception as e:
            self.db.rollback()
            raise ValidationException(f"Failed to remove offer: {str(e)}")
    
    # =============================================================================
    # HELPER METHODS
    # =============================================================================
    
    def _build_cart_item_response(self, cart_item: CartItem) -> CartItemResponse:
        """Build cart item response from database model"""
        # Get product details
        product = self.db.query(Product).filter(Product.product_id == cart_item.product_id).first()
        category = self.db.query(Category).filter(Category.category_id == cart_item.category_id).first()
        
        # Calculate discount information
        discount_amount = cart_item.original_total_price - cart_item.total_price
        discount_percentage = (discount_amount / cart_item.original_total_price * 100) if cart_item.original_total_price > 0 else 0
        
        # Determine availability
        is_available = True
        if product:
            is_available = product.is_active and product.stock_quantity >= cart_item.quantity
        else:
            is_available = False
        
        return CartItemResponse(
            cart_item_id=str(cart_item.cart_item_id),
            user_id=str(cart_item.user_id),
            product_id=str(cart_item.product_id),
            product_name=product.product_name if product else "Unknown Product",
            product_image=product.image_url if product else None,
            category_id=str(cart_item.category_id),
            category_name=category.category_name if category else "Unknown Category",
            quantity=cart_item.quantity,
            unit_price=cart_item.unit_price,
            original_unit_price=cart_item.original_unit_price,
            total_price=cart_item.total_price,
            original_total_price=cart_item.original_total_price,
            discount_amount=discount_amount,
            discount_percentage=discount_percentage,
            applied_offers=cart_item.applied_offers or [],
            stock_quantity=product.stock_quantity if product else 0,
            max_quantity_allowed=cart_item.max_quantity_allowed,
            is_available=is_available,
            status=cart_item.status,
            added_at=cart_item.created_at,
            updated_at=cart_item.updated_at
        )
    
    def _calculate_cart_summary(
        self,
        cart_items: List[CartItem],
        user_id: str
    ) -> CartSummaryResponse:
        """Calculate cart summary from cart items"""
        if not cart_items:
            return CartSummaryResponse(
                user_id=user_id,
                total_items=0,
                total_quantity=0,
                subtotal=0.0,
                total_discount=0.0,
                total_tax=0.0,
                shipping_cost=0.0,
                total_amount=0.0,
                savings_amount=0.0,
                savings_percentage=0.0,
                applied_offers=[],
                available_offers=[],
                estimated_delivery=None,
                free_shipping_threshold=50.0,
                items=[]
            )
        
        # Calculate basic totals
        total_items = len(cart_items)
        total_quantity = sum(item.quantity for item in cart_items)
        subtotal = sum(item.total_price for item in cart_items)
        original_subtotal = sum(item.original_total_price for item in cart_items)
        total_discount = original_subtotal - subtotal
        
        # Calculate savings
        savings_amount = total_discount
        savings_percentage = (savings_amount / original_subtotal * 100) if original_subtotal > 0 else 0
        
        # Calculate tax (placeholder - would typically use tax service)
        total_tax = subtotal * 0.15  # 15% tax rate placeholder
        
        # Calculate shipping (placeholder - would typically use shipping service)
        shipping_cost = 0.0
        if subtotal < 50.0:  # Free shipping threshold
            shipping_cost = 5.99
        
        # Calculate final total
        total_amount = subtotal + total_tax + shipping_cost
        
        # Get applied offers
        applied_offers = []
        all_offers = set()
        for item in cart_items:
            if item.applied_offers:
                all_offers.update(item.applied_offers)
        
        for offer_id in all_offers:
            offer = self.db.query(ProductOffer).filter(ProductOffer.offer_id == offer_id).first()
            if offer:
                applied_offers.append({
                    "offer_id": str(offer.offer_id),
                    "offer_name": offer.offer_name,
                    "discount_type": offer.discount_type,
                    "discount_value": offer.discount_value
                })
        
        # Get available offers (placeholder - would typically use offer service)
        available_offers = []
        
        # Estimate delivery (placeholder)
        estimated_delivery = "3-5 business days"
        
        # Free shipping threshold
        free_shipping_threshold = 50.0
        
        return CartSummaryResponse(
            user_id=user_id,
            total_items=total_items,
            total_quantity=total_quantity,
            subtotal=subtotal,
            total_discount=total_discount,
            total_tax=total_tax,
            shipping_cost=shipping_cost,
            total_amount=total_amount,
            savings_amount=savings_amount,
            savings_percentage=savings_percentage,
            applied_offers=applied_offers,
            available_offers=available_offers,
            estimated_delivery=estimated_delivery,
            free_shipping_threshold=free_shipping_threshold,
            items=[]
        )
    
    def _is_item_eligible_for_offer(self, cart_item: CartItem, offer: ProductOffer) -> bool:
        """Check if a cart item is eligible for an offer"""
        # Check if product is in applicable products
        if offer.applicable_products and str(cart_item.product_id) in offer.applicable_products:
            return True
        
        # Check if product category is in applicable categories
        if offer.applicable_categories and str(cart_item.category_id) in offer.applicable_categories:
            return True
        
        # Check if product is excluded
        if offer.excluded_products and str(cart_item.product_id) in offer.excluded_products:
            return False
        
        if offer.excluded_categories and str(cart_item.category_id) in offer.excluded_categories:
            return False
        
        # If no specific products/categories specified, offer applies to all
        if not offer.applicable_products and not offer.applicable_categories:
            return True
        
        return False
    
    def get_cart_analytics(self) -> Dict[str, Any]:
        """Get cart analytics (placeholder implementation)"""
        # This would typically calculate from cart and order data
        return {
            "total_carts": 0,
            "average_cart_value": 0.0,
            "average_items_per_cart": 0.0,
            "cart_abandonment_rate": 0.0,
            "top_products_in_carts": [],
            "cart_conversion_rate": 0.0,
            "average_cart_lifetime": 0.0
        }
    
    def cleanup_expired_carts(self) -> int:
        """Clean up expired cart items (placeholder implementation)"""
        # This would typically remove cart items older than a certain age
        # For now, return 0 as placeholder
        return 0