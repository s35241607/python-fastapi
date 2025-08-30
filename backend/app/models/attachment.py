"""
Attachment model for file uploads on tickets.
"""
from .base import Base, Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Enum, relationship, func
from .base import AttachmentType


class TicketAttachment(Base):
    __tablename__ = "ticket_attachments"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False)
    uploaded_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    filename = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    file_size = Column(Integer, nullable=False)  # Size in bytes
    mime_type = Column(String, nullable=False)
    attachment_type = Column(Enum(AttachmentType), default=AttachmentType.OTHER)
    description = Column(Text)
    is_public = Column(Boolean, default=True)  # Public attachments visible to requester
    checksum = Column(String)  # File integrity verification
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    ticket = relationship("Ticket", back_populates="attachments")
    uploaded_by = relationship("User")
