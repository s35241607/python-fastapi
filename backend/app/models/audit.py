"""
Audit log model for tracking system changes and user actions.
"""
from .base import Base, Column, Integer, String, DateTime, ForeignKey, Enum, JSON, relationship, func
from .base import AuditEventType


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(Enum(AuditEventType), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=True)
    entity_type = Column(String)  # Type of entity affected (ticket, user, etc.)
    entity_id = Column(Integer)  # ID of the affected entity
    old_values = Column(JSON)  # Previous state
    new_values = Column(JSON)  # New state
    extra_metadata = Column(JSON, default=dict)  # Additional context
    ip_address = Column(String)
    user_agent = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)

    # Relationships
    user = relationship("User", back_populates="audit_logs")
    ticket = relationship("Ticket", back_populates="audit_logs")
