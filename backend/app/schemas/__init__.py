"""
Schemas package for the FastAPI application.

This package contains all Pydantic schemas organized by domain for better maintainability.
All schemas are imported here for backward compatibility.
"""

# Authentication schemas
from .auth import (
    Token, TokenData, RefreshToken, LoginRequest, LoginResponse,
    RegisterRequest, PasswordChangeRequest, PasswordResetRequest,
    PasswordResetConfirm, ApiKeyCreate, ApiKeyResponse, SessionInfo
)

# User schemas
from .user import (
    UserBase, UserCreate, User, UserProfile, UserUpdate,
    UserWithItems, UserPermissions
)

# Department schemas
from .department import (
    DepartmentBase, DepartmentCreate, DepartmentUpdate,
    Department, DepartmentWithUsers
)

# Ticket schemas
from .ticket import (
    TicketBase, TicketCreate, TicketUpdate, TicketStatusUpdate,
    Ticket, TicketSummary, TicketDetail, TicketFilter, TicketSearchRequest
)

# Comment schemas
from .comment import (
    TicketCommentBase, TicketCommentCreate, TicketCommentUpdate,
    TicketComment, TicketCommentWithAuthor
)

# Attachment schemas
from .attachment import (
    TicketAttachmentBase, TicketAttachmentCreate, TicketAttachment,
    TicketAttachmentWithUploader, AttachmentResponse, AttachmentMetadata,
    AttachmentUpdate, FileUploadResponse
)

# Approval schemas
from .approval import (
    ApprovalWorkflowBase, ApprovalWorkflowCreate, ApprovalWorkflow,
    ApprovalWorkflowWithSteps, ApprovalStepBase, ApprovalActionRequest,
    ApprovalStep, ApprovalStepWithUser
)

# Common utility schemas
from .common import PaginationParams, PaginatedResponse

# Analytics and dashboard schemas
from .analytics import TicketStatistics, DashboardData

# Audit schemas
from .audit import AuditLogBase, AuditLogCreate, AuditLog, AuditLogWithUser

# Notification schemas
from .notification import NotificationTemplate, NotificationRequest

# Legacy schemas
from .item import ItemBase, ItemCreate, Item

__all__ = [
    # Authentication
    'Token', 'TokenData', 'RefreshToken', 'LoginRequest', 'LoginResponse',
    'RegisterRequest', 'PasswordChangeRequest', 'PasswordResetRequest',
    'PasswordResetConfirm', 'ApiKeyCreate', 'ApiKeyResponse', 'SessionInfo',

    # User
    'UserBase', 'UserCreate', 'User', 'UserProfile', 'UserUpdate',
    'UserWithItems', 'UserPermissions',

    # Department
    'DepartmentBase', 'DepartmentCreate', 'DepartmentUpdate',
    'Department', 'DepartmentWithUsers',

    # Ticket
    'TicketBase', 'TicketCreate', 'TicketUpdate', 'TicketStatusUpdate',
    'Ticket', 'TicketSummary', 'TicketDetail', 'TicketFilter', 'TicketSearchRequest',

    # Comment
    'TicketCommentBase', 'TicketCommentCreate', 'TicketCommentUpdate',
    'TicketComment', 'TicketCommentWithAuthor',

    # Attachment
    'TicketAttachmentBase', 'TicketAttachmentCreate', 'TicketAttachment',
    'TicketAttachmentWithUploader', 'AttachmentResponse', 'AttachmentMetadata',
    'AttachmentUpdate', 'FileUploadResponse',

    # Approval
    'ApprovalWorkflowBase', 'ApprovalWorkflowCreate', 'ApprovalWorkflow',
    'ApprovalWorkflowWithSteps', 'ApprovalStepBase', 'ApprovalActionRequest',
    'ApprovalStep', 'ApprovalStepWithUser',

    # Common
    'PaginationParams', 'PaginatedResponse',

    # Analytics
    'TicketStatistics', 'DashboardData',

    # Audit
    'AuditLogBase', 'AuditLogCreate', 'AuditLog', 'AuditLogWithUser',

    # Notification
    'NotificationTemplate', 'NotificationRequest',

    # Legacy
    'ItemBase', 'ItemCreate', 'Item'
]
