# Labanita Egyptian Sweets Store API

A modern, scalable backend API for the Labanita Egyptian sweets delivery application, built with FastAPI, SQLAlchemy, and PostgreSQL.

## 🏗️ Architecture Overview

The Labanita API is built using a modern, layered architecture:

- **FastAPI**: High-performance web framework for building APIs
- **SQLAlchemy 2.0**: Modern Python ORM with type annotations
- **PostgreSQL**: Robust, production-ready database
- **Pydantic**: Data validation and serialization
- **Alembic**: Database migration management

## 🗄️ Database Schema

The application includes a comprehensive database schema with 11 core tables:

### Core Entities
- **Users**: Customer accounts with authentication and loyalty points
- **Categories**: Product categorization (Rice Milk, Sweets, etc.)
- **Products**: Product catalog with pricing and features
- **Addresses**: Customer delivery addresses
- **Payment Methods**: Saved payment options

### Business Logic
- **Orders**: Customer orders with status tracking
- **Order Items**: Order-product relationships
- **Cart Items**: Shopping cart persistence
- **Promotions**: Discount codes and campaigns
- **Product Offers**: Time-limited product discounts
- **Order Status History**: Complete order lifecycle tracking

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- PostgreSQL 12+
- pip or poetry

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd labanita-api
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials
   ```

5. **Database Setup**
   ```bash
   # Create PostgreSQL database
   createdb labanita
   
   # Run database migrations (when implemented)
   alembic upgrade head
   ```

6. **Run the Application**
   ```bash
   uvicorn main:app --reload
   ```

## 📁 Project Structure

```
labanita-api/
├── .env                    # Environment configuration
├── database.py            # Database connection & session management
├── models.py              # SQLAlchemy ORM models
├── schemas.py             # Pydantic validation schemas
├── requirements.txt       # Python dependencies
├── README.md             # Project documentation
└── alembic/              # Database migrations (to be implemented)
    ├── versions/          # Migration files
    ├── env.py            # Alembic environment
    └── alembic.ini      # Alembic configuration
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | Required |
| `APP_NAME` | Application name | "Labanita API" |
| `DEBUG` | Debug mode | false |
| `SECRET_KEY` | JWT secret key | Required |
| `DB_POOL_SIZE` | Database connection pool size | 20 |
| `DB_MAX_OVERFLOW` | Max overflow connections | 30 |

### Database Configuration

The application uses connection pooling for optimal performance:

- **Pool Size**: 20 connections
- **Max Overflow**: 30 additional connections
- **Connection Timeout**: 30 seconds
- **Connection Recycling**: 1 hour

## 🗃️ Database Models

### User Management
- **User**: Core user information, authentication, loyalty points
- **Address**: Multiple delivery addresses per user
- **PaymentMethod**: Saved payment methods (Card, Apple Pay, Cash)

### Product Catalog
- **Category**: Product categories with slugs and sorting
- **Product**: Products with pricing, features, and status flags
- **ProductOffer**: Time-limited discounts and promotions

### Order Management
- **Order**: Complete order information with status tracking
- **OrderItem**: Individual items within orders
- **OrderStatusHistory**: Complete audit trail of status changes
- **CartItem**: Shopping cart persistence

### Promotions
- **Promotion**: Discount codes with usage limits and validation

## 📊 Data Validation

All data is validated using Pydantic schemas:

- **Input Validation**: Request body validation with detailed error messages
- **Type Safety**: Full type annotations throughout the codebase
- **Business Rules**: Custom validators for complex business logic
- **Response Models**: Structured, consistent API responses

## 🔒 Security Features

- **Input Validation**: Comprehensive request validation
- **SQL Injection Protection**: Parameterized queries via SQLAlchemy
- **Type Safety**: Runtime type checking with Pydantic
- **Environment Isolation**: Secure configuration management

## 🚀 Performance Features

- **Connection Pooling**: Efficient database connection management
- **Indexed Queries**: Optimized database indexes for common queries
- **Lazy Loading**: Efficient relationship loading
- **Batch Operations**: Support for bulk operations

## 🧪 Development

### Code Quality

- **Type Hints**: Full type annotations throughout
- **Documentation**: Comprehensive docstrings and comments
- **Code Formatting**: Black and isort for consistent formatting
- **Linting**: Flake8 for code quality checks

### Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_models.py
```

## 📈 Production Deployment

### Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

### Environment Setup

1. **Production Database**: Use managed PostgreSQL service
2. **Connection Pooling**: Adjust pool size based on load
3. **Monitoring**: Implement health checks and metrics
4. **Logging**: Configure structured logging for production

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Ensure code quality checks pass
5. Submit a pull request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:

- Create an issue in the repository
- Contact the development team
- Check the documentation

## 🔮 Roadmap

### Phase 1: Core API (Current)
- ✅ Database models and schemas
- ✅ Basic CRUD operations
- ✅ Authentication and authorization

### Phase 2: Advanced Features
- 🔄 Order processing workflow
- 🔄 Payment integration
- 🔄 Real-time notifications

### Phase 3: Optimization
- 🔄 Caching layer
- 🔄 Background job processing
- 🔄 Advanced analytics

---

**Built with ❤️ for Labanita Egyptian Sweets Store**
