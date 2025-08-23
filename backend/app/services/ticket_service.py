"""
Ticket Service Module

This module contains the business logic for ticket management including
creation, updates, status transitions, validation, and workflow integration.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.ticket_repository import TicketRepository
from app.repositories.comment_repository import CommentRepository
from app.repositories.approval_repository import ApprovalRepository
from app.models import Ticket, User
from app.schemas import (
    TicketCreate, TicketUpdate, TicketFilter, PaginationParams,
    TicketStatistics, DashboardData, TicketSummary, TicketDetail
)
from app.enums import TicketStatus, Priority, TicketType, UserRole, WorkflowType


class TicketService:
    """Service class for ticket management business logic"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.ticket_repo = TicketRepository(session)
        self.comment_repo = CommentRepository(session)
        self.approval_repo = ApprovalRepository(session)

    async def create_ticket(
        self,
        ticket_data: TicketCreate,
        requester_id: int,
        auto_assign: bool = True
    ) -> Ticket:
        """Create a new ticket with business logic validation"""
        
        # Validate ticket data
        await self._validate_ticket_creation(ticket_data, requester_id)
        
        # Prepare ticket data
        ticket_dict = ticket_data.dict(exclude_unset=True)
        
        # Auto-assign if enabled and no assignee specified
        if auto_assign and not ticket_dict.get('assignee_id'):
            assignee_id = await self._auto_assign_ticket(ticket_data.ticket_type, ticket_data.department_id)
            if assignee_id:
                ticket_dict['assignee_id'] = assignee_id
        
        # Set initial status
        ticket_dict['status'] = TicketStatus.SUBMITTED
        
        # Create the ticket
        ticket = await self.ticket_repo.create_ticket(ticket_dict, requester_id)
        
        # Create system comment for ticket creation
        await self.comment_repo.create_system_comment(
            ticket.id,
            f"Ticket created with priority {ticket.priority.value} and type {ticket.ticket_type.value}"
        )
        
        # Check if approval workflow is needed
        if await self._requires_approval(ticket):
            await self._initiate_approval_workflow(ticket)
        
        return ticket

    async def update_ticket(
        self,
        ticket_id: int,
        ticket_data: TicketUpdate,
        updated_by_id: int,
        user_role: str
    ) -> Optional[Ticket]:
        """Update a ticket with business logic validation"""
        
        # Get existing ticket
        existing_ticket = await self.ticket_repo.get_ticket_with_details(ticket_id)
        if not existing_ticket:
            return None
        
        # Check permissions
        if not await self._can_update_ticket(existing_ticket, updated_by_id, user_role):
            raise PermissionError("User does not have permission to update this ticket")
        
        # Validate update data
        await self._validate_ticket_update(existing_ticket, ticket_data, updated_by_id, user_role)
        
        # Prepare update data
        update_dict = ticket_data.dict(exclude_unset=True)
        
        # Handle status changes
        if 'status' in update_dict:
            new_status = update_dict['status']
            if not await self._can_change_status(existing_ticket, new_status, user_role):
                raise ValueError(f"Cannot change status from {existing_ticket.status} to {new_status}")
            
            # Record status change
            await self.comment_repo.create_system_comment(
                ticket_id,
                f"Status changed from {existing_ticket.status.value} to {new_status.value} by user {updated_by_id}"
            )
        
        # Handle assignee changes
        if 'assignee_id' in update_dict and update_dict['assignee_id'] != existing_ticket.assignee_id:
            await self.comment_repo.create_system_comment(
                ticket_id,
                f"Ticket reassigned to user {update_dict['assignee_id']} by user {updated_by_id}"
            )
        
        # Update the ticket
        updated_ticket = await self.ticket_repo.update(ticket_id, **update_dict)
        
        return updated_ticket

    async def get_ticket_details(
        self,
        ticket_id: int,
        user_id: int,
        user_role: str
    ) -> Optional[TicketDetail]:
        """Get ticket details with access control"""
        
        ticket = await self.ticket_repo.get_ticket_with_details(ticket_id)
        if not ticket:
            return None
        
        # Check access permissions
        if not await self._can_access_ticket(ticket, user_id, user_role):
            return None
        
        # Get additional data
        comments_count = await self.comment_repo.get_comment_count_for_ticket(ticket_id)
        
        # Check for pending approvals
        workflows = await self.approval_repo.get_ticket_workflows(ticket_id)
        has_pending_approvals = any(
            workflow.status.value == 'active' for workflow in workflows
        )
        
        # Convert to TicketDetail schema
        ticket_detail = TicketDetail.from_orm(ticket)
        ticket_detail.comments_count = comments_count
        ticket_detail.has_pending_approvals = has_pending_approvals
        
        return ticket_detail

    async def search_tickets(
        self,
        filters: TicketFilter,
        pagination: PaginationParams,
        user_id: int,
        user_role: str
    ) -> Tuple[List[TicketSummary], int]:
        """Search tickets with business logic and access control"""
        
        tickets, total = await self.ticket_repo.search_tickets(
            filters, pagination, user_id, user_role
        )
        
        # Convert to TicketSummary
        ticket_summaries = [TicketSummary.from_orm(ticket) for ticket in tickets]
        
        return ticket_summaries, total

    async def assign_ticket(
        self,
        ticket_id: int,
        assignee_id: int,
        assigned_by_id: int,
        user_role: str
    ) -> Optional[Ticket]:
        """Assign ticket to a user"""
        
        ticket = await self.ticket_repo.get_by_id(ticket_id)
        if not ticket:
            return None
        
        # Check permissions
        if not await self._can_assign_ticket(ticket, assigned_by_id, user_role):
            raise PermissionError("User does not have permission to assign this ticket")
        
        # Update assignment
        updated_ticket = await self.ticket_repo.update(
            ticket_id,
            assignee_id=assignee_id
        )
        
        # Create system comment
        await self.comment_repo.create_system_comment(
            ticket_id,
            f"Ticket assigned to user {assignee_id} by user {assigned_by_id}"
        )
        
        return updated_ticket

    async def change_ticket_status(
        self,
        ticket_id: int,
        new_status: TicketStatus,
        user_id: int,
        user_role: str,
        comment: Optional[str] = None
    ) -> Optional[Ticket]:
        """Change ticket status with business rules"""
        
        ticket = await self.ticket_repo.get_by_id(ticket_id)
        if not ticket:
            return None
        
        # Validate status change
        if not await self._can_change_status(ticket, new_status, user_role):
            raise ValueError(f"Cannot change status from {ticket.status} to {new_status}")
        
        # Update status with timestamps
        updated_ticket = await self.ticket_repo.update_ticket_status(
            ticket_id, new_status, user_id
        )
        
        # Create comment for status change
        status_comment = f"Status changed to {new_status.value}"
        if comment:
            status_comment += f": {comment}"
        
        await self.comment_repo.create_system_comment(ticket_id, status_comment)
        
        return updated_ticket

    async def get_user_dashboard_data(
        self,
        user_id: int,
        user_role: str,
        department_id: Optional[int] = None
    ) -> DashboardData:
        """Get dashboard data for a user"""
        
        # Get statistics
        statistics = await self.ticket_repo.get_ticket_statistics(
            user_id=user_id if user_role == UserRole.EMPLOYEE.value else None,
            department_id=department_id
        )
        
        # Get recent tickets
        recent_tickets = await self.ticket_repo.get_user_tickets(
            user_id, "all", limit=10
        )
        recent_summaries = [TicketSummary.from_orm(ticket) for ticket in recent_tickets]
        
        # Get pending approvals
        pending_approval_steps = await self.approval_repo.get_pending_approvals_for_user(
            user_id, limit=10
        )
        
        # Get my tickets
        my_tickets = await self.ticket_repo.get_user_tickets(
            user_id, "created", limit=10
        )
        my_summaries = [TicketSummary.from_orm(ticket) for ticket in my_tickets]
        
        # Get urgent tickets
        urgent_filter = TicketFilter(
            priority=[Priority.CRITICAL, Priority.HIGH],
            status=[TicketStatus.SUBMITTED, TicketStatus.IN_REVIEW, TicketStatus.IN_PROGRESS]
        )
        urgent_pagination = PaginationParams(page=1, size=10)
        urgent_tickets, _ = await self.ticket_repo.search_tickets(
            urgent_filter, urgent_pagination, user_id, user_role
        )
        urgent_summaries = [TicketSummary.from_orm(ticket) for ticket in urgent_tickets]
        
        return DashboardData(
            statistics=statistics,
            recent_tickets=recent_summaries,
            pending_approvals=pending_approval_steps,
            my_tickets=my_summaries,
            urgent_tickets=urgent_summaries
        )

    async def get_overdue_tickets(
        self,
        user_id: Optional[int] = None,
        department_id: Optional[int] = None
    ) -> List[TicketSummary]:
        """Get overdue tickets"""
        
        tickets = await self.ticket_repo.get_overdue_tickets(department_id)
        return [TicketSummary.from_orm(ticket) for ticket in tickets]

    async def bulk_update_tickets(
        self,
        ticket_ids: List[int],
        update_data: TicketUpdate,
        updated_by_id: int,
        user_role: str
    ) -> List[Ticket]:
        """Bulk update multiple tickets"""
        
        updated_tickets = []
        
        for ticket_id in ticket_ids:
            try:
                updated_ticket = await self.update_ticket(
                    ticket_id, update_data, updated_by_id, user_role
                )
                if updated_ticket:
                    updated_tickets.append(updated_ticket)
            except (PermissionError, ValueError):
                # Skip tickets that can't be updated
                continue
        
        return updated_tickets

    # Private helper methods

    async def _validate_ticket_creation(self, ticket_data: TicketCreate, requester_id: int) -> None:
        """Validate ticket creation data"""
        
        # Check if department exists and user has access
        if ticket_data.department_id:
            # This would check department existence and user access
            pass
        
        # Check if assignee exists and can be assigned
        if ticket_data.assignee_id:
            # This would validate assignee
            pass
        
        # Validate business rules (e.g., budget limits, approval requirements)
        if ticket_data.cost_estimate and ticket_data.cost_estimate > Decimal('10000'):
            # High-cost tickets might need special handling
            pass

    async def _validate_ticket_update(
        self,
        existing_ticket: Ticket,
        update_data: TicketUpdate,
        updated_by_id: int,
        user_role: str
    ) -> None:
        """Validate ticket update data"""
        
        # Validate status transitions
        if update_data.status and update_data.status != existing_ticket.status:
            valid_transitions = await self._get_valid_status_transitions(
                existing_ticket.status, user_role
            )
            if update_data.status not in valid_transitions:
                raise ValueError(f"Invalid status transition from {existing_ticket.status} to {update_data.status}")

    async def _can_update_ticket(self, ticket: Ticket, user_id: int, user_role: str) -> bool:
        """Check if user can update the ticket"""
        
        # Admins can update any ticket
        if user_role in [UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value]:
            return True
        
        # Managers can update tickets in their department
        if user_role == UserRole.MANAGER.value:
            # This would check department manager relationship
            return True
        
        # Users can update their own tickets (with limitations)
        if ticket.requester_id == user_id or ticket.assignee_id == user_id:
            return True
        
        return False

    async def _can_access_ticket(self, ticket: Ticket, user_id: int, user_role: str) -> bool:
        """Check if user can access the ticket"""
        
        # Admins can access any ticket
        if user_role in [UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value]:
            return True
        
        # Managers can access tickets in their department
        if user_role in [UserRole.MANAGER.value, UserRole.DEPARTMENT_HEAD.value]:
            # This would check department access
            return True
        
        # Users can access tickets they created or are assigned to
        if ticket.requester_id == user_id or ticket.assignee_id == user_id:
            return True
        
        return False

    async def _can_assign_ticket(self, ticket: Ticket, user_id: int, user_role: str) -> bool:
        """Check if user can assign the ticket"""
        
        return user_role in [
            UserRole.ADMIN.value,
            UserRole.SUPER_ADMIN.value,
            UserRole.MANAGER.value,
            UserRole.DEPARTMENT_HEAD.value
        ]

    async def _can_change_status(self, ticket: Ticket, new_status: TicketStatus, user_role: str) -> bool:
        """Check if status change is allowed"""
        
        # Define valid status transitions based on current status and user role
        status_transitions = {
            TicketStatus.DRAFT: [TicketStatus.SUBMITTED],
            TicketStatus.SUBMITTED: [TicketStatus.IN_REVIEW, TicketStatus.REJECTED],
            TicketStatus.IN_REVIEW: [TicketStatus.APPROVED, TicketStatus.REJECTED, TicketStatus.PENDING_INFO],
            TicketStatus.PENDING_INFO: [TicketStatus.IN_REVIEW],
            TicketStatus.APPROVED: [TicketStatus.IN_PROGRESS],
            TicketStatus.IN_PROGRESS: [TicketStatus.COMPLETED],
            TicketStatus.COMPLETED: [TicketStatus.CLOSED],
            TicketStatus.REJECTED: [TicketStatus.CLOSED],
        }
        
        # Admins can make any transition
        if user_role in [UserRole.ADMIN.value, UserRole.SUPER_ADMIN.value]:
            return True
        
        # Check if transition is valid
        valid_transitions = status_transitions.get(ticket.status, [])
        return new_status in valid_transitions

    async def _get_valid_status_transitions(self, current_status: TicketStatus, user_role: str) -> List[TicketStatus]:
        """Get valid status transitions for current status and user role"""
        
        # This would return valid transitions based on business rules
        # Implementation would be similar to _can_change_status but return list
        return []

    async def _auto_assign_ticket(self, ticket_type: TicketType, department_id: Optional[int]) -> Optional[int]:
        """Auto-assign ticket based on type and department"""
        
        # This would implement assignment logic based on:
        # - Ticket type (IT tickets to IT department, etc.)
        # - Department workload
        # - User availability
        # - Round-robin assignment
        
        return None

    async def _requires_approval(self, ticket: Ticket) -> bool:
        """Check if ticket requires approval workflow"""
        
        # Check approval requirements based on:
        # - Ticket type
        # - Cost estimate
        # - Department rules
        # - Priority level
        
        if ticket.cost_estimate and ticket.cost_estimate > Decimal('1000'):
            return True
        
        if ticket.ticket_type in [TicketType.PROCUREMENT, TicketType.FINANCE]:
            return True
        
        return False

    async def _initiate_approval_workflow(self, ticket: Ticket) -> None:
        """Initiate approval workflow for ticket"""
        
        # Determine approvers based on ticket properties
        approver_ids = await self._get_required_approvers(ticket)
        
        if approver_ids:
            workflow_type = WorkflowType.SEQUENTIAL  # Default to sequential
            
            await self.approval_repo.create_workflow(
                ticket_id=ticket.id,
                workflow_name=f"Approval for {ticket.ticket_type.value}",
                workflow_type=workflow_type,
                approver_ids=approver_ids,
                initiated_by_id=ticket.requester_id
            )
            
            # Update ticket status
            await self.ticket_repo.update_ticket_status(
                ticket.id, TicketStatus.IN_REVIEW, ticket.requester_id
            )

    async def _get_required_approvers(self, ticket: Ticket) -> List[int]:
        """Get list of required approvers for ticket"""
        
        approver_ids = []
        
        # Add department manager if exists
        if ticket.department and ticket.department.manager_id:
            approver_ids.append(ticket.department.manager_id)
        
        # Add additional approvers based on cost
        if ticket.cost_estimate and ticket.cost_estimate > Decimal('5000'):
            # Would add finance team or higher management
            pass
        
        return approver_ids