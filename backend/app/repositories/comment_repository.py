"""
Comment Repository Module

This module handles ticket comment management including
creation, retrieval, updates, and access control.
"""

from typing import List, Optional
from datetime import datetime

from sqlalchemy import and_, desc, asc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.repositories.base_repository import BaseRepository
from app.models import TicketComment, User, Ticket
from app.enums import UserRole


class CommentRepository(BaseRepository[TicketComment]):
    """Repository for managing ticket comments"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, TicketComment)

    async def create_comment(
        self,
        ticket_id: int,
        author_id: int,
        content: str,
        is_internal: bool = False,
        is_system_generated: bool = False
    ) -> TicketComment:
        """Create a new ticket comment"""
        comment = TicketComment(
            ticket_id=ticket_id,
            author_id=author_id,
            content=content,
            is_internal=is_internal,
            is_system_generated=is_system_generated
        )
        
        return await self.create(comment)

    async def get_ticket_comments(
        self,
        ticket_id: int,
        user_id: Optional[int] = None,
        user_role: Optional[str] = None,
        include_internal: bool = False
    ) -> List[TicketComment]:
        """Get all comments for a ticket with access control"""
        query = (
            select(TicketComment)
            .options(joinedload(TicketComment.author))
            .where(TicketComment.ticket_id == ticket_id)
        )
        
        # Apply access control
        if not include_internal or user_role == UserRole.EMPLOYEE.value:
            # Regular users can't see internal comments
            query = query.where(TicketComment.is_internal == False)
        
        # Order by creation time
        query = query.order_by(asc(TicketComment.created_at))
        
        result = await self.session.execute(query)
        return result.unique().scalars().all()

    async def get_comment_with_author(self, comment_id: int) -> Optional[TicketComment]:
        """Get comment with author information"""
        query = (
            select(TicketComment)
            .options(
                joinedload(TicketComment.author),
                joinedload(TicketComment.ticket)
            )
            .where(TicketComment.id == comment_id)
        )
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def update_comment(
        self,
        comment_id: int,
        author_id: int,
        content: str,
        is_internal: Optional[bool] = None
    ) -> Optional[TicketComment]:
        """Update a comment (only by original author or admin)"""
        comment = await self.get_comment_with_author(comment_id)
        
        if not comment:
            return None
        
        # Check permission (only author can edit their comments)
        if comment.author_id != author_id:
            return None
        
        # Don't allow editing system-generated comments
        if comment.is_system_generated:
            return None
        
        update_data = {"content": content}
        if is_internal is not None:
            update_data["is_internal"] = is_internal
        
        return await self.update(comment_id, **update_data)

    async def delete_comment(self, comment_id: int, user_id: int) -> bool:
        """Delete a comment (only by author or admin)"""
        comment = await self.get_comment_with_author(comment_id)
        
        if not comment:
            return False
        
        # Check permission
        if comment.author_id != user_id:
            # Check if user is admin (this would need user role check)
            return False
        
        # Don't allow deleting system-generated comments
        if comment.is_system_generated:
            return False
        
        return await self.delete(comment_id)

    async def get_recent_comments_by_user(
        self,
        user_id: int,
        limit: int = 20
    ) -> List[TicketComment]:
        """Get recent comments by a specific user"""
        query = (
            select(TicketComment)
            .options(
                joinedload(TicketComment.ticket),
                joinedload(TicketComment.author)
            )
            .where(TicketComment.author_id == user_id)
            .order_by(desc(TicketComment.created_at))
            .limit(limit)
        )
        
        result = await self.session.execute(query)
        return result.unique().scalars().all()

    async def get_comment_count_for_ticket(self, ticket_id: int) -> int:
        """Get total comment count for a ticket"""
        query = select(func.count(TicketComment.id)).where(
            TicketComment.ticket_id == ticket_id
        )
        
        result = await self.session.execute(query)
        return result.scalar() or 0

    async def create_system_comment(
        self,
        ticket_id: int,
        content: str,
        event_type: str = "system"
    ) -> TicketComment:
        """Create a system-generated comment for audit trail"""
        # Use a system user ID (you might want to create a dedicated system user)
        system_user_id = 1  # This should be configured properly
        
        comment = TicketComment(
            ticket_id=ticket_id,
            author_id=system_user_id,
            content=content,
            is_internal=True,
            is_system_generated=True
        )
        
        return await self.create(comment)

    async def search_comments(
        self,
        search_term: str,
        ticket_id: Optional[int] = None,
        user_id: Optional[int] = None,
        include_internal: bool = False,
        limit: int = 50
    ) -> List[TicketComment]:
        """Search comments by content"""
        query = (
            select(TicketComment)
            .options(
                joinedload(TicketComment.author),
                joinedload(TicketComment.ticket)
            )
        )
        
        # Apply search filter
        search_filter = TicketComment.content.ilike(f"%{search_term}%")
        query = query.where(search_filter)
        
        # Apply additional filters
        if ticket_id:
            query = query.where(TicketComment.ticket_id == ticket_id)
        
        if user_id:
            query = query.where(TicketComment.author_id == user_id)
        
        if not include_internal:
            query = query.where(TicketComment.is_internal == False)
        
        # Order by relevance (newest first)
        query = query.order_by(desc(TicketComment.created_at)).limit(limit)
        
        result = await self.session.execute(query)
        return result.unique().scalars().all()