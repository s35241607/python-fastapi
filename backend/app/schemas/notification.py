"""
Notification schemas for system notifications and messaging.
"""
from .base import BaseModel, Field, List, Dict, Any
from .base import Priority


# ============================================================================
# NOTIFICATION SCHEMAS
# ============================================================================

class NotificationTemplate(BaseModel):
    """Notification template data"""
    subject: str
    body: str
    template_vars: Dict[str, Any] = Field(default_factory=dict)


class NotificationRequest(BaseModel):
    """Notification sending request"""
    recipient_ids: List[int] = Field(..., min_length=1)
    template: NotificationTemplate
    channels: List[str] = Field(default=["email", "in_app"])
    priority: Priority = Priority.MEDIUM
    send_immediately: bool = True
