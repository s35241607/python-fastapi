"""
Tickets Router Module

This module provides FastAPI endpoints for ticket management including
CRUD operations, search, filtering, and status management.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.ticket_service import TicketService
from app.auth.dependencies import (
    get_current_user, get_current_active_user, require_manager,
    get_user_context, get_current_user_role
)
from app.auth.rbac import Permission, PermissionChecker
from app.schemas import (
    TicketCreate, TicketUpdate, TicketDetail, TicketSummary,
    TicketFilter, PaginationParams, PaginatedResponse,
    TicketStatusUpdate, DashboardData, TicketStatistics
)
from app.enums import TicketStatus, Priority, TicketType
from app.models import User

router = APIRouter(prefix="/api/v1/tickets", tags=["tickets"])


@router.post("/", response_model=TicketDetail, status_code=status.HTTP_201_CREATED)
async def create_ticket(
    ticket_data: TicketCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_role: str = Depends(get_current_user_role)
):
    """Create a new ticket"""
    
    try:
        current_user = user_context["user"]
        
        # Check if user can create tickets
        permission_checker = PermissionChecker(current_user)
        if not permission_checker.has_permission(Permission.CREATE_TICKETS):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized to create tickets"
            )
        
        ticket_service = TicketService(db)
        ticket = await ticket_service.create_ticket(
            ticket_data=ticket_data,
            requester_id=current_user.id,
            auto_assign=True
        )
        
        # Get detailed ticket information
        ticket_detail = await ticket_service.get_ticket_details(
            ticket.id, current_user.id, current_user.role
        )
        
        return ticket_detail
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create ticket"
        )


@router.get("/", response_model=PaginatedResponse)
async def search_tickets(
    # Search filters
    status_filter: Optional[List[TicketStatus]] = Query(None, alias="status"),
    priority_filter: Optional[List[Priority]] = Query(None, alias="priority"),
    ticket_type_filter: Optional[List[TicketType]] = Query(None, alias="type"),
    requester_id: Optional[int] = Query(None),
    assignee_id: Optional[int] = Query(None),
    department_id: Optional[int] = Query(None),
    search_query: Optional[str] = Query(None, max_length=200),
    tags: Optional[List[str]] = Query(None),
    has_overdue: Optional[bool] = Query(None),
    has_pending_approvals: Optional[bool] = Query(None),
    
    # Pagination
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    
    # Dependencies
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_role: str = Depends(get_current_user_role)
):
    """Search and filter tickets with pagination"""
    
    try:
        current_user = user_context["user"]
        user_role = current_user.role
        
        # Build filter object
        filters = TicketFilter(
            status=status_filter,
            priority=priority_filter,
            ticket_type=ticket_type_filter,
            requester_id=requester_id,
            assignee_id=assignee_id,
            department_id=department_id,
            search_query=search_query,
            tags=tags,
            has_overdue=has_overdue,
            has_pending_approvals=has_pending_approvals
        )
        
        # Build pagination object
        pagination = PaginationParams(
            page=page,
            size=size,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        ticket_service = TicketService(db)
        tickets, total = await ticket_service.search_tickets(
            filters=filters,
            pagination=pagination,
            user_id=current_user.id,
            user_role=user_role
        )
        
        # Calculate pagination metadata
        pages = (total + size - 1) // size
        has_next = page < pages
        has_prev = page > 1
        
        return PaginatedResponse(
            items=tickets,
            total=total,
            page=page,
            size=size,
            pages=pages,
            has_next=has_next,
            has_prev=has_prev
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search tickets"
        )


@router.get("/{ticket_id}", response_model=TicketDetail)
async def get_ticket(
    ticket_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_role: str = Depends(get_current_user_role)
):
    """Get ticket details by ID"""
    
    try:
        current_user = user_context["user"]
        user_role = current_user.role
        
        ticket_service = TicketService(db)
        ticket_detail = await ticket_service.get_ticket_details(
            ticket_id=ticket_id,
            user_id=current_user.id,
            user_role=user_role
        )
        
        if not ticket_detail:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ticket not found"
            )
        
        return ticket_detail
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve ticket"
        )


@router.put("/{ticket_id}", response_model=TicketDetail)
async def update_ticket(
    ticket_id: int,
    ticket_data: TicketUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_role: str = Depends(get_current_user_role)
):
    """Update a ticket"""
    
    try:
        ticket_service = TicketService(db)
        updated_ticket = await ticket_service.update_ticket(
            ticket_id=ticket_id,
            ticket_data=ticket_data,
            updated_by_id=current_user.id,
            user_role=user_role
        )
        
        if not updated_ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ticket not found"
            )
        
        # Get updated ticket details
        ticket_detail = await ticket_service.get_ticket_details(
            ticket_id, current_user.id, user_role
        )
        
        return ticket_detail
        
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this ticket"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update ticket"
        )


@router.patch("/{ticket_id}/status", response_model=TicketDetail)
async def update_ticket_status(
    ticket_id: int,
    status_update: TicketStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_role: str = Depends(get_current_user_role)
):
    """Update ticket status"""
    
    try:
        ticket_service = TicketService(db)
        updated_ticket = await ticket_service.change_ticket_status(
            ticket_id=ticket_id,
            new_status=status_update.status,
            user_id=current_user.id,
            user_role=user_role,
            comment=status_update.comment
        )
        
        if not updated_ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ticket not found"
            )
        
        # Get updated ticket details
        ticket_detail = await ticket_service.get_ticket_details(
            ticket_id, current_user.id, user_role
        )
        
        return ticket_detail
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update ticket status"
        )


@router.post("/{ticket_id}/assign", response_model=TicketDetail)
async def assign_ticket(
    ticket_id: int,
    assignee_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_role: str = Depends(get_current_user_role)
):
    """Assign ticket to a user"""
    
    try:
        ticket_service = TicketService(db)
        updated_ticket = await ticket_service.assign_ticket(
            ticket_id=ticket_id,
            assignee_id=assignee_id,
            assigned_by_id=current_user.id,
            user_role=user_role
        )
        
        if not updated_ticket:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Ticket not found"
            )
        
        # Get updated ticket details
        ticket_detail = await ticket_service.get_ticket_details(
            ticket_id, current_user.id, user_role
        )
        
        return ticket_detail
        
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to assign this ticket"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to assign ticket"
        )


@router.get("/my/dashboard", response_model=DashboardData)
async def get_my_dashboard(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_role: str = Depends(get_current_user_role)
):
    """Get dashboard data for current user"""
    
    try:
        ticket_service = TicketService(db)
        dashboard_data = await ticket_service.get_user_dashboard_data(
            user_id=current_user.id,
            user_role=user_role,
            department_id=current_user.department_id
        )
        
        return dashboard_data
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve dashboard data"
        )


@router.get("/statistics/overview", response_model=TicketStatistics)
async def get_ticket_statistics(
    user_id: Optional[int] = Query(None),
    department_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_role: str = Depends(get_current_user_role)
):
    """Get ticket statistics"""
    
    try:
        # Permission check for accessing other users' statistics
        if user_id and user_id != current_user.id:
            if user_role not in ["admin", "manager", "department_head"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to view other users' statistics"
                )
        
        ticket_service = TicketService(db)
        from app.repositories.ticket_repository import TicketRepository
        
        ticket_repo = TicketRepository(db)
        statistics = await ticket_repo.get_ticket_statistics(
            user_id=user_id,
            department_id=department_id
        )
        
        return statistics
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve statistics"
        )


@router.get("/overdue/list", response_model=List[TicketSummary])
async def get_overdue_tickets(
    department_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_role: str = Depends(get_current_user_role)
):
    """Get overdue tickets"""
    
    try:
        ticket_service = TicketService(db)
        overdue_tickets = await ticket_service.get_overdue_tickets(
            user_id=current_user.id if user_role == "employee" else None,
            department_id=department_id
        )
        
        return overdue_tickets
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve overdue tickets"
        )


@router.post("/bulk/update", response_model=List[TicketDetail])
async def bulk_update_tickets(
    ticket_ids: List[int],
    update_data: TicketUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_role: str = Depends(get_current_user_role)
):
    """Bulk update multiple tickets"""
    
    try:
        if len(ticket_ids) > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot update more than 100 tickets at once"
            )
        
        ticket_service = TicketService(db)
        updated_tickets = await ticket_service.bulk_update_tickets(
            ticket_ids=ticket_ids,
            update_data=update_data,
            updated_by_id=current_user.id,
            user_role=user_role
        )
        
        # Get detailed information for updated tickets
        ticket_details = []
        for ticket in updated_tickets:
            detail = await ticket_service.get_ticket_details(
                ticket.id, current_user.id, user_role
            )
            if detail:
                ticket_details.append(detail)
        
        return ticket_details
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to bulk update tickets"
        )


@router.get("/user/{user_id}/tickets", response_model=List[TicketSummary])
async def get_user_tickets(
    user_id: int,
    ticket_type: str = Query("all", pattern="^(created|assigned|all)$"),
    status_filter: Optional[List[TicketStatus]] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_role: str = Depends(get_current_user_role)
):
    """Get tickets for a specific user"""
    
    try:
        # Permission check
        if user_id != current_user.id:
            if user_role not in ["admin", "manager", "department_head"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Not authorized to view other users' tickets"
                )
        
        ticket_service = TicketService(db)
        from app.repositories.ticket_repository import TicketRepository
        
        ticket_repo = TicketRepository(db)
        tickets = await ticket_repo.get_user_tickets(
            user_id=user_id,
            ticket_type=ticket_type,
            status_filter=status_filter,
            limit=limit
        )
        
        # Convert to summary format
        ticket_summaries = [TicketSummary.from_orm(ticket) for ticket in tickets]
        return ticket_summaries
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user tickets"
        )


# Additional utility endpoints

@router.get("/export/csv")
async def export_tickets_csv(
    # Same filter parameters as search endpoint
    status_filter: Optional[List[TicketStatus]] = Query(None, alias="status"),
    priority_filter: Optional[List[Priority]] = Query(None, alias="priority"),
    ticket_type_filter: Optional[List[TicketType]] = Query(None, alias="type"),
    requester_id: Optional[int] = Query(None),
    assignee_id: Optional[int] = Query(None),
    department_id: Optional[int] = Query(None),
    search_query: Optional[str] = Query(None, max_length=200),
    
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    user_role: str = Depends(get_current_user_role)
):
    """Export tickets to CSV format"""
    
    try:
        # Build filter object
        filters = TicketFilter(
            status=status_filter,
            priority=priority_filter,
            ticket_type=ticket_type_filter,
            requester_id=requester_id,
            assignee_id=assignee_id,
            department_id=department_id,
            search_query=search_query
        )
        
        # Use reporting service for export
        from app.services.reporting_service import ReportingService
        
        reporting_service = ReportingService(db)
        csv_data = await reporting_service.export_report_csv(
            report_type="tickets",
            filters=filters.dict(exclude_unset=True),
            include_details=True
        )
        
        from fastapi.responses import Response
        return Response(
            content=csv_data,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=tickets_export.csv"}
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to export tickets"
        )