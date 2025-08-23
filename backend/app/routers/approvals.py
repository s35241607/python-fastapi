"""
Approvals Router Module

This module provides FastAPI endpoints for approval workflow management including
workflow creation, step processing, delegation, escalation, and reporting.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.approval_service import ApprovalService
from app.schemas import (
    ApprovalWorkflowCreate, ApprovalWorkflowWithSteps, ApprovalActionRequest,
    ApprovalStepWithUser, ApprovalStep
)
from app.enums import ApprovalAction, ApprovalStepStatus, WorkflowStatus
from app.models import User

# Placeholder for authentication dependency
async def get_current_user() -> User:
    """Get current authenticated user - placeholder"""
    return User(id=1, email="user@example.com", username="testuser", 
               first_name="Test", last_name="User", role="manager")

async def get_current_user_role() -> str:
    """Get current user role - placeholder"""
    return "manager"

router = APIRouter(prefix="/api/v1/approvals", tags=["approvals"])


@router.post("/workflows", response_model=ApprovalWorkflowWithSteps, status_code=status.HTTP_201_CREATED)
async def create_approval_workflow(
    workflow_data: ApprovalWorkflowCreate,
    ticket_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new approval workflow for a ticket"""
    
    try:
        approval_service = ApprovalService(db)
        workflow = await approval_service.create_approval_workflow(
            workflow_data=workflow_data,
            ticket_id=ticket_id,
            initiated_by_id=current_user.id
        )
        
        # Get workflow with steps
        workflow_details = await approval_service.get_workflow_details(
            workflow.id, current_user.id
        )
        
        return workflow_details
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create approval workflow"
        )


@router.get("/workflows/{workflow_id}", response_model=ApprovalWorkflowWithSteps)
async def get_workflow_details(
    workflow_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get workflow details with all steps"""
    
    try:
        approval_service = ApprovalService(db)
        workflow_details = await approval_service.get_workflow_details(
            workflow_id, current_user.id
        )
        
        if not workflow_details:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow not found or access denied"
            )
        
        return workflow_details
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve workflow details"
        )


@router.post("/steps/{step_id}/process", response_model=ApprovalStep)
async def process_approval_step(
    step_id: int,
    action_request: ApprovalActionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Process an approval step (approve, reject, delegate, etc.)"""
    
    try:
        approval_service = ApprovalService(db)
        processed_step = await approval_service.process_approval_action(
            step_id=step_id,
            action_request=action_request,
            approver_id=current_user.id
        )
        
        return processed_step
        
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to process this approval step"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process approval step"
        )


@router.get("/pending", response_model=List[ApprovalStepWithUser])
async def get_pending_approvals(
    department_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_role: str = Depends(get_current_user_role)
):
    """Get pending approvals for current user"""
    
    try:
        approval_service = ApprovalService(db)
        pending_approvals = await approval_service.get_pending_approvals(
            user_id=current_user.id,
            user_role=user_role,
            department_id=department_id
        )
        
        return pending_approvals
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve pending approvals"
        )


@router.post("/steps/{step_id}/delegate", response_model=ApprovalStep)
async def delegate_approval(
    step_id: int,
    delegate_to_id: int,
    reason: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delegate an approval to another user"""
    
    try:
        approval_service = ApprovalService(db)
        delegated_step = await approval_service.delegate_approval(
            step_id=step_id,
            delegator_id=current_user.id,
            delegate_to_id=delegate_to_id,
            reason=reason
        )
        
        return delegated_step
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delegate approval"
        )


@router.post("/steps/{step_id}/request-info", response_model=ApprovalStep)
async def request_additional_info(
    step_id: int,
    info_request: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Request additional information for approval"""
    
    try:
        approval_service = ApprovalService(db)
        updated_step = await approval_service.request_additional_info(
            step_id=step_id,
            approver_id=current_user.id,
            info_request=info_request
        )
        
        return updated_step
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to request additional information"
        )


@router.delete("/workflows/{workflow_id}")
async def cancel_workflow(
    workflow_id: int,
    reason: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Cancel an approval workflow"""
    
    try:
        approval_service = ApprovalService(db)
        success = await approval_service.cancel_workflow(
            workflow_id=workflow_id,
            cancelled_by_id=current_user.id,
            reason=reason
        )
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workflow not found"
            )
        
        return {"message": "Workflow cancelled successfully"}
        
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to cancel this workflow"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to cancel workflow"
        )


@router.get("/overdue", response_model=List[ApprovalStep])
async def get_overdue_approvals(
    department_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_role: str = Depends(get_current_user_role)
):
    """Get overdue approval steps"""
    
    try:
        # Permission check for department-wide access
        if department_id and user_role not in ["admin", "manager", "department_head"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to view department overdue approvals"
            )
        
        from app.repositories.approval_repository import ApprovalRepository
        approval_repo = ApprovalRepository(db)
        
        overdue_approvals = await approval_repo.get_overdue_approvals(department_id)
        
        return overdue_approvals
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve overdue approvals"
        )


@router.post("/escalate-overdue")
async def escalate_overdue_approvals(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_role: str = Depends(get_current_user_role)
):
    """Manually trigger escalation of overdue approvals (admin only)"""
    
    try:
        # Admin only operation
        if user_role not in ["admin", "super_admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators can trigger escalation"
            )
        
        approval_service = ApprovalService(db)
        escalated_steps = await approval_service.escalate_overdue_approvals()
        
        return {
            "message": f"Escalated {len(escalated_steps)} overdue approval steps",
            "escalated_count": len(escalated_steps)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to escalate overdue approvals"
        )


@router.get("/statistics", response_model=dict)
async def get_approval_statistics(
    user_id: Optional[int] = Query(None),
    department_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_role: str = Depends(get_current_user_role)
):
    """Get approval workflow statistics"""
    
    try:
        # Permission checks
        if user_id and user_id != current_user.id:
            if user_role not in ["admin", "manager", "department_head"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to view other users' statistics"
                )
        
        approval_service = ApprovalService(db)
        statistics = await approval_service.get_approval_statistics(
            user_id=user_id,
            department_id=department_id
        )
        
        return statistics
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve approval statistics"
        )


@router.get("/tickets/{ticket_id}/history", response_model=List[ApprovalStep])
async def get_ticket_approval_history(
    ticket_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_role: str = Depends(get_current_user_role)
):
    """Get complete approval history for a ticket"""
    
    try:
        from app.repositories.approval_repository import ApprovalRepository
        approval_repo = ApprovalRepository(db)
        
        # Get approval history
        approval_history = await approval_repo.get_workflow_history(ticket_id)
        
        # Check if user has access to the ticket
        # This would typically involve checking ticket access permissions
        
        return approval_history
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve approval history"
        )


@router.get("/workflows/ticket/{ticket_id}", response_model=List[ApprovalWorkflowWithSteps])
async def get_ticket_workflows(
    ticket_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_role: str = Depends(get_current_user_role)
):
    """Get all workflows for a specific ticket"""
    
    try:
        from app.repositories.approval_repository import ApprovalRepository
        approval_repo = ApprovalRepository(db)
        
        workflows = await approval_repo.get_ticket_workflows(ticket_id)
        
        # Convert to response format with detailed steps
        workflow_details = []
        for workflow in workflows:
            details = await approval_repo.get_workflow_with_steps(workflow.id)
            if details:
                workflow_details.append(ApprovalWorkflowWithSteps.from_orm(details))
        
        return workflow_details
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve ticket workflows"
        )


@router.get("/users/{user_id}/performance", response_model=dict)
async def get_user_approval_performance(
    user_id: int,
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_role: str = Depends(get_current_user_role)
):
    """Get approval performance metrics for a user"""
    
    try:
        # Permission check
        if user_id != current_user.id:
            if user_role not in ["admin", "manager", "department_head"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to view other users' performance"
                )
        
        from datetime import datetime, timedelta
        date_from = datetime.utcnow() - timedelta(days=days)
        date_to = datetime.utcnow()
        
        from app.services.reporting_service import ReportingService
        reporting_service = ReportingService(db)
        
        performance_data = await reporting_service._get_user_approval_performance(
            user_id, date_from, date_to
        )
        
        return performance_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve approval performance"
        )


@router.post("/bulk/approve")
async def bulk_approve_steps(
    step_ids: List[int],
    comments: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Bulk approve multiple approval steps"""
    
    try:
        if len(step_ids) > 50:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot process more than 50 approvals at once"
            )
        
        approval_service = ApprovalService(db)
        action_request = ApprovalActionRequest(
            action=ApprovalAction.APPROVE,
            comments=comments
        )
        
        processed_steps = []
        failed_steps = []
        
        for step_id in step_ids:
            try:
                processed_step = await approval_service.process_approval_action(
                    step_id=step_id,
                    action_request=action_request,
                    approver_id=current_user.id
                )
                processed_steps.append(processed_step)
            except Exception as e:
                failed_steps.append({"step_id": step_id, "error": str(e)})
        
        return {
            "message": f"Processed {len(processed_steps)} approvals",
            "successful_count": len(processed_steps),
            "failed_count": len(failed_steps),
            "failed_steps": failed_steps
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process bulk approvals"
        )


@router.get("/my/queue", response_model=List[ApprovalStepWithUser])
async def get_my_approval_queue(
    priority_filter: Optional[List[str]] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_role: str = Depends(get_current_user_role)
):
    """Get personalized approval queue for current user"""
    
    try:
        approval_service = ApprovalService(db)
        pending_approvals = await approval_service.get_pending_approvals(
            user_id=current_user.id,
            user_role=user_role
        )
        
        # Apply priority filter if specified
        if priority_filter:
            filtered_approvals = []
            for approval in pending_approvals:
                if approval.workflow.ticket.priority.value in priority_filter:
                    filtered_approvals.append(approval)
            pending_approvals = filtered_approvals
        
        # Limit results
        return pending_approvals[:limit]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve approval queue"
        )