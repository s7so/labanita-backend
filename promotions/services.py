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
from models import Promotion, Product, Category, User
from promotions.schemas import (
    PromotionResponse, ActivePromotionsResponse, PromotionValidationResponse,
    PromotionApplicationResponse, PromotionRemovalResponse, UserPromotionResponse,
    UserPromotionsResponse, PromotionCreate, PromotionUpdate, PromotionFilter,
    PaginationParams, PaginatedPromotionsResponse, PromotionStatsResponse,
    PromotionAnalyticsResponse
)

class PromotionService:
    """Promotion service for promotion management, validation, and application"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # =============================================================================
    # PROMOTION RETRIEVAL
    # =============================================================================
    
    def get_active_promotions(
        self,
        user_id: Optional[str] = None,
        category_id: Optional[str] = None,
        promotion_type: Optional[str] = None
    ) -> ActivePromotionsResponse:
        """Get all currently active promotions"""
        query = self.db.query(Promotion).filter(
            and_(
                Promotion.is_active == True,
                Promotion.start_date <= datetime.utcnow(),
                Promotion.end_date >= datetime.utcnow(),
                Promotion.status == "active"
            )
        )
        
        # Apply additional filters
        if category_id:
            query = query.filter(Promotion.applicable_categories.contains([category_id]))
        
        if promotion_type:
            query = query.filter(Promotion.promotion_type == promotion_type)
        
        # Order by priority
        promotions = query.order_by(desc(Promotion.priority)).all()
        
        promotion_responses = [self._build_promotion_response(promotion) for promotion in promotions]
        
        # Get categories with promotions
        categories_with_promotions = self._get_categories_with_promotions(promotions)
        
        # Get promotion types available
        promotion_types_available = list(set(promotion.promotion_type for promotion in promotions))
        
        # Build summary
        summary = self._build_active_promotions_summary(promotions)
        
        # Get user-specific promotions if user_id provided
        user_specific_promotions = []
        if user_id:
            user_specific_promotions = self._get_user_specific_promotions(user_id, promotions)
        
        return ActivePromotionsResponse(
            promotions=promotion_responses,
            total_count=len(promotions),
            categories_with_promotions=categories_with_promotions,
            promotion_types_available=promotion_types_available,
            summary=summary,
            user_specific_promotions=user_specific_promotions
        )
    
    def get_promotion_by_id(self, promotion_id: str) -> PromotionResponse:
        """Get a specific promotion by ID"""
        promotion = self.db.query(Promotion).filter(Promotion.promotion_id == promotion_id).first()
        
        if not promotion:
            raise NotFoundException(f"Promotion with ID {promotion_id} not found")
        
        return self._build_promotion_response(promotion)
    
    def get_promotion_by_code(self, promotion_code: str) -> PromotionResponse:
        """Get a promotion by its code"""
        promotion = self.db.query(Promotion).filter(Promotion.promotion_code == promotion_code).first()
        
        if not promotion:
            raise NotFoundException(f"Promotion with code {promotion_code} not found")
        
        return self._build_promotion_response(promotion)
    
    # =============================================================================
    # PROMOTION VALIDATION
    # =============================================================================
    
    def validate_promotion(
        self,
        promotion_id: str,
        product_ids: List[str],
        category_ids: List[str],
        cart_total: float,
        user_id: str,
        user_groups: List[str] = None,
        purchase_history: Dict[str, Any] = None
    ) -> PromotionValidationResponse:
        """Validate if a promotion can be applied"""
        try:
            # Get promotion
            promotion = self.db.query(Promotion).filter(Promotion.promotion_id == promotion_id).first()
            
            if not promotion:
                return PromotionValidationResponse(
                    is_valid=False,
                    promotion=None,
                    discount_amount=0.0,
                    discount_percentage=0.0,
                    final_price=cart_total,
                    savings_amount=0.0,
                    validation_errors=["Promotion not found"],
                    warnings=[],
                    recommendations=[],
                    terms_and_conditions=[]
                )
            
            # Check if promotion is active
            if not promotion.is_active or promotion.status != "active":
                return PromotionValidationResponse(
                    is_valid=False,
                    promotion=self._build_promotion_response(promotion),
                    discount_amount=0.0,
                    discount_percentage=0.0,
                    final_price=cart_total,
                    savings_amount=0.0,
                    validation_errors=["Promotion is not active"],
                    warnings=[],
                    recommendations=[],
                    terms_and_conditions=[]
                )
            
            # Check date validity
            now = datetime.utcnow()
            if now < promotion.start_date or now > promotion.end_date:
                return PromotionValidationResponse(
                    is_valid=False,
                    promotion=self._build_promotion_response(promotion),
                    discount_amount=0.0,
                    discount_percentage=0.0,
                    final_price=cart_total,
                    savings_amount=0.0,
                    validation_errors=["Promotion is not valid at this time"],
                    warnings=[],
                    recommendations=[],
                    terms_and_conditions=[]
                )
            
            # Check minimum purchase amount
            if promotion.min_purchase_amount and cart_total < promotion.min_purchase_amount:
                return PromotionValidationResponse(
                    is_valid=False,
                    promotion=self._build_promotion_response(promotion),
                    discount_amount=0.0,
                    discount_percentage=0.0,
                    final_price=cart_total,
                    savings_amount=0.0,
                    validation_errors=[f"Cart total must be at least ${promotion.min_purchase_amount}"],
                    warnings=[],
                    recommendations=[f"Add ${promotion.min_purchase_amount - cart_total:.2f} more to cart"],
                    terms_and_conditions=[]
                )
            
            # Check user eligibility
            if not self._is_user_eligible(promotion, user_id, user_groups, purchase_history):
                return PromotionValidationResponse(
                    is_valid=False,
                    promotion=self._build_promotion_response(promotion),
                    discount_amount=0.0,
                    discount_percentage=0.0,
                    final_price=cart_total,
                    savings_amount=0.0,
                    validation_errors=["User is not eligible for this promotion"],
                    warnings=[],
                    recommendations=[],
                    terms_and_conditions=[]
                )
            
            # Check if promotion applies to cart items
            if not self._is_promotion_applicable_to_cart(promotion, product_ids, category_ids):
                return PromotionValidationResponse(
                    is_valid=False,
                    promotion=self._build_promotion_response(promotion),
                    discount_amount=0.0,
                    discount_percentage=0.0,
                    final_price=cart_total,
                    savings_amount=0.0,
                    validation_errors=["Promotion does not apply to cart items"],
                    warnings=[],
                    recommendations=[],
                    terms_and_conditions=[]
                )
            
            # Check usage limits
            if not self._check_usage_limits(promotion, user_id):
                return PromotionValidationResponse(
                    is_valid=False,
                    promotion=self._build_promotion_response(promotion),
                    discount_amount=0.0,
                    discount_percentage=0.0,
                    final_price=cart_total,
                    savings_amount=0.0,
                    validation_errors=["Usage limit exceeded for this promotion"],
                    warnings=[],
                    recommendations=[],
                    terms_and_conditions=[]
                )
            
            # Calculate discount
            discount_amount, discount_percentage = self._calculate_discount(promotion, cart_total)
            final_price = cart_total - discount_amount
            savings_amount = discount_amount
            
            # Build terms and conditions
            terms_and_conditions = self._build_terms_and_conditions(promotion)
            
            return PromotionValidationResponse(
                is_valid=True,
                promotion=self._build_promotion_response(promotion),
                discount_amount=discount_amount,
                discount_percentage=discount_percentage,
                final_price=final_price,
                savings_amount=savings_amount,
                validation_errors=[],
                warnings=[],
                recommendations=[],
                terms_and_conditions=terms_and_conditions
            )
            
        except Exception as e:
            raise ValidationException(f"Failed to validate promotion: {str(e)}")
    
    # =============================================================================
    # PROMOTION APPLICATION
    # =============================================================================
    
    def apply_promotion(
        self,
        promotion_id: str,
        user_id: str,
        cart_items: List[Dict[str, Any]],
        cart_total: float,
        session_id: Optional[str] = None
    ) -> PromotionApplicationResponse:
        """Apply a promotion to cart items"""
        try:
            # Get promotion
            promotion = self.db.query(Promotion).filter(Promotion.promotion_id == promotion_id).first()
            
            if not promotion:
                raise NotFoundException(f"Promotion with ID {promotion_id} not found")
            
            # Validate promotion can be applied
            validation_result = self.validate_promotion(
                promotion_id=promotion_id,
                product_ids=[item.get('product_id') for item in cart_items],
                category_ids=[item.get('category_id') for item in cart_items if item.get('category_id')],
                cart_total=cart_total,
                user_id=user_id
            )
            
            if not validation_result.is_valid:
                raise ValidationException(f"Promotion cannot be applied: {', '.join(validation_result.validation_errors)}")
            
            # Apply promotion to cart items
            applied_items = []
            total_discount = 0.0
            
            for item in cart_items:
                if self._is_item_eligible_for_promotion(promotion, item):
                    item_discount = self._calculate_item_discount(promotion, item)
                    item['applied_discount'] = item_discount
                    item['final_price'] = item.get('price', 0) - item_discount
                    total_discount += item_discount
                    applied_items.append(item)
            
            # Update promotion usage count
            promotion.current_usage_count += 1
            self.db.commit()
            
            # Calculate final totals
            final_cart_total = cart_total - total_discount
            discount_percentage = (total_discount / cart_total * 100) if cart_total > 0 else 0
            
            # Get remaining usage for user
            remaining_usage = None
            if promotion.usage_limit_per_user:
                current_usage = self._get_user_promotion_usage(promotion_id, user_id)
                remaining_usage = max(0, promotion.usage_limit_per_user - current_usage)
            
            return PromotionApplicationResponse(
                success=True,
                promotion_id=str(promotion.promotion_id),
                promotion_name=promotion.promotion_name,
                discount_amount=total_discount,
                discount_percentage=discount_percentage,
                final_cart_total=final_cart_total,
                savings_amount=total_discount,
                applied_items=applied_items,
                remaining_usage=remaining_usage,
                expiration_time=promotion.end_date,
                message=f"Successfully applied {promotion.promotion_name}",
                warnings=[]
            )
            
        except (NotFoundException, ValidationException):
            raise
        except Exception as e:
            self.db.rollback()
            raise ValidationException(f"Failed to apply promotion: {str(e)}")
    
    # =============================================================================
    # PROMOTION REMOVAL
    # =============================================================================
    
    def remove_promotion(
        self,
        promotion_id: str,
        user_id: str,
        cart_items: List[Dict[str, Any]],
        reason: Optional[str] = None
    ) -> PromotionRemovalResponse:
        """Remove a promotion from cart items"""
        try:
            # Get promotion
            promotion = self.db.query(Promotion).filter(Promotion.promotion_id == promotion_id).first()
            
            if not promotion:
                raise NotFoundException(f"Promotion with ID {promotion_id} not found")
            
            # Calculate original cart total
            original_cart_total = sum(item.get('price', 0) for item in cart_items)
            
            # Remove promotion from cart items
            affected_items = []
            removed_discount = 0.0
            
            for item in cart_items:
                if item.get('applied_discount'):
                    removed_discount += item.get('applied_discount', 0)
                    item['applied_discount'] = 0
                    item['final_price'] = item.get('price', 0)
                    affected_items.append(item)
            
            # Calculate new cart total
            new_cart_total = original_cart_total
            
            return PromotionRemovalResponse(
                success=True,
                promotion_id=str(promotion.promotion_id),
                promotion_name=promotion.promotion_name,
                original_cart_total=original_cart_total,
                new_cart_total=new_cart_total,
                removed_discount=removed_discount,
                affected_items=affected_items,
                message=f"Successfully removed {promotion.promotion_name}"
            )
            
        except NotFoundException:
            raise
        except Exception as e:
            raise ValidationException(f"Failed to remove promotion: {str(e)}")
    
    # =============================================================================
    # USER PROMOTIONS
    # =============================================================================
    
    def get_user_promotions(self, user_id: str) -> UserPromotionsResponse:
        """Get all promotions available to a specific user"""
        try:
            # Get user information
            user = self.db.query(User).filter(User.user_id == user_id).first()
            if not user:
                raise NotFoundException(f"User with ID {user_id} not found")
            
            # Get all active promotions
            active_promotions = self.db.query(Promotion).filter(
                and_(
                    Promotion.is_active == True,
                    Promotion.start_date <= datetime.utcnow(),
                    Promotion.end_date >= datetime.utcnow(),
                    Promotion.status == "active"
                )
            ).order_by(desc(Promotion.priority)).all()
            
            available_promotions = []
            applied_promotions = []
            expired_promotions = []
            
            for promotion in active_promotions:
                # Check if user is eligible
                if self._is_user_eligible(promotion, user_id, user_groups=[], purchase_history={}):
                    user_promotion = self._build_user_promotion_response(promotion, user_id)
                    available_promotions.append(user_promotion)
            
            # Get expired promotions for user
            expired_promotions_query = self.db.query(Promotion).filter(
                and_(
                    Promotion.is_active == True,
                    Promotion.end_date < datetime.utcnow()
                )
            ).order_by(desc(Promotion.end_date)).limit(10).all()
            
            for promotion in expired_promotions_query:
                user_promotion = self._build_user_promotion_response(promotion, user_id)
                expired_promotions.append(user_promotion)
            
            # Calculate totals
            total_available = len(available_promotions)
            total_applied = len(applied_promotions)
            total_savings = sum(promotion.estimated_savings for promotion in applied_promotions)
            
            return UserPromotionsResponse(
                user_id=user_id,
                available_promotions=available_promotions,
                applied_promotions=applied_promotions,
                expired_promotions=expired_promotions,
                total_available=total_available,
                total_applied=total_applied,
                total_savings=total_savings
            )
            
        except NotFoundException:
            raise
        except Exception as e:
            raise ValidationException(f"Failed to get user promotions: {str(e)}")
    
    # =============================================================================
    # HELPER METHODS
    # =============================================================================
    
    def _build_promotion_response(self, promotion: Promotion) -> PromotionResponse:
        """Build promotion response from database model"""
        return PromotionResponse(
            promotion_id=str(promotion.promotion_id),
            promotion_name=promotion.promotion_name,
            description=promotion.description,
            promotion_type=promotion.promotion_type,
            discount_type=promotion.discount_type,
            discount_value=float(promotion.discount_value),
            min_purchase_amount=float(promotion.min_purchase_amount) if promotion.min_purchase_amount else None,
            max_discount_amount=float(promotion.max_discount_amount) if promotion.max_discount_amount else None,
            buy_quantity=promotion.buy_quantity,
            get_quantity=promotion.get_quantity,
            applicable_products=promotion.applicable_products or [],
            applicable_categories=promotion.applicable_categories or [],
            excluded_products=promotion.excluded_products or [],
            excluded_categories=promotion.excluded_categories or [],
            user_groups=promotion.user_groups or [],
            usage_limit_per_user=promotion.usage_limit_per_user,
            total_usage_limit=promotion.total_usage_limit,
            current_usage_count=promotion.current_usage_count or 0,
            start_date=promotion.start_date,
            end_date=promotion.end_date,
            is_active=promotion.is_active,
            status=promotion.status,
            priority=promotion.priority,
            trigger_type=promotion.trigger_type,
            conditions=promotion.conditions or {},
            created_at=promotion.created_at,
            updated_at=promotion.updated_at
        )
    
    def _build_user_promotion_response(self, promotion: Promotion, user_id: str) -> UserPromotionResponse:
        """Build user-specific promotion response"""
        # Get current usage for user
        current_usage = self._get_user_promotion_usage(str(promotion.promotion_id), user_id)
        remaining_usage = max(0, (promotion.usage_limit_per_user or 0) - current_usage)
        
        # Check eligibility
        is_eligible = self._is_user_eligible(promotion, user_id, [], {})
        eligibility_reason = "User is eligible" if is_eligible else "User does not meet eligibility criteria"
        
        # Estimate savings (placeholder calculation)
        estimated_savings = float(promotion.discount_value) if promotion.discount_type == "fixed_amount" else 0.0
        
        return UserPromotionResponse(
            promotion_id=str(promotion.promotion_id),
            promotion_name=promotion.promotion_name,
            description=promotion.description,
            promotion_type=promotion.promotion_type,
            discount_type=promotion.discount_type,
            discount_value=float(promotion.discount_value),
            min_purchase_amount=float(promotion.min_purchase_amount) if promotion.min_purchase_amount else None,
            max_discount_amount=float(promotion.max_discount_amount) if promotion.max_discount_amount else None,
            usage_limit_per_user=promotion.usage_limit_per_user,
            current_usage=current_usage,
            remaining_usage=remaining_usage,
            start_date=promotion.start_date,
            end_date=promotion.end_date,
            is_eligible=is_eligible,
            eligibility_reason=eligibility_reason,
            priority=promotion.priority,
            estimated_savings=estimated_savings
        )
    
    def _get_categories_with_promotions(self, promotions: List[Promotion]) -> List[str]:
        """Get list of categories that have active promotions"""
        category_ids = set()
        for promotion in promotions:
            if promotion.applicable_categories:
                category_ids.update(promotion.applicable_categories)
        
        # Get category names
        categories = self.db.query(Category).filter(Category.category_id.in_(list(category_ids))).all()
        return [cat.category_name for cat in categories]
    
    def _build_active_promotions_summary(self, promotions: List[Promotion]) -> Dict[str, Any]:
        """Build summary of active promotions"""
        total_discount_value = sum(promotion.discount_value for promotion in promotions)
        promotion_types = list(set(promotion.promotion_type for promotion in promotions))
        
        return {
            "total_promotions": len(promotions),
            "total_discount_value": total_discount_value,
            "promotion_types": promotion_types,
            "average_priority": sum(promotion.priority for promotion in promotions) / len(promotions) if promotions else 0
        }
    
    def _get_user_specific_promotions(self, user_id: str, promotions: List[Promotion]) -> List[PromotionResponse]:
        """Get promotions specific to a user"""
        user_specific = []
        for promotion in promotions:
            if self._is_user_eligible(promotion, user_id, [], {}):
                user_specific.append(self._build_promotion_response(promotion))
        return user_specific
    
    def _is_user_eligible(
        self,
        promotion: Promotion,
        user_id: str,
        user_groups: List[str],
        purchase_history: Dict[str, Any]
    ) -> bool:
        """Check if a user is eligible for a promotion"""
        # Check user groups
        if promotion.user_groups and not any(group in promotion.user_groups for group in user_groups):
            return False
        
        # Check usage limits
        if promotion.usage_limit_per_user:
            current_usage = self._get_user_promotion_usage(str(promotion.promotion_id), user_id)
            if current_usage >= promotion.usage_limit_per_user:
                return False
        
        # Check total usage limit
        if promotion.total_usage_limit and promotion.current_usage_count >= promotion.total_usage_limit:
            return False
        
        # Check purchase history conditions
        if promotion.conditions:
            if not self._check_purchase_history_conditions(promotion.conditions, purchase_history):
                return False
        
        return True
    
    def _is_promotion_applicable_to_cart(
        self,
        promotion: Promotion,
        product_ids: List[str],
        category_ids: List[str]
    ) -> bool:
        """Check if a promotion applies to cart items"""
        # Check if any products/categories match
        has_applicable_items = False
        
        # Check products
        if promotion.applicable_products:
            has_applicable_items = any(pid in promotion.applicable_products for pid in product_ids)
        
        # Check categories
        if promotion.applicable_categories:
            has_applicable_items = has_applicable_items or any(cid in promotion.applicable_categories for cid in category_ids)
        
        # If no specific products/categories specified, promotion applies to all
        if not promotion.applicable_products and not promotion.applicable_categories:
            has_applicable_items = True
        
        # Check exclusions
        if promotion.excluded_products:
            has_applicable_items = has_applicable_items and not any(pid in promotion.excluded_products for pid in product_ids)
        
        if promotion.excluded_categories:
            has_applicable_items = has_applicable_items and not any(cid in promotion.excluded_categories for cid in category_ids)
        
        return has_applicable_items
    
    def _check_usage_limits(self, promotion: Promotion, user_id: str) -> bool:
        """Check if user can use this promotion based on usage limits"""
        if promotion.usage_limit_per_user:
            current_usage = self._get_user_promotion_usage(str(promotion.promotion_id), user_id)
            if current_usage >= promotion.usage_limit_per_user:
                return False
        
        if promotion.total_usage_limit and promotion.current_usage_count >= promotion.total_usage_limit:
            return False
        
        return True
    
    def _calculate_discount(self, promotion: Promotion, cart_total: float) -> tuple[float, float]:
        """Calculate discount amount and percentage"""
        if promotion.discount_type == "percentage":
            discount_amount = (cart_total * promotion.discount_value) / 100
            if promotion.max_discount_amount:
                discount_amount = min(discount_amount, promotion.max_discount_amount)
            discount_percentage = promotion.discount_value
        elif promotion.discount_type == "fixed_amount":
            discount_amount = min(promotion.discount_value, cart_total)
            discount_percentage = (discount_amount / cart_total * 100) if cart_total > 0 else 0
        else:
            discount_amount = 0.0
            discount_percentage = 0.0
        
        return discount_amount, discount_percentage
    
    def _calculate_item_discount(self, promotion: Promotion, item: Dict[str, Any]) -> float:
        """Calculate discount for a specific item"""
        item_price = item.get('price', 0)
        item_quantity = item.get('quantity', 1)
        total_item_price = item_price * item_quantity
        
        if promotion.discount_type == "percentage":
            discount_amount = (total_item_price * promotion.discount_value) / 100
            if promotion.max_discount_amount:
                discount_amount = min(discount_amount, promotion.max_discount_amount)
        elif promotion.discount_type == "fixed_amount":
            discount_amount = min(promotion.discount_value, total_item_price)
        else:
            discount_amount = 0.0
        
        return discount_amount
    
    def _is_item_eligible_for_promotion(self, promotion: Promotion, item: Dict[str, Any]) -> bool:
        """Check if a cart item is eligible for a promotion"""
        product_id = item.get('product_id')
        category_id = item.get('category_id')
        
        # Check if product is excluded
        if promotion.excluded_products and product_id in promotion.excluded_products:
            return False
        
        if promotion.excluded_categories and category_id in promotion.excluded_categories:
            return False
        
        # Check if product is included
        if promotion.applicable_products:
            return product_id in promotion.applicable_products
        
        if promotion.applicable_categories:
            return category_id in promotion.applicable_categories
        
        # If no specific products/categories specified, item is eligible
        return True
    
    def _check_purchase_history_conditions(self, conditions: Dict[str, Any], purchase_history: Dict[str, Any]) -> bool:
        """Check if purchase history meets promotion conditions"""
        # This would typically implement complex logic based on conditions
        # For now, return True as placeholder
        return True
    
    def _get_user_promotion_usage(self, promotion_id: str, user_id: str) -> int:
        """Get current usage count for a user and promotion"""
        # This would typically query a promotion_usage table
        # For now, return 0 as placeholder
        return 0
    
    def _build_terms_and_conditions(self, promotion: Promotion) -> List[str]:
        """Build terms and conditions for a promotion"""
        terms = []
        
        if promotion.min_purchase_amount:
            terms.append(f"Minimum purchase amount: ${promotion.min_purchase_amount}")
        
        if promotion.usage_limit_per_user:
            terms.append(f"Usage limit: {promotion.usage_limit_per_user} times per user")
        
        if promotion.max_discount_amount:
            terms.append(f"Maximum discount: ${promotion.max_discount_amount}")
        
        terms.append(f"Valid from {promotion.start_date.strftime('%Y-%m-%d')} to {promotion.end_date.strftime('%Y-%m-%d')}")
        
        if promotion.conditions:
            terms.append("Additional terms and conditions may apply")
        
        return terms
    
    def get_promotion_analytics(self) -> Dict[str, Any]:
        """Get promotion analytics (placeholder implementation)"""
        # This would typically calculate from promotion and order data
        return {
            "total_promotions": 0,
            "active_promotions": 0,
            "expired_promotions": 0,
            "scheduled_promotions": 0,
            "total_discount_given": 0.0,
            "total_orders_with_promotions": 0,
            "average_discount_per_order": 0.0,
            "top_performing_promotions": [],
            "promotion_type_distribution": {},
            "category_performance": []
        }