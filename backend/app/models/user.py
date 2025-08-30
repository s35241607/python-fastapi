"""
User-related models including User, UserRole, UserPermission, and UserSession.
"""
from .base import Base, Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Enum, JSON, relationship, func, UserRole as UserRoleEnum


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    role = Column(Enum(UserRoleEnum), default=UserRoleEnum.EMPLOYEE)
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
