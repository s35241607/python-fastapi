"""
Approval workflow and step schemas for ticket approval processes.
"""
from .base import BaseModel, Field, validator, datetime, List, Optional, Dict, Any, Decimal
from .base import WorkflowType, WorkflowStatus, ApprovalAction, ApprovalStepStatus
from typing import TYPE_CHECKING
from pydantic import field_validator

if TYPE_CHECKING:
    from .user import User


# ============================================================================
# APPROVAL WORKFLOW SCHEMAS
# ============================================================================

class ApprovalWorkflowBase(BaseModel):
    workflow_name: str = Field(..., min_length=1, max_length=100)
    workflow_type: WorkflowType = WorkflowType.SEQUENTIAL
    workflow_config: Optional[Dict[str, Any]] = Field(default_factory=dict)
    auto_approve_threshold: Optional[Decimal] = Field(None, ge=0)
    escalation_timeout_hours: int = Field(default=24, ge=1, le=168)  # 1 hour to 1 week


class ApprovalWorkflowCreate(ApprovalWorkflowBase):
    approver_ids: List[int] = Field(..., min_length=1)  # List of approver user IDs


class ApprovalWorkflow(ApprovalWorkflowBase):
    id: int
    ticket_id: int
    status: WorkflowStatus
    initiated_by_id: int
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ApprovalWorkflowWithSteps(ApprovalWorkflow):
    steps: List['ApprovalStep'] = []
    initiated_by: "User"


# ============================================================================
# APPROVAL STEP SCHEMAS
# ============================================================================

class ApprovalStepBase(BaseModel):
    comments: Optional[str] = None


class ApprovalActionRequest(ApprovalStepBase):
    action: ApprovalAction
    delegated_to_id: Optional[int] = None
    escalated_to_id: Optional[int] = None

    @field_validator('delegated_to_id')
    @classmethod
    def validate_delegate(cls, v, values):
        if values.data.get('action') == ApprovalAction.DELEGATE and not v:
            raise ValueError('delegated_to_id is required when action is DELEGATE')
        return v

    @field_validator('escalated_to_id')
    @classmethod
    def validate_escalate(cls, v, values):
        if values.data.get('action') == ApprovalAction.ESCALATE and not v:
            raise ValueError('escalated_to_id is required when action is ESCALATE')
        return v


class ApprovalStep(ApprovalStepBase):
    id: int
    workflow_id: int
    approver_id: int
    step_order: int
    action: Optional[ApprovalAction] = None
    status: ApprovalStepStatus
    delegated_to_id: Optional[int] = None
    escalated_to_id: Optional[int] = None
    due_date: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ApprovalStepWithUser(ApprovalStep):
    approver: "User"
    delegated_to: Optional["User"] = None
    escalated_to: Optional["User"] = None
