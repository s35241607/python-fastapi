"""
Authentication-related schemas for login, registration, and token management.
"""
from .base import BaseModel, EmailStr, Field, validator, datetime, List, Optional, Dict, Any
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .user import UserProfile, UserPermissions


# ============================================================================
# TOKEN SCHEMAS
# ============================================================================

class Token(BaseModel):
    """JWT token response schema"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 1800  # 30 minutes


class TokenData(BaseModel):
    """Token payload data"""
    user_id: int
    username: str
    email: str
    role: str
    expires_at: datetime


class RefreshToken(BaseModel):
    """Refresh token request"""
    refresh_token: str


# ============================================================================
# AUTHENTICATION SCHEMAS
# ============================================================================

class LoginRequest(BaseModel):
    """User login request"""
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=1)
    remember_me: bool = False


class LoginResponse(BaseModel):
    """User login response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: "UserProfile"


class RegisterRequest(BaseModel):
    """User registration request"""
    username: str = Field(..., min_length=3, max_length=50, pattern="^[a-zA-Z0-9_]+$")
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    department_id: Optional[int] = None

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v


# ============================================================================
# PASSWORD MANAGEMENT SCHEMAS
# ============================================================================

class PasswordChangeRequest(BaseModel):
    """Password change request"""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str

    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v


class PasswordResetRequest(BaseModel):
    """Password reset request"""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation"""
    token: str
    new_password: str = Field(..., min_length=8, max_length=128)
    confirm_password: str

    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if 'new_password' in values and v != values['new_password']:
            raise ValueError('Passwords do not match')
        return v


# ============================================================================
# API KEY SCHEMAS
# ============================================================================

class ApiKeyCreate(BaseModel):
    """API key creation request"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    expires_at: Optional[datetime] = None
    permissions: List[str] = Field(default_factory=list)


class ApiKeyResponse(BaseModel):
    """API key response"""
    id: int
    name: str
    description: Optional[str] = None
    api_key: str  # Only returned on creation
    expires_at: Optional[datetime] = None
    is_active: bool
    created_at: datetime
    last_used: Optional[datetime] = None


# ============================================================================
# SESSION SCHEMAS
# ============================================================================

class SessionInfo(BaseModel):
    """User session information"""
    user: "UserProfile"
    permissions: "UserPermissions"
    session_expires_at: datetime
    last_activity: datetime
