import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from app.services.approval_service import ApprovalService
from app.models import ApprovalWorkflow, ApprovalStep, Ticket, User
from app.schemas import ApprovalActionRequest, ApprovalWorkflowCreate
from app.enums import WorkflowType, ApprovalAction, TicketStatus, Priority


class TestApprovalService:
    """Comprehensive unit tests for ApprovalService"""

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
    def mock_approval_repo(self):
        """Mock approval repository"""
        return Mock()

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
    def approval_service(self, mock_db_session, mock_approval_repo, mock_ticket_repo, mock_user_repo, mock_notification_service):
        """Create ApprovalService instance with mocked dependencies"""
        service = ApprovalService(mock_db_session)
        service.approval_repo = mock_approval_repo
        service.ticket_repo = mock_ticket_repo
        service.user_repo = mock_user_repo
        service.notification_service = mock_notification_service
        return service

    @pytest.fixture
    def mock_user(self):
        """Mock user object"""
        return User(
            id=1,
            email="approver@example.com",
            username="approver",
            first_name="Test",
            last_name="Approver",
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
            status=TicketStatus.PENDING_APPROVAL,
            priority=Priority.HIGH,
            created_by_id=1,
            department_id=1
        )

    @pytest.fixture
    def mock_workflow(self):
        """Mock approval workflow"""
        return ApprovalWorkflow(
            id=1,
            ticket_id=1,
            workflow_type=WorkflowType.SEQUENTIAL,
            status="pending",
            current_step_id=1,
            created_at=datetime.utcnow()
        )

    @pytest.fixture
    def mock_approval_step(self):
        """Mock approval step"""
        return ApprovalStep(
            id=1,
            workflow_id=1,
            step_order=1,
            step_name="Manager Approval",
            approver_id=1,
            action="pending",
            is_required=True,
            is_parallel=False
        )

    @pytest.fixture
    def valid_workflow_create(self):
        """Valid workflow creation data"""
        return ApprovalWorkflowCreate(
            ticket_id=1,
            workflow_type=WorkflowType.SEQUENTIAL,
            steps=[
                {
                    "step_name": "Manager Approval",
                    "approver_id": 1,
                    "step_order": 1,
                    "is_required": True
                },
                {
                    "step_name": "Director Approval",
                    "approver_id": 2,
                    "step_order": 2,
                    "is_required": True
                }
            ]
        )

    # Workflow Creation Tests
    @pytest.mark.asyncio
    async def test_create_workflow_success(self, approval_service, valid_workflow_create, mock_ticket, mock_approval_repo, mock_ticket_repo):
        """Test successful workflow creation"""
        mock_ticket_repo.get_by_id.return_value = mock_ticket
        
        created_workflow = ApprovalWorkflow(
            id=1,
            ticket_id=valid_workflow_create.ticket_id,
            workflow_type=valid_workflow_create.workflow_type,
            status="pending"
        )
        mock_approval_repo.create_workflow.return_value = created_workflow
        
        result = await approval_service.create_approval_workflow(valid_workflow_create)
        
        assert result.ticket_id == valid_workflow_create.ticket_id
        assert result.workflow_type == valid_workflow_create.workflow_type
        mock_approval_repo.create_workflow.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_workflow_ticket_not_found(self, approval_service, valid_workflow_create, mock_ticket_repo):
        """Test workflow creation with non-existent ticket"""
        mock_ticket_repo.get_by_id.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            await approval_service.create_approval_workflow(valid_workflow_create)
        
        assert exc_info.value.status_code == 404
        assert "Ticket not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_create_workflow_existing_workflow(self, approval_service, valid_workflow_create, mock_ticket, mock_workflow, mock_ticket_repo, mock_approval_repo):
        """Test workflow creation when workflow already exists"""
        mock_ticket_repo.get_by_id.return_value = mock_ticket
        mock_approval_repo.get_by_ticket_id.return_value = mock_workflow
        
        with pytest.raises(HTTPException) as exc_info:
            await approval_service.create_approval_workflow(valid_workflow_create)
        
        assert exc_info.value.status_code == 400
        assert "Approval workflow already exists" in str(exc_info.value.detail)

    # Workflow Processing Tests
    @pytest.mark.asyncio
    async def test_process_approval_action_approve(self, approval_service, mock_workflow, mock_approval_step, mock_user, mock_approval_repo, mock_notification_service):
        """Test processing approval action - approve"""
        action_request = ApprovalActionRequest(
            action=ApprovalAction.APPROVE,
            comments="Approved by manager"
        )
        
        mock_approval_repo.get_workflow_by_id.return_value = mock_workflow
        mock_approval_repo.get_current_step.return_value = mock_approval_step
        
        # Mock step update
        updated_step = ApprovalStep(**{**mock_approval_step.__dict__, "action": "approved"})
        mock_approval_repo.update_step.return_value = updated_step
        
        with patch.object(approval_service, '_advance_workflow', return_value=mock_workflow):
            result = await approval_service.process_approval_action(1, action_request, mock_user)
        
        assert result.id == mock_workflow.id
        mock_approval_repo.update_step.assert_called_once()
        mock_notification_service.send_approval_processed_notification.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_approval_action_reject(self, approval_service, mock_workflow, mock_approval_step, mock_user, mock_approval_repo, mock_ticket_repo):
        """Test processing approval action - reject"""
        action_request = ApprovalActionRequest(
            action=ApprovalAction.REJECT,
            comments="Rejected due to insufficient information"
        )
        
        mock_approval_repo.get_workflow_by_id.return_value = mock_workflow
        mock_approval_repo.get_current_step.return_value = mock_approval_step
        
        # Mock workflow rejection
        rejected_workflow = ApprovalWorkflow(**{**mock_workflow.__dict__, "status": "rejected"})
        mock_approval_repo.update_workflow.return_value = rejected_workflow
        
        result = await approval_service.process_approval_action(1, action_request, mock_user)
        
        assert result.status == "rejected"
        mock_ticket_repo.update_status.assert_called_once()

    @pytest.mark.asyncio
    async def test_process_approval_action_delegate(self, approval_service, mock_workflow, mock_approval_step, mock_user, mock_approval_repo, mock_user_repo):
        """Test processing approval action - delegate"""
        delegate_user = User(id=2, username="delegate")
        action_request = ApprovalActionRequest(
            action=ApprovalAction.DELEGATE,
            delegated_to_id=delegate_user.id,
            comments="Delegating to team lead"
        )
        
        mock_approval_repo.get_workflow_by_id.return_value = mock_workflow
        mock_approval_repo.get_current_step.return_value = mock_approval_step
        mock_user_repo.get_by_id.return_value = delegate_user
        
        # Mock step delegation
        delegated_step = ApprovalStep(**{**mock_approval_step.__dict__, "delegated_to_id": delegate_user.id})
        mock_approval_repo.update_step.return_value = delegated_step
        
        result = await approval_service.process_approval_action(1, action_request, mock_user)
        
        mock_user_repo.get_by_id.assert_called_once_with(delegate_user.id)

    @pytest.mark.asyncio
    async def test_process_approval_unauthorized_user(self, approval_service, mock_workflow, mock_approval_step, mock_approval_repo):
        """Test processing approval by unauthorized user"""
        unauthorized_user = User(id=999, username="unauthorized")
        action_request = ApprovalActionRequest(action=ApprovalAction.APPROVE)
        
        # Mock different approver
        mock_approval_step.approver_id = 2
        mock_approval_repo.get_workflow_by_id.return_value = mock_workflow
        mock_approval_repo.get_current_step.return_value = mock_approval_step
        
        with pytest.raises(HTTPException) as exc_info:
            await approval_service.process_approval_action(1, action_request, unauthorized_user)
        
        assert exc_info.value.status_code == 403
        assert "Not authorized to approve this step" in str(exc_info.value.detail)

    # Workflow Advancement Tests
    @pytest.mark.asyncio
    async def test_advance_workflow_sequential_next_step(self, approval_service, mock_workflow, mock_approval_repo):
        """Test advancing sequential workflow to next step"""
        mock_workflow.workflow_type = WorkflowType.SEQUENTIAL
        
        next_step = ApprovalStep(
            id=2,
            workflow_id=1,
            step_order=2,
            approver_id=2,
            action="pending"
        )
        mock_approval_repo.get_next_step.return_value = next_step
        
        # Mock workflow update
        updated_workflow = ApprovalWorkflow(**{**mock_workflow.__dict__, "current_step_id": 2})
        mock_approval_repo.update_workflow.return_value = updated_workflow
        
        result = await approval_service._advance_workflow(mock_workflow)
        
        assert result.current_step_id == 2
        mock_approval_repo.update_workflow.assert_called_once()

    @pytest.mark.asyncio
    async def test_advance_workflow_complete(self, approval_service, mock_workflow, mock_approval_repo, mock_ticket_repo):
        """Test completing workflow when no more steps"""
        mock_workflow.workflow_type = WorkflowType.SEQUENTIAL
        mock_approval_repo.get_next_step.return_value = None  # No more steps
        
        # Mock workflow completion
        completed_workflow = ApprovalWorkflow(**{
            **mock_workflow.__dict__, 
            "status": "approved",
            "completed_at": datetime.utcnow()
        })
        mock_approval_repo.update_workflow.return_value = completed_workflow
        
        result = await approval_service._advance_workflow(mock_workflow)
        
        assert result.status == "approved"
        mock_ticket_repo.update_status.assert_called_once()

    @pytest.mark.asyncio
    async def test_advance_workflow_parallel(self, approval_service, mock_workflow, mock_approval_repo):
        """Test advancing parallel workflow"""
        mock_workflow.workflow_type = WorkflowType.PARALLEL
        
        # Mock pending parallel steps
        pending_steps = [
            ApprovalStep(id=2, action="pending"),
            ApprovalStep(id=3, action="pending")
        ]
        mock_approval_repo.get_parallel_steps.return_value = pending_steps
        
        result = await approval_service._advance_workflow(mock_workflow)
        
        # Workflow should remain in current state with pending parallel steps
        assert result.id == mock_workflow.id

    # Bulk Operations Tests
    @pytest.mark.asyncio
    async def test_bulk_approve_success(self, approval_service, mock_user, mock_approval_repo):
        """Test successful bulk approval"""
        workflow_ids = [1, 2, 3]
        comments = "Bulk approval"
        
        mock_workflows = [
            ApprovalWorkflow(id=i, status="pending") for i in workflow_ids
        ]
        mock_approval_repo.get_workflows_by_ids.return_value = mock_workflows
        
        with patch.object(approval_service, 'process_approval_action') as mock_process:
            mock_process.return_value = ApprovalWorkflow(id=1, status="approved")
            result = await approval_service.bulk_approve(workflow_ids, comments, mock_user)
        
        assert result["processed"] == 3
        assert result["failed"] == 0
        assert mock_process.call_count == 3

    @pytest.mark.asyncio
    async def test_bulk_approve_partial_failure(self, approval_service, mock_user, mock_approval_repo):
        """Test bulk approval with some failures"""
        workflow_ids = [1, 2, 3]
        
        mock_workflows = [
            ApprovalWorkflow(id=i, status="pending") for i in workflow_ids
        ]
        mock_approval_repo.get_workflows_by_ids.return_value = mock_workflows
        
        def process_side_effect(workflow_id, action, user):
            if workflow_id == 2:
                raise HTTPException(status_code=403, detail="Unauthorized")
            return ApprovalWorkflow(id=workflow_id, status="approved")
        
        with patch.object(approval_service, 'process_approval_action', side_effect=process_side_effect):
            result = await approval_service.bulk_approve(workflow_ids, "comments", mock_user)
        
        assert result["processed"] == 2
        assert result["failed"] == 1
        assert len(result["errors"]) == 1

    # Workflow Retrieval Tests
    @pytest.mark.asyncio
    async def test_get_pending_approvals_for_user(self, approval_service, mock_user, mock_approval_repo):
        """Test getting pending approvals for specific user"""
        mock_workflows = [
            ApprovalWorkflow(id=1, status="pending"),
            ApprovalWorkflow(id=2, status="pending")
        ]
        mock_approval_repo.get_pending_for_user.return_value = (mock_workflows, 2)
        
        results, total = await approval_service.get_pending_approvals_for_user(mock_user.id)
        
        assert len(results) == 2
        assert total == 2
        mock_approval_repo.get_pending_for_user.assert_called_once_with(mock_user.id, 1, 50)

    @pytest.mark.asyncio
    async def test_get_workflow_history(self, approval_service, mock_approval_repo):
        """Test getting workflow history"""
        workflow_id = 1
        mock_history = [
            {"action": "approved", "timestamp": datetime.utcnow(), "user": "approver1"},
            {"action": "delegated", "timestamp": datetime.utcnow(), "user": "approver2"}
        ]
        mock_approval_repo.get_workflow_history.return_value = mock_history
        
        result = await approval_service.get_workflow_history(workflow_id)
        
        assert len(result) == 2
        mock_approval_repo.get_workflow_history.assert_called_once_with(workflow_id)

    # Escalation Tests
    @pytest.mark.asyncio
    async def test_escalate_approval(self, approval_service, mock_workflow, mock_approval_step, mock_user, mock_approval_repo, mock_user_repo):
        """Test approval escalation"""
        escalation_user = User(id=3, username="escalation_manager")
        escalation_reason = "SLA breach"
        
        mock_approval_repo.get_workflow_by_id.return_value = mock_workflow
        mock_approval_repo.get_current_step.return_value = mock_approval_step
        mock_user_repo.get_by_id.return_value = escalation_user
        
        # Mock step escalation
        escalated_step = ApprovalStep(**{**mock_approval_step.__dict__, "escalated_to_id": escalation_user.id})
        mock_approval_repo.update_step.return_value = escalated_step
        
        result = await approval_service.escalate_approval(1, escalation_user.id, escalation_reason, mock_user)
        
        mock_user_repo.get_by_id.assert_called_once_with(escalation_user.id)

    @pytest.mark.asyncio
    async def test_escalate_approval_invalid_user(self, approval_service, mock_workflow, mock_approval_step, mock_user, mock_approval_repo, mock_user_repo):
        """Test escalation to invalid user"""
        mock_approval_repo.get_workflow_by_id.return_value = mock_workflow
        mock_approval_repo.get_current_step.return_value = mock_approval_step
        mock_user_repo.get_by_id.return_value = None
        
        with pytest.raises(HTTPException) as exc_info:
            await approval_service.escalate_approval(1, 999, "reason", mock_user)
        
        assert exc_info.value.status_code == 400
        assert "Escalation user not found" in str(exc_info.value.detail)

    # Template Management Tests
    @pytest.mark.asyncio
    async def test_create_workflow_from_template(self, approval_service, mock_ticket, mock_approval_repo, mock_ticket_repo):
        """Test creating workflow from template"""
        template = {
            "workflow_type": WorkflowType.SEQUENTIAL,
            "steps": [
                {"step_name": "Manager", "approver_role": "manager", "step_order": 1},
                {"step_name": "Director", "approver_role": "director", "step_order": 2}
            ]
        }
        
        mock_ticket_repo.get_by_id.return_value = mock_ticket
        mock_approval_repo.get_by_ticket_id.return_value = None
        
        # Mock template application
        created_workflow = ApprovalWorkflow(id=1, ticket_id=1, workflow_type=WorkflowType.SEQUENTIAL)
        mock_approval_repo.create_workflow_from_template.return_value = created_workflow
        
        result = await approval_service.create_workflow_from_template(1, template)
        
        assert result.ticket_id == 1
        mock_approval_repo.create_workflow_from_template.assert_called_once()

    # SLA and Monitoring Tests
    @pytest.mark.asyncio
    async def test_check_overdue_approvals(self, approval_service, mock_approval_repo):
        """Test checking for overdue approvals"""
        overdue_workflows = [
            ApprovalWorkflow(id=1, status="pending", created_at=datetime.utcnow() - timedelta(days=3)),
            ApprovalWorkflow(id=2, status="pending", created_at=datetime.utcnow() - timedelta(days=5))
        ]
        mock_approval_repo.get_overdue_approvals.return_value = overdue_workflows
        
        result = await approval_service.check_overdue_approvals()
        
        assert len(result) == 2
        mock_approval_repo.get_overdue_approvals.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_approval_statistics(self, approval_service, mock_approval_repo):
        """Test getting approval statistics"""
        mock_stats = {
            "total_pending": 25,
            "overdue_count": 5,
            "avg_approval_time": 2.5,
            "approval_rate": 0.85
        }
        mock_approval_repo.get_approval_statistics.return_value = mock_stats
        
        result = await approval_service.get_approval_statistics()
        
        assert result == mock_stats
        mock_approval_repo.get_approval_statistics.assert_called_once()

    # Conditional Workflow Tests
    @pytest.mark.asyncio
    async def test_evaluate_conditional_workflow(self, approval_service, mock_workflow, mock_ticket, mock_approval_repo):
        """Test evaluating conditional workflow rules"""
        mock_workflow.workflow_type = WorkflowType.CONDITIONAL
        
        # Mock condition evaluation
        next_step = ApprovalStep(id=2, step_order=2, approver_id=2)
        
        with patch.object(approval_service, '_evaluate_conditions', return_value=next_step):
            result = await approval_service._advance_workflow(mock_workflow)
        
        assert result.id == mock_workflow.id

    def test_evaluate_conditions_priority_based(self, approval_service, mock_ticket):
        """Test condition evaluation based on ticket priority"""
        conditions = {
            "priority": {
                "high": {"approver_role": "director"},
                "critical": {"approver_role": "vp"}
            }
        }
        
        mock_ticket.priority = Priority.HIGH
        
        with patch.object(approval_service, '_get_approver_by_role', return_value=User(id=2)) as mock_get_approver:
            result = approval_service._evaluate_conditions(conditions, mock_ticket)
        
        mock_get_approver.assert_called_once_with("director", mock_ticket.department_id)

    # Notification Integration Tests
    @pytest.mark.asyncio
    async def test_approval_notifications(self, approval_service, mock_workflow, mock_approval_step, mock_user, mock_approval_repo, mock_notification_service):
        """Test that appropriate notifications are sent"""
        action_request = ApprovalActionRequest(action=ApprovalAction.APPROVE)
        
        mock_approval_repo.get_workflow_by_id.return_value = mock_workflow
        mock_approval_repo.get_current_step.return_value = mock_approval_step
        
        with patch.object(approval_service, '_advance_workflow', return_value=mock_workflow):
            await approval_service.process_approval_action(1, action_request, mock_user)
        
        # Verify notifications were sent
        mock_notification_service.send_approval_processed_notification.assert_called_once()

    # Error Handling and Edge Cases
    @pytest.mark.asyncio
    async def test_workflow_not_found(self, approval_service, mock_approval_repo):
        """Test handling of non-existent workflow"""
        mock_approval_repo.get_workflow_by_id.return_value = None
        
        action_request = ApprovalActionRequest(action=ApprovalAction.APPROVE)
        
        with pytest.raises(HTTPException) as exc_info:
            await approval_service.process_approval_action(999, action_request, Mock())
        
        assert exc_info.value.status_code == 404
        assert "Workflow not found" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_workflow_already_completed(self, approval_service, mock_workflow, mock_user, mock_approval_repo):
        """Test processing action on completed workflow"""
        mock_workflow.status = "approved"
        mock_approval_repo.get_workflow_by_id.return_value = mock_workflow
        
        action_request = ApprovalActionRequest(action=ApprovalAction.APPROVE)
        
        with pytest.raises(HTTPException) as exc_info:
            await approval_service.process_approval_action(1, action_request, mock_user)
        
        assert exc_info.value.status_code == 400
        assert "Workflow already completed" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_step_already_processed(self, approval_service, mock_workflow, mock_approval_step, mock_user, mock_approval_repo):
        """Test processing already completed step"""
        mock_approval_step.action = "approved"
        mock_approval_repo.get_workflow_by_id.return_value = mock_workflow
        mock_approval_repo.get_current_step.return_value = mock_approval_step
        
        action_request = ApprovalActionRequest(action=ApprovalAction.APPROVE)
        
        with pytest.raises(HTTPException) as exc_info:
            await approval_service.process_approval_action(1, action_request, mock_user)
        
        assert exc_info.value.status_code == 400
        assert "Step already processed" in str(exc_info.value.detail)