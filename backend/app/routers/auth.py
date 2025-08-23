"""
Authentication Router Module

This module provides FastAPI endpoints for user authentication including
login, logout, registration, password management, and user profile operations.
"""

from typing import Optional, List
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.auth_service import AuthenticationService
from app.auth.dependencies import (
    get_current_user, get_current_active_user, get_auth_service,
    require_admin, get_current_user_permissions
)
from app.schemas import (
    LoginRequest, LoginResponse, RegisterRequest, Token, RefreshToken,
    PasswordChangeRequest, PasswordResetRequest, PasswordResetConfirm,
    UserProfile, UserUpdate, UserPermissions, SessionInfo
)
from app.models import User
from app.enums import UserRole

router = APIRouter(prefix="/api/v1/auth", tags=["authentication"])

# Security scheme
security = HTTPBearer()


@router.post("/login", response_model=LoginResponse)
async def login(
    login_request: LoginRequest,
    response: Response,
    auth_service: AuthenticationService = Depends(get_auth_service)
):
    """Authenticate user and return JWT tokens"""
    
    try:
        # Authenticate user
        user = await auth_service.authenticate_user(
            username=login_request.username,
            password=login_request.password
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User account is disabled"
            )
        
        # Create token pair
        tokens = auth_service.create_token_pair(user)
        
        # Update last login
        await auth_service.update_last_login(user.id)
        
        # Set secure httpOnly cookie for refresh token if remember_me is True
        if login_request.remember_me:
            response.set_cookie(
                key="refresh_token",
                value=tokens["refresh_token"],
                httponly=True,
                secure=True,
                samesite="strict",
                max_age=7 * 24 * 60 * 60  # 7 days
            )
        
        return LoginResponse(
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            token_type="bearer",
            expires_in=auth_service.access_token_expire_minutes * 60,
            user=UserProfile.from_orm(user)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed"
        )


@router.post("/register", response_model=UserProfile, status_code=status.HTTP_201_CREATED)
async def register(
    register_request: RegisterRequest,
    auth_service: AuthenticationService = Depends(get_auth_service),
    # Only admins can register new users in enterprise environment
    current_user: User = Depends(require_admin())
):
    """Register a new user (admin only)"""
    
    try:
        # Prepare user data
        user_data = {
            "username": register_request.username,
            "email": register_request.email,
            "password": register_request.password,
            "first_name": register_request.first_name,
            "last_name": register_request.last_name,
            "department_id": register_request.department_id,
            "role": UserRole.EMPLOYEE.value  # Default role
        }
        
        # Create user
        user = await auth_service.create_user(user_data)
        
        return UserProfile.from_orm(user)
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User registration failed"
        )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_request: RefreshToken,
    auth_service: AuthenticationService = Depends(get_auth_service)
):
    """Refresh access token using refresh token"""
    
    try:
        tokens = await auth_service.refresh_access_token(refresh_request.refresh_token)
        
        if not tokens:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return Token(
            access_token=tokens["access_token"],
            refresh_token=refresh_request.refresh_token,  # Keep same refresh token
            token_type="bearer",
            expires_in=auth_service.access_token_expire_minutes * 60
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )


@router.post("/logout")
async def logout(
    response: Response,
    current_user: User = Depends(get_current_user)
):
    """Logout user and invalidate tokens"""
    
    try:
        # Clear refresh token cookie
        response.delete_cookie(
            key="refresh_token",
            httponly=True,
            secure=True,
            samesite="strict"
        )
        
        # In a production system, you would add the token to a blacklist
        # For now, we just rely on token expiration
        
        return {"message": "Successfully logged out"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )


@router.get("/me", response_model=UserProfile)
async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user)
):
    """Get current user's profile information"""
    
    return UserProfile.from_orm(current_user)


@router.put("/me", response_model=UserProfile)
async def update_current_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    auth_service: AuthenticationService = Depends(get_auth_service)
):
    """Update current user's profile information"""
    
    try:
        # Update user data
        update_data = user_update.dict(exclude_unset=True)
        
        # Update user attributes
        for field, value in update_data.items():
            if hasattr(current_user, field):
                setattr(current_user, field, value)
        
        await auth_service.session.commit()
        await auth_service.session.refresh(current_user)
        
        return UserProfile.from_orm(current_user)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Profile update failed"
        )


@router.post("/change-password")
async def change_password(
    password_change: PasswordChangeRequest,
    current_user: User = Depends(get_current_active_user),
    auth_service: AuthenticationService = Depends(get_auth_service)
):
    """Change current user's password"""
    
    try:
        success = await auth_service.change_password(
            user_id=current_user.id,
            current_password=password_change.current_password,
            new_password=password_change.new_password
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        return {"message": "Password changed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change failed"
        )


@router.post("/forgot-password")
async def forgot_password(
    password_reset: PasswordResetRequest,
    auth_service: AuthenticationService = Depends(get_auth_service)
):
    """Initiate password reset process"""
    
    try:
        # Check if user exists
        user = await auth_service.get_user_by_email(password_reset.email)
        
        if user:
            # Generate password reset token
            reset_token = auth_service.generate_password_reset_token(user.id)
            
            # In production, send email with reset link
            # For now, we'll just log it or return it for demo purposes
            # send_password_reset_email(user.email, reset_token)
            
            # For demo purposes, return the token (remove in production)
            return {
                "message": "Password reset email sent",
                "reset_token": reset_token  # Remove this in production
            }
        else:
            # Don't reveal if email exists or not for security
            return {"message": "If the email exists, a password reset link has been sent"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset request failed"
        )


@router.post("/reset-password")
async def reset_password(
    password_reset: PasswordResetConfirm,
    auth_service: AuthenticationService = Depends(get_auth_service)
):
    """Reset password using reset token"""
    
    try:
        success = await auth_service.reset_password(
            token=password_reset.token,
            new_password=password_reset.new_password
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )
        
        return {"message": "Password reset successfully"}
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset failed"
        )


@router.get("/permissions", response_model=UserPermissions)
async def get_user_permissions_endpoint(
    current_user: User = Depends(get_current_active_user),
    permissions: dict = Depends(get_current_user_permissions)
):
    """Get current user's permissions"""
    
    return UserPermissions(
        user_id=current_user.id,
        role=current_user.role,
        permissions=permissions,
        department_access=[current_user.department_id] if current_user.department_id else []
    )


@router.get("/session", response_model=SessionInfo)
async def get_session_info(
    current_user: User = Depends(get_current_active_user),
    permissions: dict = Depends(get_current_user_permissions),
    auth_service: AuthenticationService = Depends(get_auth_service)
):
    """Get comprehensive session information"""
    
    return SessionInfo(
        user=UserProfile.from_orm(current_user),
        permissions=UserPermissions(
            user_id=current_user.id,
            role=current_user.role,
            permissions=permissions,
            department_access=[current_user.department_id] if current_user.department_id else []
        ),
        session_expires_at=datetime.utcnow() + timedelta(minutes=auth_service.access_token_expire_minutes),
        last_activity=datetime.utcnow()
    )


@router.post("/validate-token")
async def validate_token(
    current_user: User = Depends(get_current_user)
):
    """Validate current token and return user info"""
    
    return {
        "valid": True,
        "user_id": current_user.id,
        "username": current_user.username,
        "role": current_user.role
    }


@router.get("/check-username/{username}")
async def check_username_availability(
    username: str,
    auth_service: AuthenticationService = Depends(get_auth_service)
):
    """Check if username is available"""
    
    try:
        existence_check = await auth_service.check_user_exists(username, "dummy@email.com")
        
        return {
            "username": username,
            "available": not existence_check["username_exists"]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Username check failed"
        )


@router.get("/check-email/{email}")
async def check_email_availability(
    email: str,
    auth_service: AuthenticationService = Depends(get_auth_service)
):
    """Check if email is available"""
    
    try:
        existence_check = await auth_service.check_user_exists("dummy", email)
        
        return {
            "email": email,
            "available": not existence_check["email_exists"]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Email check failed"
        )


# Admin endpoints for user management

@router.get("/users", response_model=List[UserProfile])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(require_admin()),
    auth_service: AuthenticationService = Depends(get_auth_service)
):
    """List all users (admin only)"""
    
    try:
        # This would use a user repository to get paginated users
        # For now, return empty list as placeholder
        return []
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users"
        )


@router.put("/users/{user_id}/role")
async def update_user_role(
    user_id: int,
    new_role: UserRole,
    current_user: User = Depends(require_admin()),
    auth_service: AuthenticationService = Depends(get_auth_service)
):
    """Update user role (admin only)"""
    
    try:
        user = await auth_service.get_user_by_id(user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user.role = new_role.value
        await auth_service.session.commit()
        
        return {"message": f"User role updated to {new_role.value}"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Role update failed"
        )


@router.put("/users/{user_id}/status")
async def update_user_status(
    user_id: int,
    is_active: bool,
    current_user: User = Depends(require_admin()),
    auth_service: AuthenticationService = Depends(get_auth_service)
):
    """Activate/deactivate user (admin only)"""
    
    try:
        user = await auth_service.get_user_by_id(user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user.is_active = is_active
        await auth_service.session.commit()
        
        status_text = "activated" if is_active else "deactivated"
        return {"message": f"User {status_text} successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Status update failed"
        )