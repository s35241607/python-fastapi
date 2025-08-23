"""
Authentication Package

This package contains authentication and authorization components for the
ticket management system including JWT handling, RBAC, and security dependencies.
"""

from .dependencies import (
    get_current_user,
    get_current_active_user,
    get_optional_current_user,
    require_roles,
    require_admin,
    require_manager,
    require_staff,
    get_current_user_permissions,
    require_permission,
    verify_department_access,
    verify_ticket_access,
    get_user_context,
    PermissionDependency,
    can_manage_users,
    can_manage_departments,
    can_view_analytics,
    can_export_data,
    can_manage_workflows
)

from .rbac import (
    Permission,
    RolePermissionMatrix,
    RBACValidator,
    ResourceAccessValidator,
    PermissionChecker,
    require_user_management,
    require_ticket_management,
    require_approval_permission,
    require_analytics_access,
    require_export_permission
)

__all__ = [
    # Dependencies
    "get_current_user",
    "get_current_active_user",
    "get_optional_current_user",
    "require_roles",
    "require_admin",
    "require_manager",
    "require_staff",
    "get_current_user_permissions",
    "require_permission",
    "verify_department_access",
    "verify_ticket_access",
    "get_user_context",
    "PermissionDependency",
    "can_manage_users",
    "can_manage_departments",
    "can_view_analytics",
    "can_export_data",
    "can_manage_workflows",
    
    # RBAC
    "Permission",
    "RolePermissionMatrix",
    "RBACValidator",
    "ResourceAccessValidator",
    "PermissionChecker",
    "require_user_management",
    "require_ticket_management",
    "require_approval_permission",
    "require_analytics_access",
    "require_export_permission"
]