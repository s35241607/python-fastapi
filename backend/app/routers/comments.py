"""
Comments Router Module

This module provides FastAPI endpoints for ticket comment management including
thread creation, updates, access control, and search functionality.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.repositories.comment_repository import CommentRepository
from app.schemas import (
    TicketCommentCreate, TicketCommentUpdate, TicketCommentWithAuthor,
    TicketComment
)
from app.models import User

# Placeholder for authentication dependency
async def get_current_user() -> User:
    """Get current authenticated user - placeholder"""
    return User(id=1, email="user@example.com", username="testuser", 
               first_name="Test", last_name="User", role="employee")

async def get_current_user_role() -> str:
    """Get current user role - placeholder"""
    return "employee"

router = APIRouter(prefix="/api/v1/comments", tags=["comments"])


@router.post("/tickets/{ticket_id}", response_model=TicketCommentWithAuthor, status_code=status.HTTP_201_CREATED)
async def create_comment(
    ticket_id: int,
    comment_data: TicketCommentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_role: str = Depends(get_current_user_role)
):
    """Create a new comment on a ticket"""
    
    try:
        # Check if user can comment on this ticket
        # This would involve checking ticket access permissions
        
        comment_repo = CommentRepository(db)
        comment = await comment_repo.create_comment(
            ticket_id=ticket_id,
            author_id=current_user.id,
            content=comment_data.content,
            is_internal=comment_data.is_internal
        )
        
        # Get comment with author details
        comment_with_author = await comment_repo.get_comment_with_author(comment.id)
        
        return TicketCommentWithAuthor.from_orm(comment_with_author)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create comment"
        )


@router.get("/tickets/{ticket_id}", response_model=List[TicketCommentWithAuthor])
async def get_ticket_comments(
    ticket_id: int,
    include_internal: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_role: str = Depends(get_current_user_role)
):
    """Get all comments for a ticket"""
    
    try:
        # Check if user can view this ticket
        # This would involve checking ticket access permissions
        
        comment_repo = CommentRepository(db)
        comments = await comment_repo.get_ticket_comments(
            ticket_id=ticket_id,
            user_id=current_user.id,
            user_role=user_role,
            include_internal=include_internal
        )
        
        return [TicketCommentWithAuthor.from_orm(comment) for comment in comments]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve comments"
        )


@router.get("/{comment_id}", response_model=TicketCommentWithAuthor)
async def get_comment(
    comment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_role: str = Depends(get_current_user_role)
):
    """Get a specific comment by ID"""
    
    try:
        comment_repo = CommentRepository(db)
        comment = await comment_repo.get_comment_with_author(comment_id)
        
        if not comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Comment not found"
            )
        
        # Check access permissions
        # If it's an internal comment, check if user has permission
        if comment.is_internal and user_role == "employee":
            # Additional permission checks
            if comment.ticket.requester_id != current_user.id and comment.ticket.assignee_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to internal comment"
                )
        
        return TicketCommentWithAuthor.from_orm(comment)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve comment"
        )


@router.put("/{comment_id}", response_model=TicketCommentWithAuthor)
async def update_comment(
    comment_id: int,
    comment_data: TicketCommentUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_role: str = Depends(get_current_user_role)
):
    """Update a comment (only by original author)"""
    
    try:
        comment_repo = CommentRepository(db)
        updated_comment = await comment_repo.update_comment(
            comment_id=comment_id,
            author_id=current_user.id,
            content=comment_data.content,
            is_internal=comment_data.is_internal
        )
        
        if not updated_comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Comment not found or access denied"
            )
        
        # Get updated comment with author details
        comment_with_author = await comment_repo.get_comment_with_author(comment_id)
        
        return TicketCommentWithAuthor.from_orm(comment_with_author)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update comment"
        )


@router.delete("/{comment_id}")
async def delete_comment(
    comment_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_role: str = Depends(get_current_user_role)
):
    """Delete a comment (only by author or admin)"""
    
    try:
        comment_repo = CommentRepository(db)
        success = await comment_repo.delete_comment(comment_id, current_user.id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Comment not found or access denied"
            )
        
        return {"message": "Comment deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete comment"
        )


@router.get("/users/{user_id}/recent", response_model=List[TicketCommentWithAuthor])
async def get_user_recent_comments(
    user_id: int,
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_role: str = Depends(get_current_user_role)
):
    """Get recent comments by a specific user"""
    
    try:
        # Permission check
        if user_id != current_user.id:
            if user_role not in ["admin", "manager", "department_head"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to view other users' comments"
                )
        
        comment_repo = CommentRepository(db)
        comments = await comment_repo.get_recent_comments_by_user(
            user_id=user_id,
            limit=limit
        )
        
        return [TicketCommentWithAuthor.from_orm(comment) for comment in comments]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user comments"
        )


@router.get("/tickets/{ticket_id}/count")
async def get_comment_count(
    ticket_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get total comment count for a ticket"""
    
    try:
        comment_repo = CommentRepository(db)
        count = await comment_repo.get_comment_count_for_ticket(ticket_id)
        
        return {"ticket_id": ticket_id, "comment_count": count}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get comment count"
        )


@router.post("/tickets/{ticket_id}/system", response_model=TicketComment)
async def create_system_comment(
    ticket_id: int,
    content: str,
    event_type: str = "system",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_role: str = Depends(get_current_user_role)
):
    """Create a system-generated comment (admin only)"""
    
    try:
        # Only admins can create system comments
        if user_role not in ["admin", "super_admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators can create system comments"
            )
        
        comment_repo = CommentRepository(db)
        comment = await comment_repo.create_system_comment(
            ticket_id=ticket_id,
            content=content,
            event_type=event_type
        )
        
        return TicketComment.from_orm(comment)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create system comment"
        )


@router.get("/search", response_model=List[TicketCommentWithAuthor])
async def search_comments(
    search_term: str = Query(..., min_length=3, max_length=200),
    ticket_id: Optional[int] = Query(None),
    user_id: Optional[int] = Query(None),
    include_internal: bool = Query(False),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_role: str = Depends(get_current_user_role)
):
    """Search comments by content"""
    
    try:
        # Permission checks for internal comments
        if include_internal and user_role == "employee":
            include_internal = False  # Override for regular employees
        
        comment_repo = CommentRepository(db)
        comments = await comment_repo.search_comments(
            search_term=search_term,
            ticket_id=ticket_id,
            user_id=user_id,
            include_internal=include_internal,
            limit=limit
        )
        
        return [TicketCommentWithAuthor.from_orm(comment) for comment in comments]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search comments"
        )


@router.get("/tickets/{ticket_id}/thread", response_model=List[TicketCommentWithAuthor])
async def get_comment_thread(
    ticket_id: int,
    include_system: bool = Query(True),
    include_internal: bool = Query(False),
    sort_order: str = Query("asc", pattern="^(asc|desc)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_role: str = Depends(get_current_user_role)
):
    """Get complete comment thread for a ticket with filtering options"""
    
    try:
        comment_repo = CommentRepository(db)
        comments = await comment_repo.get_ticket_comments(
            ticket_id=ticket_id,
            user_id=current_user.id,
            user_role=user_role,
            include_internal=include_internal
        )
        
        # Filter system comments if requested
        if not include_system:
            comments = [c for c in comments if not c.is_system_generated]
        
        # Apply sorting
        if sort_order == "desc":
            comments = sorted(comments, key=lambda x: x.created_at, reverse=True)
        
        return [TicketCommentWithAuthor.from_orm(comment) for comment in comments]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve comment thread"
        )


@router.post("/bulk/create")
async def bulk_create_comments(
    comments_data: List[dict],  # List of {"ticket_id": int, "content": str, "is_internal": bool}
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_role: str = Depends(get_current_user_role)
):
    """Bulk create comments on multiple tickets"""
    
    try:
        if len(comments_data) > 20:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot create more than 20 comments at once"
            )
        
        comment_repo = CommentRepository(db)
        created_comments = []
        failed_comments = []
        
        for comment_data in comments_data:
            try:
                comment = await comment_repo.create_comment(
                    ticket_id=comment_data["ticket_id"],
                    author_id=current_user.id,
                    content=comment_data["content"],
                    is_internal=comment_data.get("is_internal", False)
                )
                created_comments.append(comment.id)
            except Exception as e:
                failed_comments.append({
                    "ticket_id": comment_data["ticket_id"],
                    "error": str(e)
                })
        
        return {
            "message": f"Created {len(created_comments)} comments",
            "successful_count": len(created_comments),
            "failed_count": len(failed_comments),
            "created_comment_ids": created_comments,
            "failed_comments": failed_comments
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to bulk create comments"
        )


@router.get("/statistics", response_model=dict)
async def get_comment_statistics(
    user_id: Optional[int] = Query(None),
    ticket_id: Optional[int] = Query(None),
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_role: str = Depends(get_current_user_role)
):
    """Get comment statistics"""
    
    try:
        # Permission checks
        if user_id and user_id != current_user.id:
            if user_role not in ["admin", "manager", "department_head"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to view other users' statistics"
                )
        
        # This would calculate various comment statistics
        # For now, returning basic structure
        return {
            "total_comments": 0,
            "internal_comments": 0,
            "public_comments": 0,
            "system_comments": 0,
            "average_comments_per_ticket": 0.0,
            "most_active_users": [],
            "comment_trends": []
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve comment statistics"
        )