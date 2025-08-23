"""
Authentication Dependencies Module

This module provides FastAPI dependency functions for JWT token validation,
user authentication, and authorization checks throughout the application.
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.auth_service import AuthenticationService
from app.models import User
from app.schemas import TokenData

# Security scheme for Bearer token
security = HTTPBearer()


async def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthenticationService:
    """Get authentication service instance"""
    return AuthenticationService(db)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthenticationService = Depends(get_auth_service)
) -> User:
    """Get current authenticated user from JWT token"""
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Extract token from credentials
        token = credentials.credentials
        
        # Verify and decode token
        token_data = auth_service.verify_token(token, "access")
        if token_data is None:
            raise credentials_exception
        
        # Get user from database
        user = await auth_service.get_user_by_id(token_data.user_id)
        if user is None:
            raise credentials_exception
        
        return user
        
    except Exception:
        raise credentials_exception


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Get current active user (must be active)"""
    
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    return current_user


async def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    auth_service: AuthenticationService = Depends(get_auth_service)
) -> Optional[User]:
    """Get current user if token is provided, otherwise return None"""
    
    if not credentials:
        return None
    
    try:
        token = credentials.credentials
        token_data = auth_service.verify_token(token, "access")
        
        if token_data is None:
            return None
        
        user = await auth_service.get_user_by_id(token_data.user_id)
        return user if user and user.is_active else None
        
    except Exception:
        return None


def require_roles(*roles: str):
    """Dependency factory for role-based access control"""
    
    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {', '.join(roles)}"
            )
        return current_user
    
    return role_checker


def require_admin():
    """Require admin or super_admin role"""
    return require_roles("admin", "super_admin")


def require_manager():
    """Require manager, admin, or super_admin role"""
    return require_roles("manager", "department_head", "admin", "super_admin")


def require_staff():
    """Require manager level access (not just employee)"""
    return require_roles("manager", "department_head", "admin", "super_admin")


async def get_current_user_role(
    current_user: User = Depends(get_current_active_user)
) -> str:
    """Get current user's role as string"""
    return current_user.role


async def get_current_user_permissions(
    current_user: User = Depends(get_current_active_user)
) -> dict:
    """Get current user's permissions based on their role"""
    
    # Define permissions by role
    role_permissions = {
        "super_admin": {
            "can_manage_users": True,
            "can_manage_departments": True,
            "can_manage_system": True,
            "can_view_all_tickets": True,
            "can_manage_all_tickets": True,
            "can_approve_any": True,
            "can_view_analytics": True,
            "can_export_data": True,
            "can_manage_workflows": True
        },
        "admin": {
            "can_manage_users": True,
            "can_manage_departments": True,
            "can_manage_system": False,
            "can_view_all_tickets": True,
            "can_manage_all_tickets": True,
            "can_approve_any": True,
            "can_view_analytics": True,
            "can_export_data": True,
            "can_manage_workflows": True
        },
        "department_head": {
            "can_manage_users": False,
            "can_manage_departments": False,
            "can_manage_system": False,
            "can_view_all_tickets": False,
            "can_manage_all_tickets": False,
            "can_approve_any": False,
            "can_view_analytics": True,
            "can_export_data": True,
            "can_manage_workflows": False
        },
        "manager": {
            "can_manage_users": False,
            "can_manage_departments": False,
            "can_manage_system": False,
            "can_view_all_tickets": False,
            "can_manage_all_tickets": False,
            "can_approve_any": False,
            "can_view_analytics": True,
            "can_export_data": False,
            "can_manage_workflows": False
        },
        "manager": {
            "can_manage_users": False,
            "can_manage_departments": False,
            "can_manage_system": False,
            "can_view_all_tickets": False,
            "can_manage_all_tickets": False,
            "can_approve_any": False,
            "can_view_analytics": False,
            "can_export_data": False,
            "can_manage_workflows": False
        },
        "employee": {
            "can_manage_users": False,
            "can_manage_departments": False,
            "can_manage_system": False,
            "can_view_all_tickets": False,
            "can_manage_all_tickets": False,
            "can_approve_any": False,
            "can_view_analytics": False,
            "can_export_data": False,
            "can_manage_workflows": False
        }
    }
    
    permissions = role_permissions.get(current_user.role, role_permissions["employee"])
    
    # Add user-specific permissions
    permissions.update({
        "user_id": current_user.id,
        "username": current_user.username,
        "role": current_user.role,
        "department_id": current_user.department_id,
        "can_create_tickets": True,
        "can_view_own_tickets": True,
        "can_comment_tickets": True
    })
    
    return permissions


def require_permission(permission: str):
    """Dependency factory for permission-based access control"""
    
    async def permission_checker(
        permissions: dict = Depends(get_current_user_permissions)
    ) -> dict:
        if not permissions.get(permission, False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required permission: {permission}"
            )
        return permissions
    
    return permission_checker


async def verify_department_access(
    department_id: int,
    current_user: User = Depends(get_current_active_user)
) -> bool:
    """Verify if user can access specific department data"""
    
    # Admins can access any department
    if current_user.role in ["admin", "super_admin"]:
        return True
    
    # Department heads and managers can access their own department
    if current_user.role in ["department_head", "manager"]:
        return current_user.department_id == department_id
    
    # Regular users can only access their own department
    return current_user.department_id == department_id


async def verify_ticket_access(
    ticket_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> bool:
    """Verify if user can access specific ticket"""
    
    from app.repositories.ticket_repository import TicketRepository
    
    # Admins can access any ticket
    if current_user.role in ["admin", "super_admin"]:
        return True
    
    ticket_repo = TicketRepository(db)
    ticket = await ticket_repo.get_by_id(ticket_id)
    
    if not ticket:
        return False
    
    # Check if user is requester or assignee
    if ticket.requester_id == current_user.id or ticket.assignee_id == current_user.id:
        return True
    
    # Check department access for managers
    if current_user.role in ["department_head", "manager"]:
        return await verify_department_access(ticket.department_id, current_user)
    
    return False


def require_ticket_access(ticket_id: int):
    """Dependency for verifying ticket access"""
    
    async def ticket_access_checker(
        has_access: bool = Depends(lambda: verify_ticket_access(ticket_id))
    ) -> bool:
        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this ticket"
            )
        return True
    
    return ticket_access_checker


async def get_user_context(
    current_user: User = Depends(get_current_active_user),
    permissions: dict = Depends(get_current_user_permissions)
) -> dict:
    """Get comprehensive user context for API operations"""
    
    return {
        "user": current_user,
        "user_id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "role": current_user.role,
        "department_id": current_user.department_id,
        "permissions": permissions,
        "is_admin": current_user.role in ["admin", "super_admin"],
        "is_manager": current_user.role in ["manager", "department_head", "admin", "super_admin"]
    }


def validate_api_key():
    """Dependency for API key validation (for external integrations)"""
    
    async def api_key_checker(
        api_key: Optional[str] = None,
        db: AsyncSession = Depends(get_db)
    ) -> bool:
        # This would validate API keys for external system integration
        # Implementation would check against a database of valid API keys
        if not api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API key required"
            )
        
        # Placeholder validation - implement actual API key checking
        valid_api_keys = ["demo-api-key-123"]  # This should come from database
        
        if api_key not in valid_api_keys:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key"
            )
        
        return True
    
    return api_key_checker


async def rate_limit_checker(
    current_user: Optional[User] = Depends(get_optional_current_user)
) -> bool:
    """Basic rate limiting dependency"""
    
    # This is a placeholder for rate limiting implementation
    # In production, you would use Redis or similar for rate limiting
    
    # For now, just return True
    return True


class PermissionDependency:
    """Class-based permission dependency for more complex authorization"""
    
    def __init__(self, required_permission: str, allow_owner: bool = False):
        self.required_permission = required_permission
        self.allow_owner = allow_owner
    
    async def __call__(
        self,
        current_user: User = Depends(get_current_active_user),
        permissions: dict = Depends(get_current_user_permissions)
    ) -> User:
        
        # Check if user has the required permission
        if permissions.get(self.required_permission, False):
            return current_user
        
        # If owner access is allowed, additional checks can be implemented here
        if self.allow_owner:
            # This would need context about what resource is being accessed
            pass
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied. Required permission: {self.required_permission}"
        )


# Convenience instances for common permissions
can_manage_users = PermissionDependency("can_manage_users")
can_manage_departments = PermissionDependency("can_manage_departments")
can_view_analytics = PermissionDependency("can_view_analytics")
can_export_data = PermissionDependency("can_export_data")
can_manage_workflows = PermissionDependency("can_manage_workflows")