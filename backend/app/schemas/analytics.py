"""
Dashboard and analytics schemas for reporting and statistics.
"""
from .base import BaseModel, Field, datetime, List, Dict, Optional
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .ticket import TicketSummary
    from .approval import ApprovalStepWithUser


# ============================================================================
# DASHBOARD AND ANALYTICS SCHEMAS
# ============================================================================

class TicketStatistics(BaseModel):
    """Ticket statistics for dashboard"""
    total_tickets: int = 0
    open_tickets: int = 0
    in_progress_tickets: int = 0
    resolved_tickets: int = 0
    overdue_tickets: int = 0
    pending_approvals: int = 0
    my_tickets: int = 0
    my_assigned_tickets: int = 0
    avg_resolution_time_hours: Optional[float] = None
    tickets_by_priority: Dict[str, int] = Field(default_factory=dict)
    tickets_by_type: Dict[str, int] = Field(default_factory=dict)
    tickets_by_status: Dict[str, int] = Field(default_factory=dict)


class DashboardData(BaseModel):
    """Dashboard data aggregation"""
    statistics: TicketStatistics
    recent_tickets: List["TicketSummary"] = []
    pending_approvals: List["ApprovalStepWithUser"] = []
    my_tickets: List["TicketSummary"] = []
    urgent_tickets: List["TicketSummary"] = []
