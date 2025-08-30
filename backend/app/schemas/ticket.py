"""
Ticket-related schemas for the ticket management system.
"""
from .base import BaseModel, Field, datetime, List, Optional, Dict, Any, Decimal
from .base import TicketType, TicketStatus, Priority
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .user import User
    from .department import Department
    from .common import PaginationParams


# ============================================================================
# TICKET CORE SCHEMAS
# ============================================================================

class TicketBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    ticket_type: TicketType
    priority: Priority = Priority.MEDIUM
    due_date: Optional[datetime] = None
    estimated_hours: Optional[Decimal] = Field(None, ge=0)
    cost_estimate: Optional[Decimal] = Field(None, ge=0)
    custom_fields: Optional[Dict[str, Any]] = Field(default_factory=dict)
    tags: Optional[List[str]] = Field(default_factory=list)


class TicketCreate(TicketBase):
    assignee_id: Optional[int] = None
    department_id: Optional[int] = None


class TicketUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    ticket_type: Optional[TicketType] = None
    status: Optional[TicketStatus] = None
    priority: Optional[Priority] = None
    assignee_id: Optional[int] = None
    department_id: Optional[int] = None
    due_date: Optional[datetime] = None
    estimated_hours: Optional[Decimal] = Field(None, ge=0)
    actual_hours: Optional[Decimal] = Field(None, ge=0)
    cost_estimate: Optional[Decimal] = Field(None, ge=0)
    custom_fields: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None


class TicketStatusUpdate(BaseModel):
    status: TicketStatus
    comment: Optional[str] = None


class Ticket(TicketBase):
    id: int
    ticket_number: str
    status: TicketStatus
    requester_id: int
    assignee_id: Optional[int] = None
    department_id: Optional[int] = None
    actual_hours: Optional[Decimal] = None
    resolved_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TicketSummary(BaseModel):
    """Lightweight ticket representation for lists"""
    id: int
    ticket_number: str
    title: str
    status: TicketStatus
    priority: Priority
    ticket_type: TicketType
    requester_id: int
    assignee_id: Optional[int] = None
    created_at: datetime
    due_date: Optional[datetime] = None

    class Config:
        from_attributes = True


class TicketDetail(Ticket):
    """Full ticket representation with relationships"""
    requester: "User"
    assignee: Optional["User"] = None
    department: Optional["Department"] = None
    comments_count: int = 0
    attachments_count: int = 0
    has_pending_approvals: bool = False


# ============================================================================
# SEARCH AND FILTER SCHEMAS
# ============================================================================

class TicketFilter(BaseModel):
    """Filter parameters for ticket search"""
    status: Optional[List[TicketStatus]] = None
    priority: Optional[List[Priority]] = None
    ticket_type: Optional[List[TicketType]] = None
    requester_id: Optional[int] = None
    assignee_id: Optional[int] = None
    department_id: Optional[int] = None
    created_after: Optional[datetime] = None
    created_before: Optional[datetime] = None
    due_after: Optional[datetime] = None
    due_before: Optional[datetime] = None
    search_query: Optional[str] = Field(None, max_length=200)  # Full-text search
    tags: Optional[List[str]] = None
    has_overdue: Optional[bool] = None
    has_pending_approvals: Optional[bool] = None


class TicketSearchRequest(BaseModel):
    """Combined search and pagination request"""
    filters: Optional[TicketFilter] = None
    pagination: Optional["PaginationParams"] = None
