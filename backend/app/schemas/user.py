"""
User-related schemas for profiles, permissions, and user management.
"""
from .base import BaseModel, EmailStr, Field, datetime, List, Optional, Dict, Any
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .item import Item


# ============================================================================
# USER CORE SCHEMAS
# ============================================================================

class UserBase(BaseModel):
    email: EmailStr
    username: str


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserProfile(BaseModel):
    """User profile information"""
    id: int
    username: str
    email: str
    first_name: str
    last_name: str
    role: str
    department_id: Optional[int] = None
    is_active: bool
    last_login: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    """User profile update"""
    first_name: Optional[str] = Field(None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(None, min_length=1, max_length=50)
    email: Optional[EmailStr] = None
    department_id: Optional[int] = None
    preferences: Optional[Dict[str, Any]] = None


class UserWithItems(User):
    items: List["Item"] = []


# ============================================================================
# USER PERMISSIONS SCHEMAS
# ============================================================================

class UserPermissions(BaseModel):
    """User permissions response"""
    user_id: int
    role: str
    permissions: Dict[str, bool]
    department_access: List[int] = Field(default_factory=list)
