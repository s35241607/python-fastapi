"""
Role-Based Access Control (RBAC) Module

This module provides decorators, middleware, and utilities for implementing
comprehensive role-based access control throughout the ticket management system.
"""

from functools import wraps
from typing import List, Optional, Callable, Any, Dict, Set
from fastapi import HTTPException, status
from enum import Enum

from app.models import User
from app.enums import UserRole


class Permission(str, Enum):
    """System permissions enumeration"""
    
    # User Management
    MANAGE_USERS = "manage_users"
    VIEW_USERS = "view_users"
    CREATE_USERS = "create_users"
    UPDATE_USERS = "update_users"
    DELETE_USERS = "delete_users"
    
    # Department Management
    MANAGE_DEPARTMENTS = "manage_departments"
    VIEW_DEPARTMENTS = "view_departments"
    CREATE_DEPARTMENTS = "create_departments"
    UPDATE_DEPARTMENTS = "update_departments"
    DELETE_DEPARTMENTS = "delete_departments"
    
    # Ticket Management
    VIEW_ALL_TICKETS = "view_all_tickets"
    MANAGE_ALL_TICKETS = "manage_all_tickets"
    CREATE_TICKETS = "create_tickets"
    UPDATE_TICKETS = "update_tickets"
    DELETE_TICKETS = "delete_tickets"
    ASSIGN_TICKETS = "assign_tickets"
    CLOSE_TICKETS = "close_tickets"
    
    # Approval System
    APPROVE_TICKETS = "approve_tickets"
    APPROVE_ANY_TICKET = "approve_any_ticket"
    MANAGE_APPROVAL_WORKFLOWS = "manage_approval_workflows"
    DELEGATE_APPROVALS = "delegate_approvals"
    ESCALATE_APPROVALS = "escalate_approvals"
    
    # Reporting and Analytics
    VIEW_ANALYTICS = "view_analytics"
    VIEW_DEPARTMENT_ANALYTICS = "view_department_analytics"
    VIEW_SYSTEM_ANALYTICS = "view_system_analytics"
    EXPORT_DATA = "export_data"
    SCHEDULE_REPORTS = "schedule_reports"
    
    # File Management
    UPLOAD_FILES = "upload_files"
    DOWNLOAD_FILES = "download_files"
    DELETE_FILES = "delete_files"
    MANAGE_FILE_SECURITY = "manage_file_security"
    
    # System Administration
    MANAGE_SYSTEM = "manage_system"
    VIEW_AUDIT_LOGS = "view_audit_logs"
    MANAGE_INTEGRATIONS = "manage_integrations"
    CONFIGURE_SYSTEM = "configure_system"
    
    # Comments and Communication
    CREATE_COMMENTS = "create_comments"
    VIEW_INTERNAL_COMMENTS = "view_internal_comments"
    MODERATE_COMMENTS = "moderate_comments"


class RolePermissionMatrix:
    """Defines permissions for each role"""
    
    _role_permissions: Dict[UserRole, Set[Permission]] = {
        UserRole.SUPER_ADMIN: {
            # Super admins have all permissions
            Permission.MANAGE_USERS,
            Permission.VIEW_USERS,
            Permission.CREATE_USERS,
            Permission.UPDATE_USERS,
            Permission.DELETE_USERS,
            Permission.MANAGE_DEPARTMENTS,
            Permission.VIEW_DEPARTMENTS,
            Permission.CREATE_DEPARTMENTS,
            Permission.UPDATE_DEPARTMENTS,
            Permission.DELETE_DEPARTMENTS,
            Permission.VIEW_ALL_TICKETS,
            Permission.MANAGE_ALL_TICKETS,
            Permission.CREATE_TICKETS,
            Permission.UPDATE_TICKETS,
            Permission.DELETE_TICKETS,
            Permission.ASSIGN_TICKETS,
            Permission.CLOSE_TICKETS,
            Permission.APPROVE_TICKETS,
            Permission.APPROVE_ANY_TICKET,
            Permission.MANAGE_APPROVAL_WORKFLOWS,
            Permission.DELEGATE_APPROVALS,
            Permission.ESCALATE_APPROVALS,
            Permission.VIEW_ANALYTICS,
            Permission.VIEW_DEPARTMENT_ANALYTICS,
            Permission.VIEW_SYSTEM_ANALYTICS,
            Permission.EXPORT_DATA,
            Permission.SCHEDULE_REPORTS,
            Permission.UPLOAD_FILES,
            Permission.DOWNLOAD_FILES,
            Permission.DELETE_FILES,
            Permission.MANAGE_FILE_SECURITY,
            Permission.MANAGE_SYSTEM,
            Permission.VIEW_AUDIT_LOGS,
            Permission.MANAGE_INTEGRATIONS,
            Permission.CONFIGURE_SYSTEM,
            Permission.CREATE_COMMENTS,
            Permission.VIEW_INTERNAL_COMMENTS,
            Permission.MODERATE_COMMENTS,
        },
        
        UserRole.ADMIN: {
            # Admins have most permissions except system management
            Permission.MANAGE_USERS,
            Permission.VIEW_USERS,
            Permission.CREATE_USERS,
            Permission.UPDATE_USERS,
            Permission.DELETE_USERS,
            Permission.MANAGE_DEPARTMENTS,
            Permission.VIEW_DEPARTMENTS,
            Permission.CREATE_DEPARTMENTS,
            Permission.UPDATE_DEPARTMENTS,
            Permission.VIEW_ALL_TICKETS,
            Permission.MANAGE_ALL_TICKETS,
            Permission.CREATE_TICKETS,
            Permission.UPDATE_TICKETS,
            Permission.ASSIGN_TICKETS,
            Permission.CLOSE_TICKETS,
            Permission.APPROVE_TICKETS,
            Permission.APPROVE_ANY_TICKET,
            Permission.MANAGE_APPROVAL_WORKFLOWS,
            Permission.DELEGATE_APPROVALS,
            Permission.ESCALATE_APPROVALS,
            Permission.VIEW_ANALYTICS,
            Permission.VIEW_DEPARTMENT_ANALYTICS,
            Permission.VIEW_SYSTEM_ANALYTICS,
            Permission.EXPORT_DATA,
            Permission.SCHEDULE_REPORTS,
            Permission.UPLOAD_FILES,
            Permission.DOWNLOAD_FILES,
            Permission.DELETE_FILES,
            Permission.VIEW_AUDIT_LOGS,
            Permission.CREATE_COMMENTS,
            Permission.VIEW_INTERNAL_COMMENTS,
            Permission.MODERATE_COMMENTS,
        },
        
        UserRole.DEPARTMENT_HEAD: {
            # Department heads manage their department
            Permission.VIEW_USERS,
            Permission.VIEW_DEPARTMENTS,
            Permission.VIEW_ALL_TICKETS,  # Limited to their department
            Permission.CREATE_TICKETS,
            Permission.UPDATE_TICKETS,  # Limited scope
            Permission.ASSIGN_TICKETS,  # Within department
            Permission.CLOSE_TICKETS,
            Permission.APPROVE_TICKETS,
            Permission.DELEGATE_APPROVALS,
            Permission.ESCALATE_APPROVALS,
            Permission.VIEW_ANALYTICS,
            Permission.VIEW_DEPARTMENT_ANALYTICS,
            Permission.EXPORT_DATA,
            Permission.SCHEDULE_REPORTS,
            Permission.UPLOAD_FILES,
            Permission.DOWNLOAD_FILES,
            Permission.CREATE_COMMENTS,
            Permission.VIEW_INTERNAL_COMMENTS,
        },
        
        UserRole.MANAGER: {
            # Managers have departmental scope
            Permission.VIEW_USERS,  # Department only
            Permission.VIEW_DEPARTMENTS,
            Permission.CREATE_TICKETS,
            Permission.UPDATE_TICKETS,  # Limited scope
            Permission.ASSIGN_TICKETS,  # Limited scope
            Permission.APPROVE_TICKETS,  # Limited scope
            Permission.DELEGATE_APPROVALS,
            Permission.VIEW_ANALYTICS,  # Department only
            Permission.VIEW_DEPARTMENT_ANALYTICS,
            Permission.UPLOAD_FILES,
            Permission.DOWNLOAD_FILES,
            Permission.CREATE_COMMENTS,
            Permission.VIEW_INTERNAL_COMMENTS,
        },
        
        UserRole.EMPLOYEE: {
            # Basic employee permissions
            Permission.CREATE_TICKETS,
            Permission.UPDATE_TICKETS,  # Own tickets only
            Permission.UPLOAD_FILES,  # Own tickets only
            Permission.DOWNLOAD_FILES,  # Accessible files only
            Permission.CREATE_COMMENTS,
        }
    }
    
    @classmethod
    def get_role_permissions(cls, role: UserRole) -> Set[Permission]:
        """Get all permissions for a role"""
        return cls._role_permissions.get(role, set())
    
    @classmethod
    def has_permission(cls, role: UserRole, permission: Permission) -> bool:
        """Check if a role has a specific permission"""
        return permission in cls.get_role_permissions(role)
    
    @classmethod
    def get_user_permissions(cls, user: User) -> Set[Permission]:
        """Get all permissions for a user based on their role"""
        try:
            user_role = UserRole(user.role)
            return cls.get_role_permissions(user_role)
        except ValueError:
            # If role is not valid, return empty set
            return set()


class RBACValidator:
    """RBAC validation utilities"""
    
    @staticmethod
    def require_permission(permission: Permission):
        """Decorator factory for requiring specific permissions"""
        
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                # Extract current_user from function arguments
                current_user = None
                
                # Look for current_user in kwargs
                if 'current_user' in kwargs:
                    current_user = kwargs['current_user']
                
                # Look for current_user in args (dependency injection)
                for arg in args:
                    if isinstance(arg, User):
                        current_user = arg
                        break
                
                if not current_user:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Authentication required"
                    )
                
                # Check permission
                user_permissions = RolePermissionMatrix.get_user_permissions(current_user)
                
                if permission not in user_permissions:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Permission denied. Required: {permission.value}"
                    )
                
                return await func(*args, **kwargs)
            
            return wrapper
        return decorator
    
    @staticmethod
    def require_any_permission(*permissions: Permission):
        """Decorator factory for requiring any of the specified permissions"""
        
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                current_user = None
                
                if 'current_user' in kwargs:
                    current_user = kwargs['current_user']
                
                for arg in args:
                    if isinstance(arg, User):
                        current_user = arg
                        break
                
                if not current_user:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Authentication required"
                    )
                
                user_permissions = RolePermissionMatrix.get_user_permissions(current_user)
                
                if not any(perm in user_permissions for perm in permissions):
                    permission_names = [perm.value for perm in permissions]
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Permission denied. Required one of: {', '.join(permission_names)}"
                    )
                
                return await func(*args, **kwargs)
            
            return wrapper
        return decorator
    
    @staticmethod
    def require_role(*roles: UserRole):
        """Decorator factory for requiring specific roles"""
        
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            async def wrapper(*args, **kwargs):
                current_user = None
                
                if 'current_user' in kwargs:
                    current_user = kwargs['current_user']
                
                for arg in args:
                    if isinstance(arg, User):
                        current_user = arg
                        break
                
                if not current_user:
                    raise HTTPException(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        detail="Authentication required"
                    )
                
                try:
                    user_role = UserRole(current_user.role)
                except ValueError:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Invalid user role"
                    )
                
                if user_role not in roles:
                    role_names = [role.value for role in roles]
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail=f"Access denied. Required roles: {', '.join(role_names)}"
                    )
                
                return await func(*args, **kwargs)
            
            return wrapper
        return decorator


class ResourceAccessValidator:
    """Validators for resource-specific access control"""
    
    @staticmethod
    def can_access_ticket(user: User, ticket, action: str = "view") -> bool:
        """Check if user can access a specific ticket"""
        
        user_permissions = RolePermissionMatrix.get_user_permissions(user)
        
        # Super admins and admins can access all tickets
        if Permission.VIEW_ALL_TICKETS in user_permissions:
            return True
        
        # Users can access their own tickets
        if ticket.requester_id == user.id or ticket.assignee_id == user.id:
            return True
        
        # Department heads and managers can access department tickets
        if (Permission.VIEW_DEPARTMENT_ANALYTICS in user_permissions and 
            ticket.department_id == user.department_id):
            return True
        
        return False
    
    @staticmethod
    def can_modify_ticket(user: User, ticket, action: str = "update") -> bool:
        """Check if user can modify a specific ticket"""
        
        user_permissions = RolePermissionMatrix.get_user_permissions(user)
        
        # Admins can modify all tickets
        if Permission.MANAGE_ALL_TICKETS in user_permissions:
            return True
        
        # Users can modify their own tickets (with restrictions)
        if ticket.requester_id == user.id:
            # Basic permission check
            if Permission.UPDATE_TICKETS in user_permissions:
                return True
        
        # Assignees can update their assigned tickets
        if ticket.assignee_id == user.id:
            if Permission.UPDATE_TICKETS in user_permissions:
                return True
        
        # Managers can modify department tickets
        if (Permission.ASSIGN_TICKETS in user_permissions and 
            ticket.department_id == user.department_id):
            return True
        
        return False
    
    @staticmethod
    def can_access_department(user: User, department_id: int) -> bool:
        """Check if user can access department data"""
        
        user_permissions = RolePermissionMatrix.get_user_permissions(user)
        
        # Admins can access all departments
        if Permission.VIEW_DEPARTMENTS in user_permissions:
            return True
        
        # Users can access their own department
        if user.department_id == department_id:
            return True
        
        return False
    
    @staticmethod
    def can_approve_ticket(user: User, ticket) -> bool:
        """Check if user can approve a specific ticket"""
        
        user_permissions = RolePermissionMatrix.get_user_permissions(user)
        
        # Super permission for any ticket
        if Permission.APPROVE_ANY_TICKET in user_permissions:
            return True
        
        # Basic approval permission
        if Permission.APPROVE_TICKETS not in user_permissions:
            return False
        
        # Department-based approval
        if ticket.department_id == user.department_id:
            return True
        
        # Role-based approval rules could be added here
        
        return False


# Convenience decorators for common permission checks

def require_admin():
    """Require admin or super_admin role"""
    return RBACValidator.require_role(UserRole.ADMIN, UserRole.SUPER_ADMIN)


def require_manager():
    """Require manager level access"""
    return RBACValidator.require_role(
        UserRole.MANAGER, UserRole.DEPARTMENT_HEAD, 
        UserRole.ADMIN, UserRole.SUPER_ADMIN
    )


def require_staff():
    """Require staff level access"""
    return RBACValidator.require_role(
        UserRole.STAFF, UserRole.MANAGER, UserRole.DEPARTMENT_HEAD,
        UserRole.ADMIN, UserRole.SUPER_ADMIN
    )


def require_user_management():
    """Require user management permissions"""
    return RBACValidator.require_permission(Permission.MANAGE_USERS)


def require_ticket_management():
    """Require ticket management permissions"""
    return RBACValidator.require_any_permission(
        Permission.MANAGE_ALL_TICKETS, Permission.UPDATE_TICKETS
    )


def require_approval_permission():
    """Require approval permissions"""
    return RBACValidator.require_permission(Permission.APPROVE_TICKETS)


def require_analytics_access():
    """Require analytics viewing permissions"""
    return RBACValidator.require_any_permission(
        Permission.VIEW_ANALYTICS, Permission.VIEW_DEPARTMENT_ANALYTICS,
        Permission.VIEW_SYSTEM_ANALYTICS
    )


def require_export_permission():
    """Require data export permissions"""
    return RBACValidator.require_permission(Permission.EXPORT_DATA)


class PermissionChecker:
    """Runtime permission checking utilities"""
    
    def __init__(self, user: User):
        self.user = user
        self.permissions = RolePermissionMatrix.get_user_permissions(user)
    
    def has_permission(self, permission: Permission) -> bool:
        """Check if user has specific permission"""
        return permission in self.permissions
    
    def has_any_permission(self, *permissions: Permission) -> bool:
        """Check if user has any of the specified permissions"""
        return any(perm in self.permissions for perm in permissions)
    
    def has_role(self, *roles: UserRole) -> bool:
        """Check if user has any of the specified roles"""
        try:
            user_role = UserRole(self.user.role)
            return user_role in roles
        except ValueError:
            return False
    
    def can_access_ticket(self, ticket) -> bool:
        """Check ticket access"""
        return ResourceAccessValidator.can_access_ticket(self.user, ticket)
    
    def can_modify_ticket(self, ticket) -> bool:
        """Check ticket modification"""
        return ResourceAccessValidator.can_modify_ticket(self.user, ticket)
    
    def can_access_department(self, department_id: int) -> bool:
        """Check department access"""
        return ResourceAccessValidator.can_access_department(self.user, department_id)
    
    def can_approve_ticket(self, ticket) -> bool:
        """Check approval permission"""
        return ResourceAccessValidator.can_approve_ticket(self.user, ticket)
    
    def get_accessible_departments(self) -> List[int]:
        """Get list of department IDs user can access"""
        if self.has_permission(Permission.VIEW_DEPARTMENTS):
            # Admins can access all departments - would need to query DB
            return []  # Placeholder
        elif self.user.department_id:
            return [self.user.department_id]
        else:
            return []
    
    def get_permission_summary(self) -> Dict[str, Any]:
        """Get comprehensive permission summary for user"""
        return {
            "user_id": self.user.id,
            "username": self.user.username,
            "role": self.user.role,
            "department_id": self.user.department_id,
            "permissions": [perm.value for perm in self.permissions],
            "can_manage_users": self.has_permission(Permission.MANAGE_USERS),
            "can_manage_departments": self.has_permission(Permission.MANAGE_DEPARTMENTS),
            "can_view_all_tickets": self.has_permission(Permission.VIEW_ALL_TICKETS),
            "can_approve_tickets": self.has_permission(Permission.APPROVE_TICKETS),
            "can_view_analytics": self.has_any_permission(
                Permission.VIEW_ANALYTICS, Permission.VIEW_DEPARTMENT_ANALYTICS
            ),
            "can_export_data": self.has_permission(Permission.EXPORT_DATA),
            "is_admin": self.has_role(UserRole.ADMIN, UserRole.SUPER_ADMIN),
            "is_manager": self.has_role(
                UserRole.MANAGER, UserRole.DEPARTMENT_HEAD, 
                UserRole.ADMIN, UserRole.SUPER_ADMIN
            )
        }