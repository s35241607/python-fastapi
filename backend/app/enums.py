"""
Enums for the Enterprise Ticket Management System

This module defines all enumeration types used throughout the ticket management system,
including ticket statuses, priorities, types, approval actions, and workflow types.
"""

from enum import Enum


class TicketStatus(str, Enum):
    """Ticket status enumeration defining the lifecycle states"""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    IN_REVIEW = "in_review"
    PENDING_INFO = "pending_info"
    APPROVED = "approved"
    REJECTED = "rejected"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CLOSED = "closed"


class Priority(str, Enum):
    """Priority levels for tickets"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TicketType(str, Enum):
    """Categories of tickets supported by the system"""
    IT_SUPPORT = "it_support"
    IT_HARDWARE = "it_hardware"
    IT_SOFTWARE = "it_software"
    HR = "hr"
    FINANCE = "finance"
    FACILITY = "facility"
    PROCUREMENT = "procurement"
    LEGAL = "legal"
    CUSTOM = "custom"


class ApprovalAction(str, Enum):
    """Actions that can be taken during approval process"""
    APPROVE = "approve"
    REJECT = "reject"
    REQUEST_INFO = "request_info"
    DELEGATE = "delegate"
    ESCALATE = "escalate"


class WorkflowType(str, Enum):
    """Types of approval workflows"""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    CONDITIONAL = "conditional"
    AUTO_APPROVE = "auto_approve"


class ApprovalStepStatus(str, Enum):
    """Status of individual approval steps"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    DELEGATED = "delegated"
    ESCALATED = "escalated"
    SKIPPED = "skipped"


class WorkflowStatus(str, Enum):
    """Overall status of approval workflows"""
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    ESCALATED = "escalated"


class NotificationChannel(str, Enum):
    """Available notification channels"""
    EMAIL = "email"
    IN_APP = "in_app"
    TEAMS = "teams"
    SLACK = "slack"
    SMS = "sms"


class UserRole(str, Enum):
    """User roles in the system"""
    EMPLOYEE = "employee"
    MANAGER = "manager"
    DEPARTMENT_HEAD = "department_head"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


class AttachmentType(str, Enum):
    """File attachment types"""
    DOCUMENT = "document"
    IMAGE = "image"
    SPREADSHEET = "spreadsheet"
    PRESENTATION = "presentation"
    OTHER = "other"


class AuditEventType(str, Enum):
    """Types of auditable events"""
    TICKET_CREATED = "ticket_created"
    TICKET_UPDATED = "ticket_updated"
    TICKET_ASSIGNED = "ticket_assigned"
    TICKET_STATUS_CHANGED = "ticket_status_changed"
    APPROVAL_REQUESTED = "approval_requested"
    APPROVAL_COMPLETED = "approval_completed"
    COMMENT_ADDED = "comment_added"
    ATTACHMENT_UPLOADED = "attachment_uploaded"
    WORKFLOW_INITIATED = "workflow_initiated"
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    PERMISSION_CHANGED = "permission_changed"