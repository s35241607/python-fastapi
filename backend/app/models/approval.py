"""
Approval workflow and step models for ticket approval processes.
"""
from .base import Base, Column, Integer, String, Text, DateTime, ForeignKey, Enum, JSON, Numeric, relationship, func
from .base import WorkflowType, WorkflowStatus, ApprovalAction, ApprovalStepStatus


class ApprovalWorkflow(Base):
    __tablename__ = "approval_workflows"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id"), nullable=False)
    workflow_name = Column(String, nullable=False)
    workflow_type = Column(Enum(WorkflowType), default=WorkflowType.SEQUENTIAL)
    status = Column(Enum(WorkflowStatus), default=WorkflowStatus.ACTIVE, index=True)
    workflow_config = Column(JSON, default=dict)  # Configuration for complex workflows
    auto_approve_threshold = Column(Numeric(12, 2), nullable=True)
    escalation_timeout_hours = Column(Integer, default=24)
    initiated_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    ticket = relationship("Ticket", back_populates="workflows")
    initiated_by = relationship("User")
    steps = relationship("ApprovalStep", back_populates="workflow", cascade="all, delete-orphan")


class ApprovalStep(Base):
    __tablename__ = "approval_steps"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("approval_workflows.id"), nullable=False)
    approver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    step_order = Column(Integer, nullable=False)  # Order in the approval sequence
    action = Column(Enum(ApprovalAction), nullable=True)
    status = Column(Enum(ApprovalStepStatus), default=ApprovalStepStatus.PENDING, index=True)
    comments = Column(Text)
    delegated_to_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    escalated_to_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    due_date = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    workflow = relationship("ApprovalWorkflow", back_populates="steps")
    approver = relationship("User", foreign_keys=[approver_id], back_populates="approval_steps")
    delegated_to = relationship("User", foreign_keys=[delegated_to_id])
    escalated_to = relationship("User", foreign_keys=[escalated_to_id])
