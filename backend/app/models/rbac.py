"""
RBAC (Role-Based Access Control) models including Role and Permission.
"""
from .base import Base, Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Table, relationship, func

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
