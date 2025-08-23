"""
Approval Repository Module

This module handles approval workflow and step management,
including workflow creation, step processing, and escalation logic.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from sqlalchemy import and_, or_, func, desc, asc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from app.repositories.base_repository import BaseRepository
from app.models import ApprovalWorkflow, ApprovalStep, Ticket, User
from app.enums import (
    ApprovalStepStatus, WorkflowStatus, ApprovalAction,
    WorkflowType, TicketStatus
)


class ApprovalRepository(BaseRepository[ApprovalWorkflow]):
    """Repository for managing approval workflows and steps"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, ApprovalWorkflow)

    async def create_workflow(
        self,
        ticket_id: int,
        workflow_name: str,
        workflow_type: WorkflowType,
        approver_ids: List[int],
        initiated_by_id: int,
        workflow_config: Optional[Dict[str, Any]] = None,
        auto_approve_threshold: Optional[float] = None,
        escalation_timeout_hours: int = 24
    ) -> ApprovalWorkflow:
        """Create a new approval workflow with steps"""
        
        workflow = ApprovalWorkflow(
            ticket_id=ticket_id,
            workflow_name=workflow_name,
            workflow_type=workflow_type,
            workflow_config=workflow_config or {},
            auto_approve_threshold=auto_approve_threshold,
            escalation_timeout_hours=escalation_timeout_hours,
            initiated_by_id=initiated_by_id,
            status=WorkflowStatus.ACTIVE
        )
        
        workflow = await self.create(workflow)
        
        # Create approval steps based on workflow type
        await self._create_approval_steps(workflow.id, approver_ids, workflow_type)
        
        return workflow

    async def get_workflow_with_steps(self, workflow_id: int) -> Optional[ApprovalWorkflow]:
        """Get workflow with all related steps and user data"""
        query = (
            select(ApprovalWorkflow)
            .options(
                selectinload(ApprovalWorkflow.steps).selectinload(ApprovalStep.approver),
                selectinload(ApprovalWorkflow.steps).selectinload(ApprovalStep.delegated_to),
                selectinload(ApprovalWorkflow.steps).selectinload(ApprovalStep.escalated_to),
                joinedload(ApprovalWorkflow.ticket),
                joinedload(ApprovalWorkflow.initiated_by)
            )
            .where(ApprovalWorkflow.id == workflow_id)
        )
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_ticket_workflows(self, ticket_id: int) -> List[ApprovalWorkflow]:
        """Get all workflows for a ticket"""
        query = (
            select(ApprovalWorkflow)
            .options(
                selectinload(ApprovalWorkflow.steps).selectinload(ApprovalStep.approver)
            )
            .where(ApprovalWorkflow.ticket_id == ticket_id)
            .order_by(desc(ApprovalWorkflow.created_at))
        )
        
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_pending_approvals_for_user(
        self, 
        user_id: int,
        limit: int = 50
    ) -> List[ApprovalStep]:
        """Get pending approval steps for a specific user"""
        query = (
            select(ApprovalStep)
            .options(
                joinedload(ApprovalStep.workflow).joinedload(ApprovalWorkflow.ticket),
                joinedload(ApprovalStep.approver)
            )
            .where(
                and_(
                    ApprovalStep.approver_id == user_id,
                    ApprovalStep.status == ApprovalStepStatus.PENDING
                )
            )
            .order_by(asc(ApprovalStep.due_date))
            .limit(limit)
        )
        
        result = await self.session.execute(query)
        return result.unique().scalars().all()

    async def get_overdue_approvals(
        self, 
        department_id: Optional[int] = None
    ) -> List[ApprovalStep]:
        """Get approval steps that are overdue"""
        now = datetime.utcnow()
        
        query = (
            select(ApprovalStep)
            .options(
                joinedload(ApprovalStep.workflow).joinedload(ApprovalWorkflow.ticket),
                joinedload(ApprovalStep.approver)
            )
            .where(
                and_(
                    ApprovalStep.status == ApprovalStepStatus.PENDING,
                    ApprovalStep.due_date < now
                )
            )
        )
        
        if department_id:
            query = query.join(ApprovalWorkflow).join(Ticket).where(
                Ticket.department_id == department_id
            )
        
        result = await self.session.execute(query)
        return result.unique().scalars().all()

    async def process_approval_step(
        self,
        step_id: int,
        action: ApprovalAction,
        approver_id: int,
        comments: Optional[str] = None,
        delegated_to_id: Optional[int] = None,
        escalated_to_id: Optional[int] = None
    ) -> Optional[ApprovalStep]:
        """Process an approval step and update workflow status"""
        
        # Get the step with workflow
        step = await self.get_step_with_workflow(step_id)
        if not step or step.approver_id != approver_id:
            return None
        
        # Update step based on action
        update_data = {
            "action": action,
            "comments": comments,
            "completed_at": datetime.utcnow()
        }
        
        if action == ApprovalAction.APPROVE:
            update_data["status"] = ApprovalStepStatus.APPROVED
        elif action == ApprovalAction.REJECT:
            update_data["status"] = ApprovalStepStatus.REJECTED
        elif action == ApprovalAction.REQUEST_INFO:
            update_data["status"] = ApprovalStepStatus.PENDING
            # Don't set completed_at for info requests
            del update_data["completed_at"]
        elif action == ApprovalAction.DELEGATE:
            update_data["status"] = ApprovalStepStatus.DELEGATED
            update_data["delegated_to_id"] = delegated_to_id
            # Create new step for delegated user
            await self._create_delegated_step(step, delegated_to_id)
        elif action == ApprovalAction.ESCALATE:
            update_data["status"] = ApprovalStepStatus.ESCALATED
            update_data["escalated_to_id"] = escalated_to_id
            # Create new step for escalated user
            await self._create_escalated_step(step, escalated_to_id)
        
        # Update the step
        updated_step = await self._update_step(step_id, **update_data)
        
        # Check if workflow is complete and update accordingly
        await self._check_and_update_workflow_status(step.workflow_id)
        
        return updated_step

    async def auto_escalate_overdue_steps(self) -> List[ApprovalStep]:
        """Automatically escalate overdue approval steps"""
        overdue_steps = await self.get_overdue_approvals()
        escalated_steps = []
        
        for step in overdue_steps:
            workflow = step.workflow
            
            # Find escalation target (department manager or next level)
            escalation_target = await self._find_escalation_target(step)
            
            if escalation_target:
                # Create escalated step
                escalated_step = await self._create_escalated_step(step, escalation_target.id)
                
                # Mark original step as escalated
                await self._update_step(
                    step.id,
                    status=ApprovalStepStatus.ESCALATED,
                    escalated_to_id=escalation_target.id,
                    completed_at=datetime.utcnow()
                )
                
                escalated_steps.append(escalated_step)
        
        return escalated_steps

    async def get_workflow_history(self, ticket_id: int) -> List[ApprovalStep]:
        """Get complete approval history for a ticket"""
        query = (
            select(ApprovalStep)
            .join(ApprovalWorkflow)
            .options(
                joinedload(ApprovalStep.approver),
                joinedload(ApprovalStep.delegated_to),
                joinedload(ApprovalStep.escalated_to),
                joinedload(ApprovalStep.workflow)
            )
            .where(ApprovalWorkflow.ticket_id == ticket_id)
            .order_by(asc(ApprovalStep.created_at))
        )
        
        result = await self.session.execute(query)
        return result.unique().scalars().all()

    async def cancel_workflow(self, workflow_id: int) -> bool:
        """Cancel an active workflow"""
        workflow = await self.get_by_id(workflow_id)
        if not workflow or workflow.status != WorkflowStatus.ACTIVE:
            return False
        
        # Update workflow status
        await self.update(workflow_id, status=WorkflowStatus.CANCELLED)
        
        # Cancel all pending steps
        await self._cancel_pending_steps(workflow_id)
        
        return True

    async def get_step_with_workflow(self, step_id: int) -> Optional[ApprovalStep]:
        """Get approval step with workflow data"""
        query = (
            select(ApprovalStep)
            .options(
                joinedload(ApprovalStep.workflow),
                joinedload(ApprovalStep.approver)
            )
            .where(ApprovalStep.id == step_id)
        )
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    # Private helper methods

    async def _create_approval_steps(
        self,
        workflow_id: int,
        approver_ids: List[int],
        workflow_type: WorkflowType
    ) -> None:
        """Create approval steps based on workflow type"""
        
        for i, approver_id in enumerate(approver_ids):
            # Calculate due date based on workflow timeout
            workflow = await self.get_by_id(workflow_id)
            due_date = datetime.utcnow() + timedelta(hours=workflow.escalation_timeout_hours)
            
            step = ApprovalStep(
                workflow_id=workflow_id,
                approver_id=approver_id,
                step_order=i + 1,
                status=ApprovalStepStatus.PENDING,
                due_date=due_date
            )
            
            self.session.add(step)
        
        await self.session.flush()

    async def _create_delegated_step(
        self, 
        original_step: ApprovalStep, 
        delegated_to_id: int
    ) -> ApprovalStep:
        """Create a new step for delegated approval"""
        new_step = ApprovalStep(
            workflow_id=original_step.workflow_id,
            approver_id=delegated_to_id,
            step_order=original_step.step_order,
            status=ApprovalStepStatus.PENDING,
            due_date=original_step.due_date,
            comments=f"Delegated from user {original_step.approver_id}"
        )
        
        self.session.add(new_step)
        await self.session.flush()
        return new_step

    async def _create_escalated_step(
        self, 
        original_step: ApprovalStep, 
        escalated_to_id: int
    ) -> ApprovalStep:
        """Create a new step for escalated approval"""
        # Shorter timeout for escalated approvals
        escalation_due = datetime.utcnow() + timedelta(hours=12)
        
        new_step = ApprovalStep(
            workflow_id=original_step.workflow_id,
            approver_id=escalated_to_id,
            step_order=original_step.step_order,
            status=ApprovalStepStatus.PENDING,
            due_date=escalation_due,
            comments=f"Escalated from user {original_step.approver_id}"
        )
        
        self.session.add(new_step)
        await self.session.flush()
        return new_step

    async def _update_step(self, step_id: int, **kwargs) -> Optional[ApprovalStep]:
        """Update approval step"""
        from app.models import ApprovalStep
        
        await self.session.execute(
            select(ApprovalStep)
            .where(ApprovalStep.id == step_id)
            .update(kwargs)
        )
        
        # Return updated step
        result = await self.session.execute(
            select(ApprovalStep).where(ApprovalStep.id == step_id)
        )
        return result.scalar_one_or_none()

    async def _check_and_update_workflow_status(self, workflow_id: int) -> None:
        """Check if workflow is complete and update status accordingly"""
        workflow = await self.get_workflow_with_steps(workflow_id)
        if not workflow:
            return
        
        # Get all steps for this workflow
        steps = workflow.steps
        
        # Check if any step is rejected
        if any(step.status == ApprovalStepStatus.REJECTED for step in steps):
            await self.update(workflow_id, 
                            status=WorkflowStatus.COMPLETED,
                            completed_at=datetime.utcnow())
            # Update ticket status to rejected
            await self._update_ticket_status(workflow.ticket_id, TicketStatus.REJECTED)
            return
        
        # For sequential workflows, check if current step is approved
        if workflow.workflow_type == WorkflowType.SEQUENTIAL:
            # Find the current pending step
            pending_steps = [s for s in steps if s.status == ApprovalStepStatus.PENDING]
            
            if not pending_steps:
                # All steps completed
                await self.update(workflow_id,
                                status=WorkflowStatus.COMPLETED,
                                completed_at=datetime.utcnow())
                await self._update_ticket_status(workflow.ticket_id, TicketStatus.APPROVED)
        
        # For parallel workflows, check if all steps are approved
        elif workflow.workflow_type == WorkflowType.PARALLEL:
            approved_steps = [s for s in steps if s.status == ApprovalStepStatus.APPROVED]
            
            if len(approved_steps) == len(steps):
                await self.update(workflow_id,
                                status=WorkflowStatus.COMPLETED,
                                completed_at=datetime.utcnow())
                await self._update_ticket_status(workflow.ticket_id, TicketStatus.APPROVED)

    async def _cancel_pending_steps(self, workflow_id: int) -> None:
        """Cancel all pending steps for a workflow"""
        from app.models import ApprovalStep
        
        await self.session.execute(
            select(ApprovalStep)
            .where(
                and_(
                    ApprovalStep.workflow_id == workflow_id,
                    ApprovalStep.status == ApprovalStepStatus.PENDING
                )
            )
            .update({"status": ApprovalStepStatus.SKIPPED})
        )

    async def _find_escalation_target(self, step: ApprovalStep) -> Optional[User]:
        """Find appropriate escalation target for a step"""
        # This is a simplified escalation logic
        # In practice, this would be more sophisticated based on org structure
        
        # Try to find department manager
        ticket = step.workflow.ticket
        if ticket.department and ticket.department.manager_id:
            manager_query = select(User).where(User.id == ticket.department.manager_id)
            result = await self.session.execute(manager_query)
            return result.scalar_one_or_none()
        
        # Fallback to admin users
        admin_query = select(User).where(User.role == "admin").limit(1)
        result = await self.session.execute(admin_query)
        return result.scalar_one_or_none()

    async def _update_ticket_status(self, ticket_id: int, status: TicketStatus) -> None:
        """Update ticket status"""
        from app.models import Ticket
        
        await self.session.execute(
            select(Ticket)
            .where(Ticket.id == ticket_id)
            .update({"status": status})
        )