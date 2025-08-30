"""
Models package for the FastAPI application.

This package contains all SQLAlchemy models organized by domain for better maintainability.
All models are imported here for backward compatibility.
"""

# Import all models for backward compatibility
from .user import User, UserRole, UserPermission, UserSession
from .auth import ApiKey
from .rbac import Role, Permission, role_permission_association
from .department import Department
from .ticket import Ticket
from .comment import TicketComment
from .attachment import TicketAttachment
from .approval import ApprovalWorkflow, ApprovalStep
from .audit import AuditLog
from .item import Item

# Import Base for database initialization
from .base import Base

__all__ = [
    # Base
    'Base',

    # User related
    'User', 'UserRole', 'UserPermission', 'UserSession',

    # Authentication
    'ApiKey',

    # RBAC
    'Role', 'Permission', 'role_permission_association',

    # Core models
    'Department', 'Ticket', 'TicketComment', 'TicketAttachment',

    # Approval system
    'ApprovalWorkflow', 'ApprovalStep',

    # Audit
    'AuditLog',

    # Legacy
    'Item'
]
