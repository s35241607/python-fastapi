from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, JSON, Enum, Numeric, LargeBinary
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Enum, JSON, Numeric, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base
from app.enums import (
    UserRole, TicketStatus, Priority, TicketType, ApprovalAction,
    WorkflowType, ApprovalStepStatus, WorkflowStatus, AttachmentType,
    AuditEventType
)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    role = Column(Enum(UserRole), default=UserRole.EMPLOYEE)
    preferences = Column(JSON, default=dict)
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime(timezone=True), nullable=True)
    password_changed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    items = relationship("Item", back_populates="owner")
    department = relationship("Department", back_populates="users")
    created_tickets = relationship("Ticket", foreign_keys="Ticket.requester_id", back_populates="requester")
    assigned_tickets = relationship("Ticket", foreign_keys="Ticket.assignee_id", back_populates="assignee")
    approval_steps = relationship("ApprovalStep", back_populates="approver")
    ticket_comments = relationship("TicketComment", back_populates="author")
    audit_logs = relationship("AuditLog", back_populates="user")
    user_roles = relationship("UserRole", back_populates="user", cascade="all, delete-orphan")


class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    description = Column(String)
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    owner = relationship("User", back_populates="items")


class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    description = Column(Text)
    manager_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    budget_limit = Column(Numeric(12, 2), default=0.00)
    approval_rules = Column(JSON, default=dict)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    users = relationship("User", back_populates="department", foreign_keys="User.department_id")
    manager = relationship("User", foreign_keys=[manager_id])
    tickets = relationship("Ticket", back_populates="department")


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    ticket_number = Column(String, unique=True, index=True, nullable=False)
    title = Column(String, nullable=False, index=True)
    description = Column(Text)
    ticket_type = Column(Enum(TicketType), nullable=False)
    status = Column(Enum(TicketStatus), default=TicketStatus.DRAFT, index=True)
    priority = Column(Enum(Priority), default=Priority.MEDIUM, index=True)
    requester_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    assignee_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    due_date = Column(DateTime(timezone=True), nullable=True)
    estimated_hours = Column(Numeric(8, 2), nullable=True)
    actual_hours = Column(Numeric(8, 2), nullable=True)
    cost_estimate = Column(Numeric(12, 2), nullable=True)
    custom_fields = Column(JSON, default=dict)
    tags = Column(JSON, default=list)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    closed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    requester = relationship("User", foreign_keys=[requester_id], back_populates="created_tickets")
    assignee = relationship("User", foreign_keys=[assignee_id], back_populates="assigned_tickets")
    department = relationship("Department", back_populates="tickets")
    comments = relationship("TicketComment", back_populates="ticket", cascade="all, delete-orphan")
    attachments = relationship("TicketAttachment", back_populates="ticket", cascade="all, delete-orphan")
    workflows = relationship("ApprovalWorkflow", back_populates="ticket", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="ticket")


class TicketComment(Base):
    __tablename__ = "ticket_comments"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    is_internal = Column(Boolean, default=False)  # Internal comments only visible to staff
    is_system_generated = Column(Boolean, default=False)  # Auto-generated system comments
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    ticket = relationship("Ticket", back_populates="comments")
    author = relationship("User", back_populates="ticket_comments")


class ApprovalWorkflow(Base):
    __tablename__ = "approval_workflows"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False)
    workflow_name = Column(String, nullable=False)
    workflow_type = Column(Enum(WorkflowType), default=WorkflowType.SEQUENTIAL)
    status = Column(Enum(WorkflowStatus), default=WorkflowStatus.ACTIVE, index=True)
    workflow_config = Column(JSON, default=dict)  # Configuration for complex workflows
    auto_approve_threshold = Column(Numeric(12, 2), nullable=True)
    escalation_timeout_hours = Column(Integer, default=24)
    initiated_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    ticket = relationship("Ticket", back_populates="workflows")
    initiated_by = relationship("User")
    steps = relationship("ApprovalStep", back_populates="workflow", cascade="all, delete-orphan")


class ApprovalStep(Base):
    __tablename__ = "approval_steps"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("approval_workflows.id"), nullable=False)
    approver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    step_order = Column(Integer, nullable=False)  # Order in the approval sequence
    action = Column(Enum(ApprovalAction), nullable=True)
    status = Column(Enum(ApprovalStepStatus), default=ApprovalStepStatus.PENDING, index=True)
    comments = Column(Text)
    delegated_to_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    escalated_to_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    due_date = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    workflow = relationship("ApprovalWorkflow", back_populates="steps")
    approver = relationship("User", foreign_keys=[approver_id], back_populates="approval_steps")
    delegated_to = relationship("User", foreign_keys=[delegated_to_id])
    escalated_to = relationship("User", foreign_keys=[escalated_to_id])


class TicketAttachment(Base):
    __tablename__ = "ticket_attachments"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False)
    uploaded_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)  # Size in bytes
    mime_type = Column(String, nullable=False)
    attachment_type = Column(Enum(AttachmentType), default=AttachmentType.OTHER)
    description = Column(Text)
    is_public = Column(Boolean, default=True)  # Public attachments visible to requester
    checksum = Column(String)  # File integrity verification
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    ticket = relationship("Ticket", back_populates="attachments")
    uploaded_by = relationship("User")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(Enum(AuditEventType), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=True)
    entity_type = Column(String)  # Type of entity affected (ticket, user, etc.)
    entity_id = Column(Integer)  # ID of the affected entity
    old_values = Column(JSON)  # Previous state
    new_values = Column(JSON)  # New state
    extra_metadata = Column(JSON, default=dict)  # Additional context
    ip_address = Column(String)
    user_agent = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    user = relationship("User", back_populates="audit_logs")
    ticket = relationship("Ticket", back_populates="audit_logs")


# ============================================================================
# ROLE-BASED ACCESS CONTROL MODELS
# ============================================================================

# Association table for many-to-many relationship between roles and permissions
role_permission_association = Table(
    'role_permissions',
    Base.metadata,
    Column('role_id', Integer, ForeignKey('roles.id'), primary_key=True),
    Column('permission_id', Integer, ForeignKey('permissions.id'), primary_key=True)
)


class Role(Base):
    """Role model for RBAC system"""
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    display_name = Column(String, nullable=False)  # Human-readable name
    description = Column(Text)
    is_system_role = Column(Boolean, default=False)  # System roles cannot be deleted
    is_active = Column(Boolean, default=True)
    priority = Column(Integer, default=0)  # Higher priority roles override lower ones
    max_permissions = Column(Integer, nullable=True)  # Optional permission limit
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    permissions = relationship("Permission", secondary=role_permission_association, back_populates="roles")
    user_roles = relationship("UserRole", back_populates="role", cascade="all, delete-orphan")
    created_by = relationship("User", foreign_keys=[created_by_id])


class Permission(Base):
    """Permission model for RBAC system"""
    __tablename__ = "permissions"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)  # e.g., 'manage_users'
    display_name = Column(String, nullable=False)  # Human-readable name
    description = Column(Text)
    category = Column(String, nullable=False, index=True)  # e.g., 'user_management', 'ticket_management'
    resource_type = Column(String, nullable=True)  # What type of resource this applies to
    is_system_permission = Column(Boolean, default=False)  # System permissions cannot be deleted
    is_active = Column(Boolean, default=True)
    requires_context = Column(Boolean, default=False)  # Whether permission needs additional context
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    roles = relationship("Role", secondary=role_permission_association, back_populates="permissions")
    user_permissions = relationship("UserPermission", back_populates="permission", cascade="all, delete-orphan")


class UserRole(Base):
    """Association model for user-role relationships with additional metadata"""
    __tablename__ = "user_roles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)  # Role scoped to department
    is_active = Column(Boolean, default=True)
    granted_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    granted_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)  # Optional role expiration
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    revoked_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="user_roles")
    role = relationship("Role", back_populates="user_roles")
    department = relationship("Department", foreign_keys=[department_id])
    granted_by = relationship("User", foreign_keys=[granted_by_id])
    revoked_by = relationship("User", foreign_keys=[revoked_by_id])


class UserPermission(Base):
    """Direct user-permission assignments for fine-grained control"""
    __tablename__ = "user_permissions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    permission_id = Column(Integer, ForeignKey("permissions.id"), nullable=False)
    is_granted = Column(Boolean, default=True)  # True for grant, False for explicit deny
    resource_id = Column(Integer, nullable=True)  # Specific resource this permission applies to
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)  # Department scope
    conditions = Column(JSON, default=dict)  # Additional conditions for permission
    granted_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    granted_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    revoked_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    permission = relationship("Permission", back_populates="user_permissions")
    department = relationship("Department", foreign_keys=[department_id])
    granted_by = relationship("User", foreign_keys=[granted_by_id])
    revoked_by = relationship("User", foreign_keys=[revoked_by_id])


class ApiKey(Base):
    """API key model for external system access"""
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)  # Human-readable name
    description = Column(Text)
    key_hash = Column(String, nullable=False, unique=True, index=True)  # Hashed API key
    key_prefix = Column(String, nullable=False, index=True)  # First few characters for identification
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    permissions = Column(JSON, default=list)  # List of permission names
    ip_whitelist = Column(JSON, default=list)  # Allowed IP addresses
    rate_limit = Column(Integer, default=1000)  # Requests per hour
    is_active = Column(Boolean, default=True)
    last_used = Column(DateTime(timezone=True), nullable=True)
    usage_count = Column(Integer, default=0)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    owner = relationship("User", foreign_keys=[user_id])


class UserSession(Base):
    """User session tracking for security and analytics"""
    __tablename__ = "user_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_token = Column(String, nullable=False, unique=True, index=True)
    refresh_token = Column(String, nullable=True, unique=True, index=True)
    ip_address = Column(String, nullable=True)
    user_agent = Column(String, nullable=True)
    device_info = Column(JSON, default=dict)
    location_info = Column(JSON, default=dict)  # City, country, etc.
    is_active = Column(Boolean, default=True)
    last_activity = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    ended_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
