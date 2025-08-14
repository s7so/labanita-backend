import uuid
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from sqlalchemy.exc import IntegrityError

from core.exceptions import (
    NotFoundException, 
    ValidationException, 
    ConflictException,
    InvalidCredentialsException
)
from core.responses import success_response, error_response
from core.security import security
from auth.models import User
from models import Order, OrderItem, Product, Category
from user.schemas import (
    UserUpdate, PointsUpdate, UserProfileResponse, 
    UserPointsResponse, UserPointsHistoryResponse, UserStatsResponse
)

class UserService:
    """User service for profile management and points tracking"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # =============================================================================
    # PROFILE MANAGEMENT
    # =============================================================================
    
    def get_user_profile(self, user_id: str) -> UserProfileResponse:
        """Get user profile by ID"""
        user = self.db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise NotFoundException("User not found")
        
        return UserProfileResponse(
            user_id=str(user.user_id),
            phone_number=user.phone_number,
            full_name=user.full_name,
            email=user.email,
            facebook_id=user.facebook_id,
            google_id=user.google_id,
            points_balance=user.points_balance,
            points_expiry_date=user.points_expiry_date,
            is_verified=user.is_verified,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
    
    def update_user_profile(self, user_id: str, update_data: UserUpdate) -> UserProfileResponse:
        """Update user profile"""
        user = self.db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise NotFoundException("User not found")
        
        # Check if email is being changed and if it's already taken
        if update_data.email and update_data.email != user.email:
            existing_user = self.db.query(User).filter(
                User.email == update_data.email,
                User.user_id != user_id
            ).first()
            if existing_user:
                raise ConflictException("Email already taken by another user")
        
        # Check if phone number is being changed and if it's already taken
        if update_data.phone_number and update_data.phone_number != user.phone_number:
            existing_user = self.db.query(User).filter(
                User.phone_number == update_data.phone_number,
                User.user_id != user_id
            ).first()
            if existing_user:
                raise ConflictException("Phone number already taken by another user")
        
        # Update fields
        if update_data.full_name is not None:
            user.full_name = update_data.full_name
        
        if update_data.email is not None:
            user.email = update_data.email
        
        if update_data.phone_number is not None:
            user.phone_number = update_data.phone_number
        
        if update_data.is_verified is not None:
            user.is_verified = update_data.is_verified
        
        if update_data.is_active is not None:
            user.is_active = update_data.is_active
        
        user.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(user)
        
        return self.get_user_profile(user_id)
    
    def change_user_password(self, user_id: str, current_password: str, new_password: str) -> bool:
        """Change user password"""
        user = self.db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise NotFoundException("User not found")
        
        if not user.password_hash:
            raise InvalidCredentialsException("User has no password set")
        
        # Verify current password
        if not security.verify_password(current_password, user.password_hash):
            raise InvalidCredentialsException("Current password is incorrect")
        
        # Hash new password
        password_hash = security.get_password_hash(new_password)
        user.password_hash = password_hash
        user.updated_at = datetime.utcnow()
        
        self.db.commit()
        return True
    
    def delete_user_account(self, user_id: str, reason: Optional[str] = None) -> bool:
        """Delete user account (soft delete)"""
        user = self.db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise NotFoundException("User not found")
        
        # Soft delete
        user.is_active = False
        user.updated_at = datetime.utcnow()
        
        # Store deletion reason (you might want to create a separate table for this)
        # For now, we'll just mark as inactive
        
        # Deactivate all sessions (if you have the auth service)
        try:
            from auth.services import AuthService
            auth_service = AuthService(self.db)
            auth_service.logout_all_sessions(user_id)
        except ImportError:
            # If auth service is not available, just continue
            pass
        
        self.db.commit()
        return True
    
    def reactivate_user_account(self, user_id: str) -> bool:
        """Reactivate deleted user account"""
        user = self.db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise NotFoundException("User not found")
        
        if user.is_active:
            raise ConflictException("User account is already active")
        
        user.is_active = True
        user.updated_at = datetime.utcnow()
        
        self.db.commit()
        return True
    
    # =============================================================================
    # POINTS MANAGEMENT
    # =============================================================================
    
    def get_user_points(self, user_id: str) -> UserPointsResponse:
        """Get user points information"""
        user = self.db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise NotFoundException("User not found")
        
        # Calculate points statistics
        points_stats = self._calculate_points_statistics(user_id)
        
        return UserPointsResponse(
            user_id=str(user.user_id),
            points_balance=user.points_balance,
            points_expiry_date=user.points_expiry_date,
            points_earned_total=points_stats.get('earned_total', 0),
            points_used_total=points_stats.get('used_total', 0),
            points_expired_total=points_stats.get('expired_total', 0),
            next_expiry_batch=points_stats.get('next_expiry', None)
        )
    
    def get_user_points_history(self, user_id: str, skip: int = 0, limit: int = 50) -> List[UserPointsHistoryResponse]:
        """Get user points history"""
        user = self.db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise NotFoundException("User not found")
        
        # For now, we'll return a mock history since we don't have a points history table
        # In a real implementation, you'd query from a points_history table
        
        # Mock data for demonstration
        history = [
            UserPointsHistoryResponse(
                history_id=str(uuid.uuid4()),
                points_change=100,
                change_type="EARNED",
                description="Points earned from order #12345",
                order_id="12345",
                created_at=datetime.utcnow() - timedelta(days=1)
            ),
            UserPointsHistoryResponse(
                history_id=str(uuid.uuid4()),
                points_change=-50,
                change_type="USED",
                description="Points used for discount on order #12346",
                order_id="12346",
                created_at=datetime.utcnow() - timedelta(hours=2)
            )
        ]
        
        return history[skip:skip + limit]
    
    def add_user_points(self, user_id: str, points: int, reason: str, order_id: Optional[str] = None) -> bool:
        """Add points to user account"""
        user = self.db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise NotFoundException("User not found")
        
        if points <= 0:
            raise ValidationException("Points must be positive")
        
        # Update points balance
        user.points_balance += points
        
        # Set expiry date if not set (e.g., 1 year from now)
        if not user.points_expiry_date:
            user.points_expiry_date = datetime.utcnow() + timedelta(days=365)
        
        user.updated_at = datetime.utcnow()
        
        # TODO: Add to points history table
        # self._add_points_history(user_id, points, "EARNED", reason, order_id)
        
        self.db.commit()
        return True
    
    def use_user_points(self, user_id: str, points: int, reason: str, order_id: Optional[str] = None) -> bool:
        """Use points from user account"""
        user = self.db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise NotFoundException("User not found")
        
        if points <= 0:
            raise ValidationException("Points must be positive")
        
        if user.points_balance < points:
            raise ValidationException("Insufficient points balance")
        
        # Update points balance
        user.points_balance -= points
        user.updated_at = datetime.utcnow()
        
        # TODO: Add to points history table
        # self._add_points_history(user_id, -points, "USED", reason, order_id)
        
        self.db.commit()
        return True
    
    def expire_user_points(self, user_id: str, points: int, reason: str = "Points expired") -> bool:
        """Expire points from user account"""
        user = self.db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise NotFoundException("User not found")
        
        if points <= 0:
            raise ValidationException("Points must be positive")
        
        if user.points_balance < points:
            points = user.points_balance  # Expire only available points
        
        # Update points balance
        user.points_balance -= points
        user.updated_at = datetime.utcnow()
        
        # TODO: Add to points history table
        # self._add_points_history(user_id, -points, "EXPIRED", reason)
        
        self.db.commit()
        return True
    
    # =============================================================================
    # USER STATISTICS
    # =============================================================================
    
    def get_user_statistics(self, user_id: str) -> UserStatsResponse:
        """Get user statistics and analytics"""
        user = self.db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise NotFoundException("User not found")
        
        # Get order statistics
        orders = self.db.query(Order).filter(Order.user_id == user_id).all()
        
        total_orders = len(orders)
        total_spent = sum(order.total_amount for order in orders) if orders else 0
        average_order_value = total_spent / total_orders if total_orders > 0 else 0
        
        # Get last order date
        last_order_date = None
        if orders:
            last_order = max(orders, key=lambda x: x.created_at)
            last_order_date = last_order.created_at
        
        # Get favorite categories
        favorite_categories = self._get_favorite_categories(user_id)
        
        return UserStatsResponse(
            user_id=str(user.user_id),
            total_orders=total_orders,
            total_spent=float(total_spent),
            average_order_value=float(average_order_value),
            favorite_categories=favorite_categories,
            last_order_date=last_order_date,
            member_since=user.created_at
        )
    
    # =============================================================================
    # HELPER METHODS
    # =============================================================================
    
    def _calculate_points_statistics(self, user_id: str) -> Dict[str, Any]:
        """Calculate points statistics for user"""
        # This is a placeholder implementation
        # In a real system, you'd query from a points_history table
        
        return {
            'earned_total': 500,  # Mock data
            'used_total': 200,    # Mock data
            'expired_total': 50,  # Mock data
            'next_expiry': datetime.utcnow() + timedelta(days=30)  # Mock data
        }
    
    def _get_favorite_categories(self, user_id: str) -> List[str]:
        """Get user's favorite product categories"""
        # Query to get most ordered categories
        category_counts = self.db.query(
            Category.category_name,
            func.count(OrderItem.order_item_id).label('order_count')
        ).join(Product, Category.category_id == Product.category_id)\
         .join(OrderItem, Product.product_id == OrderItem.product_id)\
         .join(Order, OrderItem.order_id == Order.order_id)\
         .filter(Order.user_id == user_id)\
         .group_by(Category.category_name)\
         .order_by(desc('order_count'))\
         .limit(5)\
         .all()
        
        return [cat.category_name for cat in category_counts]
    
    def _add_points_history(self, user_id: str, points_change: int, change_type: str, 
                           description: str, order_id: Optional[str] = None) -> None:
        """Add points history record"""
        # TODO: Implement when points_history table is created
        # This would create a record in a points_history table
        pass
    
    def cleanup_expired_points(self) -> int:
        """Clean up expired points for all users"""
        current_time = datetime.utcnow()
        
        # Find users with expired points
        users_with_expired_points = self.db.query(User).filter(
            User.points_expiry_date < current_time,
            User.points_balance > 0
        ).all()
        
        expired_count = 0
        for user in users_with_expired_points:
            expired_points = user.points_balance
            user.points_balance = 0
            user.points_expiry_date = None
            expired_count += expired_points
            
            # TODO: Add to points history
            # self._add_points_history(str(user.user_id), -expired_points, "EXPIRED", "Points expired")
        
        self.db.commit()
        return expired_count
    
    def get_user_by_phone(self, phone_number: str) -> Optional[User]:
        """Get user by phone number"""
        return self.db.query(User).filter(User.phone_number == phone_number).first()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return self.db.query(User).filter(User.email == email).first()
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        return self.db.query(User).filter(User.user_id == user_id).first()
    
    def search_users(self, query: str, skip: int = 0, limit: int = 50) -> List[User]:
        """Search users by name, email, or phone"""
        search_filter = f"%{query}%"
        
        users = self.db.query(User).filter(
            (User.full_name.ilike(search_filter)) |
            (User.email.ilike(search_filter)) |
            (User.phone_number.ilike(search_filter))
        ).offset(skip).limit(limit).all()
        
        return users
    
    def get_users_by_points_range(self, min_points: int, max_points: int, 
                                 skip: int = 0, limit: int = 50) -> List[User]:
        """Get users within a points range"""
        users = self.db.query(User).filter(
            User.points_balance >= min_points,
            User.points_balance <= max_points
        ).order_by(desc(User.points_balance)).offset(skip).limit(limit).all()
        
        return users