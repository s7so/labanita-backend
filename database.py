"""
Database configuration and session management for Labanita API.
Handles SQLAlchemy engine setup, connection pooling, and session creation.
"""

import os
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL")
DB_POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "20"))
DB_MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "30"))
DB_POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", "30"))
DB_POOL_RECYCLE = int(os.getenv("DB_POOL_RECYCLE", "3600"))

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")

# Create SQLAlchemy engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=DB_POOL_SIZE,
    max_overflow=DB_MAX_OVERFLOW,
    pool_timeout=DB_POOL_TIMEOUT,
    pool_recycle=DB_POOL_RECYCLE,
    pool_pre_ping=True,  # Verify connections before use
    echo=False,  # Set to True for SQL query logging in development
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Create declarative base for models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function to get database session.
    Yields a database session and ensures it's closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create all tables in the database."""
    Base.metadata.create_all(bind=engine)


def drop_tables():
    """Drop all tables from the database. Use with caution!"""
    Base.metadata.drop_all(bind=engine)


# Database health check
def check_database_connection() -> bool:
    """Check if database connection is working."""
    try:
        with engine.connect() as connection:
            connection.execute("SELECT 1")
        return True
    except Exception:
        return False