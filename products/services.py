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
from models import Product, Category, OrderItem, Order
from products.schemas import (
    ProductResponse, ProductListResponse, ProductDetailResponse,
    FeaturedProductsResponse, NewArrivalsResponse, BestSellingProductsResponse,
    ProductSearchResponse, ProductFilterResponse, PaginatedProductsResponse,
    ProductStatsResponse, ProductAnalyticsResponse, RelatedProductsResponse,
    ProductFilter, ProductSearch, PaginationParams
)

class ProductService:
    """Product service for product management, search, and analytics"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # =============================================================================
    # PRODUCT RETRIEVAL
    # =============================================================================
    
    def get_all_products(
        self,
        skip: int = 0,
        limit: int = 100,
        category_id: Optional[str] = None,
        is_active: Optional[bool] = None,
        is_featured: Optional[bool] = None,
        is_new_arrival: Optional[bool] = None,
        is_best_selling: Optional[bool] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> ProductListResponse:
        """Get all products with optional filtering and sorting"""
        query = self.db.query(Product).join(Category, Product.category_id == Category.category_id)
        
        # Apply filters
        if category_id is not None:
            query = query.filter(Product.category_id == category_id)
        
        if is_active is not None:
            query = query.filter(Product.is_active == is_active)
        
        if is_featured is not None:
            query = query.filter(Product.is_featured == is_featured)
        
        if is_new_arrival is not None:
            query = query.filter(Product.is_new_arrival == is_new_arrival)
        
        if is_best_selling is not None:
            query = query.filter(Product.is_best_selling == is_best_selling)
        
        # Apply sorting
        if hasattr(Product, sort_by):
            sort_column = getattr(Product, sort_by)
            if sort_order.lower() == "desc":
                query = query.order_by(desc(sort_column))
            else:
                query = query.order_by(asc(sort_column))
        else:
            # Default sorting
            query = query.order_by(desc(Product.created_at))
        
        # Get total count before pagination
        total_count = query.count()
        
        # Apply pagination
        products = query.offset(skip).limit(limit).all()
        
        # Convert to response format
        product_responses = []
        for product in products:
            product_responses.append(self._build_product_response(product))
        
        # Count different types
        active_count = self.db.query(Product).filter(Product.is_active == True).count()
        featured_count = self.db.query(Product).filter(Product.is_featured == True).count()
        new_arrivals_count = self.db.query(Product).filter(Product.is_new_arrival == True).count()
        best_selling_count = self.db.query(Product).filter(Product.is_best_selling == True).count()
        
        return ProductListResponse(
            products=product_responses,
            total_count=total_count,
            active_count=active_count,
            featured_count=featured_count,
            new_arrivals_count=new_arrivals_count,
            best_selling_count=best_selling_count
        )
    
    def get_product_by_id(self, product_id: str) -> ProductResponse:
        """Get a specific product by ID"""
        product = self.db.query(Product).join(Category, Product.category_id == Category.category_id)\
                         .filter(Product.product_id == product_id).first()
        
        if not product:
            raise NotFoundException(f"Product with ID {product_id} not found")
        
        return self._build_product_response(product)
    
    def get_product_detail(self, product_id: str) -> ProductDetailResponse:
        """Get detailed product information with related data"""
        product = self.db.query(Product).join(Category, Product.category_id == Category.category_id)\
                         .filter(Product.product_id == product_id).first()
        
        if not product:
            raise NotFoundException(f"Product with ID {product_id} not found")
        
        # Build product response
        product_response = self._build_product_response(product)
        
        # Get related products (same category, different products)
        related_products = self.db.query(Product).join(Category, Product.category_id == Category.category_id)\
                                  .filter(
                                      and_(
                                          Product.category_id == product.category_id,
                                          Product.product_id != product_id,
                                          Product.is_active == True
                                      )
                                  ).limit(6).all()
        
        related_responses = [self._build_product_response(p) for p in related_products]
        
        # Build category path
        category_path = self._build_category_path(product.category_id)
        
        # Determine stock status
        stock_status = self._determine_stock_status(product.stock_quantity, product.min_stock_threshold)
        
        # Calculate discount percentage
        discount_percentage = None
        if product.sale_price and product.price:
            discount_percentage = ((product.price - product.sale_price) / product.price) * 100
        
        # Check if low stock
        is_low_stock = product.stock_quantity <= product.min_stock_threshold
        
        # Estimate delivery time
        estimated_delivery = self._estimate_delivery_time(product.stock_quantity)
        
        return ProductDetailResponse(
            product=product_response,
            related_products=related_responses,
            category_path=category_path,
            stock_status=stock_status,
            discount_percentage=discount_percentage,
            is_low_stock=is_low_stock,
            estimated_delivery=estimated_delivery
        )
    
    # =============================================================================
    # FEATURED PRODUCTS
    # =============================================================================
    
    def get_featured_products(
        self,
        limit: int = 20,
        category_id: Optional[str] = None
    ) -> FeaturedProductsResponse:
        """Get featured products"""
        query = self.db.query(Product).join(Category, Product.category_id == Category.category_id)\
                       .filter(Product.is_featured == True, Product.is_active == True)
        
        if category_id:
            query = query.filter(Product.category_id == category_id)
        
        # Order by featured priority (you might want to add a featured_order field)
        products = query.order_by(desc(Product.rating), desc(Product.sales_count)).limit(limit).all()
        
        product_responses = [self._build_product_response(p) for p in products]
        
        # Get category breakdown
        category_breakdown = {}
        for product in products:
            cat_name = product.category.category_name
            category_breakdown[cat_name] = category_breakdown.get(cat_name, 0) + 1
        
        return FeaturedProductsResponse(
            products=product_responses,
            total_count=len(products),
            category_breakdown=category_breakdown
        )
    
    # =============================================================================
    # NEW ARRIVALS
    # =============================================================================
    
    def get_new_arrivals(
        self,
        limit: int = 20,
        days: int = 30
    ) -> NewArrivalsResponse:
        """Get new arrival products"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        products = self.db.query(Product).join(Category, Product.category_id == Category.category_id)\
                         .filter(
                             and_(
                                 Product.is_new_arrival == True,
                                 Product.is_active == True,
                                 Product.created_at >= cutoff_date
                             )
                         ).order_by(desc(Product.created_at)).limit(limit).all()
        
        product_responses = [self._build_product_response(p) for p in products]
        
        arrival_period = f"Last {days} days"
        
        return NewArrivalsResponse(
            products=product_responses,
            total_count=len(products),
            arrival_period=arrival_period
        )
    
    # =============================================================================
    # BEST SELLING PRODUCTS
    # =============================================================================
    
    def get_best_selling_products(
        self,
        limit: int = 20,
        days: int = 90
    ) -> BestSellingProductsResponse:
        """Get best selling products based on sales data"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Get products with sales in the specified period
        products = self.db.query(Product).join(Category, Product.category_id == Category.category_id)\
                         .filter(
                             and_(
                                 Product.is_best_selling == True,
                                 Product.is_active == True
                             )
                         ).order_by(desc(Product.sales_count)).limit(limit).all()
        
        product_responses = [self._build_product_response(p) for p in products]
        
        sales_period = f"Last {days} days"
        
        # Build sales ranking
        sales_ranking = []
        for i, product in enumerate(products, 1):
            sales_ranking.append({
                "rank": i,
                "product_id": str(product.product_id),
                "product_name": product.product_name,
                "sales_count": product.sales_count,
                "total_revenue": float(product.sales_count * product.price) if product.sales_count else 0
            })
        
        return BestSellingProductsResponse(
            products=product_responses,
            total_count=len(products),
            sales_period=sales_period,
            sales_ranking=sales_ranking
        )
    
    # =============================================================================
    # PRODUCT SEARCH
    # =============================================================================
    
    def search_products(
        self,
        search_query: ProductSearch
    ) -> ProductSearchResponse:
        """Search products by query with filters"""
        query = self.db.query(Product).join(Category, Product.category_id == Category.category_id)\
                       .filter(Product.is_active == True)
        
        # Apply search query
        search_filter = f"%{search_query.query}%"
        query = query.filter(
            or_(
                Product.product_name.ilike(search_filter),
                Product.description.ilike(search_filter),
                Product.tags.any(lambda tag: tag.ilike(search_filter)) if Product.tags else False
            )
        )
        
        # Apply additional filters
        if search_query.category_id:
            query = query.filter(Product.category_id == search_query.category_id)
        
        if search_query.price_min is not None:
            query = query.filter(Product.price >= search_query.price_min)
        
        if search_query.price_max is not None:
            query = query.filter(Product.price <= search_query.price_max)
        
        if search_query.in_stock is not None:
            if search_query.in_stock:
                query = query.filter(Product.stock_quantity > 0)
            else:
                query = query.filter(Product.stock_quantity <= 0)
        
        if search_query.min_rating is not None:
            query = query.filter(Product.rating >= search_query.min_rating)
        
        # Apply sorting
        if hasattr(Product, search_query.sort_by):
            sort_column = getattr(Product, search_query.sort_by)
            if search_query.sort_order == "desc":
                query = query.order_by(desc(sort_column))
            else:
                query = query.order_by(asc(sort_column))
        
        # Get total count
        total_count = query.count()
        
        # Get products
        products = query.limit(100).all()  # Limit search results
        
        product_responses = [self._build_product_response(p) for p in products]
        
        # Generate search suggestions
        search_suggestions = self._generate_search_suggestions(search_query.query)
        
        # Get category filters
        category_filters = self._get_category_filters_for_search()
        
        # Calculate price range
        price_range = self._calculate_price_range(products)
        
        return ProductSearchResponse(
            products=product_responses,
            total_count=total_count,
            search_query=search_query.query,
            search_suggestions=search_suggestions,
            category_filters=category_filters,
            price_range=price_range
        )
    
    # =============================================================================
    # PRODUCT FILTERING
    # =============================================================================
    
    def filter_products(
        self,
        filters: ProductFilter,
        pagination: PaginationParams
    ) -> ProductFilterResponse:
        """Filter products based on multiple criteria"""
        query = self.db.query(Product).join(Category, Product.category_id == Category.category_id)\
                       .filter(Product.is_active == True)
        
        # Apply filters
        if filters.category_id:
            query = query.filter(Product.category_id == filters.category_id)
        
        if filters.category_name:
            query = query.filter(Category.category_name.ilike(f"%{filters.category_name}%"))
        
        if filters.price_min is not None:
            query = query.filter(Product.price >= filters.price_min)
        
        if filters.price_max is not None:
            query = query.filter(Product.price <= filters.price_max)
        
        if filters.in_stock is not None:
            if filters.in_stock:
                query = query.filter(Product.stock_quantity > 0)
            else:
                query = query.filter(Product.stock_quantity <= 0)
        
        if filters.on_sale is not None:
            if filters.on_sale:
                query = query.filter(Product.sale_price.isnot(None))
            else:
                query = query.filter(Product.sale_price.is_(None))
        
        if filters.min_rating is not None:
            query = query.filter(Product.rating >= filters.min_rating)
        
        if filters.is_featured is not None:
            query = query.filter(Product.is_featured == filters.is_featured)
        
        if filters.is_new_arrival is not None:
            query = query.filter(Product.is_new_arrival == filters.is_new_arrival)
        
        if filters.is_best_selling is not None:
            query = query.filter(Product.is_best_selling == filters.is_best_selling)
        
        if filters.tags:
            for tag in filters.tags:
                query = query.filter(Product.tags.any(lambda t: t.ilike(f"%{tag}%")))
        
        if filters.allergens:
            for allergen in filters.allergens:
                query = query.filter(Product.allergens.any(lambda a: a.ilike(f"%{allergen}%")))
        
        if filters.weight_min is not None:
            query = query.filter(Product.weight >= filters.weight_min)
        
        if filters.weight_max is not None:
            query = query.filter(Product.weight <= filters.weight_max)
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination
        products = query.offset(pagination.offset).limit(pagination.size).all()
        
        product_responses = [self._build_product_response(p) for p in products]
        
        # Build applied filters
        applied_filters = filters.dict(exclude_none=True)
        
        # Get available filter options
        available_filters = self._get_available_filter_options()
        
        # Build filter summary
        filter_summary = {
            "total_products": total_count,
            "filtered_products": len(products),
            "categories_found": len(set(p.category_id for p in products)),
            "price_range": self._calculate_price_range(products),
            "rating_distribution": self._calculate_rating_distribution(products)
        }
        
        return ProductFilterResponse(
            products=product_responses,
            total_count=total_count,
            applied_filters=applied_filters,
            available_filters=available_filters,
            filter_summary=filter_summary
        )
    
    # =============================================================================
    # PAGINATED PRODUCTS
    # =============================================================================
    
    def get_products_paginated(
        self,
        pagination: PaginationParams,
        category_id: Optional[str] = None,
        is_active: Optional[bool] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc"
    ) -> PaginatedProductsResponse:
        """Get paginated products with optional filtering"""
        query = self.db.query(Product).join(Category, Product.category_id == Category.category_id)
        
        # Apply filters
        if category_id:
            query = query.filter(Product.category_id == category_id)
        
        if is_active is not None:
            query = query.filter(Product.is_active == is_active)
        
        # Apply sorting
        if hasattr(Product, sort_by):
            sort_column = getattr(Product, sort_by)
            if sort_order.lower() == "desc":
                query = query.order_by(desc(sort_column))
            else:
                query = query.order_by(asc(sort_column))
        
        # Get total count
        total = query.count()
        
        # Calculate pagination
        pages = (total + pagination.size - 1) // pagination.size
        has_next = pagination.page < pages
        has_prev = pagination.page > 1
        
        # Get products for current page
        products = query.offset(pagination.offset).limit(pagination.size).all()
        
        # Convert to response format
        product_responses = [self._build_product_response(p) for p in products]
        
        return PaginatedProductsResponse(
            products=product_responses,
            page=pagination.page,
            size=pagination.size,
            total=total,
            pages=pages,
            has_next=has_next,
            has_prev=has_prev
        )
    
    # =============================================================================
    # PRODUCT STATISTICS
    # =============================================================================
    
    def get_product_statistics(self, product_id: str) -> ProductStatsResponse:
        """Get comprehensive statistics for a product"""
        product = self.db.query(Product).filter(Product.product_id == product_id).first()
        if not product:
            raise NotFoundException(f"Product with ID {product_id} not found")
        
        # Get sales statistics
        sales_query = self.db.query(
            func.sum(OrderItem.quantity * OrderItem.unit_price).label('total_sales'),
            func.sum(OrderItem.quantity).label('total_quantity_sold'),
            func.avg(OrderItem.unit_price).label('average_order_value')
        ).join(Product, OrderItem.product_id == Product.product_id)\
         .join(Order, OrderItem.order_id == Order.order_id)\
         .filter(
            Product.product_id == product_id,
            Order.status == 'completed'
        )
        
        sales_result = sales_query.first()
        
        total_sales = float(sales_result.total_sales) if sales_result.total_sales else 0.0
        total_quantity_sold = int(sales_result.total_quantity_sold) if sales_result.total_quantity_sold else 0
        average_order_value = float(sales_result.average_order_value) if sales_result.average_order_value else 0.0
        
        # Calculate conversion rate
        view_count = product.view_count or 0
        conversion_rate = (total_quantity_sold / view_count * 100) if view_count > 0 else 0.0
        
        # Calculate stock turnover
        stock_turnover = (total_quantity_sold / product.stock_quantity) if product.stock_quantity > 0 else 0.0
        
        # Calculate profit margin
        profit_margin = None
        if product.cost_price and product.price:
            profit_margin = ((product.price - product.cost_price) / product.price) * 100
        
        # Get last sale date
        last_sale = self.db.query(OrderItem).join(Order, OrderItem.order_id == Order.order_id)\
                           .filter(
                               OrderItem.product_id == product_id,
                               Order.status == 'completed'
                           ).order_by(desc(Order.created_at)).first()
        
        last_sale_date = last_sale.order.created_at if last_sale else None
        
        # Get sales trend (last 12 months)
        sales_trend = self._get_sales_trend(product_id)
        
        return ProductStatsResponse(
            product_id=str(product.product_id),
            product_name=product.product_name,
            total_sales=total_sales,
            total_quantity_sold=total_quantity_sold,
            average_order_value=average_order_value,
            view_count=view_count,
            conversion_rate=conversion_rate,
            stock_turnover=stock_turnover,
            profit_margin=profit_margin,
            last_sale_date=last_sale_date,
            sales_trend=sales_trend
        )
    
    def get_product_analytics(self) -> ProductAnalyticsResponse:
        """Get overall product analytics"""
        # Get basic counts
        total_products = self.db.query(Product).count()
        active_products = self.db.query(Product).filter(Product.is_active == True).count()
        out_of_stock_products = self.db.query(Product).filter(Product.stock_quantity <= 0).count()
        low_stock_products = self.db.query(Product).filter(
            and_(
                Product.stock_quantity > 0,
                Product.stock_quantity <= Product.min_stock_threshold
            )
        ).count()
        featured_products = self.db.query(Product).filter(Product.is_featured == True).count()
        new_arrivals = self.db.query(Product).filter(Product.is_new_arrival == True).count()
        best_selling_products = self.db.query(Product).filter(Product.is_best_selling == True).count()
        
        # Calculate total stock value
        stock_value_query = self.db.query(func.sum(Product.stock_quantity * Product.price)).scalar()
        total_stock_value = float(stock_value_query) if stock_value_query else 0.0
        
        # Calculate average price
        avg_price_query = self.db.query(func.avg(Product.price)).scalar()
        average_price = float(avg_price_query) if avg_price_query else 0.0
        
        # Calculate average rating
        avg_rating_query = self.db.query(func.avg(Product.rating)).filter(Product.rating.isnot(None)).scalar()
        average_rating = float(avg_rating_query) if avg_rating_query else None
        
        # Get top categories
        top_categories = self._get_top_categories()
        
        # Get sales performance
        sales_performance = self._get_sales_performance()
        
        return ProductAnalyticsResponse(
            total_products=total_products,
            active_products=active_products,
            out_of_stock_products=out_of_stock_products,
            low_stock_products=low_stock_products,
            featured_products=featured_products,
            new_arrivals=new_arrivals,
            best_selling_products=best_selling_products,
            total_stock_value=total_stock_value,
            average_price=average_price,
            average_rating=average_rating,
            top_categories=top_categories,
            sales_performance=sales_performance
        )
    
    # =============================================================================
    # RELATED PRODUCTS
    # =============================================================================
    
    def get_related_products(
        self,
        product_id: str,
        limit: int = 6
    ) -> RelatedProductsResponse:
        """Get related products based on category and tags"""
        product = self.db.query(Product).filter(Product.product_id == product_id).first()
        if not product:
            raise NotFoundException(f"Product with ID {product_id} not found")
        
        # Get products from same category
        related_products = self.db.query(Product).join(Category, Product.category_id == Category.category_id)\
                                  .filter(
                                      and_(
                                          Product.category_id == product.category_id,
                                          Product.product_id != product_id,
                                          Product.is_active == True
                                      )
                                  ).limit(limit).all()
        
        # If not enough products from same category, add products with similar tags
        if len(related_products) < limit and product.tags:
            remaining_limit = limit - len(related_products)
            tag_products = self.db.query(Product).filter(
                and_(
                    Product.product_id != product_id,
                    Product.is_active == True,
                    Product.tags.any(lambda tag: tag.in_(product.tags))
                )
            ).limit(remaining_limit).all()
            
            related_products.extend(tag_products)
        
        product_responses = [self._build_product_response(p) for p in related_products]
        
        # Get categories of related products
        categories = list(set(p.category_name for p in related_products))
        
        return RelatedProductsResponse(
            product_id=product_id,
            related_products=product_responses,
            relationship_type="category_and_tags",
            total_count=len(related_products),
            categories=categories
        )
    
    # =============================================================================
    # HELPER METHODS
    # =============================================================================
    
    def _build_product_response(self, product: Product) -> ProductResponse:
        """Build product response from database model"""
        return ProductResponse(
            product_id=str(product.product_id),
            product_name=product.product_name,
            description=product.description,
            price=float(product.price),
            sale_price=float(product.sale_price) if product.sale_price else None,
            cost_price=float(product.cost_price) if product.cost_price else None,
            sku=product.sku,
            barcode=product.barcode,
            weight=float(product.weight) if product.weight else None,
            dimensions=product.dimensions,
            image_url=product.image_url,
            gallery_images=product.gallery_images,
            category_id=str(product.category_id),
            category_name=product.category.category_name,
            is_active=product.is_active,
            is_featured=product.is_featured,
            is_new_arrival=product.is_new_arrival,
            is_best_selling=product.is_best_selling,
            stock_quantity=product.stock_quantity,
            min_stock_threshold=product.min_stock_threshold,
            max_stock_threshold=product.max_stock_threshold,
            rating=float(product.rating) if product.rating else None,
            review_count=product.review_count,
            sales_count=product.sales_count,
            view_count=product.view_count,
            tags=product.tags,
            allergens=product.allergens,
            nutritional_info=product.nutritional_info,
            ingredients=product.ingredients,
            storage_instructions=product.storage_instructions,
            expiry_date=product.expiry_date,
            created_at=product.created_at,
            updated_at=product.updated_at
        )
    
    def _build_category_path(self, category_id: str) -> List[Dict[str, str]]:
        """Build category navigation path"""
        path = []
        current_category = self.db.query(Category).filter(Category.category_id == category_id).first()
        
        while current_category:
            path.insert(0, {
                "category_id": str(current_category.category_id),
                "category_name": current_category.category_name
            })
            
            if current_category.parent_category_id:
                current_category = self.db.query(Category).filter(
                    Category.category_id == current_category.parent_category_id
                ).first()
            else:
                break
        
        return path
    
    def _determine_stock_status(self, stock_quantity: int, min_threshold: int) -> str:
        """Determine stock status based on quantity and threshold"""
        if stock_quantity <= 0:
            return "out_of_stock"
        elif stock_quantity <= min_threshold:
            return "low_stock"
        else:
            return "in_stock"
    
    def _estimate_delivery_time(self, stock_quantity: int) -> str:
        """Estimate delivery time based on stock"""
        if stock_quantity <= 0:
            return "2-3 business days"
        elif stock_quantity <= 10:
            return "1-2 business days"
        else:
            return "Same day delivery"
    
    def _generate_search_suggestions(self, query: str) -> List[str]:
        """Generate search suggestions based on query"""
        # This is a simple implementation - you might want to use more sophisticated algorithms
        suggestions = []
        
        # Add category suggestions
        categories = self.db.query(Category.category_name).filter(
            Category.category_name.ilike(f"%{query}%")
        ).limit(3).all()
        
        for cat in categories:
            suggestions.append(f"Category: {cat.category_name}")
        
        # Add tag suggestions
        products_with_tags = self.db.query(Product.tags).filter(
            Product.tags.isnot(None),
            Product.is_active == True
        ).limit(5).all()
        
        for product_tags in products_with_tags:
            if product_tags.tags:
                for tag in product_tags.tags:
                    if query.lower() in tag.lower() and tag not in suggestions:
                        suggestions.append(f"Tag: {tag}")
                        if len(suggestions) >= 5:
                            break
        
        return suggestions[:5]
    
    def _get_category_filters_for_search(self) -> List[Dict[str, Any]]:
        """Get available category filters for search"""
        categories = self.db.query(Category).filter(Category.is_active == True).all()
        
        filters = []
        for cat in categories:
            product_count = self.db.query(Product).filter(
                Product.category_id == cat.category_id,
                Product.is_active == True
            ).count()
            
            if product_count > 0:
                filters.append({
                    "category_id": str(cat.category_id),
                    "category_name": cat.category_name,
                    "product_count": product_count
                })
        
        return filters
    
    def _calculate_price_range(self, products: List[Product]) -> Dict[str, float]:
        """Calculate price range from products"""
        if not products:
            return {"min": 0.0, "max": 0.0}
        
        prices = [float(p.price) for p in products if p.price]
        if not prices:
            return {"min": 0.0, "max": 0.0}
        
        return {
            "min": min(prices),
            "max": max(prices)
        }
    
    def _get_available_filter_options(self) -> Dict[str, Any]:
        """Get available filter options for products"""
        # Price ranges
        price_ranges = [
            {"label": "Under $10", "min": 0, "max": 10},
            {"label": "$10 - $25", "min": 10, "max": 25},
            {"label": "$25 - $50", "min": 25, "max": 50},
            {"label": "$50 - $100", "min": 50, "max": 100},
            {"label": "Over $100", "min": 100, "max": None}
        ]
        
        # Rating options
        rating_options = [
            {"label": "4+ Stars", "value": 4.0},
            {"label": "3+ Stars", "value": 3.0},
            {"label": "2+ Stars", "value": 2.0}
        ]
        
        # Stock options
        stock_options = [
            {"label": "In Stock", "value": True},
            {"label": "Out of Stock", "value": False}
        ]
        
        return {
            "price_ranges": price_ranges,
            "rating_options": rating_options,
            "stock_options": stock_options
        }
    
    def _calculate_rating_distribution(self, products: List[Product]) -> Dict[str, int]:
        """Calculate rating distribution for products"""
        distribution = {
            "5_stars": 0,
            "4_stars": 0,
            "3_stars": 0,
            "2_stars": 0,
            "1_star": 0,
            "no_rating": 0
        }
        
        for product in products:
            if product.rating is None:
                distribution["no_rating"] += 1
            elif product.rating >= 4.5:
                distribution["5_stars"] += 1
            elif product.rating >= 3.5:
                distribution["4_stars"] += 1
            elif product.rating >= 2.5:
                distribution["3_stars"] += 1
            elif product.rating >= 1.5:
                distribution["2_stars"] += 1
            else:
                distribution["1_star"] += 1
        
        return distribution
    
    def _get_sales_trend(self, product_id: str, months: int = 12) -> List[Dict[str, Any]]:
        """Get sales trend for a product over specified months"""
        trend = []
        current_date = datetime.utcnow()
        
        for i in range(months):
            month_start = current_date.replace(day=1) - timedelta(days=30*i)
            month_end = month_start.replace(day=28) + timedelta(days=4)
            month_end = month_end.replace(day=1) - timedelta(days=1)
            
            # Get sales for this month
            month_sales = self.db.query(func.sum(OrderItem.quantity * OrderItem.unit_price))\
                                 .join(Product, OrderItem.product_id == Product.product_id)\
                                 .join(Order, OrderItem.order_id == Order.order_id)\
                                 .filter(
                                    Product.product_id == product_id,
                                    Order.status == 'completed',
                                    Order.created_at >= month_start,
                                    Order.created_at <= month_end
                                 ).scalar()
            
            trend.append({
                "month": month_start.strftime("%Y-%m"),
                "sales_amount": float(month_sales) if month_sales else 0.0,
                "month_name": month_start.strftime("%B %Y")
            })
        
        return list(reversed(trend))
    
    def _get_top_categories(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Get top product categories by product count"""
        categories = self.db.query(
            Category.category_name,
            func.count(Product.product_id).label('product_count'),
            func.avg(Product.price).label('avg_price')
        ).join(Product, Category.category_id == Product.category_id)\
         .filter(Product.is_active == True)\
         .group_by(Category.category_id, Category.category_name)\
         .order_by(desc('product_count'))\
         .limit(limit)\
         .all()
        
        return [
            {
                "category_name": cat.category_name,
                "product_count": int(cat.product_count),
                "average_price": float(cat.avg_price) if cat.avg_price else 0.0
            }
            for cat in categories
        ]
    
    def _get_sales_performance(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get sales performance data over specified days"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Get daily sales
        daily_sales = self.db.query(
            func.date(Order.created_at).label('date'),
            func.sum(OrderItem.quantity * OrderItem.unit_price).label('daily_sales'),
            func.count(Order.order_id).label('order_count')
        ).join(OrderItem, Order.order_id == OrderItem.order_id)\
         .filter(
            Order.status == 'completed',
            Order.created_at >= cutoff_date
         ).group_by(func.date(Order.created_at))\
         .order_by(func.date(Order.created_at))\
         .all()
        
        return [
            {
                "date": sale.date.strftime("%Y-%m-%d"),
                "sales_amount": float(sale.daily_sales) if sale.daily_sales else 0.0,
                "order_count": int(sale.order_count) if sale.order_count else 0
            }
            for sale in daily_sales
        ]