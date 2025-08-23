from datetime import datetime
from decimal import Decimal
from typing import List, Optional, Dict, Any
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, validator

from app.enums import (
    TicketStatus, Priority, TicketType, ApprovalAction, WorkflowType,
    ApprovalStepStatus, WorkflowStatus, UserRole, AttachmentType,
    AuditEventType
)


# ============================================================================
# AUTHENTICATION SCHEMAS
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


class UserPermissions(BaseModel):
    """User permissions response"""
    user_id: int
    role: str
    permissions: Dict[str, bool]
    department_access: List[int] = Field(default_factory=list)


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


class SessionInfo(BaseModel):
    """User session information"""
    user: UserProfile
    permissions: UserPermissions
    session_expires_at: datetime
    last_activity: datetime


class ItemBase(BaseModel):
    title: str
    description: Optional[str] = None


class ItemCreate(ItemBase):
    pass


class Item(ItemBase):
    id: int
    owner_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


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


class UserWithItems(User):
    items: List[Item] = []

    class Config:
        from_attributes = True


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
    users: List[User] = []
    manager: Optional[User] = None

    class Config:
        from_attributes = True


# ============================================================================
# TICKET SCHEMAS
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
    requester: User
    assignee: Optional[User] = None
    department: Optional[Department] = None
    comments_count: int = 0
    attachments_count: int = 0
    has_pending_approvals: bool = False

    class Config:
        from_attributes = True


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
    author: User

    class Config:
        from_attributes = True


# ============================================================================
# APPROVAL WORKFLOW SCHEMAS
# ============================================================================

class ApprovalWorkflowBase(BaseModel):
    workflow_name: str = Field(..., min_length=1, max_length=100)
    workflow_type: WorkflowType = WorkflowType.SEQUENTIAL
    workflow_config: Optional[Dict[str, Any]] = Field(default_factory=dict)
    auto_approve_threshold: Optional[Decimal] = Field(None, ge=0)
    escalation_timeout_hours: int = Field(default=24, ge=1, le=168)  # 1 hour to 1 week


class ApprovalWorkflowCreate(ApprovalWorkflowBase):
    approver_ids: List[int] = Field(..., min_items=1)  # List of approver user IDs


class ApprovalWorkflow(ApprovalWorkflowBase):
    id: int
    ticket_id: int
    status: WorkflowStatus
    initiated_by_id: int
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ApprovalWorkflowWithSteps(ApprovalWorkflow):
    steps: List['ApprovalStep'] = []
    initiated_by: User

    class Config:
        from_attributes = True


# ============================================================================
# APPROVAL STEP SCHEMAS
# ============================================================================

class ApprovalStepBase(BaseModel):
    comments: Optional[str] = None


class ApprovalActionRequest(ApprovalStepBase):
    action: ApprovalAction
    delegated_to_id: Optional[int] = None
    escalated_to_id: Optional[int] = None

    @validator('delegated_to_id')
    def validate_delegate(cls, v, values):
        if values.get('action') == ApprovalAction.DELEGATE and not v:
            raise ValueError('delegated_to_id is required when action is DELEGATE')
        return v

    @validator('escalated_to_id')
    def validate_escalate(cls, v, values):
        if values.get('action') == ApprovalAction.ESCALATE and not v:
            raise ValueError('escalated_to_id is required when action is ESCALATE')
        return v


class ApprovalStep(ApprovalStepBase):
    id: int
    workflow_id: int
    approver_id: int
    step_order: int
    action: Optional[ApprovalAction] = None
    status: ApprovalStepStatus
    delegated_to_id: Optional[int] = None
    escalated_to_id: Optional[int] = None
    due_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ApprovalStepWithUser(ApprovalStep):
    approver: User
    delegated_to: Optional[User] = None
    escalated_to: Optional[User] = None

    class Config:
        from_attributes = True


# ============================================================================
# ATTACHMENT SCHEMAS
# ============================================================================

class TicketAttachmentBase(BaseModel):
    description: Optional[str] = None
    is_public: bool = True


class TicketAttachmentCreate(TicketAttachmentBase):
    filename: str = Field(..., min_length=1)
    file_size: int = Field(..., gt=0)
    mime_type: str = Field(..., min_length=1)
    attachment_type: AttachmentType = AttachmentType.OTHER


class TicketAttachment(TicketAttachmentBase):
    id: int
    ticket_id: int
    uploaded_by_id: int
    filename: str
    original_filename: str
    file_path: str
    file_size: int
    mime_type: str
    attachment_type: AttachmentType
    checksum: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class TicketAttachmentWithUploader(TicketAttachment):
    uploaded_by: User

    class Config:
        from_attributes = True


class AttachmentResponse(TicketAttachment):
    """Alias for TicketAttachment for API responses"""
    pass


class AttachmentMetadata(BaseModel):
    """Attachment metadata for updates"""
    description: Optional[str] = None
    is_public: bool = True


class AttachmentUpdate(AttachmentMetadata):
    """Update data for attachments"""
    pass


class FileUploadResponse(BaseModel):
    """Response after file upload"""
    attachment_id: int
    filename: str
    file_size: int
    mime_type: str
    message: str = "File uploaded successfully"


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


class PaginationParams(BaseModel):
    """Pagination parameters"""
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)
    sort_by: str = Field(default="created_at")
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$")


class PaginatedResponse(BaseModel):
    """Generic paginated response"""
    items: List[Any]
    total: int
    page: int
    size: int
    pages: int
    has_next: bool
    has_prev: bool

    class Config:
        from_attributes = True


class TicketSearchRequest(BaseModel):
    """Combined search and pagination request"""
    filters: Optional[TicketFilter] = Field(default_factory=TicketFilter)
    pagination: Optional[PaginationParams] = Field(default_factory=PaginationParams)


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
    recent_tickets: List[TicketSummary] = []
    pending_approvals: List[ApprovalStepWithUser] = []
    my_tickets: List[TicketSummary] = []
    urgent_tickets: List[TicketSummary] = []


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
    user: Optional[User] = None

    class Config:
        from_attributes = True


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
    recipient_ids: List[int] = Field(..., min_items=1)
    template: NotificationTemplate
    channels: List[str] = Field(default=["email", "in_app"])
    priority: Priority = Priority.MEDIUM
    send_immediately: bool = True
