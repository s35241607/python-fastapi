"""
Ticket model for the ticket management system.
"""
from .base import Base, Column, Integer, String, Text, DateTime, ForeignKey, Enum, JSON, Numeric, relationship, func
from .base import TicketType, TicketStatus, Priority


class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    ticket_number = Column(String, unique=True, index=True, nullable=False)
    title = Column(String, nullable=False, index=True)
    description = Column(Text)
    ticket_type = Column(Enum(TicketType), nullable=False)
    status = Column(Enum(TicketStatus), default=TicketStatus.DRAFT, index=True)
    priority = Column(Enum(Priority), default=Priority.MEDIUM, index=True)
    requester_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    assignee_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    due_date = Column(DateTime(timezone=True), nullable=True)
    estimated_hours = Column(Numeric(8, 2), nullable=True)
    actual_hours = Column(Numeric(8, 2), nullable=True)
    cost_estimate = Column(Numeric(12, 2), nullable=True)
    custom_fields = Column(JSON, default=dict)
    tags = Column(JSON, default=list)
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    closed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    requester = relationship("User", foreign_keys=[requester_id], back_populates="created_tickets")
    assignee = relationship("User", foreign_keys=[assignee_id], back_populates="assigned_tickets")
    department = relationship("Department", back_populates="tickets")
    comments = relationship("TicketComment", back_populates="ticket", cascade="all, delete-orphan")
    attachments = relationship("TicketAttachment", back_populates="ticket", cascade="all, delete-orphan")
    workflows = relationship("ApprovalWorkflow", back_populates="ticket", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="ticket")
