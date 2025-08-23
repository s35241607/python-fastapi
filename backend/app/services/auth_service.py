"""
Authentication Service Module

This module provides JWT token management, user authentication,
password hashing, and security utilities for the ticket management system.
"""

import os
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from passlib.context import CryptContext
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import User
from app.schemas import TokenData


class AuthenticationService:
    """Service class for authentication and JWT token management"""

    def __init__(self, session: AsyncSession):
        self.session = session
        
        # JWT Configuration
        self.secret_key = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
        self.algorithm = "HS256"
        self.access_token_expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
        self.refresh_token_expire_days = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
        
        # Password hashing
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """Hash a password"""
        return self.pwd_context.hash(password)

    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """Create a JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=self.refresh_token_expire_days)
        
        to_encode.update({
            "exp": expire,
            "type": "refresh",
            "jti": secrets.token_urlsafe(32)  # JWT ID for token revocation
        })
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def verify_token(self, token: str, token_type: str = "access") -> Optional[TokenData]:
        """Verify and decode a JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Check token type
            if payload.get("type") != token_type:
                return None
            
            # Extract user information
            user_id: int = payload.get("sub")
            username: str = payload.get("username")
            email: str = payload.get("email")
            role: str = payload.get("role")
            
            if user_id is None or username is None:
                return None
            
            token_data = TokenData(
                user_id=user_id,
                username=username,
                email=email,
                role=role,
                expires_at=datetime.fromtimestamp(payload.get("exp"))
            )
            
            return token_data
            
        except JWTError:
            return None

    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate a user with username/email and password"""
        
        # Try to find user by username or email
        stmt = select(User).where(
            (User.username == username) | (User.email == username)
        ).where(User.is_active == True)
        
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            return None
        
        if not self.verify_password(password, user.hashed_password):
            return None
        
        return user

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID for token validation"""
        stmt = select(User).where(User.id == user_id).where(User.is_active == True)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        stmt = select(User).where(User.username == username).where(User.is_active == True)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        stmt = select(User).where(User.email == email).where(User.is_active == True)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    def create_token_pair(self, user: User) -> Dict[str, str]:
        """Create both access and refresh tokens for a user"""
        
        token_data = {
            "sub": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "department_id": user.department_id
        }
        
        access_token = self.create_access_token(token_data)
        refresh_token = self.create_refresh_token({"sub": user.id, "username": user.username})
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer"
        }

    async def refresh_access_token(self, refresh_token: str) -> Optional[Dict[str, str]]:
        """Create a new access token using a refresh token"""
        
        token_data = self.verify_token(refresh_token, "refresh")
        if not token_data:
            return None
        
        # Get current user data
        user = await self.get_user_by_id(token_data.user_id)
        if not user:
            return None
        
        # Create new access token
        new_token_data = {
            "sub": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "department_id": user.department_id
        }
        
        access_token = self.create_access_token(new_token_data)
        
        return {
            "access_token": access_token,
            "token_type": "bearer"
        }

    async def change_password(self, user_id: int, current_password: str, new_password: str) -> bool:
        """Change user password"""
        
        user = await self.get_user_by_id(user_id)
        if not user:
            return False
        
        # Verify current password
        if not self.verify_password(current_password, user.hashed_password):
            return False
        
        # Update password
        user.hashed_password = self.get_password_hash(new_password)
        user.password_changed_at = datetime.utcnow()
        
        await self.session.commit()
        return True

    def validate_password_strength(self, password: str) -> Dict[str, Any]:
        """Validate password strength"""
        
        errors = []
        
        if len(password) < 8:
            errors.append("Password must be at least 8 characters long")
        
        if not any(c.isupper() for c in password):
            errors.append("Password must contain at least one uppercase letter")
        
        if not any(c.islower() for c in password):
            errors.append("Password must contain at least one lowercase letter")
        
        if not any(c.isdigit() for c in password):
            errors.append("Password must contain at least one digit")
        
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            errors.append("Password must contain at least one special character")
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "strength": self._calculate_password_strength(password)
        }

    def _calculate_password_strength(self, password: str) -> str:
        """Calculate password strength score"""
        
        score = 0
        
        if len(password) >= 8:
            score += 1
        if len(password) >= 12:
            score += 1
        if any(c.isupper() for c in password):
            score += 1
        if any(c.islower() for c in password):
            score += 1
        if any(c.isdigit() for c in password):
            score += 1
        if any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            score += 1
        
        if score <= 2:
            return "weak"
        elif score <= 4:
            return "medium"
        else:
            return "strong"

    async def check_user_exists(self, username: str, email: str) -> Dict[str, bool]:
        """Check if username or email already exists"""
        
        username_stmt = select(User).where(User.username == username)
        email_stmt = select(User).where(User.email == email)
        
        username_result = await self.session.execute(username_stmt)
        email_result = await self.session.execute(email_stmt)
        
        return {
            "username_exists": username_result.scalar_one_or_none() is not None,
            "email_exists": email_result.scalar_one_or_none() is not None
        }

    async def create_user(self, user_data: Dict[str, Any]) -> User:
        """Create a new user with hashed password"""
        
        # Validate password
        password_validation = self.validate_password_strength(user_data["password"])
        if not password_validation["is_valid"]:
            raise ValueError(f"Password validation failed: {password_validation['errors']}")
        
        # Check if user exists
        existence_check = await self.check_user_exists(
            user_data["username"], 
            user_data["email"]
        )
        
        if existence_check["username_exists"]:
            raise ValueError("Username already exists")
        
        if existence_check["email_exists"]:
            raise ValueError("Email already exists")
        
        # Create user
        hashed_password = self.get_password_hash(user_data["password"])
        
        user = User(
            username=user_data["username"],
            email=user_data["email"],
            hashed_password=hashed_password,
            first_name=user_data.get("first_name", ""),
            last_name=user_data.get("last_name", ""),
            role=user_data.get("role", "employee"),
            department_id=user_data.get("department_id"),
            is_active=True,
            created_at=datetime.utcnow()
        )
        
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        
        return user

    async def update_last_login(self, user_id: int) -> None:
        """Update user's last login timestamp"""
        
        user = await self.get_user_by_id(user_id)
        if user:
            user.last_login = datetime.utcnow()
            await self.session.commit()

    def is_token_expired(self, token: str) -> bool:
        """Check if a token is expired"""
        
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            exp = payload.get("exp")
            if exp is None:
                return True
            
            return datetime.fromtimestamp(exp) < datetime.utcnow()
            
        except JWTError:
            return True

    def generate_password_reset_token(self, user_id: int) -> str:
        """Generate a password reset token"""
        
        data = {
            "sub": user_id,
            "type": "password_reset",
            "exp": datetime.utcnow() + timedelta(hours=1)  # 1 hour expiry
        }
        
        return jwt.encode(data, self.secret_key, algorithm=self.algorithm)

    def verify_password_reset_token(self, token: str) -> Optional[int]:
        """Verify password reset token and return user ID"""
        
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            if payload.get("type") != "password_reset":
                return None
            
            user_id = payload.get("sub")
            return user_id
            
        except JWTError:
            return None

    async def reset_password(self, token: str, new_password: str) -> bool:
        """Reset user password using reset token"""
        
        user_id = self.verify_password_reset_token(token)
        if not user_id:
            return False
        
        # Validate new password
        password_validation = self.validate_password_strength(new_password)
        if not password_validation["is_valid"]:
            raise ValueError(f"Password validation failed: {password_validation['errors']}")
        
        user = await self.get_user_by_id(user_id)
        if not user:
            return False
        
        # Update password
        user.hashed_password = self.get_password_hash(new_password)
        user.password_changed_at = datetime.utcnow()
        
        await self.session.commit()
        return True