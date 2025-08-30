"""
Comment model for ticket discussions.
"""
from .base import Base, Column, Integer, Text, Boolean, DateTime, ForeignKey, relationship, func


class TicketComment(Base):
    __tablename__ = "ticket_comments"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    is_internal = Column(Boolean, default=False)  # Internal comments only visible to staff
    is_system_generated = Column(Boolean, default=False)  # Auto-generated system comments
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    ticket = relationship("Ticket", back_populates="comments")
    author = relationship("User", back_populates="ticket_comments")
