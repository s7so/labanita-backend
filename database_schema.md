# Labanita Database Schema - Entity Relationship Design

## Core Entities and Attributes

### 1. Users
| Column Name | Data Type | Constraints/Notes |
|-------------|-----------|-------------------|
| user_id | UUID | PRIMARY KEY |
| phone_number | VARCHAR(20) | UNIQUE, NOT NULL #PII |
| full_name | VARCHAR(255) | #PII |
| email | VARCHAR(255) | UNIQUE #PII |
| facebook_id | VARCHAR(255) | UNIQUE, NULL (for Facebook login) |
| google_id | VARCHAR(255) | UNIQUE, NULL (for Google login) |
| points_balance | INTEGER | DEFAULT 0, NOT NULL |
| points_expiry_date | TIMESTAMP | NULL |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP |
| is_active | BOOLEAN | DEFAULT TRUE |

### 2. Categories
| Column Name | Data Type | Constraints/Notes |
|-------------|-----------|-------------------|
| category_id | UUID | PRIMARY KEY |
| category_name | VARCHAR(100) | NOT NULL, UNIQUE |
| category_slug | VARCHAR(100) | NOT NULL, UNIQUE |
| description | TEXT | NULL |
| image_url | VARCHAR(500) | NULL |
| sort_order | INTEGER | DEFAULT 0 |
| is_active | BOOLEAN | DEFAULT TRUE |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP |

### 3. Products
| Column Name | Data Type | Constraints/Notes |
|-------------|-----------|-------------------|
| product_id | UUID | PRIMARY KEY |
| category_id | UUID | FOREIGN KEY References Categories(category_id) |
| product_name | VARCHAR(255) | NOT NULL |
| product_slug | VARCHAR(255) | NOT NULL, UNIQUE |
| description | TEXT | NULL |
| base_price | DECIMAL(10, 2) | NOT NULL |
| image_url | VARCHAR(500) | NULL |
| sort_order | INTEGER | DEFAULT 0 |
| is_featured | BOOLEAN | DEFAULT FALSE |
| is_new_arrival | BOOLEAN | DEFAULT FALSE |
| is_best_selling | BOOLEAN | DEFAULT FALSE |
| is_active | BOOLEAN | DEFAULT TRUE |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP |

### 4. Addresses
| Column Name | Data Type | Constraints/Notes |
|-------------|-----------|-------------------|
| address_id | UUID | PRIMARY KEY |
| user_id | UUID | FOREIGN KEY References Users(user_id) |
| address_type | VARCHAR(50) | NOT NULL (e.g., 'Home', 'Work', 'Other') |
| full_name | VARCHAR(255) | NOT NULL #PII |
| phone_number | VARCHAR(20) | NOT NULL #PII |
| email | VARCHAR(255) | NULL #PII |
| street_address | TEXT | NOT NULL #PII |
| building_number | VARCHAR(50) | NULL #PII |
| flat_number | VARCHAR(50) | NULL #PII |
| city | VARCHAR(100) | NOT NULL |
| area | VARCHAR(100) | NULL |
| is_default | BOOLEAN | DEFAULT FALSE |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP |

### 5. Payment_Methods
| Column Name | Data Type | Constraints/Notes |
|-------------|-----------|-------------------|
| payment_method_id | UUID | PRIMARY KEY |
| user_id | UUID | FOREIGN KEY References Users(user_id) |
| payment_type | VARCHAR(50) | NOT NULL (e.g., 'CARD', 'APPLE_PAY', 'CASH') |
| card_holder_name | VARCHAR(255) | NULL #PII |
| card_last_four | VARCHAR(4) | NULL |
| card_brand | VARCHAR(50) | NULL (e.g., 'Visa', 'Mastercard') |
| expiry_month | INTEGER | NULL |
| expiry_year | INTEGER | NULL |
| is_default | BOOLEAN | DEFAULT FALSE |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP |

### 6. Promotions
| Column Name | Data Type | Constraints/Notes |
|-------------|-----------|-------------------|
| promotion_id | UUID | PRIMARY KEY |
| promotion_code | VARCHAR(50) | UNIQUE, NOT NULL |
| promotion_name | VARCHAR(255) | NOT NULL |
| description | TEXT | NULL |
| discount_type | VARCHAR(20) | NOT NULL (e.g., 'PERCENTAGE', 'FIXED_AMOUNT') |
| discount_value | DECIMAL(10, 2) | NOT NULL |
| minimum_order_amount | DECIMAL(10, 2) | DEFAULT 0 |
| maximum_discount_amount | DECIMAL(10, 2) | NULL |
| usage_limit | INTEGER | NULL (NULL = unlimited) |
| usage_count | INTEGER | DEFAULT 0 |
| start_date | TIMESTAMP | NOT NULL |
| end_date | TIMESTAMP | NOT NULL |
| is_active | BOOLEAN | DEFAULT TRUE |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP |

### 7. Orders
| Column Name | Data Type | Constraints/Notes |
|-------------|-----------|-------------------|
| order_id | UUID | PRIMARY KEY |
| order_number | VARCHAR(50) | UNIQUE, NOT NULL |
| user_id | UUID | FOREIGN KEY References Users(user_id) |
| address_id | UUID | FOREIGN KEY References Addresses(address_id) |
| payment_method_id | UUID | FOREIGN KEY References Payment_Methods(payment_method_id) |
| promotion_id | UUID | NULL, FOREIGN KEY References Promotions(promotion_id) |
| order_status | VARCHAR(50) | NOT NULL, DEFAULT 'PENDING' |
| subtotal | DECIMAL(10, 2) | NOT NULL |
| delivery_fee | DECIMAL(10, 2) | NOT NULL |
| discount_amount | DECIMAL(10, 2) | DEFAULT 0 |
| points_used | INTEGER | DEFAULT 0 |
| points_earned | INTEGER | DEFAULT 0 |
| total_amount | DECIMAL(10, 2) | NOT NULL |
| order_notes | TEXT | NULL |
| estimated_delivery_time | TIMESTAMP | NULL |
| delivered_at | TIMESTAMP | NULL |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP |

### 8. Order_Items
| Column Name | Data Type | Constraints/Notes |
|-------------|-----------|-------------------|
| order_item_id | UUID | PRIMARY KEY |
| order_id | UUID | FOREIGN KEY References Orders(order_id) |
| product_id | UUID | FOREIGN KEY References Products(product_id) |
| quantity | INTEGER | NOT NULL, CHECK (quantity > 0) |
| unit_price | DECIMAL(10, 2) | NOT NULL |
| total_price | DECIMAL(10, 2) | NOT NULL |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP |

### 9. Cart_Items
| Column Name | Data Type | Constraints/Notes |
|-------------|-----------|-------------------|
| cart_item_id | UUID | PRIMARY KEY |
| user_id | UUID | FOREIGN KEY References Users(user_id) |
| product_id | UUID | FOREIGN KEY References Products(product_id) |
| quantity | INTEGER | NOT NULL, CHECK (quantity > 0) |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP |

### 10. Order_Status_History
| Column Name | Data Type | Constraints/Notes |
|-------------|-----------|-------------------|
| status_history_id | UUID | PRIMARY KEY |
| order_id | UUID | FOREIGN KEY References Orders(order_id) |
| status | VARCHAR(50) | NOT NULL |
| notes | TEXT | NULL |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP |

### 11. Product_Offers
| Column Name | Data Type | Constraints/Notes |
|-------------|-----------|-------------------|
| offer_id | UUID | PRIMARY KEY |
| product_id | UUID | FOREIGN KEY References Products(product_id) |
| offer_name | VARCHAR(255) | NOT NULL |
| discount_type | VARCHAR(20) | NOT NULL (e.g., 'PERCENTAGE', 'FIXED_AMOUNT') |
| discount_value | DECIMAL(10, 2) | NOT NULL |
| original_price | DECIMAL(10, 2) | NOT NULL |
| sale_price | DECIMAL(10, 2) | NOT NULL |
| start_date | TIMESTAMP | NOT NULL |
| end_date | TIMESTAMP | NOT NULL |
| is_active | BOOLEAN | DEFAULT TRUE |
| created_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT CURRENT_TIMESTAMP |

## Entity Relationships

### Primary Relationships

**Users ↔ Addresses**
- **Relationship Type:** One-to-Many
- **Description:** One user can have multiple delivery addresses, but each address belongs to only one user.

**Users ↔ Payment_Methods**
- **Relationship Type:** One-to-Many  
- **Description:** One user can have multiple payment methods saved, but each payment method belongs to only one user.

**Users ↔ Orders**
- **Relationship Type:** One-to-Many
- **Description:** One user can place multiple orders, but each order belongs to only one user.

**Users ↔ Cart_Items**
- **Relationship Type:** One-to-Many
- **Description:** One user can have multiple items in their cart, but each cart item belongs to only one user.

**Categories ↔ Products**
- **Relationship Type:** One-to-Many
- **Description:** One category can contain multiple products, but each product belongs to only one category.

**Products ↔ Cart_Items**
- **Relationship Type:** One-to-Many
- **Description:** One product can be in multiple users' carts, but each cart item references only one product.

**Products ↔ Order_Items**
- **Relationship Type:** One-to-Many
- **Description:** One product can be ordered multiple times across different orders, but each order item references only one product.

**Products ↔ Product_Offers**
- **Relationship Type:** One-to-Many
- **Description:** One product can have multiple offers over time, but each offer applies to only one product.

**Orders ↔ Order_Items**
- **Relationship Type:** One-to-Many
- **Description:** One order can contain multiple products (through order items), but each order item belongs to only one order.

**Orders ↔ Order_Status_History**
- **Relationship Type:** One-to-Many
- **Description:** One order can have multiple status changes tracked over time, but each status history entry belongs to only one order.

**Orders ↔ Addresses**
- **Relationship Type:** Many-to-One
- **Description:** Multiple orders can be delivered to the same address, but each order has only one delivery address.

**Orders ↔ Payment_Methods**
- **Relationship Type:** Many-to-One
- **Description:** Multiple orders can use the same payment method, but each order uses only one payment method.

**Orders ↔ Promotions**
- **Relationship Type:** Many-to-One
- **Description:** Multiple orders can use the same promotion code, but each order can only use one promotion (or none).

### Indirect Many-to-Many Relationships

**Orders ↔ Products** (via Order_Items)
- **Relationship Type:** Many-to-Many
- **Description:** One order can contain multiple products, and one product can be in multiple orders. This is implemented through the Order_Items junction table.

**Users ↔ Products** (via Cart_Items)
- **Relationship Type:** Many-to-Many
- **Description:** One user can have multiple products in their cart, and one product can be in multiple users' carts. This is implemented through the Cart_Items junction table.

## Data Integrity Constraints

### Referential Integrity
- All foreign key relationships maintain referential integrity
- Cascade delete rules should be carefully implemented (e.g., deleting a user should handle their orders appropriately)

### Business Logic Constraints
- Order total_amount must equal subtotal + delivery_fee - discount_amount
- Order_Items total_price must equal quantity × unit_price
- Promotion usage_count cannot exceed usage_limit
- Product offers must have end_date > start_date
- User points_balance cannot be negative

### Unique Constraints
- User phone numbers must be unique across the system
- Order numbers must be unique for tracking
- Promotion codes must be unique
- Product slugs must be unique for URL generation

## Indexes Recommendations

### Performance Indexes
- `idx_users_phone` on Users(phone_number)
- `idx_users_email` on Users(email) 
- `idx_products_category` on Products(category_id)
- `idx_products_featured` on Products(is_featured, is_active)
- `idx_orders_user` on Orders(user_id)
- `idx_orders_status` on Orders(order_status)
- `idx_orders_created` on Orders(created_at)
- `idx_cart_items_user` on Cart_Items(user_id)
- `idx_order_items_order` on Order_Items(order_id)

## Privacy and Security Considerations

### PII Fields Identified
All fields marked with #PII contain personally identifiable information and require:
- Encryption at rest
- Restricted access controls
- Compliance with data protection regulations (GDPR, etc.)
- Secure handling in application logs
- Data retention policies

### Sensitive Data
- Payment card information is tokenized (only last 4 digits stored)
- Full card details should never be stored in the database
- Integration with secure payment processors required

## Implementation Status

### ✅ Completed
- **SQLAlchemy Models**: All 11 models implemented in `models.py`
- **Database Schema**: Complete PostgreSQL DDL script
- **Relationships**: All relationships properly defined
- **Constraints**: All business logic constraints implemented
- **Indexes**: Performance indexes created
- **API Endpoints**: Basic CRUD operations implemented
- **Data Validation**: Pydantic schemas for all models

### 🔄 Next Steps
- **Database Migrations**: Alembic setup for version control
- **Authentication**: JWT-based user authentication
- **Authorization**: Role-based access control
- **Business Logic**: Order processing workflow
- **Payment Integration**: Secure payment processing
- **Testing**: Comprehensive test suite
- **Documentation**: API documentation and examples

## Database Connection

### Environment Configuration
```env
DATABASE_URL="postgresql://postgres:password@localhost/labanita"
```

### Required Extensions
```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
```

### Table Creation
Tables are automatically created when the application starts using:
```python
Base.metadata.create_all(bind=engine)
```

---

**Last Updated**: August 2024  
**Version**: 1.0.0  
**Status**: Ready for Development