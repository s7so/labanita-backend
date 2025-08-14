import uuid
from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status

from core.config import settings
from core.security import security
from core.exceptions import (
    UserAlreadyExistsException, 
    InvalidCredentialsException, 
    OTPException,
    PhoneNumberException,
    NotFoundException
)
from core.responses import success_response, error_response
from auth.models import User, UserSession, OTP, PasswordReset
from auth.schemas import (
    UserCreate, UserUpdate, OTPCreate, SessionCreate,
    UserProfileResponse, TokenResponse, OTPResponse
)

class AuthService:
    """Authentication service for user management"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # =============================================================================
    # USER REGISTRATION & LOGIN
    # =============================================================================
    
    def register_user(self, user_data: UserCreate) -> User:
        """Register a new user"""
        try:
            # Check if user already exists
            existing_user = self.get_user_by_phone(user_data.phone_number)
            if existing_user:
                raise UserAlreadyExistsException("User with this phone number already exists")
            
            # Create new user
            user = User(
                phone_number=user_data.phone_number,
                full_name=user_data.full_name,
                email=user_data.email,
                password_hash=user_data.password_hash,
                facebook_id=user_data.facebook_id,
                google_id=user_data.google_id,
                is_verified=False,  # Will be verified after OTP
                is_active=True
            )
            
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            
            return user
            
        except IntegrityError:
            self.db.rollback()
            raise UserAlreadyExistsException("User with this phone number or email already exists")
    
    def login_user(self, phone_number: str, password: Optional[str] = None) -> User:
        """Login user with phone number and optional password"""
        user = self.get_user_by_phone(phone_number)
        if not user:
            raise InvalidCredentialsException("Invalid phone number or password")
        
        if not user.is_active:
            raise InvalidCredentialsException("User account is deactivated")
        
        # If password is provided, verify it
        if password and user.password_hash:
            if not security.verify_password(password, user.password_hash):
                raise InvalidCredentialsException("Invalid phone number or password")
        
        # For phone-only login, user must be verified
        if not password and not user.is_verified:
            raise InvalidCredentialsException("Please verify your phone number first")
        
        return user
    
    def verify_otp(self, phone_number: str, otp_code: str, otp_type: str) -> User:
        """Verify OTP and return user"""
        # Get the most recent valid OTP
        otp = self.db.query(OTP).filter(
            OTP.phone_number == phone_number,
            OTP.otp_type == otp_type,
            OTP.is_used == False,
            OTP.expires_at > datetime.utcnow()
        ).order_by(OTP.created_at.desc()).first()
        
        if not otp:
            raise OTPException("Invalid or expired OTP")
        
        if not otp.can_attempt():
            raise OTPException("Maximum OTP attempts exceeded")
        
        if otp.otp_code != otp_code:
            otp.increment_attempts()
            self.db.commit()
            raise OTPException("Invalid OTP code")
        
        # Mark OTP as used
        otp.mark_as_used()
        
        # Get or create user
        user = self.get_user_by_phone(phone_number)
        if not user:
            # Create user if this is a registration OTP
            if otp_type == "REGISTRATION":
                user = User(
                    phone_number=phone_number,
                    full_name="",  # Will be updated later
                    is_verified=True,
                    is_active=True
                )
                self.db.add(user)
            else:
                raise NotFoundException("User not found")
        
        # Mark user as verified
        user.is_verified = True
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    # =============================================================================
    # OTP MANAGEMENT
    # =============================================================================
    
    def generate_and_send_otp(self, phone_number: str, otp_type: str) -> OTPResponse:
        """Generate and send OTP to phone number"""
        # Validate phone number format
        if not self._validate_phone_number(phone_number):
            raise PhoneNumberException("Invalid phone number format")
        
        # Check if user exists (for login/reset) or doesn't exist (for registration)
        user = self.get_user_by_phone(phone_number)
        if otp_type in ["LOGIN", "RESET_PASSWORD"] and not user:
            raise NotFoundException("User not found")
        elif otp_type == "REGISTRATION" and user:
            raise UserAlreadyExistsException("User already exists")
        
        # Generate OTP
        otp_code = security.generate_otp()
        expires_at = datetime.utcnow() + timedelta(minutes=settings.OTP_EXPIRE_MINUTES)
        
        # Create OTP record
        otp = OTP(
            user_id=user.user_id if user else None,
            phone_number=phone_number,
            otp_code=otp_code,
            otp_type=otp_type,
            expires_at=expires_at
        )
        
        self.db.add(otp)
        self.db.commit()
        
        # TODO: Integrate with SMS service (Twilio, etc.)
        # For development, we'll just return the OTP
        if settings.DEBUG:
            print(f"DEBUG: OTP for {phone_number}: {otp_code}")
        
        return OTPResponse(
            message="OTP sent successfully",
            expires_in=settings.OTP_EXPIRE_MINUTES * 60,
            phone_number=phone_number
        )
    
    def resend_otp(self, phone_number: str, otp_type: str) -> OTPResponse:
        """Resend OTP to phone number"""
        # Check if there's a recent OTP (within 1 minute)
        recent_otp = self.db.query(OTP).filter(
            OTP.phone_number == phone_number,
            OTP.otp_type == otp_type,
            OTP.created_at > datetime.utcnow() - timedelta(minutes=1)
        ).first()
        
        if recent_otp:
            raise OTPException("Please wait before requesting another OTP")
        
        return self.generate_and_send_otp(phone_number, otp_type)
    
    # =============================================================================
    # SESSION MANAGEMENT
    # =============================================================================
    
    def create_user_session(self, user: User, device_info: Optional[str] = None, 
                           ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> TokenResponse:
        """Create user session and return tokens"""
        # Generate tokens
        access_token = security.create_access_token(
            data={"sub": str(user.user_id), "phone": user.phone_number}
        )
        refresh_token = security.create_refresh_token(
            data={"sub": str(user.user_id), "phone": user.phone_number}
        )
        
        # Create session record
        session = UserSession(
            user_id=user.user_id,
            refresh_token=refresh_token,
            device_info=device_info,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
        )
        
        self.db.add(session)
        self.db.commit()
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            refresh_expires_in=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
        )
    
    def refresh_access_token(self, refresh_token: str) -> TokenResponse:
        """Refresh access token using refresh token"""
        # Verify refresh token
        try:
            payload = security.verify_token(refresh_token, "refresh")
            user_id = payload.get("sub")
            
            if not user_id:
                raise InvalidCredentialsException("Invalid refresh token")
            
            # Check if session exists and is valid
            session = self.db.query(UserSession).filter(
                UserSession.refresh_token == refresh_token,
                UserSession.is_active == True,
                UserSession.expires_at > datetime.utcnow()
            ).first()
            
            if not session:
                raise InvalidCredentialsException("Invalid or expired refresh token")
            
            # Get user
            user = self.get_user_by_id(user_id)
            if not user or not user.is_active:
                raise InvalidCredentialsException("User not found or inactive")
            
            # Generate new access token
            access_token = security.create_access_token(
                data={"sub": str(user.user_id), "phone": user.phone_number}
            )
            
            # Update session last used
            session.refresh()
            self.db.commit()
            
            return TokenResponse(
                access_token=access_token,
                refresh_token=refresh_token,
                token_type="bearer",
                expires_in=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60,
                refresh_expires_in=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
            )
            
        except Exception as e:
            raise InvalidCredentialsException("Invalid refresh token")
    
    def logout_user(self, refresh_token: str) -> bool:
        """Logout user by deactivating session"""
        session = self.db.query(UserSession).filter(
            UserSession.refresh_token == refresh_token
        ).first()
        
        if session:
            session.is_active = False
            self.db.commit()
            return True
        
        return False
    
    def logout_all_sessions(self, user_id: str) -> bool:
        """Logout user from all sessions"""
        sessions = self.db.query(UserSession).filter(
            UserSession.user_id == user_id,
            UserSession.is_active == True
        ).all()
        
        for session in sessions:
            session.is_active = False
        
        self.db.commit()
        return True
    
    # =============================================================================
    # USER PROFILE MANAGEMENT
    # =============================================================================
    
    def get_user_profile(self, user_id: str) -> UserProfileResponse:
        """Get user profile by ID"""
        user = self.get_user_by_id(user_id)
        if not user:
            raise NotFoundException("User not found")
        
        return UserProfileResponse(
            user_id=str(user.user_id),
            phone_number=user.phone_number,
            full_name=user.full_name,
            email=user.email,
            points_balance=user.points_balance,
            points_expiry_date=user.points_expiry_date,
            is_verified=user.is_verified,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at
        )
    
    def update_user_profile(self, user_id: str, update_data: UserUpdate) -> UserProfileResponse:
        """Update user profile"""
        user = self.get_user_by_id(user_id)
        if not user:
            raise NotFoundException("User not found")
        
        # Update fields
        if update_data.full_name is not None:
            user.full_name = update_data.full_name
        
        if update_data.email is not None:
            user.email = update_data.email
        
        if update_data.password_hash is not None:
            user.password_hash = update_data.password_hash
        
        if update_data.is_verified is not None:
            user.is_verified = update_data.is_verified
        
        if update_data.is_active is not None:
            user.is_active = update_data.is_active
        
        user.updated_at = datetime.utcnow()
        
        self.db.commit()
        self.db.refresh(user)
        
        return self.get_user_profile(user_id)
    
    def delete_user_account(self, user_id: str) -> bool:
        """Delete user account (soft delete)"""
        user = self.get_user_by_id(user_id)
        if not user:
            raise NotFoundException("User not found")
        
        # Soft delete
        user.is_active = False
        user.updated_at = datetime.utcnow()
        
        # Deactivate all sessions
        self.logout_all_sessions(user_id)
        
        self.db.commit()
        return True
    
    # =============================================================================
    # PASSWORD MANAGEMENT
    # =============================================================================
    
    def reset_password(self, phone_number: str, new_password: str) -> bool:
        """Reset user password"""
        user = self.get_user_by_phone(phone_number)
        if not user:
            raise NotFoundException("User not found")
        
        # Hash new password
        password_hash = security.get_password_hash(new_password)
        user.password_hash = password_hash
        user.updated_at = datetime.utcnow()
        
        self.db.commit()
        return True
    
    def change_password(self, user_id: str, current_password: str, new_password: str) -> bool:
        """Change user password"""
        user = self.get_user_by_id(user_id)
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
    
    # =============================================================================
    # HELPER METHODS
    # =============================================================================
    
    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        return self.db.query(User).filter(User.user_id == user_id).first()
    
    def get_user_by_phone(self, phone_number: str) -> Optional[User]:
        """Get user by phone number"""
        return self.db.query(User).filter(User.phone_number == phone_number).first()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return self.db.query(User).filter(User.email == email).first()
    
    def get_user_sessions(self, user_id: str) -> List[UserSession]:
        """Get all active sessions for user"""
        return self.db.query(UserSession).filter(
            UserSession.user_id == user_id,
            UserSession.is_active == True
        ).all()
    
    def _validate_phone_number(self, phone_number: str) -> bool:
        """Validate phone number format"""
        import re
        return bool(re.match(r'^\+[1-9]\d{1,14}$', phone_number))
    
    def cleanup_expired_sessions(self) -> int:
        """Clean up expired sessions and return count of cleaned sessions"""
        expired_sessions = self.db.query(UserSession).filter(
            UserSession.expires_at < datetime.utcnow()
        ).all()
        
        count = len(expired_sessions)
        for session in expired_sessions:
            session.is_active = False
        
        self.db.commit()
        return count
    
    def cleanup_expired_otps(self) -> int:
        """Clean up expired OTPs and return count of cleaned OTPs"""
        expired_otps = self.db.query(OTP).filter(
            OTP.expires_at < datetime.utcnow()
        ).all()
        
        count = len(expired_otps)
        for otp in expired_otps:
            self.db.delete(otp)
        
        self.db.commit()
        return count