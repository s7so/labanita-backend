-- =====================================================
-- Labanita Sample Data Insertion Script
-- Comprehensive test data for development and testing
-- =====================================================

-- =====================================================
-- 1. INSERTING CATEGORIES (7 categories as per DDL)
-- =====================================================

INSERT INTO categories (category_id, category_name, category_slug, description, image_url, sort_order, is_active, created_at, updated_at) VALUES
('550e8400-e29b-41d4-a716-446655440001', 'Rice Milk', 'rice-milk', 'Traditional Egyptian rice pudding variations with rich flavors and textures', 'https://labanita.com/images/categories/rice-milk.jpg', 1, true, '2024-01-01 00:00:00', '2024-01-01 00:00:00'),
('550e8400-e29b-41d4-a716-446655440002', 'Cheesecake', 'cheesecake', 'Creamy cheesecake varieties with Egyptian-inspired toppings', 'https://labanita.com/images/categories/cheesecake.jpg', 2, true, '2024-01-01 00:00:00', '2024-01-01 00:00:00'),
('550e8400-e29b-41d4-a716-446655440003', 'Breakfast', 'breakfast', 'Morning treats and breakfast items perfect for starting your day', 'https://labanita.com/images/categories/breakfast.jpg', 3, true, '2024-01-01 00:00:00', '2024-01-01 00:00:00'),
('550e8400-e29b-41d4-a716-446655440004', 'Farghaly Juice', 'farghaly-juice', 'Fresh fruit juices and beverages made from seasonal fruits', 'https://labanita.com/images/categories/farghaly-juice.jpg', 4, true, '2024-01-01 00:00:00', '2024-01-01 00:00:00'),
('550e8400-e29b-41d4-a716-446655440005', 'Ashtoota', 'ashtoota', 'Traditional Egyptian layered desserts with nuts and honey', 'https://labanita.com/images/categories/ashtoota.jpg', 5, true, '2024-01-01 00:00:00', '2024-01-01 00:00:00'),
('550e8400-e29b-41d4-a716-446655440006', 'Um Ali', 'um-ali', 'Classic Egyptian bread pudding with rich cream and nuts', 'https://labanita.com/images/categories/um-ali.jpg', 6, true, '2024-01-01 00:00:00', '2024-01-01 00:00:00'),
('550e8400-e29b-41d4-a716-446655440007', 'Basabeso', 'basabeso', 'Sweet semolina-based desserts with coconut and syrup', 'https://labanita.com/images/categories/basabeso.jpg', 7, true, '2024-01-01 00:00:00', '2024-01-01 00:00:00');

-- =====================================================
-- 2. INSERTING PRODUCTS (15 products across categories)
-- =====================================================

INSERT INTO products (product_id, category_id, product_name, product_slug, description, base_price, image_url, sort_order, is_featured, is_new_arrival, is_best_selling, is_active, created_at, updated_at) VALUES
-- Rice Milk Category
('660e8400-e29b-41d4-a716-446655440001', '550e8400-e29b-41d4-a716-446655440001', 'Roz Bel Laban Classic', 'roz-bel-laban-classic', 'Traditional Egyptian rice pudding with creamy milk and rose water', 25.00, 'https://labanita.com/images/products/roz-bel-laban-classic.jpg', 1, true, false, true, true, '2024-01-01 00:00:00', '2024-01-01 00:00:00'),
('660e8400-e29b-41d4-a716-446655440002', '550e8400-e29b-41d4-a716-446655440001', 'Roz Bel Laban with Pistachios', 'roz-bel-laban-pistachios', 'Rich rice pudding topped with premium pistachios', 35.00, 'https://labanita.com/images/products/roz-bel-laban-pistachios.jpg', 2, false, true, false, true, '2024-01-01 00:00:00', '2024-01-01 00:00:00'),
('660e8400-e29b-41d4-a716-446655440003', '550e8400-e29b-41d4-a716-446655440001', 'Roz Bel Laban with Dates', 'roz-bel-laban-dates', 'Sweet rice pudding with fresh Egyptian dates', 30.00, 'https://labanita.com/images/products/roz-bel-laban-dates.jpg', 3, false, false, false, true, '2024-01-01 00:00:00', '2024-01-01 00:00:00'),

-- Cheesecake Category
('660e8400-e29b-41d4-a716-446655440004', '550e8400-e29b-41d4-a716-446655440002', 'New York Cheesecake', 'new-york-cheesecake', 'Classic New York style cheesecake with strawberry sauce', 45.00, 'https://labanita.com/images/products/new-york-cheesecake.jpg', 1, true, false, true, true, '2024-01-01 00:00:00', '2024-01-01 00:00:00'),
('660e8400-e29b-41d4-a716-446655440005', '550e8400-e29b-41d4-a716-446655440002', 'Oreo Cheesecake', 'oreo-cheesecake', 'Creamy cheesecake with Oreo cookie crust and pieces', 50.00, 'https://labanita.com/images/products/oreo-cheesecake.jpg', 2, false, true, false, true, '2024-01-01 00:00:00', '2024-01-01 00:00:00'),

-- Breakfast Category
('660e8400-e29b-41d4-a716-446655440006', '550e8400-e29b-41d4-a716-446655440003', 'Feteer Meshaltet', 'feteer-meshaltet', 'Traditional Egyptian layered pastry with honey and nuts', 20.00, 'https://labanita.com/images/products/feteer-meshaltet.jpg', 1, false, false, true, true, '2024-01-01 00:00:00', '2024-01-01 00:00:00'),
('660e8400-e29b-41d4-a716-446655440007', '550e8400-e29b-41d4-a716-446655440003', 'Kunafa with Cream', 'kunafa-cream', 'Crispy kunafa filled with sweet cream cheese', 28.00, 'https://labanita.com/images/products/kunafa-cream.jpg', 2, true, false, false, true, '2024-01-01 00:00:00', '2024-01-01 00:00:00'),

-- Farghaly Juice Category
('660e8400-e29b-41d4-a716-446655440008', '550e8400-e29b-41d4-a716-446655440004', 'Fresh Mango Juice', 'fresh-mango-juice', '100% natural mango juice from Egyptian mangoes', 15.00, 'https://labanita.com/images/products/fresh-mango-juice.jpg', 1, false, true, true, true, '2024-01-01 00:00:00', '2024-01-01 00:00:00'),
('660e8400-e29b-41d4-a716-446655440009', '550e8400-e29b-41d4-a716-446655440004', 'Strawberry Banana Smoothie', 'strawberry-banana-smoothie', 'Refreshing smoothie with fresh strawberries and bananas', 18.00, 'https://labanita.com/images/products/strawberry-banana-smoothie.jpg', 2, false, false, false, true, '2024-01-01 00:00:00', '2024-01-01 00:00:00'),

-- Ashtoota Category
('660e8400-e29b-41d4-a716-446655440010', '550e8400-e29b-41d4-a716-446655440005', 'Classic Ashtoota', 'classic-ashtoota', 'Traditional layered dessert with nuts, honey, and cream', 40.00, 'https://labanita.com/images/products/classic-ashtoota.jpg', 1, true, false, true, true, '2024-01-01 00:00:00', '2024-01-01 00:00:00'),
('660e8400-e29b-41d4-a716-446655440011', '550e8400-e29b-41d4-a716-446655440005', 'Ashtoota with Pistachios', 'ashtoota-pistachios', 'Premium ashtoota with extra pistachios and gold leaf', 55.00, 'https://labanita.com/images/products/ashtoota-pistachios.jpg', 2, false, true, false, true, '2024-01-01 00:00:00', '2024-01-01 00:00:00'),

-- Um Ali Category
('660e8400-e29b-41d4-a716-446655440012', '550e8400-e29b-41d4-a716-446655440006', 'Traditional Um Ali', 'traditional-um-ali', 'Classic Egyptian bread pudding with nuts and cream', 22.00, 'https://labanita.com/images/products/traditional-um-ali.jpg', 1, false, false, true, true, '2024-01-01 00:00:00', '2024-01-01 00:00:00'),
('660e8400-e29b-41d4-a716-446655440013', '550e8400-e29b-41d4-a716-446655440006', 'Um Ali with Chocolate', 'um-ali-chocolate', 'Um Ali with rich chocolate chips and cocoa powder', 25.00, 'https://labanita.com/images/products/um-ali-chocolate.jpg', 2, false, true, false, true, '2024-01-01 00:00:00', '2024-01-01 00:00:00'),

-- Basabeso Category
('660e8400-e29b-41d4-a716-446655440014', '550e8400-e29b-41d4-a716-446655440007', 'Classic Basabeso', 'classic-basabeso', 'Traditional semolina dessert with coconut and syrup', 18.00, 'https://labanita.com/images/products/classic-basabeso.jpg', 1, false, false, true, true, '2024-01-01 00:00:00', '2024-01-01 00:00:00'),
('660e8400-e29b-41d4-a716-446655440015', '550e8400-e29b-41d4-a716-446655440007', 'Basabeso with Nuts', 'basabeso-nuts', 'Basabeso topped with mixed nuts and honey', 22.00, 'https://labanita.com/images/products/basabeso-nuts.jpg', 2, false, false, false, true, '2024-01-01 00:00:00', '2024-01-01 00:00:00');

-- =====================================================
-- 3. INSERTING PROMOTIONS (2 active promotions)
-- =====================================================

INSERT INTO promotions (promotion_id, promotion_code, promotion_name, description, discount_type, discount_value, minimum_order_amount, maximum_discount_amount, usage_limit, usage_count, start_date, end_date, is_active, created_at, updated_at) VALUES
('770e8400-e29b-41d4-a716-446655440001', 'WELCOME20', 'Welcome Discount', '20% off for new customers on orders above 50 EGP', 'PERCENTAGE', 20.00, 50.00, 100.00, 100, 0, '2024-01-01 00:00:00', '2024-12-31 23:59:59', true, '2024-01-01 00:00:00', '2024-01-01 00:00:00'),
('770e8400-e29b-41d4-a716-446655440002', 'SAVE15', 'Fixed Amount Savings', 'Save 15 EGP on orders above 100 EGP', 'FIXED_AMOUNT', 15.00, 100.00, 15.00, 50, 0, '2024-01-01 00:00:00', '2024-12-31 23:59:59', true, '2024-01-01 00:00:00', '2024-01-01 00:00:00');

-- =====================================================
-- 4. INSERTING PRODUCT OFFERS (1 active offer)
-- =====================================================

INSERT INTO product_offers (offer_id, product_id, offer_name, discount_type, discount_value, original_price, sale_price, start_date, end_date, is_active, created_at, updated_at) VALUES
('880e8400-e29b-41d4-a716-446655440001', '660e8400-e29b-41d4-a716-446655440001', 'Summer Rice Pudding Sale', 'PERCENTAGE', 15.00, 25.00, 21.25, '2024-06-01 00:00:00', '2024-08-31 23:59:59', true, '2024-06-01 00:00:00', '2024-06-01 00:00:00');

-- =====================================================
-- 5. CREATING DATA FOR ALI (Power User - User A)
-- =====================================================

-- Insert Ali's user account
INSERT INTO users (user_id, phone_number, full_name, email, facebook_id, google_id, points_balance, points_expiry_date, is_active, created_at, updated_at) VALUES
('110e8400-e29b-41d4-a716-446655440001', '+201234567890', 'Ali Hassan Ahmed', 'ali.hassan@email.com', 'ali.hassan.123', NULL, 450, '2024-12-31 23:59:59', true, '2023-06-01 10:00:00', '2024-01-15 14:30:00');

-- Insert Ali's addresses
INSERT INTO addresses (address_id, user_id, address_type, full_name, phone_number, email, street_address, building_number, flat_number, city, area, is_default, created_at, updated_at) VALUES
('220e8400-e29b-41d4-a716-446655440001', '110e8400-e29b-41d4-a716-446655440001', 'Home', 'Ali Hassan Ahmed', '+201234567890', 'ali.hassan@email.com', '123 El Tahrir Street', 'Building 15', 'Apartment 8', 'Cairo', 'Downtown', true, '2023-06-01 10:00:00', '2023-06-01 10:00:00'),
('220e8400-e29b-41d4-a716-446655440002', '110e8400-e29b-41d4-a716-446655440001', 'Work', 'Ali Hassan Ahmed', '+201234567890', 'ali.hassan@email.com', '456 Zamalek Street', 'Building 22', 'Office 12', 'Cairo', 'Zamalek', false, '2023-06-15 09:00:00', '2023-06-15 09:00:00');

-- Insert Ali's payment methods
INSERT INTO payment_methods (payment_method_id, user_id, payment_type, card_holder_name, card_last_four, card_brand, expiry_month, expiry_year, is_default, created_at, updated_at) VALUES
('330e8400-e29b-41d4-a716-446655440001', '110e8400-e29b-41d4-a716-446655440001', 'CARD', 'Ali Hassan Ahmed', '1234', 'Visa', 12, 2026, true, '2023-06-01 10:00:00', '2023-06-01 10:00:00'),
('330e8400-e29b-41d4-a716-446655440002', '110e8400-e29b-41d4-a716-446655440001', 'CARD', 'Ali Hassan Ahmed', '5678', 'Mastercard', 8, 2027, false, '2023-07-01 11:00:00', '2023-07-01 11:00:00');

-- =====================================================
-- 6. CREATING DATA FOR FATIMA (New User - User B)
-- =====================================================

-- Insert Fatima's user account
INSERT INTO users (user_id, phone_number, full_name, email, facebook_id, google_id, points_balance, points_expiry_date, is_active, created_at, updated_at) VALUES
('110e8400-e29b-41d4-a716-446655440002', '+201112223334', 'Fatima Mahmoud', 'fatima.mahmoud@email.com', NULL, NULL, 25, '2024-12-31 23:59:59', true, '2024-01-10 15:00:00', '2024-01-10 15:00:00');

-- Insert Fatima's address
INSERT INTO addresses (address_id, user_id, address_type, full_name, phone_number, email, street_address, building_number, flat_number, city, area, is_default, created_at, updated_at) VALUES
('220e8400-e29b-41d4-a716-446655440003', '110e8400-e29b-41d4-a716-446655440002', 'Home', 'Fatima Mahmoud', '+201112223334', 'fatima.mahmoud@email.com', '789 Heliopolis Street', 'Building 33', 'Apartment 15', 'Cairo', 'Heliopolis', true, '2024-01-10 15:00:00', '2024-01-10 15:00:00');

-- Insert Fatima's payment method
INSERT INTO payment_methods (payment_method_id, user_id, payment_type, card_holder_name, card_last_four, card_brand, expiry_month, expiry_year, is_default, created_at, updated_at) VALUES
('330e8400-e29b-41d4-a716-446655440003', '110e8400-e29b-41d4-a716-446655440002', 'CASH', NULL, NULL, NULL, NULL, NULL, true, '2024-01-10 15:00:00', '2024-01-10 15:00:00');

-- =====================================================
-- 7. CREATING DATA FOR OMAR (Cart User - User C)
-- =====================================================

-- Insert Omar's user account
INSERT INTO users (user_id, phone_number, full_name, email, facebook_id, google_id, points_balance, points_expiry_date, is_active, created_at, updated_at) VALUES
('110e8400-e29b-41d4-a716-446655440003', '+201556667778', 'Omar Khalil', 'omar.khalil@gmail.com', NULL, 'omar.khalil.456', 0, NULL, true, '2024-01-05 12:00:00', '2024-01-05 12:00:00');

-- Insert Omar's address
INSERT INTO addresses (address_id, user_id, address_type, full_name, phone_number, email, street_address, building_number, flat_number, city, area, is_default, created_at, updated_at) VALUES
('220e8400-e29b-41d4-a716-446655440004', '110e8400-e29b-41d4-a716-446655440003', 'Home', 'Omar Khalil', '+201556667778', 'omar.khalil@gmail.com', '321 Maadi Street', 'Building 45', 'Apartment 22', 'Cairo', 'Maadi', true, '2024-01-05 12:00:00', '2024-01-05 12:00:00');

-- Insert Omar's payment method
INSERT INTO payment_methods (payment_method_id, user_id, payment_type, card_holder_name, card_last_four, card_brand, expiry_month, expiry_year, is_default, created_at, updated_at) VALUES
('330e8400-e29b-41d4-a716-446655440004', '110e8400-e29b-41d4-a716-446655440003', 'APPLE_PAY', 'Omar Khalil', NULL, NULL, NULL, NULL, true, '2024-01-05 12:00:00', '2024-01-05 12:00:00');

-- =====================================================
-- 8. CREATING ORDERS FOR ALI (Power User)
-- =====================================================

-- Order 1: DELIVERED order from last week (using promotion)
INSERT INTO orders (order_id, order_number, user_id, address_id, payment_method_id, promotion_id, order_status, subtotal, delivery_fee, discount_amount, points_used, points_earned, total_amount, order_notes, estimated_delivery_time, delivered_at, created_at, updated_at) VALUES
('440e8400-e29b-41d4-a716-446655440001', 'LBN202401080001', '110e8400-e29b-41d4-a716-446655440001', '220e8400-e29b-41d4-a716-446655440001', '330e8400-e29b-41d4-a716-446655440001', '770e8400-e29b-41d4-a716-446655440001', 'DELIVERED', 120.00, 15.00, 24.00, 0, 12, 111.00, 'Please deliver to the main entrance', '2024-01-08 19:00:00', '2024-01-08 18:45:00', '2024-01-08 16:00:00', '2024-01-08 18:45:00');

-- Order 1 Items
INSERT INTO order_items (order_item_id, order_id, product_id, quantity, unit_price, total_price, created_at) VALUES
('550e8400-e29b-41d4-a716-446655440001', '440e8400-e29b-41d4-a716-446655440001', '660e8400-e29b-41d4-a716-446655440001', 2, 25.00, 50.00, '2024-01-08 16:00:00'),
('550e8400-e29b-41d4-a716-446655440002', '440e8400-e29b-41d4-a716-446655440001', '660e8400-e29b-41d4-a716-446655440004', 1, 45.00, 45.00, '2024-01-08 16:00:00'),
('550e8400-e29b-41d4-a716-446655440003', '440e8400-e29b-41d4-a716-446655440001', '660e8400-e29b-41d4-a716-446655440008', 2, 15.00, 30.00, '2024-01-08 16:00:00');

-- Order 2: OUT_FOR_DELIVERY order from today
INSERT INTO orders (order_id, order_number, user_id, address_id, payment_method_id, promotion_id, order_status, subtotal, delivery_fee, discount_amount, points_used, points_earned, total_amount, order_notes, estimated_delivery_time, delivered_at, created_at, updated_at) VALUES
('440e8400-e29b-41d4-a716-446655440002', 'LBN202401150002', '110e8400-e29b-41d4-a716-446655440001', '220e8400-e29b-41d4-a716-446655440002', '330e8400-e29b-41d4-a716-446655440002', NULL, 'OUT_FOR_DELIVERY', 95.00, 15.00, 0.00, 50, 10, 110.00, 'Deliver to office reception', '2024-01-15 20:00:00', NULL, '2024-01-15 17:00:00', '2024-01-15 19:30:00');

-- Order 2 Items
INSERT INTO order_items (order_item_id, order_id, product_id, quantity, unit_price, total_price, created_at) VALUES
('550e8400-e29b-41d4-a716-446655440004', '440e8400-e29b-41d4-a716-446655440002', '660e8400-e29b-41d4-a716-446655440010', 1, 40.00, 40.00, '2024-01-15 17:00:00'),
('550e8400-e29b-41d4-a716-446655440005', '440e8400-e29b-41d4-a716-446655440002', '660e8400-e29b-41d4-a716-446655440012', 2, 22.00, 44.00, '2024-01-15 17:00:00'),
('550e8400-e29b-41d4-a716-446655440006', '440e8400-e29b-41d4-a716-446655440002', '660e8400-e29b-41d4-a716-446655440009', 1, 18.00, 18.00, '2024-01-15 17:00:00');

-- Order 3: PENDING order (recent)
INSERT INTO orders (order_id, order_number, user_id, address_id, payment_method_id, promotion_id, order_status, subtotal, delivery_fee, discount_amount, points_used, points_earned, total_amount, order_notes, estimated_delivery_time, delivered_at, created_at, updated_at) VALUES
('440e8400-e29b-41d4-a716-446655440003', 'LBN202401150003', '110e8400-e29b-41d4-a716-446655440001', '220e8400-e29b-41d4-a716-446655440001', '330e8400-e29b-41d4-a716-446655440001', '770e8400-e29b-41d4-a716-446655440002', 'PENDING', 150.00, 15.00, 15.00, 0, 15, 150.00, 'Please call before delivery', '2024-01-15 22:00:00', NULL, '2024-01-15 20:00:00', '2024-01-15 20:00:00');

-- Order 3 Items
INSERT INTO order_items (order_item_id, order_id, product_id, quantity, unit_price, total_price, created_at) VALUES
('550e8400-e29b-41d4-a716-446655440007', '440e8400-e29b-41d4-a716-446655440003', '660e8400-e29b-41d4-a716-446655440005', 1, 50.00, 50.00, '2024-01-15 20:00:00'),
('550e8400-e29b-41d4-a716-446655440008', '440e8400-e29b-41d4-a716-446655440003', '660e8400-e29b-41d4-a716-446655440011', 1, 55.00, 55.00, '2024-01-15 20:00:00'),
('550e8400-e29b-41d4-a716-446655440009', '440e8400-e29b-41d4-a716-446655440003', '660e8400-e29b-41d4-a716-446655440013', 2, 25.00, 50.00, '2024-01-15 20:00:00');

-- =====================================================
-- 9. CREATING ORDER FOR FATIMA (New User)
-- =====================================================

-- Order 4: CONFIRMED order for Fatima
INSERT INTO orders (order_id, order_number, user_id, address_id, payment_method_id, promotion_id, order_status, subtotal, delivery_fee, discount_amount, points_used, points_earned, total_amount, order_notes, estimated_delivery_time, delivered_at, created_at, updated_at) VALUES
('440e8400-e29b-41d4-a716-446655440004', 'LBN202401100004', '110e8400-e29b-41d4-a716-446655440002', '220e8400-e29b-41d4-a716-446655440003', '330e8400-e29b-41d4-a716-446655440003', NULL, 'CONFIRMED', 65.00, 15.00, 0.00, 0, 7, 80.00, 'Please deliver to apartment 15', '2024-01-10 19:00:00', NULL, '2024-01-10 16:00:00', '2024-01-10 16:30:00');

-- Order 4 Items
INSERT INTO order_items (order_item_id, order_id, product_id, quantity, unit_price, total_price, created_at) VALUES
('550e8400-e29b-41d4-a716-446655440010', '440e8400-e29b-41d4-a716-446655440004', '660e8400-e29b-41d4-a716-446655440002', 1, 35.00, 35.00, '2024-01-10 16:00:00'),
('550e8400-e29b-41d4-a716-446655440011', '440e8400-e29b-41d4-a716-446655440004', '660e8400-e29b-41d4-a716-446655440007', 1, 28.00, 28.00, '2024-01-10 16:00:00'),
('550e8400-e29b-41d4-a716-446655440012', '440e8400-e29b-41d4-a716-446655440004', '660e8400-e29b-41d4-a716-446655440008', 1, 15.00, 15.00, '2024-01-10 16:00:00');

-- =====================================================
-- 10. CREATING CART ITEMS FOR OMAR (Cart User)
-- =====================================================

-- Omar has items in cart but no order yet
INSERT INTO cart_items (cart_item_id, user_id, product_id, quantity, created_at, updated_at) VALUES
('660e8400-e29b-41d4-a716-446655440016', '110e8400-e29b-41d4-a716-446655440003', '660e8400-e29b-41d4-a716-446655440001', 2, '2024-01-15 18:00:00', '2024-01-15 18:00:00'),
('660e8400-e29b-41d4-a716-446655440017', '110e8400-e29b-41d4-a716-446655440003', '660e8400-e29b-41d4-a716-446655440004', 1, '2024-01-15 18:00:00', '2024-01-15 18:00:00');

-- =====================================================
-- 11. ORDER STATUS HISTORY (Automatically created by triggers)
-- =====================================================

-- Note: The order_status_history table is automatically populated by triggers
-- when orders are created and updated. The data above will trigger:
-- - Order creation entries
-- - Status change entries for Ali's orders

-- =====================================================
-- 12. VERIFICATION QUERIES
-- =====================================================

-- Uncomment these queries to verify the data insertion:

/*
-- Check all users
SELECT user_id, full_name, phone_number, points_balance, is_active FROM users;

-- Check all categories
SELECT category_name, category_slug, is_active FROM categories;

-- Check all products
SELECT product_name, category_id, base_price, is_featured, is_new_arrival, is_best_selling FROM products;

-- Check user addresses
SELECT u.full_name, a.address_type, a.city, a.area, a.is_default 
FROM users u 
JOIN addresses a ON u.user_id = a.user_id;

-- Check user payment methods
SELECT u.full_name, pm.payment_type, pm.card_brand, pm.is_default 
FROM users u 
JOIN payment_methods pm ON u.user_id = pm.user_id;

-- Check orders with details
SELECT o.order_number, u.full_name, o.order_status, o.subtotal, o.delivery_fee, o.total_amount 
FROM orders o 
JOIN users u ON o.user_id = u.user_id;

-- Check order items
SELECT oi.order_id, p.product_name, oi.quantity, oi.unit_price, oi.total_price 
FROM order_items oi 
JOIN products p ON oi.product_id = p.product_id;

-- Check cart items
SELECT u.full_name, p.product_name, ci.quantity 
FROM cart_items ci 
JOIN users u ON ci.user_id = u.user_id 
JOIN products p ON ci.product_id = p.product_id;

-- Check promotions usage
SELECT p.promotion_code, p.promotion_name, p.usage_count 
FROM promotions p;

-- Check product offers
SELECT po.offer_name, p.product_name, po.original_price, po.sale_price 
FROM product_offers po 
JOIN products p ON po.product_id = p.product_id;
*/

-- =====================================================
-- SAMPLE DATA INSERTION COMPLETE
-- =====================================================
-- 
-- Summary of inserted data:
-- - 3 Users (Ali, Fatima, Omar)
-- - 7 Categories
-- - 15 Products
-- - 2 Promotions
-- - 1 Product Offer
-- - 4 Orders (3 for Ali, 1 for Fatima)
-- - 12 Order Items
-- - 2 Cart Items (for Omar)
-- - Multiple addresses and payment methods
-- 
-- All data is interconnected and follows business logic constraints.
-- Triggers will automatically populate order_status_history table.