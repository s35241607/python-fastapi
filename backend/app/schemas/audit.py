"""
Audit log schemas for tracking system changes and user actions.
"""
from .base import BaseModel, Field, datetime, Optional, Dict, Any
from .base import AuditEventType
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .user import User


# ============================================================================
# AUDIT LOG SCHEMAS
# ============================================================================

class AuditLogBase(BaseModel):
    event_type: AuditEventType
    entity_type: Optional[str] = None
    entity_id: Optional[int] = None
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    extra_metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class AuditLogCreate(AuditLogBase):
    pass


class AuditLog(AuditLogBase):
    id: int
    user_id: Optional[int] = None
    ticket_id: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class AuditLogWithUser(AuditLog):
    user: Optional["User"] = None
