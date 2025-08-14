# Labanita Database Setup Guide

## 🗄️ Database Setup Instructions

This guide will help you set up the complete Labanita database schema with all tables, constraints, indexes, and business logic triggers.

## 📋 Prerequisites

### 1. PostgreSQL Installation
- **PostgreSQL 12+** installed and running
- **psql** command-line tool available
- **pgAdmin** (optional, for GUI management)

### 2. Database Access
- **PostgreSQL user** with CREATE privileges
- **Password** for the PostgreSQL user
- **Port** (default: 5432)

## 🚀 Quick Setup

### Step 1: Create Database
```bash
# Connect to PostgreSQL as superuser
psql -U postgres

# Create the database
CREATE DATABASE labanita;

# Connect to the new database
\c labanita

# Exit psql
\q
```

### Step 2: Run the Setup Script
```bash
# Run the complete setup script
psql -U postgres -d labanita -f database_setup.sql
```

### Step 3: Verify Setup
```bash
# Connect to the database
psql -U postgres -d labanita

# List all tables
\dt

# Check table structure
\d users
\d categories
\d products

# Exit
\q
```

## 🔧 Detailed Setup Process

### Option 1: Command Line (Recommended)

#### 1. Create Database
```bash
# Create database
createdb -U postgres labanita

# Or using psql
psql -U postgres -c "CREATE DATABASE labanita;"
```

#### 2. Run Setup Script
```bash
# Execute the complete setup
psql -U postgres -d labanita -f database_setup.sql
```

#### 3. Verify Installation
```bash
# Connect and verify
psql -U postgres -d labanita

# Check tables
\dt

# Check functions
\df

# Check triggers
\dy

# Exit
\q
```

### Option 2: Using pgAdmin

#### 1. Open pgAdmin
- Launch pgAdmin application
- Connect to your PostgreSQL server

#### 2. Create Database
- Right-click on "Databases"
- Select "Create" → "Database"
- Name: `labanita`
- Click "Save"

#### 3. Run Script
- Right-click on `labanita` database
- Select "Query Tool"
- Copy and paste the contents of `database_setup.sql`
- Click "Execute" (F5)

## 📊 What Gets Created

### Tables (11)
1. **users** - User accounts and authentication
2. **categories** - Product categories
3. **products** - Product catalog
4. **addresses** - Delivery addresses
5. **payment_methods** - Payment options
6. **promotions** - Discount codes
7. **orders** - Customer orders
8. **order_items** - Order line items
9. **cart_items** - Shopping cart
10. **order_status_history** - Order tracking
11. **product_offers** - Product discounts

### Constraints
- **Primary Keys**: UUID with auto-generation
- **Foreign Keys**: Referential integrity
- **Check Constraints**: Business logic validation
- **Unique Constraints**: Data uniqueness
- **Format Validation**: Phone numbers, slugs, etc.

### Indexes
- **Performance indexes** for common queries
- **Composite indexes** for complex searches
- **Partial indexes** for active records

### Triggers
- **Automatic timestamps** (updated_at)
- **Business logic** (single default address/payment)
- **Order number generation** (LBN + date + sequence)
- **Status history tracking**
- **Promotion usage counting**

### Functions
- **update_updated_at_column()** - Timestamp updates
- **ensure_single_default_address()** - Address logic
- **ensure_single_default_payment()** - Payment logic
- **update_promotion_usage()** - Usage tracking
- **create_order_status_history()** - Status tracking
- **generate_order_number()** - Order numbering

## 🔍 Verification Queries

### Check Tables
```sql
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
```

### Check Functions
```sql
SELECT 
    proname,
    prosrc
FROM pg_proc 
WHERE pronamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public');
```

### Check Triggers
```sql
SELECT 
    tgname,
    tgrelid::regclass as table_name,
    tgfoid::regproc as function_name
FROM pg_trigger 
WHERE tgrelid IN (
    SELECT oid FROM pg_class 
    WHERE relnamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')
);
```

### Check Indexes
```sql
SELECT 
    indexname,
    tablename,
    indexdef
FROM pg_indexes 
WHERE schemaname = 'public'
ORDER BY tablename, indexname;
```

## 🚨 Troubleshooting

### Common Issues

#### 1. Permission Denied
```bash
# Ensure user has proper privileges
psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE labanita TO your_user;"
```

#### 2. Extension Not Found
```sql
-- Install uuid-ossp extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
```

#### 3. Constraint Violation
```sql
-- Check constraint details
SELECT conname, contype, pg_get_constraintdef(oid) 
FROM pg_constraint 
WHERE conrelid = 'table_name'::regclass;
```

#### 4. Trigger Errors
```sql
-- Check trigger status
SELECT 
    tgname,
    tgenabled,
    tgrelid::regclass as table_name
FROM pg_trigger;
```

### Reset Database (Development Only)
```bash
# Drop and recreate (WARNING: All data will be lost!)
psql -U postgres -c "DROP DATABASE IF EXISTS labanita;"
psql -U postgres -c "CREATE DATABASE labanita;"
psql -U postgres -d labanita -f database_setup.sql
```

## 🔐 Security Considerations

### PII Fields
The following fields contain Personally Identifiable Information (PII):
- **users**: phone_number, full_name, email
- **addresses**: full_name, phone_number, email, street_address
- **payment_methods**: card_holder_name

### Recommendations
1. **Encrypt PII fields** at rest
2. **Implement access controls** for sensitive data
3. **Audit access** to PII-containing tables
4. **Comply with GDPR** and local data protection laws

## 📈 Performance Optimization

### Index Strategy
- **Primary indexes** on UUID fields
- **Composite indexes** for common query patterns
- **Partial indexes** for active records only
- **Covering indexes** for frequently accessed columns

### Query Optimization
- Use **EXPLAIN ANALYZE** for query performance analysis
- Monitor **slow query logs**
- Regular **VACUUM** and **ANALYZE** operations
- **Connection pooling** for high-traffic applications

## 🔄 Maintenance

### Regular Tasks
```sql
-- Update table statistics
ANALYZE;

-- Clean up dead tuples
VACUUM;

-- Full vacuum with analyze
VACUUM ANALYZE;
```

### Monitoring
```sql
-- Check table sizes
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables 
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

## 📚 Additional Resources

### Documentation
- [PostgreSQL Official Docs](https://www.postgresql.org/docs/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [FastAPI Database](https://fastapi.tiangolo.com/tutorial/sql-databases/)

### Tools
- **pgAdmin**: GUI database management
- **DBeaver**: Universal database tool
- **DataGrip**: JetBrains database IDE

---

## 🎯 Next Steps

After successful database setup:

1. **Update `.env`** with database connection details
2. **Test API endpoints** with sample data
3. **Implement authentication** and authorization
4. **Add business logic** services
5. **Set up monitoring** and logging

---

**Last Updated**: August 2024  
**Version**: 1.0.0  
**Status**: Ready for Production