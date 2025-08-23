"""
Approval Service Module

This module contains the business logic for approval workflow management including
workflow creation, step processing, escalation, and routing logic.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.approval_repository import ApprovalRepository
from app.repositories.ticket_repository import TicketRepository
from app.repositories.comment_repository import CommentRepository
from app.models import ApprovalWorkflow, ApprovalStep, Ticket, User, Department
from app.schemas import (
    ApprovalWorkflowCreate, ApprovalActionRequest, ApprovalWorkflowWithSteps,
    ApprovalStepWithUser, TicketStatistics
)
from app.enums import (
    ApprovalAction, ApprovalStepStatus, WorkflowStatus, WorkflowType,
    TicketStatus, TicketType, UserRole, Priority
)


class ApprovalService:
    """Service class for approval workflow management business logic"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.approval_repo = ApprovalRepository(session)
        self.ticket_repo = TicketRepository(session)
        self.comment_repo = CommentRepository(session)

    async def create_approval_workflow(
        self,
        workflow_data: ApprovalWorkflowCreate,
        ticket_id: int,
        initiated_by_id: int
    ) -> ApprovalWorkflow:
        """Create a new approval workflow with business logic"""
        
        # Get ticket details
        ticket = await self.ticket_repo.get_ticket_with_details(ticket_id)
        if not ticket:
            raise ValueError("Ticket not found")
        
        # Validate workflow creation
        await self._validate_workflow_creation(ticket, workflow_data, initiated_by_id)
        
        # Auto-determine approvers if not provided or enhance provided list
        if not workflow_data.approver_ids:
            workflow_data.approver_ids = await self._determine_approvers(ticket)
        else:
            # Validate provided approvers
            await self._validate_approvers(workflow_data.approver_ids, ticket)
        
        # Create the workflow
        workflow = await self.approval_repo.create_workflow(
            ticket_id=ticket_id,
            workflow_name=workflow_data.workflow_name,
            workflow_type=workflow_data.workflow_type,
            approver_ids=workflow_data.approver_ids,
            initiated_by_id=initiated_by_id,
            workflow_config=workflow_data.workflow_config,
            auto_approve_threshold=workflow_data.auto_approve_threshold,
            escalation_timeout_hours=workflow_data.escalation_timeout_hours
        )
        
        # Update ticket status
        await self.ticket_repo.update_ticket_status(
            ticket_id, TicketStatus.IN_REVIEW, initiated_by_id
        )
        
        # Create system comment
        await self.comment_repo.create_system_comment(
            ticket_id,
            f"Approval workflow '{workflow_data.workflow_name}' initiated with {len(workflow_data.approver_ids)} approvers"
        )
        
        # Check for auto-approval
        if workflow_data.auto_approve_threshold and ticket.cost_estimate:
            if ticket.cost_estimate <= workflow_data.auto_approve_threshold:
                await self._auto_approve_workflow(workflow.id, initiated_by_id)
        
        return workflow

    async def process_approval_action(
        self,
        step_id: int,
        action_request: ApprovalActionRequest,
        approver_id: int
    ) -> ApprovalStep:
        """Process an approval action with business logic"""
        
        # Validate the action
        step = await self.approval_repo.get_step_with_workflow(step_id)
        if not step:
            raise ValueError("Approval step not found")
        
        if step.approver_id != approver_id:
            raise PermissionError("User is not authorized to approve this step")
        
        if step.status != ApprovalStepStatus.PENDING:
            raise ValueError(f"Step is already {step.status.value}")
        
        # Validate action-specific requirements
        await self._validate_approval_action(step, action_request)
        
        # Process the action
        processed_step = await self.approval_repo.process_approval_step(
            step_id=step_id,
            action=action_request.action,
            approver_id=approver_id,
            comments=action_request.comments,
            delegated_to_id=action_request.delegated_to_id,
            escalated_to_id=action_request.escalated_to_id
        )
        
        # Create system comment
        await self._create_approval_comment(step, action_request, approver_id)
        
        # Handle post-action business logic
        await self._handle_post_approval_logic(processed_step, action_request)
        
        return processed_step

    async def get_pending_approvals(
        self,
        user_id: int,
        user_role: str,
        department_id: Optional[int] = None
    ) -> List[ApprovalStepWithUser]:
        """Get pending approvals for a user with access control"""
        
        # Get pending steps
        pending_steps = await self.approval_repo.get_pending_approvals_for_user(user_id)
        
        # For managers, also get department approvals
        if user_role in [UserRole.MANAGER.value, UserRole.DEPARTMENT_HEAD.value] and department_id:
            dept_approvals = await self._get_department_pending_approvals(department_id)
            pending_steps.extend(dept_approvals)
        
        # Convert to schema and add business logic data
        approval_steps = []
        for step in pending_steps:
            step_data = ApprovalStepWithUser.from_orm(step)
            
            # Add urgency indicators
            step_data.is_urgent = await self._is_approval_urgent(step)
            step_data.days_pending = (datetime.utcnow() - step.created_at).days
            
            approval_steps.append(step_data)
        
        # Sort by urgency and due date
        approval_steps.sort(key=lambda x: (not x.is_urgent, x.due_date or datetime.max))
        
        return approval_steps

    async def get_workflow_details(self, workflow_id: int, user_id: int) -> Optional[ApprovalWorkflowWithSteps]:
        """Get workflow details with access control"""
        
        workflow = await self.approval_repo.get_workflow_with_steps(workflow_id)
        if not workflow:
            return None
        
        # Check access permissions
        if not await self._can_access_workflow(workflow, user_id):
            return None
        
        # Convert to schema
        workflow_data = ApprovalWorkflowWithSteps.from_orm(workflow)
        
        # Add business logic data
        workflow_data.is_overdue = await self._is_workflow_overdue(workflow)
        workflow_data.completion_percentage = await self._calculate_completion_percentage(workflow)
        
        return workflow_data

    async def escalate_overdue_approvals(self) -> List[ApprovalStep]:
        """Automatically escalate overdue approval steps"""
        
        escalated_steps = await self.approval_repo.auto_escalate_overdue_steps()
        
        # Create notifications and comments for escalated steps
        for step in escalated_steps:
            await self.comment_repo.create_system_comment(
                step.workflow.ticket_id,
                f"Approval step escalated due to timeout. Original approver: {step.workflow.steps[0].approver.username}"
            )
        
        return escalated_steps

    async def cancel_workflow(
        self,
        workflow_id: int,
        cancelled_by_id: int,
        reason: Optional[str] = None
    ) -> bool:
        """Cancel an approval workflow"""
        
        workflow = await self.approval_repo.get_by_id(workflow_id)
        if not workflow:
            return False
        
        # Check permissions
        if not await self._can_cancel_workflow(workflow, cancelled_by_id):
            raise PermissionError("User cannot cancel this workflow")
        
        # Cancel the workflow
        success = await self.approval_repo.cancel_workflow(workflow_id)
        
        if success:
            # Update ticket status back to submitted
            await self.ticket_repo.update_ticket_status(
                workflow.ticket_id, TicketStatus.SUBMITTED, cancelled_by_id
            )
            
            # Create system comment
            comment = f"Approval workflow cancelled by user {cancelled_by_id}"
            if reason:
                comment += f": {reason}"
            
            await self.comment_repo.create_system_comment(
                workflow.ticket_id, comment
            )
        
        return success

    async def get_approval_statistics(
        self,
        user_id: Optional[int] = None,
        department_id: Optional[int] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get approval workflow statistics"""
        
        # This would calculate various metrics
        # For now, returning a basic structure
        return {
            "total_workflows": 0,
            "active_workflows": 0,
            "completed_workflows": 0,
            "average_approval_time_hours": 0.0,
            "approval_rate": 0.0,
            "escalation_rate": 0.0,
            "workflows_by_type": {},
            "approvals_by_user": {}
        }

    async def delegate_approval(
        self,
        step_id: int,
        delegator_id: int,
        delegate_to_id: int,
        reason: Optional[str] = None
    ) -> ApprovalStep:
        """Delegate an approval to another user"""
        
        action_request = ApprovalActionRequest(
            action=ApprovalAction.DELEGATE,
            delegated_to_id=delegate_to_id,
            comments=reason or "Approval delegated"
        )
        
        return await self.process_approval_action(step_id, action_request, delegator_id)

    async def request_additional_info(
        self,
        step_id: int,
        approver_id: int,
        info_request: str
    ) -> ApprovalStep:
        """Request additional information for approval"""
        
        action_request = ApprovalActionRequest(
            action=ApprovalAction.REQUEST_INFO,
            comments=info_request
        )
        
        step = await self.process_approval_action(step_id, action_request, approver_id)
        
        # Update ticket status to pending info
        workflow = step.workflow
        await self.ticket_repo.update_ticket_status(
            workflow.ticket_id, TicketStatus.PENDING_INFO, approver_id
        )
        
        return step

    # Private helper methods

    async def _validate_workflow_creation(
        self,
        ticket: Ticket,
        workflow_data: ApprovalWorkflowCreate,
        initiated_by_id: int
    ) -> None:
        """Validate workflow creation business rules"""
        
        # Check if ticket already has active workflow
        existing_workflows = await self.approval_repo.get_ticket_workflows(ticket.id)
        active_workflows = [w for w in existing_workflows if w.status == WorkflowStatus.ACTIVE]
        
        if active_workflows:
            raise ValueError("Ticket already has an active approval workflow")
        
        # Check if user can initiate workflow
        if ticket.requester_id != initiated_by_id:
            # Additional checks for managers/admins
            pass

    async def _determine_approvers(self, ticket: Ticket) -> List[int]:
        """Determine required approvers based on ticket properties"""
        
        approver_ids = []
        
        # Department manager approval
        if ticket.department and ticket.department.manager_id:
            approver_ids.append(ticket.department.manager_id)
        
        # Cost-based approvals
        if ticket.cost_estimate:
            if ticket.cost_estimate > Decimal('1000'):
                # Add finance approval
                pass
            if ticket.cost_estimate > Decimal('10000'):
                # Add executive approval
                pass
        
        # Type-based approvals
        if ticket.ticket_type in [TicketType.PROCUREMENT, TicketType.LEGAL]:
            # Add specialized approvers
            pass
        
        return approver_ids

    async def _validate_approvers(self, approver_ids: List[int], ticket: Ticket) -> None:
        """Validate that provided approvers are valid"""
        
        # Check if users exist and have appropriate roles
        for approver_id in approver_ids:
            # This would validate user exists and has approval permissions
            pass

    async def _validate_approval_action(
        self,
        step: ApprovalStep,
        action_request: ApprovalActionRequest
    ) -> None:
        """Validate approval action business rules"""
        
        # Check delegation permissions
        if action_request.action == ApprovalAction.DELEGATE:
            if not action_request.delegated_to_id:
                raise ValueError("Delegate user ID is required for delegation")
            
            # Check if delegate user is valid
            pass
        
        # Check escalation permissions
        if action_request.action == ApprovalAction.ESCALATE:
            if not action_request.escalated_to_id:
                raise ValueError("Escalation target is required")

    async def _create_approval_comment(
        self,
        step: ApprovalStep,
        action_request: ApprovalActionRequest,
        approver_id: int
    ) -> None:
        """Create system comment for approval action"""
        
        action_descriptions = {
            ApprovalAction.APPROVE: "approved",
            ApprovalAction.REJECT: "rejected",
            ApprovalAction.REQUEST_INFO: "requested additional information for",
            ApprovalAction.DELEGATE: "delegated",
            ApprovalAction.ESCALATE: "escalated"
        }
        
        action_desc = action_descriptions.get(action_request.action, "processed")
        comment = f"User {approver_id} {action_desc} the approval request"
        
        if action_request.comments:
            comment += f": {action_request.comments}"
        
        await self.comment_repo.create_system_comment(
            step.workflow.ticket_id, comment
        )

    async def _handle_post_approval_logic(
        self,
        step: ApprovalStep,
        action_request: ApprovalActionRequest
    ) -> None:
        """Handle business logic after approval action"""
        
        workflow = step.workflow
        
        # If rejected, update ticket status
        if action_request.action == ApprovalAction.REJECT:
            await self.ticket_repo.update_ticket_status(
                workflow.ticket_id, TicketStatus.REJECTED, step.approver_id
            )
        
        # Check if workflow is complete
        workflow_with_steps = await self.approval_repo.get_workflow_with_steps(workflow.id)
        if workflow_with_steps and workflow_with_steps.status == WorkflowStatus.COMPLETED:
            # All approvals complete - update ticket to approved
            await self.ticket_repo.update_ticket_status(
                workflow.ticket_id, TicketStatus.APPROVED, step.approver_id
            )

    async def _auto_approve_workflow(self, workflow_id: int, initiated_by_id: int) -> None:
        """Auto-approve workflow based on business rules"""
        
        workflow = await self.approval_repo.get_workflow_with_steps(workflow_id)
        if not workflow:
            return
        
        # Auto-approve all pending steps
        for step in workflow.steps:
            if step.status == ApprovalStepStatus.PENDING:
                await self.approval_repo.process_approval_step(
                    step.id,
                    ApprovalAction.APPROVE,
                    step.approver_id,
                    "Auto-approved based on threshold"
                )
        
        # Create system comment
        await self.comment_repo.create_system_comment(
            workflow.ticket_id,
            "Workflow auto-approved based on configured threshold"
        )

    async def _is_approval_urgent(self, step: ApprovalStep) -> bool:
        """Check if approval step is urgent"""
        
        # Check due date
        if step.due_date and step.due_date <= datetime.utcnow() + timedelta(hours=24):
            return True
        
        # Check ticket priority
        ticket = step.workflow.ticket
        if ticket.priority in [Priority.CRITICAL, Priority.HIGH]:
            return True
        
        return False

    async def _is_workflow_overdue(self, workflow: ApprovalWorkflow) -> bool:
        """Check if workflow is overdue"""
        
        # Check if any pending steps are overdue
        for step in workflow.steps:
            if step.status == ApprovalStepStatus.PENDING and step.due_date:
                if step.due_date < datetime.utcnow():
                    return True
        
        return False

    async def _calculate_completion_percentage(self, workflow: ApprovalWorkflow) -> float:
        """Calculate workflow completion percentage"""
        
        if not workflow.steps:
            return 0.0
        
        completed_steps = len([
            step for step in workflow.steps
            if step.status in [ApprovalStepStatus.APPROVED, ApprovalStepStatus.REJECTED]
        ])
        
        return (completed_steps / len(workflow.steps)) * 100

    async def _can_access_workflow(self, workflow: ApprovalWorkflow, user_id: int) -> bool:
        """Check if user can access workflow details"""
        
        # Ticket participants can access
        ticket = workflow.ticket
        if ticket.requester_id == user_id or ticket.assignee_id == user_id:
            return True
        
        # Approvers can access
        approver_ids = [step.approver_id for step in workflow.steps]
        if user_id in approver_ids:
            return True
        
        # Workflow initiator can access
        if workflow.initiated_by_id == user_id:
            return True
        
        return False

    async def _can_cancel_workflow(self, workflow: ApprovalWorkflow, user_id: int) -> bool:
        """Check if user can cancel workflow"""
        
        # Only initiator or admins can cancel
        return (
            workflow.initiated_by_id == user_id or
            workflow.ticket.requester_id == user_id
            # Add admin role check here
        )

    async def _get_department_pending_approvals(self, department_id: int) -> List[ApprovalStep]:
        """Get pending approvals for department"""
        
        # This would get approvals for tickets in the department
        # Implementation would involve joining with tickets and departments
        return []