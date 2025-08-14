"""
SQLAlchemy ORM models for Labanita API.
All models correspond exactly to the PostgreSQL database schema.
"""

import uuid
from datetime import datetime
from typing import List, Optional
from sqlalchemy import (
    Column, String, Integer, Boolean, Text, Numeric, DateTime, 
    ForeignKey, CheckConstraint, UniqueConstraint, Index
)
from sqlalchemy.dialects.postgresql import UUID, TIMESTAMP
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func

from database import Base


class User(Base):
    """Users table - Core user information and authentication."""
    __tablename__ = "users"
    
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    phone_number: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(255))
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True)
    facebook_id: Mapped[Optional[str]] = mapped_column(String(255), unique=True)
    google_id: Mapped[Optional[str]] = mapped_column(String(255), unique=True)
    points_balance: Mapped[int] = mapped_column(
        Integer, 
        default=0, 
        nullable=False,
        server_default="0"
    )
    points_expiry_date: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), 
        nullable=False, 
        server_default=func.current_timestamp()
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), 
        nullable=False, 
        server_default=func.current_timestamp()
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, 
        default=True, 
        nullable=False,
        server_default="true"
    )
    
    # Relationships
    addresses: Mapped[List["Address"]] = relationship("Address", back_populates="user", cascade="all, delete-orphan")
    payment_methods: Mapped[List["PaymentMethod"]] = relationship("PaymentMethod", back_populates="user", cascade="all, delete-orphan")
    orders: Mapped[List["Order"]] = relationship("Order", back_populates="user")
    cart_items: Mapped[List["CartItem"]] = relationship("CartItem", back_populates="user", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("points_balance >= 0", name="check_points_balance_positive"),
    )


class Category(Base):
    """Categories table - Product categories (Rice Milk, Sweets, etc.)."""
    __tablename__ = "categories"
    
    category_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    category_name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    category_slug: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    image_url: Mapped[Optional[str]] = mapped_column(String(500))
    sort_order: Mapped[int] = mapped_column(
        Integer, 
        default=0,
        server_default="0"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, 
        default=True, 
        nullable=False,
        server_default="true"
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), 
        nullable=False, 
        server_default=func.current_timestamp()
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), 
        nullable=False, 
        server_default=func.current_timestamp()
    )
    
    # Relationships
    products: Mapped[List["Product"]] = relationship("Product", back_populates="category")
    
    # Indexes
    __table_args__ = (
        Index("idx_categories_slug", "category_slug"),
        Index("idx_categories_active", "is_active"),
        Index("idx_categories_sort_order", "sort_order"),
    )


class Product(Base):
    """Products table - Core product information."""
    __tablename__ = "products"
    
    product_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    category_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("categories.category_id", ondelete="RESTRICT"), 
        nullable=False
    )
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    product_slug: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    base_price: Mapped[float] = mapped_column(
        Numeric(10, 2), 
        nullable=False
    )
    image_url: Mapped[Optional[str]] = mapped_column(String(500))
    sort_order: Mapped[int] = mapped_column(
        Integer, 
        default=0,
        server_default="0"
    )
    is_featured: Mapped[bool] = mapped_column(
        Boolean, 
        default=False,
        server_default="false"
    )
    is_new_arrival: Mapped[bool] = mapped_column(
        Boolean, 
        default=False,
        server_default="false"
    )
    is_best_selling: Mapped[bool] = mapped_column(
        Boolean, 
        default=False,
        server_default="false"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, 
        default=True, 
        nullable=False,
        server_default="true"
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), 
        nullable=False, 
        server_default=func.current_timestamp()
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), 
        nullable=False, 
        server_default=func.current_timestamp()
    )
    
    # Relationships
    category: Mapped["Category"] = relationship("Category", back_populates="products")
    order_items: Mapped[List["OrderItem"]] = relationship("OrderItem", back_populates="product")
    cart_items: Mapped[List["CartItem"]] = relationship("CartItem", back_populates="product", cascade="all, delete-orphan")
    product_offers: Mapped[List["ProductOffer"]] = relationship("ProductOffer", back_populates="product", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("base_price >= 0", name="check_base_price_positive"),
        Index("idx_products_category", "category_id"),
        Index("idx_products_slug", "product_slug"),
        Index("idx_products_featured", "is_featured"),
        Index("idx_products_new_arrival", "is_new_arrival"),
        Index("idx_products_best_selling", "is_best_selling"),
        Index("idx_products_active", "is_active"),
        Index("idx_products_price", "base_price"),
    )


class Address(Base):
    """Addresses table - User delivery addresses."""
    __tablename__ = "addresses"
    
    address_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("users.user_id", ondelete="CASCADE"), 
        nullable=False
    )
    address_type: Mapped[str] = mapped_column(String(50), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(20), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(255))
    street_address: Mapped[str] = mapped_column(Text, nullable=False)
    building_number: Mapped[Optional[str]] = mapped_column(String(50))
    flat_number: Mapped[Optional[str]] = mapped_column(String(50))
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    area: Mapped[Optional[str]] = mapped_column(String(100))
    is_default: Mapped[bool] = mapped_column(
        Boolean, 
        default=False,
        server_default="false"
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), 
        nullable=False, 
        server_default=func.current_timestamp()
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), 
        nullable=False, 
        server_default=func.current_timestamp()
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="addresses")
    orders: Mapped[List["Order"]] = relationship("Order", back_populates="address")
    
    # Indexes
    __table_args__ = (
        Index("idx_addresses_user", "user_id"),
        Index("idx_addresses_default", "user_id", "is_default"),
    )


class PaymentMethod(Base):
    """Payment Methods table - User saved payment methods."""
    __tablename__ = "payment_methods"
    
    payment_method_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("users.user_id", ondelete="CASCADE"), 
        nullable=False
    )
    payment_type: Mapped[str] = mapped_column(
        String(50), 
        nullable=False
    )
    card_holder_name: Mapped[Optional[str]] = mapped_column(String(255))
    card_last_four: Mapped[Optional[str]] = mapped_column(String(4))
    card_brand: Mapped[Optional[str]] = mapped_column(String(50))
    expiry_month: Mapped[Optional[int]] = mapped_column(
        Integer
    )
    expiry_year: Mapped[Optional[int]] = mapped_column(
        Integer
    )
    is_default: Mapped[bool] = mapped_column(
        Boolean, 
        default=False,
        server_default="false"
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), 
        nullable=False, 
        server_default=func.current_timestamp()
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), 
        nullable=False, 
        server_default=func.current_timestamp()
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="payment_methods")
    orders: Mapped[List["Order"]] = relationship("Order", back_populates="payment_method")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("payment_type IN ('CARD', 'APPLE_PAY', 'CASH')", name="check_payment_type"),
        CheckConstraint("expiry_month BETWEEN 1 AND 12", name="check_expiry_month"),
        CheckConstraint("expiry_year >= EXTRACT(YEAR FROM CURRENT_DATE)", name="check_expiry_year"),
        Index("idx_payment_methods_user", "user_id"),
        Index("idx_payment_methods_default", "user_id", "is_default"),
    )


class Promotion(Base):
    """Promotions table - Promo codes and discount campaigns."""
    __tablename__ = "promotions"
    
    promotion_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    promotion_code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    promotion_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    discount_type: Mapped[str] = mapped_column(
        String(20), 
        nullable=False
    )
    discount_value: Mapped[float] = mapped_column(
        Numeric(10, 2), 
        nullable=False
    )
    minimum_order_amount: Mapped[float] = mapped_column(
        Numeric(10, 2), 
        default=0,
        server_default="0"
    )
    maximum_discount_amount: Mapped[Optional[float]] = mapped_column(
        Numeric(10, 2)
    )
    usage_limit: Mapped[Optional[int]] = mapped_column(Integer)
    usage_count: Mapped[int] = mapped_column(
        Integer, 
        default=0,
        server_default="0"
    )
    start_date: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    end_date: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, 
        default=True, 
        nullable=False,
        server_default="true"
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), 
        nullable=False, 
        server_default=func.current_timestamp()
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), 
        nullable=False, 
        server_default=func.current_timestamp()
    )
    
    # Relationships
    orders: Mapped[List["Order"]] = relationship("Order", back_populates="promotion")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("discount_type IN ('PERCENTAGE', 'FIXED_AMOUNT')", name="check_discount_type"),
        CheckConstraint("discount_value > 0", name="check_discount_value_positive"),
        CheckConstraint("minimum_order_amount >= 0", name="check_minimum_order_amount"),
        CheckConstraint("maximum_discount_amount > 0", name="check_maximum_discount_amount"),
        CheckConstraint("usage_limit > 0", name="check_usage_limit_positive"),
        CheckConstraint("usage_count >= 0", name="check_usage_count_non_negative"),
        CheckConstraint("end_date > start_date", name="check_end_date_after_start"),
        Index("idx_promotions_code", "promotion_code"),
        Index("idx_promotions_active", "is_active"),
        Index("idx_promotions_dates", "start_date", "end_date"),
    )


class Order(Base):
    """Orders table - Customer orders."""
    __tablename__ = "orders"
    
    order_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    order_number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("users.user_id", ondelete="RESTRICT"), 
        nullable=False
    )
    address_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("addresses.address_id", ondelete="RESTRICT"), 
        nullable=False
    )
    payment_method_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("payment_methods.payment_method_id", ondelete="RESTRICT"), 
        nullable=False
    )
    promotion_id: Mapped[Optional[UUID]] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("promotions.promotion_id", ondelete="SET NULL")
    )
    order_status: Mapped[str] = mapped_column(
        String(50), 
        nullable=False, 
        default="PENDING",
        server_default="PENDING"
    )
    subtotal: Mapped[float] = mapped_column(
        Numeric(10, 2), 
        nullable=False
    )
    delivery_fee: Mapped[float] = mapped_column(
        Numeric(10, 2), 
        nullable=False
    )
    discount_amount: Mapped[float] = mapped_column(
        Numeric(10, 2), 
        default=0,
        server_default="0"
    )
    points_used: Mapped[int] = mapped_column(
        Integer, 
        default=0,
        server_default="0"
    )
    points_earned: Mapped[int] = mapped_column(
        Integer, 
        default=0,
        server_default="0"
    )
    total_amount: Mapped[float] = mapped_column(
        Numeric(10, 2), 
        nullable=False
    )
    order_notes: Mapped[Optional[str]] = mapped_column(Text)
    estimated_delivery_time: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True))
    delivered_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), 
        nullable=False, 
        server_default=func.current_timestamp()
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), 
        nullable=False, 
        server_default=func.current_timestamp()
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="orders")
    address: Mapped["Address"] = relationship("Address", back_populates="orders")
    payment_method: Mapped["PaymentMethod"] = relationship("PaymentMethod", back_populates="orders")
    promotion: Mapped[Optional["Promotion"]] = relationship("Promotion", back_populates="orders")
    order_items: Mapped[List["OrderItem"]] = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    status_history: Mapped[List["OrderStatusHistory"]] = relationship("OrderStatusHistory", back_populates="order", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("order_status IN ('PENDING', 'CONFIRMED', 'PREPARING', 'OUT_FOR_DELIVERY', 'DELIVERED', 'CANCELLED')", name="check_order_status"),
        CheckConstraint("subtotal >= 0", name="check_subtotal_positive"),
        CheckConstraint("delivery_fee >= 0", name="check_delivery_fee_positive"),
        CheckConstraint("discount_amount >= 0", name="check_discount_amount_positive"),
        CheckConstraint("points_used >= 0", name="check_points_used_positive"),
        CheckConstraint("points_earned >= 0", name="check_points_earned_positive"),
        CheckConstraint("total_amount >= 0", name="check_total_amount_positive"),
        Index("idx_orders_user", "user_id"),
        Index("idx_orders_status", "order_status"),
        Index("idx_orders_created", "created_at"),
        Index("idx_orders_number", "order_number"),
        Index("idx_orders_address", "address_id"),
        Index("idx_orders_payment_method", "payment_method_id"),
    )


class OrderItem(Base):
    """Order Items table - Junction table for orders and products."""
    __tablename__ = "order_items"
    
    order_item_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    order_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("orders.order_id", ondelete="CASCADE"), 
        nullable=False
    )
    product_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("products.product_id", ondelete="RESTRICT"), 
        nullable=False
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[float] = mapped_column(
        Numeric(10, 2), 
        nullable=False
    )
    total_price: Mapped[float] = mapped_column(
        Numeric(10, 2), 
        nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), 
        nullable=False, 
        server_default=func.current_timestamp()
    )
    
    # Relationships
    order: Mapped["Order"] = relationship("Order", back_populates="order_items")
    product: Mapped["Product"] = relationship("Product", back_populates="order_items")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("quantity > 0", name="check_quantity_positive"),
        CheckConstraint("unit_price >= 0", name="check_unit_price_positive"),
        CheckConstraint("total_price >= 0", name="check_total_price_positive"),
        Index("idx_order_items_order", "order_id"),
        Index("idx_order_items_product", "product_id"),
    )


class CartItem(Base):
    """Cart Items table - Shopping cart persistence."""
    __tablename__ = "cart_items"
    
    cart_item_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("users.user_id", ondelete="CASCADE"), 
        nullable=False
    )
    product_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("products.product_id", ondelete="CASCADE"), 
        nullable=False
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), 
        nullable=False, 
        server_default=func.current_timestamp()
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), 
        nullable=False, 
        server_default=func.current_timestamp()
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="cart_items")
    product: Mapped["Product"] = relationship("Product", back_populates="cart_items")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("quantity > 0", name="check_cart_quantity_positive"),
        UniqueConstraint("user_id", "product_id", name="uq_cart_user_product"),
        Index("idx_cart_items_user", "user_id"),
        Index("idx_cart_items_product", "product_id"),
    )


class OrderStatusHistory(Base):
    """Order Status History table - Track order status changes."""
    __tablename__ = "order_status_history"
    
    status_history_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    order_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("orders.order_id", ondelete="CASCADE"), 
        nullable=False
    )
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), 
        nullable=False, 
        server_default=func.current_timestamp()
    )
    
    # Relationships
    order: Mapped["Order"] = relationship("Order", back_populates="status_history")
    
    # Indexes
    __table_args__ = (
        Index("idx_order_status_history_order", "order_id"),
        Index("idx_order_status_history_created", "created_at"),
    )


class ProductOffer(Base):
    """Product Offers table - Time-limited product discounts."""
    __tablename__ = "product_offers"
    
    offer_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4
    )
    product_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), 
        ForeignKey("products.product_id", ondelete="CASCADE"), 
        nullable=False
    )
    offer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    discount_type: Mapped[str] = mapped_column(
        String(20), 
        nullable=False
    )
    discount_value: Mapped[float] = mapped_column(
        Numeric(10, 2), 
        nullable=False
    )
    original_price: Mapped[float] = mapped_column(
        Numeric(10, 2), 
        nullable=False
    )
    sale_price: Mapped[float] = mapped_column(
        Numeric(10, 2), 
        nullable=False
    )
    start_date: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    end_date: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, 
        default=True, 
        nullable=False,
        server_default="true"
    )
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), 
        nullable=False, 
        server_default=func.current_timestamp()
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), 
        nullable=False, 
        server_default=func.current_timestamp()
    )
    
    # Relationships
    product: Mapped["Product"] = relationship("Product", back_populates="product_offers")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("discount_type IN ('PERCENTAGE', 'FIXED_AMOUNT')", name="check_offer_discount_type"),
        CheckConstraint("discount_value > 0", name="check_offer_discount_value_positive"),
        CheckConstraint("original_price > 0", name="check_original_price_positive"),
        CheckConstraint("sale_price > 0", name="check_sale_price_positive"),
        CheckConstraint("end_date > start_date", name="check_offer_end_date_after_start"),
        Index("idx_product_offers_product", "product_id"),
        Index("idx_product_offers_active", "is_active"),
        Index("idx_product_offers_dates", "start_date", "end_date"),
    )