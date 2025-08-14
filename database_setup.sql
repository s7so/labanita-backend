-- =====================================================
-- Labanita Database Schema - DDL Scripts
-- Phase 3: Database Creation
-- =====================================================

-- Enable UUID extension for PostgreSQL
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =====================================================
-- 1. USERS TABLE
-- =====================================================
CREATE TABLE users (
    user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    phone_number VARCHAR(20) UNIQUE NOT NULL, -- #PII
    full_name VARCHAR(255), -- #PII
    email VARCHAR(255) UNIQUE, -- #PII
    facebook_id VARCHAR(255) UNIQUE,
    google_id VARCHAR(255) UNIQUE,
    points_balance INTEGER NOT NULL DEFAULT 0,
    points_expiry_date TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Constraints
    CONSTRAINT chk_points_balance CHECK (points_balance >= 0),
    CONSTRAINT chk_phone_format CHECK (phone_number ~ '^\+?[0-9\s\-\(\)]+$')
);

-- =====================================================
-- 2. CATEGORIES TABLE
-- =====================================================
CREATE TABLE categories (
    category_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    category_name VARCHAR(100) NOT NULL UNIQUE,
    category_slug VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    image_url VARCHAR(500),
    sort_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT chk_category_slug_format CHECK (category_slug ~ '^[a-z0-9\-_]+$')
);

-- =====================================================
-- 3. PRODUCTS TABLE
-- =====================================================
CREATE TABLE products (
    product_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    category_id UUID NOT NULL REFERENCES categories(category_id) ON DELETE RESTRICT,
    product_name VARCHAR(255) NOT NULL,
    product_slug VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    base_price DECIMAL(10, 2) NOT NULL,
    image_url VARCHAR(500),
    sort_order INTEGER DEFAULT 0,
    is_featured BOOLEAN DEFAULT FALSE,
    is_new_arrival BOOLEAN DEFAULT FALSE,
    is_best_selling BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT chk_base_price CHECK (base_price > 0),
    CONSTRAINT chk_product_slug_format CHECK (product_slug ~ '^[a-z0-9\-_]+$')
);

-- =====================================================
-- 4. ADDRESSES TABLE
-- =====================================================
CREATE TABLE addresses (
    address_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    address_type VARCHAR(50) NOT NULL DEFAULT 'Home',
    full_name VARCHAR(255) NOT NULL, -- #PII
    phone_number VARCHAR(20) NOT NULL, -- #PII
    email VARCHAR(255), -- #PII
    street_address TEXT NOT NULL, -- #PII
    building_number VARCHAR(50), -- #PII
    flat_number VARCHAR(50), -- #PII
    city VARCHAR(100) NOT NULL,
    area VARCHAR(100),
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT chk_address_type CHECK (address_type IN ('Home', 'Work', 'Other')),
    CONSTRAINT chk_address_phone_format CHECK (phone_number ~ '^\+?[0-9\s\-\(\)]+$')
);

-- =====================================================
-- 5. PAYMENT_METHODS TABLE
-- =====================================================
CREATE TABLE payment_methods (
    payment_method_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    payment_type VARCHAR(50) NOT NULL,
    card_holder_name VARCHAR(255), -- #PII
    card_last_four VARCHAR(4),
    card_brand VARCHAR(50),
    expiry_month INTEGER,
    expiry_year INTEGER,
    is_default BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT chk_payment_type CHECK (payment_type IN ('CARD', 'APPLE_PAY', 'CASH')),
    CONSTRAINT chk_card_last_four CHECK (card_last_four ~ '^[0-9]{4}$' OR card_last_four IS NULL),
    CONSTRAINT chk_expiry_month CHECK (expiry_month BETWEEN 1 AND 12 OR expiry_month IS NULL),
    CONSTRAINT chk_expiry_year CHECK (expiry_year >= EXTRACT(YEAR FROM CURRENT_DATE) OR expiry_year IS NULL)
);

-- =====================================================
-- 6. PROMOTIONS TABLE
-- =====================================================
CREATE TABLE promotions (
    promotion_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    promotion_code VARCHAR(50) UNIQUE NOT NULL,
    promotion_name VARCHAR(255) NOT NULL,
    description TEXT,
    discount_type VARCHAR(20) NOT NULL,
    discount_value DECIMAL(10, 2) NOT NULL,
    minimum_order_amount DECIMAL(10, 2) DEFAULT 0,
    maximum_discount_amount DECIMAL(10, 2),
    usage_limit INTEGER,
    usage_count INTEGER DEFAULT 0,
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT chk_discount_type CHECK (discount_type IN ('PERCENTAGE', 'FIXED_AMOUNT')),
    CONSTRAINT chk_discount_value CHECK (discount_value > 0),
    CONSTRAINT chk_minimum_order CHECK (minimum_order_amount >= 0),
    CONSTRAINT chk_usage_count CHECK (usage_count >= 0),
    CONSTRAINT chk_usage_limit CHECK (usage_limit IS NULL OR usage_limit > 0),
    CONSTRAINT chk_date_range CHECK (end_date > start_date),
    CONSTRAINT chk_percentage_discount CHECK (
        discount_type != 'PERCENTAGE' OR discount_value <= 100
    )
);

-- =====================================================
-- 7. ORDERS TABLE
-- =====================================================
CREATE TABLE orders (
    order_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_number VARCHAR(50) UNIQUE NOT NULL,
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE RESTRICT,
    address_id UUID NOT NULL REFERENCES addresses(address_id) ON DELETE RESTRICT,
    payment_method_id UUID NOT NULL REFERENCES payment_methods(payment_method_id) ON DELETE RESTRICT,
    promotion_id UUID REFERENCES promotions(promotion_id) ON DELETE SET NULL,
    order_status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    subtotal DECIMAL(10, 2) NOT NULL,
    delivery_fee DECIMAL(10, 2) NOT NULL,
    discount_amount DECIMAL(10, 2) DEFAULT 0,
    points_used INTEGER DEFAULT 0,
    points_earned INTEGER DEFAULT 0,
    total_amount DECIMAL(10, 2) NOT NULL,
    order_notes TEXT,
    estimated_delivery_time TIMESTAMP,
    delivered_at TIMESTAMP,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT chk_order_status CHECK (order_status IN (
        'PENDING', 'CONFIRMED', 'PREPARING', 'OUT_FOR_DELIVERY', 'DELIVERED', 'CANCELLED'
    )),
    CONSTRAINT chk_subtotal CHECK (subtotal >= 0),
    CONSTRAINT chk_delivery_fee CHECK (delivery_fee >= 0),
    CONSTRAINT chk_discount_amount CHECK (discount_amount >= 0),
    CONSTRAINT chk_points_used CHECK (points_used >= 0),
    CONSTRAINT chk_points_earned CHECK (points_earned >= 0),
    CONSTRAINT chk_total_amount CHECK (total_amount >= 0),
    CONSTRAINT chk_total_calculation CHECK (
        total_amount = subtotal + delivery_fee - discount_amount
    )
);

-- =====================================================
-- 8. ORDER_ITEMS TABLE
-- =====================================================
CREATE TABLE order_items (
    order_item_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_id UUID NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES products(product_id) ON DELETE RESTRICT,
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10, 2) NOT NULL,
    total_price DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT chk_quantity CHECK (quantity > 0),
    CONSTRAINT chk_unit_price CHECK (unit_price > 0),
    CONSTRAINT chk_total_price CHECK (total_price > 0),
    CONSTRAINT chk_item_total_calculation CHECK (
        total_price = quantity * unit_price
    )
);

-- =====================================================
-- 9. CART_ITEMS TABLE
-- =====================================================
CREATE TABLE cart_items (
    cart_item_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    product_id UUID NOT NULL REFERENCES products(product_id) ON DELETE CASCADE,
    quantity INTEGER NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT chk_cart_quantity CHECK (quantity > 0),
    UNIQUE(user_id, product_id) -- Prevent duplicate products in same user's cart
);

-- =====================================================
-- 10. ORDER_STATUS_HISTORY TABLE
-- =====================================================
CREATE TABLE order_status_history (
    status_history_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    order_id UUID NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL,
    notes TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT chk_history_status CHECK (status IN (
        'PENDING', 'CONFIRMED', 'PREPARING', 'OUT_FOR_DELIVERY', 'DELIVERED', 'CANCELLED'
    ))
);

-- =====================================================
-- 11. PRODUCT_OFFERS TABLE
-- =====================================================
CREATE TABLE product_offers (
    offer_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    product_id UUID NOT NULL REFERENCES products(product_id) ON DELETE CASCADE,
    offer_name VARCHAR(255) NOT NULL,
    discount_type VARCHAR(20) NOT NULL,
    discount_value DECIMAL(10, 2) NOT NULL,
    original_price DECIMAL(10, 2) NOT NULL,
    sale_price DECIMAL(10, 2) NOT NULL,
    start_date TIMESTAMP NOT NULL,
    end_date TIMESTAMP NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT chk_offer_discount_type CHECK (discount_type IN ('PERCENTAGE', 'FIXED_AMOUNT')),
    CONSTRAINT chk_offer_discount_value CHECK (discount_value > 0),
    CONSTRAINT chk_original_price CHECK (original_price > 0),
    CONSTRAINT chk_sale_price CHECK (sale_price > 0),
    CONSTRAINT chk_offer_date_range CHECK (end_date > start_date),
    CONSTRAINT chk_price_difference CHECK (sale_price < original_price),
    CONSTRAINT chk_offer_percentage_discount CHECK (
        discount_type != 'PERCENTAGE' OR discount_value <= 100
    )
);

-- =====================================================
-- INDEXES FOR PERFORMANCE OPTIMIZATION
-- =====================================================

-- Users indexes
CREATE INDEX idx_users_phone ON users(phone_number);
CREATE INDEX idx_users_email ON users(email) WHERE email IS NOT NULL;
CREATE INDEX idx_users_facebook ON users(facebook_id) WHERE facebook_id IS NOT NULL;
CREATE INDEX idx_users_google ON users(google_id) WHERE google_id IS NOT NULL;
CREATE INDEX idx_users_active ON users(is_active) WHERE is_active = TRUE;

-- Categories indexes
CREATE INDEX idx_categories_slug ON categories(category_slug);
CREATE INDEX idx_categories_active ON categories(is_active, sort_order) WHERE is_active = TRUE;

-- Products indexes
CREATE INDEX idx_products_category ON products(category_id);
CREATE INDEX idx_products_slug ON products(product_slug);
CREATE INDEX idx_products_featured ON products(is_featured, is_active) WHERE is_featured = TRUE AND is_active = TRUE;
CREATE INDEX idx_products_new_arrival ON products(is_new_arrival, is_active) WHERE is_new_arrival = TRUE AND is_active = TRUE;
CREATE INDEX idx_products_best_selling ON products(is_best_selling, is_active) WHERE is_best_selling = TRUE AND is_active = TRUE;
CREATE INDEX idx_products_active ON products(is_active, sort_order) WHERE is_active = TRUE;

-- Addresses indexes
CREATE INDEX idx_addresses_user ON addresses(user_id);
CREATE INDEX idx_addresses_default ON addresses(user_id, is_default) WHERE is_default = TRUE;

-- Payment methods indexes
CREATE INDEX idx_payment_methods_user ON payment_methods(user_id);
CREATE INDEX idx_payment_methods_default ON payment_methods(user_id, is_default) WHERE is_default = TRUE;

-- Promotions indexes
CREATE INDEX idx_promotions_code ON promotions(promotion_code);
CREATE INDEX idx_promotions_active ON promotions(is_active, start_date, end_date) WHERE is_active = TRUE;
CREATE INDEX idx_promotions_date_range ON promotions(start_date, end_date);

-- Orders indexes
CREATE INDEX idx_orders_user ON orders(user_id);
CREATE INDEX idx_orders_number ON orders(order_number);
CREATE INDEX idx_orders_status ON orders(order_status);
CREATE INDEX idx_orders_created ON orders(created_at);
CREATE INDEX idx_orders_user_status ON orders(user_id, order_status);

-- Order items indexes
CREATE INDEX idx_order_items_order ON order_items(order_id);
CREATE INDEX idx_order_items_product ON order_items(product_id);

-- Cart items indexes
CREATE INDEX idx_cart_items_user ON cart_items(user_id);
CREATE INDEX idx_cart_items_product ON cart_items(product_id);

-- Order status history indexes
CREATE INDEX idx_order_status_history_order ON order_status_history(order_id);
CREATE INDEX idx_order_status_history_created ON order_status_history(created_at);

-- Product offers indexes
CREATE INDEX idx_product_offers_product ON product_offers(product_id);
CREATE INDEX idx_product_offers_active ON product_offers(is_active, start_date, end_date) WHERE is_active = TRUE;
CREATE INDEX idx_product_offers_date_range ON product_offers(start_date, end_date);

-- =====================================================
-- TRIGGERS FOR AUTOMATIC TIMESTAMP UPDATES
-- =====================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply triggers to all tables with updated_at column
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_categories_updated_at BEFORE UPDATE ON categories
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_products_updated_at BEFORE UPDATE ON products
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_addresses_updated_at BEFORE UPDATE ON addresses
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_payment_methods_updated_at BEFORE UPDATE ON payment_methods
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_promotions_updated_at BEFORE UPDATE ON promotions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_orders_updated_at BEFORE UPDATE ON orders
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_cart_items_updated_at BEFORE UPDATE ON cart_items
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_product_offers_updated_at BEFORE UPDATE ON product_offers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- BUSINESS LOGIC TRIGGERS
-- =====================================================

-- Trigger to ensure only one default address per user
CREATE OR REPLACE FUNCTION ensure_single_default_address()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.is_default = TRUE THEN
        UPDATE addresses 
        SET is_default = FALSE 
        WHERE user_id = NEW.user_id 
        AND address_id != NEW.address_id 
        AND is_default = TRUE;
    END IF;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER trigger_single_default_address 
    BEFORE INSERT OR UPDATE ON addresses
    FOR EACH ROW EXECUTE FUNCTION ensure_single_default_address();

-- Trigger to ensure only one default payment method per user
CREATE OR REPLACE FUNCTION ensure_single_default_payment()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.is_default = TRUE THEN
        UPDATE payment_methods 
        SET is_default = FALSE 
        WHERE user_id = NEW.user_id 
        AND payment_method_id != NEW.payment_method_id 
        AND is_default = TRUE;
    END IF;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER trigger_single_default_payment 
    BEFORE INSERT OR UPDATE ON payment_methods
    FOR EACH ROW EXECUTE FUNCTION ensure_single_default_payment();

-- Trigger to update promotion usage count
CREATE OR REPLACE FUNCTION update_promotion_usage()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.promotion_id IS NOT NULL THEN
        UPDATE promotions 
        SET usage_count = usage_count + 1 
        WHERE promotion_id = NEW.promotion_id;
    END IF;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER trigger_promotion_usage 
    AFTER INSERT ON orders
    FOR EACH ROW EXECUTE FUNCTION update_promotion_usage();

-- Trigger to automatically create order status history
CREATE OR REPLACE FUNCTION create_order_status_history()
RETURNS TRIGGER AS $$
BEGIN
    -- Insert initial status on order creation
    IF TG_OP = 'INSERT' THEN
        INSERT INTO order_status_history (order_id, status, notes)
        VALUES (NEW.order_id, NEW.order_status, 'Order created');
        RETURN NEW;
    END IF;
    
    -- Insert status change on order update
    IF TG_OP = 'UPDATE' AND OLD.order_status != NEW.order_status THEN
        INSERT INTO order_status_history (order_id, status, notes)
        VALUES (NEW.order_id, NEW.order_status, 'Status updated');
        RETURN NEW;
    END IF;
    
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER trigger_order_status_history 
    AFTER INSERT OR UPDATE ON orders
    FOR EACH ROW EXECUTE FUNCTION create_order_status_history();

-- =====================================================
-- GENERATE ORDER NUMBERS FUNCTION
-- =====================================================
CREATE OR REPLACE FUNCTION generate_order_number()
RETURNS TRIGGER AS $$
BEGIN
    NEW.order_number = 'LBN' || TO_CHAR(CURRENT_DATE, 'YYYYMMDD') || 
                       LPAD(NEXTVAL('order_number_seq')::TEXT, 4, '0');
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create sequence for order numbers
CREATE SEQUENCE IF NOT EXISTS order_number_seq START 1;

-- Apply trigger to generate order numbers
CREATE TRIGGER trigger_generate_order_number 
    BEFORE INSERT ON orders
    FOR EACH ROW EXECUTE FUNCTION generate_order_number();

-- =====================================================
-- COMMENTS FOR DOCUMENTATION
-- =====================================================

COMMENT ON TABLE users IS 'Store user account information with authentication methods';
COMMENT ON TABLE categories IS 'Product categories for organizing the catalog';
COMMENT ON TABLE products IS 'Main product catalog with pricing and metadata';
COMMENT ON TABLE addresses IS 'User delivery addresses with PII encryption requirements';
COMMENT ON TABLE payment_methods IS 'Tokenized payment method storage for users';
COMMENT ON TABLE promotions IS 'Discount codes and promotional campaigns';
COMMENT ON TABLE orders IS 'Complete order information with financial calculations';
COMMENT ON TABLE order_items IS 'Line items for each order linking products and quantities';
COMMENT ON TABLE cart_items IS 'Persistent shopping cart storage';
COMMENT ON TABLE order_status_history IS 'Audit trail for order status changes';
COMMENT ON TABLE product_offers IS 'Time-limited product discounts and sales';

-- =====================================================
-- INITIAL DATA SETUP (OPTIONAL)
-- =====================================================

-- Insert default categories
INSERT INTO categories (category_name, category_slug, description, sort_order) VALUES
('Rice Milk', 'rice-milk', 'Traditional Egyptian rice pudding variations', 1),
('Cheesecake', 'cheesecake', 'Creamy cheesecake varieties', 2),
('Breakfast', 'breakfast', 'Morning treats and breakfast items', 3),
('Farghaly Juice', 'farghaly-juice', 'Fresh fruit juices and beverages', 4),
('Ashtoota', 'ashtoota', 'Traditional Egyptian layered desserts', 5),
('Um Ali', 'um-ali', 'Classic Egyptian bread pudding', 6),
('Basabeso', 'basabeso', 'Sweet semolina-based desserts', 7);

-- =====================================================
-- SCHEMA VALIDATION QUERIES
-- =====================================================

-- Query to validate schema creation
/*
SELECT 
    schemaname,
    tablename,
    tableowner
FROM pg_tables 
WHERE schemaname = 'public'
AND tablename IN (
    'users', 'categories', 'products', 'addresses', 
    'payment_methods', 'promotions', 'orders', 
    'order_items', 'cart_items', 'order_status_history', 
    'product_offers'
);
*/