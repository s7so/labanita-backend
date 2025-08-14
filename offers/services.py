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
from models import ProductOffer, Product, Category, Order, OrderItem
from offers.schemas import (
    OfferResponse, ProductOfferResponse, ActiveOffersResponse,
    OfferListResponse, OfferDetailResponse, PaginatedOffersResponse,
    OfferStatsResponse, OfferAnalyticsResponse, OfferValidationResponse,
    OfferCreate, OfferUpdate, OfferFilter, PaginationParams
)

class OfferService:
    """Offer service for offer management, validation, and analytics"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # =============================================================================
    # OFFER RETRIEVAL
    # =============================================================================
    
    def get_all_offers(
        self,
        skip: int = 0,
        limit: int = 100,
        is_active: Optional[bool] = None,
        offer_type: Optional[str] = None,
        discount_type: Optional[str] = None,
        sort_by: str = "priority",
        sort_order: str = "desc"
    ) -> OfferListResponse:
        """Get all offers with optional filtering and sorting"""
        query = self.db.query(ProductOffer)
        
        # Apply filters
        if is_active is not None:
            query = query.filter(ProductOffer.is_active == is_active)
        
        if offer_type:
            query = query.filter(ProductOffer.offer_type == offer_type)
        
        if discount_type:
            query = query.filter(ProductOffer.discount_type == discount_type)
        
        # Apply sorting
        if hasattr(ProductOffer, sort_by):
            sort_column = getattr(ProductOffer, sort_by)
            if sort_order.lower() == "desc":
                query = query.order_by(desc(sort_column))
            else:
                query = query.order_by(asc(sort_column))
        else:
            # Default sorting
            query = query.order_by(desc(ProductOffer.priority))
        
        # Get total count before pagination
        total_count = query.count()
        
        # Apply pagination
        offers = query.offset(skip).limit(limit).all()
        
        # Convert to response format
        offer_responses = []
        for offer in offers:
            offer_responses.append(self._build_offer_response(offer))
        
        # Count different statuses
        active_count = self.db.query(ProductOffer).filter(ProductOffer.is_active == True).count()
        expired_count = self.db.query(ProductOffer).filter(
            and_(
                ProductOffer.end_date < datetime.utcnow(),
                ProductOffer.is_active == True
            )
        ).count()
        scheduled_count = self.db.query(ProductOffer).filter(
            and_(
                ProductOffer.start_date > datetime.utcnow(),
                ProductOffer.is_active == True
            )
        ).count()
        
        return OfferListResponse(
            offers=offer_responses,
            total_count=total_count,
            active_count=active_count,
            expired_count=expired_count,
            scheduled_count=scheduled_count
        )
    
    def get_offer_by_id(self, offer_id: str) -> OfferResponse:
        """Get a specific offer by ID"""
        offer = self.db.query(ProductOffer).filter(ProductOffer.offer_id == offer_id).first()
        
        if not offer:
            raise NotFoundException(f"Offer with ID {offer_id} not found")
        
        return self._build_offer_response(offer)
    
    def get_offer_detail(self, offer_id: str) -> OfferDetailResponse:
        """Get detailed offer information with related data"""
        offer = self.db.query(ProductOffer).filter(ProductOffer.offer_id == offer_id).first()
        
        if not offer:
            raise NotFoundException(f"Offer with ID {offer_id} not found")
        
        # Build offer response
        offer_response = self._build_offer_response(offer)
        
        # Get applicable products details
        applicable_products_details = self._get_applicable_products_details(offer)
        
        # Get usage statistics
        usage_statistics = self._get_offer_usage_statistics(offer_id)
        
        # Get performance metrics
        performance_metrics = self._get_offer_performance_metrics(offer_id)
        
        # Get related offers
        related_offers = self._get_related_offers(offer)
        
        return OfferDetailResponse(
            offer=offer_response,
            applicable_products_details=applicable_products_details,
            usage_statistics=usage_statistics,
            performance_metrics=performance_metrics,
            related_offers=related_offers
        )
    
    # =============================================================================
    # PRODUCT OFFERS
    # =============================================================================
    
    def get_product_offers(
        self,
        product_id: str,
        user_id: Optional[str] = None
    ) -> List[ProductOfferResponse]:
        """Get all offers applicable to a specific product"""
        # Get offers that apply to this product
        offers = self.db.query(ProductOffer).filter(
            and_(
                ProductOffer.is_active == True,
                ProductOffer.start_date <= datetime.utcnow(),
                ProductOffer.end_date >= datetime.utcnow(),
                or_(
                    ProductOffer.applicable_products.contains([product_id]),
                    ProductOffer.applicable_categories.contains(
                        self._get_product_category_id(product_id)
                    )
                )
            )
        ).order_by(desc(ProductOffer.priority)).all()
        
        # Filter out offers that exclude this product
        filtered_offers = []
        for offer in offers:
            if not self._is_product_excluded(offer, product_id):
                filtered_offers.append(offer)
        
        # Convert to response format
        product_offer_responses = []
        for offer in filtered_offers:
            product_offer_responses.append(self._build_product_offer_response(offer, product_id, user_id))
        
        return product_offer_responses
    
    def get_products_with_offers(self) -> List[Dict[str, Any]]:
        """Get all products that have active offers"""
        # Get products with active offers
        products_with_offers = self.db.query(
            Product.product_id,
            Product.product_name,
            Product.price,
            Product.image_url,
            func.count(ProductOffer.offer_id).label('offer_count')
        ).join(
            ProductOffer,
            or_(
                ProductOffer.applicable_products.contains([Product.product_id]),
                ProductOffer.applicable_categories.contains([Product.category_id])
            )
        ).filter(
            and_(
                ProductOffer.is_active == True,
                ProductOffer.start_date <= datetime.utcnow(),
                ProductOffer.end_date >= datetime.utcnow(),
                Product.is_active == True
            )
        ).group_by(
            Product.product_id,
            Product.product_name,
            Product.price,
            Product.image_url
        ).order_by(desc('offer_count')).all()
        
        result = []
        for product in products_with_offers:
            # Get best offer for this product
            best_offer = self._get_best_offer_for_product(str(product.product_id))
            
            result.append({
                "product_id": str(product.product_id),
                "product_name": product.product_name,
                "original_price": float(product.price),
                "image_url": product.image_url,
                "offer_count": int(product.offer_count),
                "best_offer": best_offer
            })
        
        return result
    
    # =============================================================================
    # ACTIVE OFFERS
    # =============================================================================
    
    def get_active_offers(
        self,
        category_id: Optional[str] = None,
        offer_type: Optional[str] = None
    ) -> ActiveOffersResponse:
        """Get all currently active offers"""
        query = self.db.query(ProductOffer).filter(
            and_(
                ProductOffer.is_active == True,
                ProductOffer.start_date <= datetime.utcnow(),
                ProductOffer.end_date >= datetime.utcnow()
            )
        )
        
        # Apply additional filters
        if category_id:
            query = query.filter(ProductOffer.applicable_categories.contains([category_id]))
        
        if offer_type:
            query = query.filter(ProductOffer.offer_type == offer_type)
        
        # Order by priority
        offers = query.order_by(desc(ProductOffer.priority)).all()
        
        offer_responses = [self._build_offer_response(offer) for offer in offers]
        
        # Get categories with offers
        categories_with_offers = self._get_categories_with_offers(offers)
        
        # Get offer types available
        offer_types_available = list(set(offer.offer_type for offer in offers))
        
        # Build summary
        summary = self._build_active_offers_summary(offers)
        
        return ActiveOffersResponse(
            offers=offer_responses,
            total_count=len(offers),
            categories_with_offers=categories_with_offers,
            offer_types_available=offer_types_available,
            summary=summary
        )
    
    # =============================================================================
    # OFFER VALIDATION
    # =============================================================================
    
    def validate_offers(
        self,
        product_ids: List[str],
        category_ids: List[str],
        cart_total: float,
        user_id: Optional[str] = None
    ) -> OfferValidationResponse:
        """Validate which offers can be applied to a cart"""
        # Get all active offers
        active_offers = self.db.query(ProductOffer).filter(
            and_(
                ProductOffer.is_active == True,
                ProductOffer.start_date <= datetime.utcnow(),
                ProductOffer.end_date >= datetime.utcnow()
            )
        ).all()
        
        applicable_offers = []
        validation_errors = []
        recommendations = []
        
        for offer in active_offers:
            # Check if offer applies to cart
            if self._is_offer_applicable_to_cart(offer, product_ids, category_ids, cart_total):
                # Check user usage limits
                if self._check_user_usage_limits(offer, user_id):
                    applicable_offers.append(self._build_offer_response(offer))
                else:
                    validation_errors.append(f"Usage limit exceeded for offer: {offer.offer_name}")
            else:
                # Provide recommendations
                if cart_total < (offer.min_purchase_amount or 0):
                    recommendations.append(
                        f"Add ${offer.min_purchase_amount - cart_total:.2f} more to cart for offer: {offer.offer_name}"
                    )
        
        # Find best offer
        best_offer = self._find_best_offer(applicable_offers, cart_total) if applicable_offers else None
        
        # Calculate total savings
        total_savings = self._calculate_total_savings(applicable_offers, cart_total)
        
        return OfferValidationResponse(
            applicable_offers=applicable_offers,
            best_offer=best_offer,
            total_savings=total_savings,
            validation_errors=validation_errors,
            recommendations=recommendations
        )
    
    # =============================================================================
    # OFFER STATISTICS
    # =============================================================================
    
    def get_offer_statistics(self, offer_id: str) -> OfferStatsResponse:
        """Get comprehensive statistics for an offer"""
        offer = self.db.query(ProductOffer).filter(ProductOffer.offer_id == offer_id).first()
        if not offer:
            raise NotFoundException(f"Offer with ID {offer_id} not found")
        
        # Get usage statistics
        usage_stats = self._get_offer_usage_statistics(offer_id)
        
        # Get performance metrics
        performance_metrics = self._get_offer_performance_metrics(offer_id)
        
        # Calculate performance score
        performance_score = self._calculate_performance_score(usage_stats, performance_metrics)
        
        return OfferStatsResponse(
            offer_id=str(offer.offer_id),
            offer_name=offer.offer_name,
            total_usage=usage_stats.get('total_usage', 0),
            total_discount_given=usage_stats.get('total_discount_given', 0.0),
            average_order_value=performance_metrics.get('average_order_value', 0.0),
            conversion_rate=performance_metrics.get('conversion_rate', 0.0),
            user_engagement=usage_stats.get('unique_users', 0),
            revenue_impact=performance_metrics.get('revenue_impact', 0.0),
            performance_score=performance_score
        )
    
    def get_offer_analytics(self) -> OfferAnalyticsResponse:
        """Get overall offer analytics"""
        # Get basic counts
        total_offers = self.db.query(ProductOffer).count()
        active_offers = self.db.query(ProductOffer).filter(ProductOffer.is_active == True).count()
        expired_offers = self.db.query(ProductOffer).filter(
            and_(
                ProductOffer.end_date < datetime.utcnow(),
                ProductOffer.is_active == True
            )
        ).count()
        scheduled_offers = self.db.query(ProductOffer).filter(
            and_(
                ProductOffer.start_date > datetime.utcnow(),
                ProductOffer.is_active == True
            )
        ).count()
        
        # Get performance data
        total_discount_given = self._calculate_total_discount_given()
        total_orders_with_offers = self._get_total_orders_with_offers()
        average_discount_per_order = self._calculate_average_discount_per_order()
        
        # Get top performing offers
        top_performing_offers = self._get_top_performing_offers()
        
        # Get offer type distribution
        offer_type_distribution = self._get_offer_type_distribution()
        
        # Get category performance
        category_performance = self._get_category_performance_with_offers()
        
        return OfferAnalyticsResponse(
            total_offers=total_offers,
            active_offers=active_offers,
            expired_offers=expired_offers,
            scheduled_offers=scheduled_offers,
            total_discount_given=total_discount_given,
            total_orders_with_offers=total_orders_with_offers,
            average_discount_per_order=average_discount_per_order,
            top_performing_offers=top_performing_offers,
            offer_type_distribution=offer_type_distribution,
            category_performance=category_performance
        )
    
    # =============================================================================
    # PAGINATED OFFERS
    # =============================================================================
    
    def get_offers_paginated(
        self,
        pagination: PaginationParams,
        filters: Optional[OfferFilter] = None
    ) -> PaginatedOffersResponse:
        """Get paginated offers with optional filtering"""
        query = self.db.query(ProductOffer)
        
        # Apply filters if provided
        if filters:
            query = self._apply_offer_filters(query, filters)
        
        # Get total count
        total = query.count()
        
        # Calculate pagination
        pages = (total + pagination.size - 1) // pagination.size
        has_next = pagination.page < pages
        has_prev = pagination.page > 1
        
        # Get offers for current page
        offers = query.offset(pagination.offset).limit(pagination.size).all()
        
        # Convert to response format
        offer_responses = [self._build_offer_response(offer) for offer in offers]
        
        return PaginatedOffersResponse(
            offers=offer_responses,
            page=pagination.page,
            size=pagination.size,
            total=total,
            pages=pages,
            has_next=has_next,
            has_prev=has_prev
        )
    
    # =============================================================================
    # HELPER METHODS
    # =============================================================================
    
    def _build_offer_response(self, offer: ProductOffer) -> OfferResponse:
        """Build offer response from database model"""
        return OfferResponse(
            offer_id=str(offer.offer_id),
            offer_name=offer.offer_name,
            description=offer.description,
            offer_type=offer.offer_type,
            discount_type=offer.discount_type,
            discount_value=float(offer.discount_value),
            min_purchase_amount=float(offer.min_purchase_amount) if offer.min_purchase_amount else None,
            max_discount_amount=float(offer.max_discount_amount) if offer.max_discount_amount else None,
            buy_quantity=offer.buy_quantity,
            get_quantity=offer.get_quantity,
            applicable_products=offer.applicable_products or [],
            applicable_categories=offer.applicable_categories or [],
            excluded_products=offer.excluded_products or [],
            excluded_categories=offer.excluded_categories or [],
            usage_limit_per_user=offer.usage_limit_per_user,
            total_usage_limit=offer.total_usage_limit,
            current_usage_count=offer.current_usage_count or 0,
            start_date=offer.start_date,
            end_date=offer.end_date,
            is_active=offer.is_active,
            status=offer.status,
            priority=offer.priority,
            created_at=offer.created_at,
            updated_at=offer.updated_at
        )
    
    def _build_product_offer_response(
        self,
        offer: ProductOffer,
        product_id: str,
        user_id: Optional[str] = None
    ) -> ProductOfferResponse:
        """Build product offer response from database model"""
        # Get product details
        product = self.db.query(Product).filter(Product.product_id == product_id).first()
        if not product:
            raise NotFoundException(f"Product with ID {product_id} not found")
        
        # Calculate discounted price
        original_price = float(product.price)
        discounted_price = self._calculate_discounted_price(offer, original_price)
        savings_amount = original_price - discounted_price
        savings_percentage = (savings_amount / original_price) * 100 if original_price > 0 else 0
        
        # Get remaining usage for user
        remaining_usage = None
        if user_id and offer.usage_limit_per_user:
            user_usage = self._get_user_offer_usage(offer.offer_id, user_id)
            remaining_usage = max(0, offer.usage_limit_per_user - user_usage)
        
        return ProductOfferResponse(
            offer_id=str(offer.offer_id),
            product_id=product_id,
            offer_name=offer.offer_name,
            description=offer.description,
            offer_type=offer.offer_type,
            discount_type=offer.discount_type,
            discount_value=float(offer.discount_value),
            original_price=original_price,
            discounted_price=discounted_price,
            savings_amount=savings_amount,
            savings_percentage=savings_percentage,
            min_purchase_amount=float(offer.min_purchase_amount) if offer.min_purchase_amount else None,
            max_discount_amount=float(offer.max_discount_amount) if offer.max_discount_amount else None,
            usage_limit_per_user=offer.usage_limit_per_user,
            remaining_usage=remaining_usage,
            start_date=offer.start_date,
            end_date=offer.end_date,
            is_active=offer.is_active,
            priority=offer.priority
        )
    
    def _calculate_discounted_price(self, offer: ProductOffer, original_price: float) -> float:
        """Calculate discounted price based on offer type"""
        if offer.discount_type == "percentage":
            discount_amount = (original_price * offer.discount_value) / 100
            if offer.max_discount_amount:
                discount_amount = min(discount_amount, offer.max_discount_amount)
            return max(0, original_price - discount_amount)
        elif offer.discount_type == "fixed_amount":
            discount_amount = min(offer.discount_value, original_price)
            return max(0, original_price - discount_amount)
        else:
            return original_price
    
    def _get_product_category_id(self, product_id: str) -> str:
        """Get category ID for a product"""
        product = self.db.query(Product).filter(Product.product_id == product_id).first()
        return str(product.category_id) if product else None
    
    def _is_product_excluded(self, offer: ProductOffer, product_id: str) -> bool:
        """Check if a product is excluded from an offer"""
        if offer.excluded_products and product_id in offer.excluded_products:
            return True
        
        product_category = self._get_product_category_id(product_id)
        if offer.excluded_categories and product_category in offer.excluded_categories:
            return True
        
        return False
    
    def _get_best_offer_for_product(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Get the best offer for a specific product"""
        offers = self.get_product_offers(product_id)
        if not offers:
            return None
        
        # Sort by priority and discount value
        best_offer = max(offers, key=lambda x: (x.priority, x.savings_percentage))
        
        return {
            "offer_id": best_offer.offer_id,
            "offer_name": best_offer.offer_name,
            "savings_percentage": best_offer.savings_percentage,
            "savings_amount": best_offer.savings_amount
        }
    
    def _get_categories_with_offers(self, offers: List[ProductOffer]) -> List[str]:
        """Get list of categories that have active offers"""
        category_ids = set()
        for offer in offers:
            if offer.applicable_categories:
                category_ids.update(offer.applicable_categories)
        
        # Get category names
        categories = self.db.query(Category).filter(Category.category_id.in_(list(category_ids))).all()
        return [cat.category_name for cat in categories]
    
    def _build_active_offers_summary(self, offers: List[ProductOffer]) -> Dict[str, Any]:
        """Build summary of active offers"""
        total_discount_value = sum(offer.discount_value for offer in offers)
        offer_types = list(set(offer.offer_type for offer in offers))
        
        return {
            "total_offers": len(offers),
            "total_discount_value": total_discount_value,
            "offer_types": offer_types,
            "average_priority": sum(offer.priority for offer in offers) / len(offers) if offers else 0
        }
    
    def _is_offer_applicable_to_cart(
        self,
        offer: ProductOffer,
        product_ids: List[str],
        category_ids: List[str],
        cart_total: float
    ) -> bool:
        """Check if an offer is applicable to a cart"""
        # Check minimum purchase amount
        if offer.min_purchase_amount and cart_total < offer.min_purchase_amount:
            return False
        
        # Check if any products/categories match
        has_applicable_items = False
        
        # Check products
        if offer.applicable_products:
            has_applicable_items = any(pid in offer.applicable_products for pid in product_ids)
        
        # Check categories
        if offer.applicable_categories:
            has_applicable_items = has_applicable_items or any(cid in offer.applicable_categories for cid in category_ids)
        
        # If no specific products/categories specified, offer applies to all
        if not offer.applicable_products and not offer.applicable_categories:
            has_applicable_items = True
        
        return has_applicable_items
    
    def _check_user_usage_limits(self, offer: ProductOffer, user_id: Optional[str] = None) -> bool:
        """Check if user can use this offer based on usage limits"""
        if not user_id or not offer.usage_limit_per_user:
            return True
        
        current_usage = self._get_user_offer_usage(offer.offer_id, user_id)
        return current_usage < offer.usage_limit_per_user
    
    def _get_user_offer_usage(self, offer_id: str, user_id: str) -> int:
        """Get current usage count for a user and offer"""
        # This would typically query an offer_usage table
        # For now, return 0 as placeholder
        return 0
    
    def _find_best_offer(self, offers: List[OfferResponse], cart_total: float) -> Optional[OfferResponse]:
        """Find the best offer from a list of applicable offers"""
        if not offers:
            return None
        
        # Score offers based on priority and potential savings
        scored_offers = []
        for offer in offers:
            score = offer.priority * 10
            
            # Add bonus for higher discount value
            if offer.discount_type == "percentage":
                score += offer.discount_value
            elif offer.discount_type == "fixed_amount":
                score += (offer.discount_value / cart_total) * 100 if cart_total > 0 else 0
            
            scored_offers.append((score, offer))
        
        # Return offer with highest score
        return max(scored_offers, key=lambda x: x[0])[1]
    
    def _calculate_total_savings(self, offers: List[OfferResponse], cart_total: float) -> float:
        """Calculate total potential savings from offers"""
        total_savings = 0.0
        
        for offer in offers:
            if offer.discount_type == "percentage":
                savings = (cart_total * offer.discount_value) / 100
                if offer.max_discount_amount:
                    savings = min(savings, offer.max_discount_amount)
            elif offer.discount_type == "fixed_amount":
                savings = min(offer.discount_value, cart_total)
            else:
                savings = 0
            
            total_savings += savings
        
        return total_savings
    
    def _get_applicable_products_details(self, offer: ProductOffer) -> List[Dict[str, Any]]:
        """Get details of products applicable to an offer"""
        products = []
        
        if offer.applicable_products:
            product_details = self.db.query(Product).filter(
                Product.product_id.in_(offer.applicable_products)
            ).all()
            
            for product in product_details:
                products.append({
                    "product_id": str(product.product_id),
                    "product_name": product.product_name,
                    "price": float(product.price),
                    "image_url": product.image_url
                })
        
        return products
    
    def _get_offer_usage_statistics(self, offer_id: str) -> Dict[str, Any]:
        """Get usage statistics for an offer"""
        # This would typically query order/offer usage tables
        # For now, return placeholder data
        return {
            "total_usage": 0,
            "total_discount_given": 0.0,
            "unique_users": 0
        }
    
    def _get_offer_performance_metrics(self, offer_id: str) -> Dict[str, Any]:
        """Get performance metrics for an offer"""
        # This would typically calculate from order data
        # For now, return placeholder data
        return {
            "average_order_value": 0.0,
            "conversion_rate": 0.0,
            "revenue_impact": 0.0
        }
    
    def _calculate_performance_score(
        self,
        usage_stats: Dict[str, Any],
        performance_metrics: Dict[str, Any]
    ) -> float:
        """Calculate overall performance score for an offer"""
        # Simple scoring algorithm
        score = 0.0
        
        # Usage score (0-40 points)
        if usage_stats.get('total_usage', 0) > 0:
            score += min(40, usage_stats['total_usage'] * 2)
        
        # Revenue impact score (0-30 points)
        revenue_impact = performance_metrics.get('revenue_impact', 0)
        if revenue_impact > 0:
            score += min(30, revenue_impact / 100)
        
        # Conversion rate score (0-30 points)
        conversion_rate = performance_metrics.get('conversion_rate', 0)
        score += min(30, conversion_rate * 10)
        
        return min(100, score)
    
    def _get_related_offers(self, offer: ProductOffer) -> List[OfferResponse]:
        """Get related or similar offers"""
        # Get offers with similar characteristics
        related_offers = self.db.query(ProductOffer).filter(
            and_(
                ProductOffer.offer_id != offer.offer_id,
                ProductOffer.is_active == True,
                or_(
                    ProductOffer.offer_type == offer.offer_type,
                    ProductOffer.discount_type == offer.discount_type
                )
            )
        ).limit(5).all()
        
        return [self._build_offer_response(rel_offer) for rel_offer in related_offers]
    
    def _apply_offer_filters(self, query, filters: OfferFilter):
        """Apply filters to offer query"""
        if filters.offer_type:
            query = query.filter(ProductOffer.offer_type == filters.offer_type)
        
        if filters.discount_type:
            query = query.filter(ProductOffer.discount_type == filters.discount_type)
        
        if filters.is_active is not None:
            query = query.filter(ProductOffer.is_active == filters.is_active)
        
        if filters.status:
            query = query.filter(ProductOffer.status == filters.status)
        
        if filters.min_discount_value is not None:
            query = query.filter(ProductOffer.discount_value >= filters.min_discount_value)
        
        if filters.max_discount_value is not None:
            query = query.filter(ProductOffer.discount_value <= filters.max_discount_value)
        
        if filters.category_id:
            query = query.filter(ProductOffer.applicable_categories.contains([filters.category_id]))
        
        if filters.product_id:
            query = query.filter(ProductOffer.applicable_products.contains([filters.product_id]))
        
        if filters.start_date_from:
            query = query.filter(ProductOffer.start_date >= filters.start_date_from)
        
        if filters.start_date_to:
            query = query.filter(ProductOffer.start_date <= filters.start_date_to)
        
        if filters.end_date_from:
            query = query.filter(ProductOffer.end_date >= filters.end_date_from)
        
        if filters.end_date_to:
            query = query.filter(ProductOffer.end_date <= filters.end_date_to)
        
        if filters.search:
            search_filter = f"%{filters.search}%"
            query = query.filter(
                or_(
                    ProductOffer.offer_name.ilike(search_filter),
                    ProductOffer.description.ilike(search_filter)
                )
            )
        
        # Apply sorting
        if hasattr(ProductOffer, filters.sort_by):
            sort_column = getattr(ProductOffer, filters.sort_by)
            if filters.sort_order.lower() == "desc":
                query = query.order_by(desc(sort_column))
            else:
                query = query.order_by(asc(sort_column))
        
        return query
    
    def _calculate_total_discount_given(self) -> float:
        """Calculate total discount amount given across all offers"""
        # This would typically query order data
        # For now, return placeholder
        return 0.0
    
    def _get_total_orders_with_offers(self) -> int:
        """Get total number of orders that used offers"""
        # This would typically query order data
        # For now, return placeholder
        return 0
    
    def _calculate_average_discount_per_order(self) -> float:
        """Calculate average discount per order"""
        # This would typically calculate from order data
        # For now, return placeholder
        return 0.0
    
    def _get_top_performing_offers(self) -> List[Dict[str, Any]]:
        """Get top performing offers based on usage and revenue impact"""
        # This would typically query and calculate from order data
        # For now, return placeholder
        return []
    
    def _get_offer_type_distribution(self) -> Dict[str, int]:
        """Get distribution of offer types"""
        # This would typically count from offer data
        # For now, return placeholder
        return {}
    
    def _get_category_performance_with_offers(self) -> List[Dict[str, Any]]:
        """Get category performance data with offers"""
        # This would typically calculate from order and offer data
        # For now, return placeholder
        return []