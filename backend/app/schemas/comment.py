"""
Comment-related schemas for ticket discussions.
"""
from .base import BaseModel, Field, datetime, Optional
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .user import User


# ============================================================================
# COMMENT SCHEMAS
# ============================================================================

class TicketCommentBase(BaseModel):
    content: str = Field(..., min_length=1)
    is_internal: bool = False


class TicketCommentCreate(TicketCommentBase):
    pass


class TicketCommentUpdate(BaseModel):
    content: Optional[str] = Field(None, min_length=1)
    is_internal: Optional[bool] = None


class TicketComment(TicketCommentBase):
    id: int
    ticket_id: int
    author_id: int
    is_system_generated: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TicketCommentWithAuthor(TicketComment):
    author: "User"
