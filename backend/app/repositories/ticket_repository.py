"""
Ticket Repository Module

This module provides comprehensive data access layer for ticket management,
including CRUD operations, advanced search, filtering, and aggregation functions.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from decimal import Decimal

from sqlalchemy import and_, or_, func, text, desc, asc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.sql import Select

from app.repositories.base_repository import BaseRepository
from app.models import Ticket, User, Department, TicketComment, TicketAttachment, ApprovalWorkflow
from app.schemas import TicketFilter, PaginationParams, TicketStatistics
from app.enums import TicketStatus, Priority, TicketType


class TicketRepository(BaseRepository[Ticket]):
    """Repository for ticket management with advanced search and filtering"""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Ticket)

    async def create_ticket(self, ticket_data: dict, requester_id: int) -> Ticket:
        """Create a new ticket with auto-generated ticket number"""
        # Generate unique ticket number
        ticket_number = await self._generate_ticket_number()
        
        ticket = Ticket(
            ticket_number=ticket_number,
            requester_id=requester_id,
            **ticket_data
        )
        
        return await self.create(ticket)

    async def get_ticket_with_details(self, ticket_id: int) -> Optional[Ticket]:
        """Get ticket with all related data (requester, assignee, department, etc.)"""
        query = (
            select(Ticket)
            .options(
                joinedload(Ticket.requester),
                joinedload(Ticket.assignee),
                joinedload(Ticket.department),
                selectinload(Ticket.comments).joinedload(TicketComment.author),
                selectinload(Ticket.attachments),
                selectinload(Ticket.workflows)
            )
            .where(Ticket.id == ticket_id)
        )
        
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_ticket_by_number(self, ticket_number: str) -> Optional[Ticket]:
        """Get ticket by ticket number"""
        query = select(Ticket).where(Ticket.ticket_number == ticket_number)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def search_tickets(
        self, 
        filters: TicketFilter, 
        pagination: PaginationParams,
        user_id: Optional[int] = None,
        user_role: Optional[str] = None
    ) -> Tuple[List[Ticket], int]:
        """Advanced ticket search with filtering and pagination"""
        
        query = self._build_search_query(filters, user_id, user_role)
        count_query = self._build_count_query(filters, user_id, user_role)
        
        # Apply sorting
        query = self._apply_sorting(query, pagination.sort_by, pagination.sort_order)
        
        # Apply pagination
        offset = (pagination.page - 1) * pagination.size
        query = query.offset(offset).limit(pagination.size)
        
        # Load related data
        query = query.options(
            joinedload(Ticket.requester),
            joinedload(Ticket.assignee),
            joinedload(Ticket.department)
        )
        
        # Execute queries
        result = await self.session.execute(query)
        tickets = result.unique().scalars().all()
        
        count_result = await self.session.execute(count_query)
        total = count_result.scalar()
        
        return tickets, total

    async def get_user_tickets(
        self, 
        user_id: int, 
        ticket_type: str = "all",  # "created", "assigned", "all"
        status_filter: Optional[List[TicketStatus]] = None,
        limit: int = 50
    ) -> List[Ticket]:
        """Get tickets for a specific user"""
        query = select(Ticket)
        
        if ticket_type == "created":
            query = query.where(Ticket.requester_id == user_id)
        elif ticket_type == "assigned":
            query = query.where(Ticket.assignee_id == user_id)
        else:  # all
            query = query.where(
                or_(Ticket.requester_id == user_id, Ticket.assignee_id == user_id)
            )
        
        if status_filter:
            query = query.where(Ticket.status.in_(status_filter))
        
        query = query.options(
            joinedload(Ticket.requester),
            joinedload(Ticket.assignee),
            joinedload(Ticket.department)
        ).order_by(desc(Ticket.created_at)).limit(limit)
        
        result = await self.session.execute(query)
        return result.unique().scalars().all()

    async def get_overdue_tickets(self, department_id: Optional[int] = None) -> List[Ticket]:
        """Get tickets that are past their due date"""
        now = datetime.utcnow()
        query = (
            select(Ticket)
            .where(
                and_(
                    Ticket.due_date < now,
                    Ticket.status.in_([
                        TicketStatus.SUBMITTED,
                        TicketStatus.IN_REVIEW,
                        TicketStatus.APPROVED,
                        TicketStatus.IN_PROGRESS
                    ])
                )
            )
            .options(
                joinedload(Ticket.requester),
                joinedload(Ticket.assignee),
                joinedload(Ticket.department)
            )
        )
        
        if department_id:
            query = query.where(Ticket.department_id == department_id)
        
        result = await self.session.execute(query)
        return result.unique().scalars().all()

    async def get_tickets_pending_approval(self, user_id: int) -> List[Ticket]:
        """Get tickets with pending approvals for a user"""
        from app.models import ApprovalStep
        from app.enums import ApprovalStepStatus
        
        query = (
            select(Ticket)
            .join(ApprovalWorkflow, Ticket.id == ApprovalWorkflow.ticket_id)
            .join(ApprovalStep, ApprovalWorkflow.id == ApprovalStep.workflow_id)
            .where(
                and_(
                    ApprovalStep.approver_id == user_id,
                    ApprovalStep.status == ApprovalStepStatus.PENDING
                )
            )
            .options(
                joinedload(Ticket.requester),
                joinedload(Ticket.assignee),
                joinedload(Ticket.department)
            )
            .distinct()
        )
        
        result = await self.session.execute(query)
        return result.unique().scalars().all()

    async def get_ticket_statistics(
        self, 
        user_id: Optional[int] = None,
        department_id: Optional[int] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> TicketStatistics:
        """Generate ticket statistics for dashboard"""
        
        base_query = select(Ticket)
        filters = []
        
        if user_id:
            filters.append(
                or_(Ticket.requester_id == user_id, Ticket.assignee_id == user_id)
            )
        
        if department_id:
            filters.append(Ticket.department_id == department_id)
        
        if date_from:
            filters.append(Ticket.created_at >= date_from)
        
        if date_to:
            filters.append(Ticket.created_at <= date_to)
        
        if filters:
            base_query = base_query.where(and_(*filters))
        
        # Total tickets
        total_query = select(func.count(Ticket.id)).select_from(base_query.subquery())
        total_result = await self.session.execute(total_query)
        total_tickets = total_result.scalar() or 0
        
        # Status counts
        status_counts = {}
        for status in TicketStatus:
            status_query = base_query.where(Ticket.status == status)
            count_query = select(func.count(Ticket.id)).select_from(status_query.subquery())
            count_result = await self.session.execute(count_query)
            status_counts[status.value] = count_result.scalar() or 0
        
        # Priority counts
        priority_counts = {}
        for priority in Priority:
            priority_query = base_query.where(Ticket.priority == priority)
            count_query = select(func.count(Ticket.id)).select_from(priority_query.subquery())
            count_result = await self.session.execute(count_query)
            priority_counts[priority.value] = count_result.scalar() or 0
        
        # Type counts
        type_counts = {}
        for ticket_type in TicketType:
            type_query = base_query.where(Ticket.ticket_type == ticket_type)
            count_query = select(func.count(Ticket.id)).select_from(type_query.subquery())
            count_result = await self.session.execute(count_query)
            type_counts[ticket_type.value] = count_result.scalar() or 0
        
        # Overdue tickets
        now = datetime.utcnow()
        overdue_query = base_query.where(
            and_(
                Ticket.due_date < now,
                Ticket.status.in_([
                    TicketStatus.SUBMITTED,
                    TicketStatus.IN_REVIEW,
                    TicketStatus.APPROVED,
                    TicketStatus.IN_PROGRESS
                ])
            )
        )
        overdue_count_query = select(func.count(Ticket.id)).select_from(overdue_query.subquery())
        overdue_result = await self.session.execute(overdue_count_query)
        overdue_tickets = overdue_result.scalar() or 0
        
        # Average resolution time (in hours)
        resolution_query = base_query.where(
            and_(
                Ticket.resolved_at.isnot(None),
                Ticket.created_at.isnot(None)
            )
        )
        
        avg_query = select(
            func.avg(
                func.extract('epoch', Ticket.resolved_at - Ticket.created_at) / 3600
            )
        ).select_from(resolution_query.subquery())
        
        avg_result = await self.session.execute(avg_query)
        avg_resolution_time = avg_result.scalar()
        
        return TicketStatistics(
            total_tickets=total_tickets,
            open_tickets=status_counts.get(TicketStatus.SUBMITTED.value, 0) + 
                        status_counts.get(TicketStatus.IN_REVIEW.value, 0),
            in_progress_tickets=status_counts.get(TicketStatus.IN_PROGRESS.value, 0),
            resolved_tickets=status_counts.get(TicketStatus.COMPLETED.value, 0),
            overdue_tickets=overdue_tickets,
            avg_resolution_time_hours=float(avg_resolution_time) if avg_resolution_time else None,
            tickets_by_priority=priority_counts,
            tickets_by_type=type_counts,
            tickets_by_status=status_counts
        )

    async def update_ticket_status(
        self, 
        ticket_id: int, 
        new_status: TicketStatus,
        updated_by_id: int
    ) -> Optional[Ticket]:
        """Update ticket status with timestamp tracking"""
        update_data = {"status": new_status}
        
        # Set resolution/closure timestamps
        if new_status == TicketStatus.COMPLETED:
            update_data["resolved_at"] = datetime.utcnow()
        elif new_status == TicketStatus.CLOSED:
            update_data["closed_at"] = datetime.utcnow()
        
        return await self.update(ticket_id, **update_data)

    def _build_search_query(
        self, 
        filters: TicketFilter,
        user_id: Optional[int] = None,
        user_role: Optional[str] = None
    ) -> Select:
        """Build search query with filters"""
        query = select(Ticket)
        
        # Apply filters
        conditions = []
        
        if filters.status:
            conditions.append(Ticket.status.in_(filters.status))
        
        if filters.priority:
            conditions.append(Ticket.priority.in_(filters.priority))
        
        if filters.ticket_type:
            conditions.append(Ticket.ticket_type.in_(filters.ticket_type))
        
        if filters.requester_id:
            conditions.append(Ticket.requester_id == filters.requester_id)
        
        if filters.assignee_id:
            conditions.append(Ticket.assignee_id == filters.assignee_id)
        
        if filters.department_id:
            conditions.append(Ticket.department_id == filters.department_id)
        
        if filters.created_after:
            conditions.append(Ticket.created_at >= filters.created_after)
        
        if filters.created_before:
            conditions.append(Ticket.created_at <= filters.created_before)
        
        if filters.due_after:
            conditions.append(Ticket.due_date >= filters.due_after)
        
        if filters.due_before:
            conditions.append(Ticket.due_date <= filters.due_before)
        
        if filters.search_query:
            search_term = f"%{filters.search_query}%"
            conditions.append(
                or_(
                    Ticket.title.ilike(search_term),
                    Ticket.description.ilike(search_term),
                    Ticket.ticket_number.ilike(search_term)
                )
            )
        
        if filters.tags:
            # Search for tickets that have any of the specified tags
            tag_conditions = []
            for tag in filters.tags:
                tag_conditions.append(
                    func.json_extract(Ticket.tags, '$').op('LIKE')(f'%"{tag}"%')
                )
            conditions.append(or_(*tag_conditions))
        
        if filters.has_overdue:
            now = datetime.utcnow()
            if filters.has_overdue:
                conditions.append(
                    and_(
                        Ticket.due_date < now,
                        Ticket.status.in_([
                            TicketStatus.SUBMITTED,
                            TicketStatus.IN_REVIEW,
                            TicketStatus.APPROVED,
                            TicketStatus.IN_PROGRESS
                        ])
                    )
                )
            else:
                conditions.append(
                    or_(
                        Ticket.due_date >= now,
                        Ticket.due_date.is_(None),
                        Ticket.status.in_([
                            TicketStatus.COMPLETED,
                            TicketStatus.CLOSED,
                            TicketStatus.REJECTED
                        ])
                    )
                )
        
        # Apply role-based filtering
        if user_role == "employee" and user_id:
            # Employees can only see their own tickets
            conditions.append(
                or_(
                    Ticket.requester_id == user_id,
                    Ticket.assignee_id == user_id
                )
            )
        
        if conditions:
            query = query.where(and_(*conditions))
        
        return query

    def _build_count_query(
        self, 
        filters: TicketFilter,
        user_id: Optional[int] = None,
        user_role: Optional[str] = None
    ) -> Select:
        """Build count query for pagination"""
        base_query = self._build_search_query(filters, user_id, user_role)
        return select(func.count(Ticket.id)).select_from(base_query.subquery())

    def _apply_sorting(self, query: Select, sort_by: str, sort_order: str) -> Select:
        """Apply sorting to query"""
        sort_column = getattr(Ticket, sort_by, None)
        
        if sort_column is None:
            sort_column = Ticket.created_at
        
        if sort_order.lower() == "asc":
            query = query.order_by(asc(sort_column))
        else:
            query = query.order_by(desc(sort_column))
        
        return query

    async def _generate_ticket_number(self) -> str:
        """Generate unique ticket number with format: TICKET-YYYYMMDD-XXXX"""
        today = datetime.utcnow().strftime("%Y%m%d")
        prefix = f"TICKET-{today}"
        
        # Get the highest ticket number for today
        query = (
            select(Ticket.ticket_number)
            .where(Ticket.ticket_number.like(f"{prefix}%"))
            .order_by(desc(Ticket.ticket_number))
            .limit(1)
        )
        
        result = await self.session.execute(query)
        latest_number = result.scalar_one_or_none()
        
        if latest_number:
            # Extract sequence number and increment
            sequence = int(latest_number.split("-")[-1]) + 1
        else:
            sequence = 1
        
        return f"{prefix}-{sequence:04d}"