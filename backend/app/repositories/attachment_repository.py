"""
Attachment Repository Module

This module handles ticket attachment management including
file upload, download, access control, and metadata management.
"""

import os
import hashlib
from typing import List, Optional, Dict, Any
from datetime import datetime

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.repositories.base_repository import BaseRepository
from app.models import TicketAttachment, User, Ticket
from app.enums import AttachmentType, UserRole


class AttachmentRepository(BaseRepository[TicketAttachment]):
    """Repository for managing ticket attachments"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, TicketAttachment)

    async def create_attachment(
        self,
        ticket_id: int,
        uploaded_by_id: int,
        filename: str,
        original_filename: str,
        file_path: str,
        file_size: int,
        mime_type: str,
        attachment_type: AttachmentType = AttachmentType.OTHER,
        description: Optional[str] = None,
        is_public: bool = True,
        file_content: Optional[bytes] = None
    ) -> TicketAttachment:
        """Create a new attachment record"""
        
        # Calculate checksum if file content is provided
        checksum = None
        if file_content:
            checksum = hashlib.sha256(file_content).hexdigest()
        
        attachment = TicketAttachment(
            ticket_id=ticket_id,
            uploaded_by_id=uploaded_by_id,
            filename=filename,
            original_filename=original_filename,
            file_path=file_path,
            file_size=file_size,
            mime_type=mime_type,
            attachment_type=attachment_type,
            description=description,
            is_public=is_public,
            checksum=checksum
        )
        
        return await self.create(attachment)

    async def get_ticket_attachments(
        self,
        ticket_id: int,
        user_id: Optional[int] = None,
        user_role: Optional[str] = None,
        include_private: bool = False
    ) -> List[TicketAttachment]:
        """Get all attachments for a ticket with access control"""
        query = (
            select(TicketAttachment)
            .options(joinedload(TicketAttachment.uploaded_by))
            .where(TicketAttachment.ticket_id == ticket_id)
        )
        
        # Apply access control
        if not include_private or user_role == UserRole.EMPLOYEE.value:
            query = query.where(TicketAttachment.is_public == True)
        
        # Order by upload time (newest first)
        query = query.order_by(desc(TicketAttachment.created_at))
        
        result = await self.session.execute(query)
        return result.unique().scalars().all()

    async def get_attachment_with_details(self, attachment_id: int) -> Optional[TicketAttachment]:
        """Get attachment with full details including uploader and ticket info"""
        query = (
            select(TicketAttachment)
            .options(
                joinedload(TicketAttachment.uploaded_by),
                joinedload(TicketAttachment.ticket)
            )
            .where(TicketAttachment.id == attachment_id)
        )
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def check_attachment_access(
        self,
        attachment_id: int,
        user_id: int,
        user_role: Optional[str] = None
    ) -> bool:
        """Check if user has access to view/download an attachment"""
        attachment = await self.get_attachment_with_details(attachment_id)
        
        if not attachment:
            return False
        
        # Admins and managers can access all attachments
        if user_role in [UserRole.ADMIN.value, UserRole.MANAGER.value, UserRole.DEPARTMENT_HEAD.value]:
            return True
        
        # Private attachments are only accessible to uploader and ticket participants
        if not attachment.is_public:
            ticket = attachment.ticket
            return (
                attachment.uploaded_by_id == user_id or
                ticket.requester_id == user_id or
                ticket.assignee_id == user_id
            )
        
        # Public attachments are accessible to anyone with ticket access
        return True

    async def update_attachment_metadata(
        self,
        attachment_id: int,
        user_id: int,
        description: Optional[str] = None,
        is_public: Optional[bool] = None
    ) -> Optional[TicketAttachment]:
        """Update attachment metadata (only by uploader or admin)"""
        attachment = await self.get_attachment_with_details(attachment_id)
        
        if not attachment:
            return None
        
        # Only uploader can modify their own attachments
        if attachment.uploaded_by_id != user_id:
            return None
        
        update_data = {}
        if description is not None:
            update_data["description"] = description
        if is_public is not None:
            update_data["is_public"] = is_public
        
        if update_data:
            return await self.update(attachment_id, **update_data)
        
        return attachment

    async def delete_attachment(
        self,
        attachment_id: int,
        user_id: int,
        user_role: Optional[str] = None
    ) -> bool:
        """Delete an attachment (only by uploader or admin)"""
        attachment = await self.get_attachment_with_details(attachment_id)
        
        if not attachment:
            return False
        
        # Check permission
        can_delete = (
            attachment.uploaded_by_id == user_id or
            user_role in [UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value]
        )
        
        if not can_delete:
            return False
        
        # Delete file from filesystem (if needed)
        if attachment.file_path and os.path.exists(attachment.file_path):
            try:
                os.remove(attachment.file_path)
            except OSError:
                pass  # File might be already deleted or inaccessible
        
        return await self.delete(attachment_id)

    async def get_attachments_by_type(
        self,
        attachment_type: AttachmentType,
        limit: int = 100
    ) -> List[TicketAttachment]:
        """Get attachments by type"""
        query = (
            select(TicketAttachment)
            .options(
                joinedload(TicketAttachment.uploaded_by),
                joinedload(TicketAttachment.ticket)
            )
            .where(TicketAttachment.attachment_type == attachment_type)
            .order_by(desc(TicketAttachment.created_at))
            .limit(limit)
        )
        
        result = await self.session.execute(query)
        return result.unique().scalars().all()

    async def get_user_attachments(
        self,
        user_id: int,
        limit: int = 50
    ) -> List[TicketAttachment]:
        """Get attachments uploaded by a specific user"""
        query = (
            select(TicketAttachment)
            .options(joinedload(TicketAttachment.ticket))
            .where(TicketAttachment.uploaded_by_id == user_id)
            .order_by(desc(TicketAttachment.created_at))
            .limit(limit)
        )
        
        result = await self.session.execute(query)
        return result.unique().scalars().all()

    async def get_attachment_statistics(
        self,
        ticket_id: Optional[int] = None,
        user_id: Optional[int] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get attachment statistics"""
        
        base_query = select(TicketAttachment)
        filters = []
        
        if ticket_id:
            filters.append(TicketAttachment.ticket_id == ticket_id)
        
        if user_id:
            filters.append(TicketAttachment.uploaded_by_id == user_id)
        
        if date_from:
            filters.append(TicketAttachment.created_at >= date_from)
        
        if date_to:
            filters.append(TicketAttachment.created_at <= date_to)
        
        if filters:
            base_query = base_query.where(and_(*filters))
        
        # Total count
        count_query = select(func.count(TicketAttachment.id)).select_from(base_query.subquery())
        count_result = await self.session.execute(count_query)
        total_count = count_result.scalar() or 0
        
        # Total size
        size_query = select(func.sum(TicketAttachment.file_size)).select_from(base_query.subquery())
        size_result = await self.session.execute(size_query)
        total_size = size_result.scalar() or 0
        
        # Count by type
        type_counts = {}
        for att_type in AttachmentType:
            type_query = base_query.where(TicketAttachment.attachment_type == att_type)
            type_count_query = select(func.count(TicketAttachment.id)).select_from(type_query.subquery())
            type_result = await self.session.execute(type_count_query)
            type_counts[att_type.value] = type_result.scalar() or 0
        
        return {
            "total_count": total_count,
            "total_size_bytes": int(total_size),
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "count_by_type": type_counts
        }

    async def search_attachments(
        self,
        search_term: str,
        ticket_id: Optional[int] = None,
        attachment_type: Optional[AttachmentType] = None,
        user_id: Optional[int] = None,
        limit: int = 50
    ) -> List[TicketAttachment]:
        """Search attachments by filename or description"""
        query = (
            select(TicketAttachment)
            .options(
                joinedload(TicketAttachment.uploaded_by),
                joinedload(TicketAttachment.ticket)
            )
        )
        
        # Search in filename, original filename, and description
        search_filter = or_(
            TicketAttachment.filename.ilike(f"%{search_term}%"),
            TicketAttachment.original_filename.ilike(f"%{search_term}%"),
            TicketAttachment.description.ilike(f"%{search_term}%")
        )
        query = query.where(search_filter)
        
        # Apply additional filters
        if ticket_id:
            query = query.where(TicketAttachment.ticket_id == ticket_id)
        
        if attachment_type:
            query = query.where(TicketAttachment.attachment_type == attachment_type)
        
        if user_id:
            query = query.where(TicketAttachment.uploaded_by_id == user_id)
        
        # Order by relevance (newest first)
        query = query.order_by(desc(TicketAttachment.created_at)).limit(limit)
        
        result = await self.session.execute(query)
        return result.unique().scalars().all()

    async def verify_attachment_integrity(self, attachment_id: int) -> bool:
        """Verify attachment file integrity using checksum"""
        attachment = await self.get_by_id(attachment_id)
        
        if not attachment or not attachment.checksum or not attachment.file_path:
            return False
        
        if not os.path.exists(attachment.file_path):
            return False
        
        try:
            with open(attachment.file_path, 'rb') as f:
                file_content = f.read()
                calculated_checksum = hashlib.sha256(file_content).hexdigest()
                return calculated_checksum == attachment.checksum
        except (OSError, IOError):
            return False

    async def cleanup_orphaned_attachments(self) -> int:
        """Clean up attachment records where files no longer exist"""
        query = select(TicketAttachment)
        result = await self.session.execute(query)
        attachments = result.scalars().all()
        
        deleted_count = 0
        for attachment in attachments:
            if attachment.file_path and not os.path.exists(attachment.file_path):
                await self.delete(attachment.id)
                deleted_count += 1
        
        return deleted_count