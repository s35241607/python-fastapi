import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.services.ticket_service import TicketService
from app.models import Ticket, User, Department, TicketComment, TicketAttachment
from app.schemas import TicketCreate, TicketUpdate, TicketFilters
from app.enums import TicketStatus, Priority, TicketType


class TestTicketService:
    """Comprehensive unit tests for TicketService"""

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session"""
        session = Mock(spec=AsyncSession)
        session.add = Mock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        session.execute = AsyncMock()
        session.scalar = AsyncMock()
        session.delete = Mock()
        return session

    @pytest.fixture
    def mock_ticket_repo(self):
        """Mock ticket repository"""
        return Mock()

    @pytest.fixture
    def mock_user_repo(self):
        """Mock user repository"""
        return Mock()

    @pytest.fixture
    def mock_notification_service(self):
        """Mock notification service"""
        return Mock()

    @pytest.fixture
    def ticket_service(self, mock_db_session, mock_ticket_repo, mock_user_repo, mock_notification_service):
        """Create TicketService instance with mocked dependencies"""
        service = TicketService(mock_db_session)
        service.ticket_repo = mock_ticket_repo
        service.user_repo = mock_user_repo
        service.notification_service = mock_notification_service
        return service

    @pytest.fixture
    def mock_user(self):
        """Mock user object"""
        return User(
            id=1,
            email="test@example.com",
            username="testuser",
            first_name="Test",
            last_name="User",
            department_id=1,
            is_active=True
        )

    @pytest.fixture
    def mock_ticket(self):
        """Mock ticket object"""
        return Ticket(
            id=1,
            ticket_number="TKT-001",
            title="Test Ticket",
            description="Test description",
            status=TicketStatus.OPEN,
            priority=Priority.MEDIUM,
            ticket_type=TicketType.INCIDENT,
            created_by_id=1,
            department_id=1,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

    @pytest.fixture
    def valid_ticket_create(self):
        """Valid ticket creation data"""
        return TicketCreate(
            title="New Test Ticket",
            description="New test description",
            priority=Priority.HIGH,
            ticket_type=TicketType.REQUEST,
            department_id=1,
            tags=["urgent", "system"]
        )

    @pytest.fixture
    def valid_ticket_update(self):
        """Valid ticket update data"""
        return TicketUpdate(
            title="Updated Ticket Title",
            description="Updated description",
            priority=Priority.LOW,
            status=TicketStatus.IN_PROGRESS
        )

    # Ticket Creation Tests
    @pytest.mark.asyncio
    async def test_create_ticket_success(self, ticket_service, valid_ticket_create, mock_user, mock_ticket_repo, mock_notification_service):
        """Test successful ticket creation"""
        # Mock repository response
        created_ticket = Ticket(
            id=1,
            ticket_number="TKT-001",
            title=valid_ticket_create.title,
            description=valid_ticket_create.description,
            priority=valid_ticket_create.priority,
            ticket_type=valid_ticket_create.ticket_type,
            status=TicketStatus.OPEN,
            created_by_id=mock_user.id,
            department_id=valid_ticket_create.department_id
        )
        mock_ticket_repo.create.return_value = created_ticket
        
        # Mock ticket number generation
        with patch.object(ticket_service, '_generate_ticket_number', return_value="TKT-001"):
            result = await ticket_service.create_ticket(valid_ticket_create, mock_user)
        
        assert result.title == valid_ticket_create.title
        assert result.created_by_id == mock_user.id
        assert result.status == TicketStatus.OPEN
        mock_ticket_repo.create.assert_called_once()
        mock_notification_service.send_ticket_created_notification.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_ticket_with_assignee(self, ticket_service, valid_ticket_create, mock_user, mock_ticket_repo, mock_user_repo):
        """Test ticket creation with assignee"""
        assignee = User(id=2, username="assignee", email="assignee@example.com")
        valid_ticket_create.assigned_to_id = assignee.id
        
        # Mock user repository
        mock_user_repo.get_by_id.return_value = assignee
        
        created_ticket = Ticket(
            id=1,
            ticket_number="TKT-001",
            assigned_to_id=assignee.id,
            **valid_ticket_create.dict()
        )
        mock_ticket_repo.create.return_value = created_ticket
        
        with patch.object(ticket_service, '_generate_ticket_number', return_value="TKT-001"):
            result = await ticket_service.create_ticket(valid_ticket_create, mock_user)
        
        assert result.assigned_to_id == assignee.id
        mock_user_repo.get_by_id.assert_called_once_with(assignee.id)

    @pytest.mark.asyncio
    async def test_create_ticket_invalid_assignee(self, ticket_service, valid_ticket_create, mock_user, mock_user_repo):
        """Test ticket creation with invalid assignee"""
        valid_ticket_create.assigned_to_id = 999
        mock_user_repo.get_by_id.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            await ticket_service.create_ticket(valid_ticket_create, mock_user)
        
        assert exc_info.value.status_code == 400
        assert "Assigned user not found" in str(exc_info.value.detail)

    # Ticket Retrieval Tests
    @pytest.mark.asyncio
    async def test_get_ticket_by_id_success(self, ticket_service, mock_ticket, mock_ticket_repo):
        """Test successful ticket retrieval by ID"""
        mock_ticket_repo.get_by_id.return_value = mock_ticket
        
        result = await ticket_service.get_ticket_by_id(1)
        
        assert result == mock_ticket
        mock_ticket_repo.get_by_id.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_get_ticket_by_id_not_found(self, ticket_service, mock_ticket_repo):
        """Test ticket retrieval with non-existent ID"""
        mock_ticket_repo.get_by_id.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            await ticket_service.get_ticket_by_id(999)
        
        assert exc_info.value.status_code == 404
        assert "Ticket not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_get_ticket_by_number_success(self, ticket_service, mock_ticket, mock_ticket_repo):
        """Test successful ticket retrieval by number"""
        mock_ticket_repo.get_by_number.return_value = mock_ticket
        
        result = await ticket_service.get_ticket_by_number("TKT-001")
        
        assert result == mock_ticket
        mock_ticket_repo.get_by_number.assert_called_once_with("TKT-001")

    # Ticket Update Tests
    @pytest.mark.asyncio
    async def test_update_ticket_success(self, ticket_service, mock_ticket, valid_ticket_update, mock_user, mock_ticket_repo, mock_notification_service):
        """Test successful ticket update"""
        mock_ticket_repo.get_by_id.return_value = mock_ticket
        updated_ticket = Ticket(**{**mock_ticket.__dict__, **valid_ticket_update.dict(exclude_unset=True)})
        mock_ticket_repo.update.return_value = updated_ticket
        
        result = await ticket_service.update_ticket(1, valid_ticket_update, mock_user)
        
        assert result.title == valid_ticket_update.title
        mock_ticket_repo.update.assert_called_once()
        mock_notification_service.send_ticket_updated_notification.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_ticket_status_change(self, ticket_service, mock_ticket, mock_user, mock_ticket_repo, mock_notification_service):
        """Test ticket update with status change"""
        status_update = TicketUpdate(status=TicketStatus.RESOLVED)
        mock_ticket_repo.get_by_id.return_value = mock_ticket
        
        updated_ticket = Ticket(**{**mock_ticket.__dict__, "status": TicketStatus.RESOLVED})
        mock_ticket_repo.update.return_value = updated_ticket
        
        result = await ticket_service.update_ticket(1, status_update, mock_user)
        
        assert result.status == TicketStatus.RESOLVED
        mock_notification_service.send_ticket_status_changed_notification.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_ticket_unauthorized(self, ticket_service, mock_ticket, valid_ticket_update, mock_ticket_repo):
        """Test ticket update by unauthorized user"""
        unauthorized_user = User(id=999, username="unauthorized")
        mock_ticket_repo.get_by_id.return_value = mock_ticket
        
        with patch.object(ticket_service, '_can_modify_ticket', return_value=False):
            with pytest.raises(HTTPException) as exc_info:
                await ticket_service.update_ticket(1, valid_ticket_update, unauthorized_user)
        
        assert exc_info.value.status_code == 403
        assert "Permission denied" in str(exc_info.value.detail)

    # Ticket Assignment Tests
    @pytest.mark.asyncio
    async def test_assign_ticket_success(self, ticket_service, mock_ticket, mock_user, mock_ticket_repo, mock_user_repo, mock_notification_service):
        """Test successful ticket assignment"""
        assignee = User(id=2, username="assignee")
        mock_ticket_repo.get_by_id.return_value = mock_ticket
        mock_user_repo.get_by_id.return_value = assignee
        
        assigned_ticket = Ticket(**{**mock_ticket.__dict__, "assigned_to_id": assignee.id})
        mock_ticket_repo.update.return_value = assigned_ticket
        
        result = await ticket_service.assign_ticket(1, assignee.id, mock_user)
        
        assert result.assigned_to_id == assignee.id
        mock_notification_service.send_ticket_assigned_notification.assert_called_once()

    @pytest.mark.asyncio
    async def test_assign_ticket_invalid_assignee(self, ticket_service, mock_ticket, mock_user, mock_ticket_repo, mock_user_repo):
        """Test ticket assignment to invalid user"""
        mock_ticket_repo.get_by_id.return_value = mock_ticket
        mock_user_repo.get_by_id.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            await ticket_service.assign_ticket(1, 999, mock_user)
        
        assert exc_info.value.status_code == 400
        assert "Assignee not found" in str(exc_info.value.detail)

    # Ticket Search and Filtering Tests
    @pytest.mark.asyncio
    async def test_search_tickets_success(self, ticket_service, mock_ticket_repo):
        """Test successful ticket search"""
        filters = TicketFilters(
            status=[TicketStatus.OPEN, TicketStatus.IN_PROGRESS],
            priority=[Priority.HIGH],
            created_by_id=1
        )
        
        mock_results = [mock_ticket for _ in range(3)]
        mock_ticket_repo.search.return_value = (mock_results, 3)
        
        results, total = await ticket_service.search_tickets(filters, page=1, size=10)
        
        assert len(results) == 3
        assert total == 3
        mock_ticket_repo.search.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_tickets_with_text(self, ticket_service, mock_ticket_repo):
        """Test ticket search with text query"""
        filters = TicketFilters(search="test query")
        
        mock_results = [mock_ticket]
        mock_ticket_repo.search_with_text.return_value = (mock_results, 1)
        
        results, total = await ticket_service.search_tickets(filters, page=1, size=10)
        
        assert len(results) == 1
        mock_ticket_repo.search_with_text.assert_called_once()

    # Ticket Deletion Tests
    @pytest.mark.asyncio
    async def test_delete_ticket_success(self, ticket_service, mock_ticket, mock_user, mock_ticket_repo):
        """Test successful ticket deletion"""
        mock_ticket_repo.get_by_id.return_value = mock_ticket
        
        with patch.object(ticket_service, '_can_delete_ticket', return_value=True):
            result = await ticket_service.delete_ticket(1, mock_user)
        
        assert result is True
        mock_ticket_repo.delete.assert_called_once_with(1)

    @pytest.mark.asyncio
    async def test_delete_ticket_unauthorized(self, ticket_service, mock_ticket, mock_ticket_repo):
        """Test ticket deletion by unauthorized user"""
        unauthorized_user = User(id=999, username="unauthorized")
        mock_ticket_repo.get_by_id.return_value = mock_ticket
        
        with patch.object(ticket_service, '_can_delete_ticket', return_value=False):
            with pytest.raises(HTTPException) as exc_info:
                await ticket_service.delete_ticket(1, unauthorized_user)
        
        assert exc_info.value.status_code == 403

    # Bulk Operations Tests
    @pytest.mark.asyncio
    async def test_bulk_update_tickets_success(self, ticket_service, mock_user, mock_ticket_repo):
        """Test successful bulk ticket update"""
        ticket_ids = [1, 2, 3]
        updates = {"status": TicketStatus.CLOSED, "priority": Priority.LOW}
        
        mock_tickets = [Ticket(id=i, created_by_id=mock_user.id) for i in ticket_ids]
        mock_ticket_repo.get_by_ids.return_value = mock_tickets
        mock_ticket_repo.bulk_update.return_value = 3
        
        with patch.object(ticket_service, '_can_modify_ticket', return_value=True):
            result = await ticket_service.bulk_update_tickets(ticket_ids, updates, mock_user)
        
        assert result == 3
        mock_ticket_repo.bulk_update.assert_called_once()

    @pytest.mark.asyncio
    async def test_bulk_update_tickets_partial_permission(self, ticket_service, mock_user, mock_ticket_repo):
        """Test bulk update with partial permissions"""
        ticket_ids = [1, 2, 3]
        updates = {"status": TicketStatus.CLOSED}
        
        mock_tickets = [
            Ticket(id=1, created_by_id=mock_user.id),  # Can modify
            Ticket(id=2, created_by_id=999),           # Cannot modify
            Ticket(id=3, created_by_id=mock_user.id)   # Can modify
        ]
        mock_ticket_repo.get_by_ids.return_value = mock_tickets
        
        def can_modify_side_effect(ticket, user):
            return ticket.created_by_id == user.id
        
        with patch.object(ticket_service, '_can_modify_ticket', side_effect=can_modify_side_effect):
            mock_ticket_repo.bulk_update.return_value = 2
            result = await ticket_service.bulk_update_tickets(ticket_ids, updates, mock_user)
        
        assert result == 2  # Only 2 tickets updated

    # Statistics and Analytics Tests
    @pytest.mark.asyncio
    async def test_get_ticket_statistics(self, ticket_service, mock_ticket_repo):
        """Test ticket statistics retrieval"""
        mock_stats = {
            "total_tickets": 100,
            "open_tickets": 25,
            "in_progress_tickets": 30,
            "resolved_tickets": 45,
            "avg_resolution_time": 2.5
        }
        mock_ticket_repo.get_statistics.return_value = mock_stats
        
        result = await ticket_service.get_ticket_statistics()
        
        assert result == mock_stats
        mock_ticket_repo.get_statistics.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_user_ticket_stats(self, ticket_service, mock_user, mock_ticket_repo):
        """Test user-specific ticket statistics"""
        mock_stats = {
            "created_tickets": 15,
            "assigned_tickets": 8,
            "resolved_tickets": 12,
            "avg_response_time": 1.2
        }
        mock_ticket_repo.get_user_statistics.return_value = mock_stats
        
        result = await ticket_service.get_user_ticket_statistics(mock_user.id)
        
        assert result == mock_stats
        mock_ticket_repo.get_user_statistics.assert_called_once_with(mock_user.id)

    # Helper Method Tests
    def test_generate_ticket_number(self, ticket_service):
        """Test ticket number generation"""
        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.utcnow.return_value.strftime.return_value = "20231201"
            with patch('random.randint', return_value=123):
                result = ticket_service._generate_ticket_number()
        
        assert result.startswith("TKT-")
        assert "20231201" in result

    def test_can_modify_ticket_owner(self, ticket_service, mock_ticket, mock_user):
        """Test permission check for ticket owner"""
        mock_ticket.created_by_id = mock_user.id
        
        result = ticket_service._can_modify_ticket(mock_ticket, mock_user)
        
        assert result is True

    def test_can_modify_ticket_assignee(self, ticket_service, mock_ticket, mock_user):
        """Test permission check for ticket assignee"""
        mock_ticket.created_by_id = 999
        mock_ticket.assigned_to_id = mock_user.id
        
        result = ticket_service._can_modify_ticket(mock_ticket, mock_user)
        
        assert result is True

    def test_can_modify_ticket_unauthorized(self, ticket_service, mock_ticket, mock_user):
        """Test permission check for unauthorized user"""
        mock_ticket.created_by_id = 999
        mock_ticket.assigned_to_id = 888
        
        with patch.object(ticket_service, '_has_admin_permission', return_value=False):
            result = ticket_service._can_modify_ticket(mock_ticket, mock_user)
        
        assert result is False

    # SLA and Priority Tests
    @pytest.mark.asyncio
    async def test_check_sla_breaches(self, ticket_service, mock_ticket_repo):
        """Test SLA breach checking"""
        overdue_tickets = [
            Ticket(id=1, title="Overdue 1", priority=Priority.HIGH),
            Ticket(id=2, title="Overdue 2", priority=Priority.CRITICAL)
        ]
        mock_ticket_repo.get_overdue_tickets.return_value = overdue_tickets
        
        result = await ticket_service.check_sla_breaches()
        
        assert len(result) == 2
        mock_ticket_repo.get_overdue_tickets.assert_called_once()

    @pytest.mark.asyncio
    async def test_escalate_priority(self, ticket_service, mock_ticket, mock_user, mock_ticket_repo, mock_notification_service):
        """Test ticket priority escalation"""
        mock_ticket.priority = Priority.MEDIUM
        mock_ticket_repo.get_by_id.return_value = mock_ticket
        
        escalated_ticket = Ticket(**{**mock_ticket.__dict__, "priority": Priority.HIGH})
        mock_ticket_repo.update.return_value = escalated_ticket
        
        result = await ticket_service.escalate_priority(1, mock_user, "SLA breach")
        
        assert result.priority == Priority.HIGH
        mock_notification_service.send_ticket_escalated_notification.assert_called_once()

    # Integration and Edge Cases
    @pytest.mark.asyncio
    async def test_create_ticket_with_attachments(self, ticket_service, valid_ticket_create, mock_user, mock_ticket_repo):
        """Test ticket creation with file attachments"""
        # Mock file attachments
        attachments = ["file1.pdf", "file2.jpg"]
        
        created_ticket = Ticket(id=1, **valid_ticket_create.dict())
        mock_ticket_repo.create.return_value = created_ticket
        
        with patch.object(ticket_service, '_generate_ticket_number', return_value="TKT-001"):
            with patch.object(ticket_service, '_process_attachments') as mock_process:
                result = await ticket_service.create_ticket(valid_ticket_create, mock_user, attachments)
        
        mock_process.assert_called_once_with(created_ticket.id, attachments)

    @pytest.mark.asyncio
    async def test_ticket_workflow_transitions(self, ticket_service, mock_ticket, mock_user, mock_ticket_repo):
        """Test valid ticket status transitions"""
        # Test valid transition: OPEN -> IN_PROGRESS
        mock_ticket.status = TicketStatus.OPEN
        mock_ticket_repo.get_by_id.return_value = mock_ticket
        
        update = TicketUpdate(status=TicketStatus.IN_PROGRESS)
        
        with patch.object(ticket_service, '_is_valid_status_transition', return_value=True):
            updated_ticket = Ticket(**{**mock_ticket.__dict__, "status": TicketStatus.IN_PROGRESS})
            mock_ticket_repo.update.return_value = updated_ticket
            
            result = await ticket_service.update_ticket(1, update, mock_user)
        
        assert result.status == TicketStatus.IN_PROGRESS

    @pytest.mark.asyncio
    async def test_invalid_status_transition(self, ticket_service, mock_ticket, mock_user, mock_ticket_repo):
        """Test invalid ticket status transition"""
        mock_ticket.status = TicketStatus.CLOSED
        mock_ticket_repo.get_by_id.return_value = mock_ticket
        
        update = TicketUpdate(status=TicketStatus.OPEN)
        
        with patch.object(ticket_service, '_is_valid_status_transition', return_value=False):
            with pytest.raises(HTTPException) as exc_info:
                await ticket_service.update_ticket(1, update, mock_user)
        
        assert exc_info.value.status_code == 400
        assert "Invalid status transition" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_concurrent_ticket_updates(self, ticket_service, mock_ticket, mock_user, mock_ticket_repo):
        """Test handling of concurrent ticket updates"""
        mock_ticket_repo.get_by_id.return_value = mock_ticket
        
        update1 = TicketUpdate(title="Update 1")
        update2 = TicketUpdate(title="Update 2")
        
        updated_ticket1 = Ticket(**{**mock_ticket.__dict__, "title": "Update 1"})
        updated_ticket2 = Ticket(**{**mock_ticket.__dict__, "title": "Update 2"})
        
        mock_ticket_repo.update.side_effect = [updated_ticket1, updated_ticket2]
        
        # Simulate concurrent updates
        with patch.object(ticket_service, '_can_modify_ticket', return_value=True):
            tasks = [
                ticket_service.update_ticket(1, update1, mock_user),
                ticket_service.update_ticket(1, update2, mock_user)
            ]
            
            results = await asyncio.gather(*tasks)
        
        assert len(results) == 2
        assert results[0].title == "Update 1"
        assert results[1].title == "Update 2"