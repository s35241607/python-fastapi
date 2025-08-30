"""
Department-related schemas for organizational structure management.
"""
from .base import BaseModel, Field, datetime, List, Optional, Dict, Any, Decimal
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .user import User


# ============================================================================
# DEPARTMENT SCHEMAS
# ============================================================================

class DepartmentBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    budget_limit: Optional[Decimal] = Field(default=Decimal('0.00'), ge=0)
    approval_rules: Optional[Dict[str, Any]] = Field(default_factory=dict)


class DepartmentCreate(DepartmentBase):
    manager_id: Optional[int] = None


class DepartmentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    manager_id: Optional[int] = None
    budget_limit: Optional[Decimal] = Field(None, ge=0)
    approval_rules: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None


class Department(DepartmentBase):
    id: int
    manager_id: Optional[int] = None
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class DepartmentWithUsers(Department):
    users: List["User"] = []
    manager: Optional["User"] = None
