"""
Attachment-related schemas for file uploads and management.
"""
from .base import BaseModel, Field, datetime, Optional
from .base import AttachmentType
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .user import User


# ============================================================================
# ATTACHMENT SCHEMAS
# ============================================================================

class TicketAttachmentBase(BaseModel):
    description: Optional[str] = None
    is_public: bool = True


class TicketAttachmentCreate(TicketAttachmentBase):
    filename: str = Field(..., min_length=1)
    file_size: int = Field(..., gt=0)
    mime_type: str = Field(..., min_length=1)
    attachment_type: AttachmentType = AttachmentType.OTHER


class TicketAttachment(TicketAttachmentBase):
    id: int
    ticket_id: int
    uploaded_by_id: int
    filename: str
    original_filename: str
    file_path: str
    file_size: int
    mime_type: str
    attachment_type: AttachmentType
    checksum: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class TicketAttachmentWithUploader(TicketAttachment):
    uploaded_by: "User"


class AttachmentResponse(TicketAttachment):
    """Alias for TicketAttachment for API responses"""
    pass


class AttachmentMetadata(BaseModel):
    """Attachment metadata for updates"""
    description: Optional[str] = None
    is_public: bool = True


class AttachmentUpdate(AttachmentMetadata):
    """Update data for attachments"""
    pass


class FileUploadResponse(BaseModel):
    """Response after file upload"""
    attachment_id: int
    filename: str
    file_size: int
    mime_type: str
    message: str = "File uploaded successfully"
