import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from fastapi import HTTPException

from app.services.notification_service import NotificationService
from app.services.reporting_service import ReportingService
from app.models import User, Ticket, Department
from app.enums import TicketStatus, Priority, TicketType


class TestNotificationService:
    """Comprehensive unit tests for NotificationService"""

    @pytest.fixture
    def mock_email_service(self):
        """Mock email service"""
        return Mock()

    @pytest.fixture
    def mock_teams_service(self):
        """Mock Teams service"""
        return Mock()

    @pytest.fixture
    def mock_slack_service(self):
        """Mock Slack service"""
        return Mock()

    @pytest.fixture
    def notification_service(self, mock_email_service, mock_teams_service, mock_slack_service):
        """Create NotificationService with mocked dependencies"""
        service = NotificationService()
        service.email_service = mock_email_service
        service.teams_service = mock_teams_service
        service.slack_service = mock_slack_service
        return service

    @pytest.fixture
    def mock_user(self):
        """Mock user object"""
        return User(
            id=1,
            email="user@example.com",
            username="testuser",
            first_name="Test",
            last_name="User",
            department_id=1,
            preferences={
                "email_notifications": True,
                "teams_notifications": True,
                "slack_notifications": False
            }
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
            priority=Priority.HIGH,
            created_by_id=1,
            department_id=1
        )

    # Email Notification Tests
    @pytest.mark.asyncio
    async def test_send_email_notification_success(self, notification_service, mock_user, mock_email_service):
        """Test successful email notification"""
        subject = "Test Subject"
        body = "Test email body"
        
        mock_email_service.send_email.return_value = True
        
        result = await notification_service.send_email_notification(mock_user.email, subject, body)
        
        assert result is True
        mock_email_service.send_email.assert_called_once_with(
            to_email=mock_user.email,
            subject=subject,
            body=body,
            html_body=None
        )

    @pytest.mark.asyncio
    async def test_send_email_notification_failure(self, notification_service, mock_user, mock_email_service):
        """Test email notification failure"""
        mock_email_service.send_email.side_effect = Exception("SMTP Error")
        
        result = await notification_service.send_email_notification(mock_user.email, "Subject", "Body")
        
        assert result is False

    @pytest.mark.asyncio
    async def test_send_email_with_template(self, notification_service, mock_user, mock_email_service):
        """Test email notification with template"""
        template_name = "ticket_created"
        template_data = {"ticket_number": "TKT-001", "user_name": "Test User"}
        
        with patch.object(notification_service, '_render_email_template') as mock_render:
            mock_render.return_value = ("Subject", "Body", "HTML Body")
            mock_email_service.send_email.return_value = True
            
            result = await notification_service.send_email_from_template(
                mock_user.email, template_name, template_data
            )
        
        assert result is True
        mock_render.assert_called_once_with(template_name, template_data)

    # Teams Notification Tests
    @pytest.mark.asyncio
    async def test_send_teams_notification_success(self, notification_service, mock_teams_service):
        """Test successful Teams notification"""
        webhook_url = "https://outlook.office.com/webhook/test"
        message = "Test Teams message"
        
        mock_teams_service.send_message.return_value = True
        
        result = await notification_service.send_teams_notification(webhook_url, message)
        
        assert result is True
        mock_teams_service.send_message.assert_called_once_with(webhook_url, message)

    @pytest.mark.asyncio
    async def test_send_teams_card_notification(self, notification_service, mock_teams_service):
        """Test Teams card notification"""
        webhook_url = "https://outlook.office.com/webhook/test"
        card_data = {
            "title": "New Ticket Created",
            "subtitle": "TKT-001",
            "text": "A new high priority ticket has been created"
        }
        
        mock_teams_service.send_card.return_value = True
        
        result = await notification_service.send_teams_card(webhook_url, card_data)
        
        assert result is True
        mock_teams_service.send_card.assert_called_once_with(webhook_url, card_data)

    # Slack Notification Tests
    @pytest.mark.asyncio
    async def test_send_slack_notification_success(self, notification_service, mock_slack_service):
        """Test successful Slack notification"""
        webhook_url = "https://hooks.slack.com/services/test"
        message = "Test Slack message"
        channel = "#general"
        
        mock_slack_service.send_message.return_value = True
        
        result = await notification_service.send_slack_notification(webhook_url, message, channel)
        
        assert result is True
        mock_slack_service.send_message.assert_called_once_with(webhook_url, message, channel)

    # Ticket Event Notifications
    @pytest.mark.asyncio
    async def test_send_ticket_created_notification(self, notification_service, mock_ticket, mock_user):
        """Test ticket created notification"""
        with patch.object(notification_service, 'send_email_from_template') as mock_email:
            with patch.object(notification_service, 'send_teams_card') as mock_teams:
                mock_email.return_value = True
                mock_teams.return_value = True
                
                await notification_service.send_ticket_created_notification(mock_ticket, mock_user)
        
        mock_email.assert_called_once()
        # Teams notification should only be called if user has Teams enabled
        if mock_user.preferences.get("teams_notifications"):
            mock_teams.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_ticket_assigned_notification(self, notification_service, mock_ticket, mock_user):
        """Test ticket assigned notification"""
        assignee = User(id=2, email="assignee@example.com", username="assignee")
        
        with patch.object(notification_service, 'send_email_from_template') as mock_email:
            mock_email.return_value = True
            
            await notification_service.send_ticket_assigned_notification(mock_ticket, assignee, mock_user)
        
        mock_email.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_ticket_status_changed_notification(self, notification_service, mock_ticket, mock_user):
        """Test ticket status changed notification"""
        old_status = TicketStatus.OPEN
        new_status = TicketStatus.RESOLVED
        
        with patch.object(notification_service, 'send_email_from_template') as mock_email:
            mock_email.return_value = True
            
            await notification_service.send_ticket_status_changed_notification(
                mock_ticket, old_status, new_status, mock_user
            )
        
        mock_email.assert_called_once()

    # Approval Notifications
    @pytest.mark.asyncio
    async def test_send_approval_requested_notification(self, notification_service, mock_ticket, mock_user):
        """Test approval requested notification"""
        approver = User(id=2, email="approver@example.com", username="approver")
        
        with patch.object(notification_service, 'send_email_from_template') as mock_email:
            mock_email.return_value = True
            
            await notification_service.send_approval_requested_notification(mock_ticket, approver)
        
        mock_email.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_approval_processed_notification(self, notification_service, mock_ticket, mock_user):
        """Test approval processed notification"""
        action = "approved"
        comments = "Approved by manager"
        
        with patch.object(notification_service, 'send_email_from_template') as mock_email:
            mock_email.return_value = True
            
            await notification_service.send_approval_processed_notification(
                mock_ticket, action, mock_user, comments
            )
        
        mock_email.assert_called_once()

    # Bulk Notifications
    @pytest.mark.asyncio
    async def test_send_bulk_notifications(self, notification_service):
        """Test sending bulk notifications"""
        recipients = ["user1@example.com", "user2@example.com", "user3@example.com"]
        subject = "Bulk Notification"
        message = "This is a bulk notification"
        
        with patch.object(notification_service, 'send_email_notification') as mock_send:
            mock_send.return_value = True
            
            results = await notification_service.send_bulk_notifications(recipients, subject, message)
        
        assert len(results) == 3
        assert all(result is True for result in results)
        assert mock_send.call_count == 3

    # Template Rendering Tests
    def test_render_email_template_success(self, notification_service):
        """Test successful email template rendering"""
        template_name = "ticket_created"
        template_data = {"ticket_number": "TKT-001", "user_name": "Test User"}
        
        with patch('jinja2.Environment.get_template') as mock_get_template:
            mock_template = Mock()
            mock_template.render.return_value = "Rendered HTML"
            mock_get_template.return_value = mock_template
            
            result = notification_service._render_email_template(template_name, template_data)
        
        assert result is not None

    def test_render_email_template_not_found(self, notification_service):
        """Test email template not found"""
        with patch('jinja2.Environment.get_template') as mock_get_template:
            mock_get_template.side_effect = Exception("Template not found")
            
            result = notification_service._render_email_template("nonexistent", {})
        
        assert result == ("", "", "")

    # User Preference Tests
    @pytest.mark.asyncio
    async def test_notification_respects_user_preferences(self, notification_service, mock_ticket, mock_user):
        """Test that notifications respect user preferences"""
        # User has email enabled but Teams disabled
        mock_user.preferences = {
            "email_notifications": True,
            "teams_notifications": False,
            "slack_notifications": False
        }
        
        with patch.object(notification_service, 'send_email_from_template') as mock_email:
            with patch.object(notification_service, 'send_teams_card') as mock_teams:
                mock_email.return_value = True
                
                await notification_service.send_ticket_created_notification(mock_ticket, mock_user)
        
        mock_email.assert_called_once()
        mock_teams.assert_not_called()

    # Rate Limiting Tests
    @pytest.mark.asyncio
    async def test_notification_rate_limiting(self, notification_service, mock_user):
        """Test notification rate limiting"""
        with patch.object(notification_service, '_check_rate_limit') as mock_rate_limit:
            mock_rate_limit.return_value = False  # Rate limit exceeded
            
            result = await notification_service.send_email_notification(
                mock_user.email, "Subject", "Body"
            )
        
        assert result is False


class TestReportingService:
    """Comprehensive unit tests for ReportingService"""

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session"""
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
    def reporting_service(self, mock_db_session, mock_ticket_repo, mock_user_repo):
        """Create ReportingService with mocked dependencies"""
        service = ReportingService(mock_db_session)
        service.ticket_repo = mock_ticket_repo
        service.user_repo = mock_user_repo
        return service

    # Dashboard Statistics Tests
    @pytest.mark.asyncio
    async def test_get_dashboard_statistics(self, reporting_service, mock_ticket_repo):
        """Test dashboard statistics retrieval"""
        mock_stats = {
            "total_tickets": 150,
            "open_tickets": 45,
            "in_progress_tickets": 30,
            "resolved_tickets": 60,
            "closed_tickets": 15,
            "high_priority_tickets": 20,
            "overdue_tickets": 8
        }
        mock_ticket_repo.get_dashboard_statistics.return_value = mock_stats
        
        result = await reporting_service.get_dashboard_statistics()
        
        assert result == mock_stats
        mock_ticket_repo.get_dashboard_statistics.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_department_statistics(self, reporting_service, mock_ticket_repo):
        """Test department-specific statistics"""
        department_id = 1
        mock_stats = {
            "total_tickets": 50,
            "avg_resolution_time": 2.5,
            "sla_compliance": 0.95,
            "user_performance": []
        }
        mock_ticket_repo.get_department_statistics.return_value = mock_stats
        
        result = await reporting_service.get_department_statistics(department_id)
        
        assert result == mock_stats
        mock_ticket_repo.get_department_statistics.assert_called_once_with(department_id)

    # Performance Metrics Tests
    @pytest.mark.asyncio
    async def test_get_performance_metrics(self, reporting_service, mock_ticket_repo):
        """Test performance metrics calculation"""
        date_from = datetime.utcnow() - timedelta(days=30)
        date_to = datetime.utcnow()
        
        mock_metrics = {
            "avg_response_time": 1.2,
            "avg_resolution_time": 24.5,
            "first_contact_resolution": 0.65,
            "customer_satisfaction": 4.2,
            "agent_utilization": 0.75
        }
        mock_ticket_repo.get_performance_metrics.return_value = mock_metrics
        
        result = await reporting_service.get_performance_metrics(date_from, date_to)
        
        assert result == mock_metrics
        mock_ticket_repo.get_performance_metrics.assert_called_once_with(date_from, date_to)

    @pytest.mark.asyncio
    async def test_get_user_performance(self, reporting_service, mock_ticket_repo):
        """Test individual user performance metrics"""
        user_id = 1
        mock_performance = {
            "tickets_created": 25,
            "tickets_resolved": 30,
            "avg_resolution_time": 18.5,
            "customer_rating": 4.5,
            "sla_compliance": 0.98
        }
        mock_ticket_repo.get_user_performance.return_value = mock_performance
        
        result = await reporting_service.get_user_performance(user_id)
        
        assert result == mock_performance
        mock_ticket_repo.get_user_performance.assert_called_once_with(user_id)

    # Trend Analysis Tests
    @pytest.mark.asyncio
    async def test_get_ticket_trends(self, reporting_service, mock_ticket_repo):
        """Test ticket trend analysis"""
        period = "month"
        mock_trends = [
            {"date": "2023-01", "created": 45, "resolved": 42},
            {"date": "2023-02", "created": 38, "resolved": 41},
            {"date": "2023-03", "created": 52, "resolved": 48}
        ]
        mock_ticket_repo.get_ticket_trends.return_value = mock_trends
        
        result = await reporting_service.get_ticket_trends(period)
        
        assert result == mock_trends
        mock_ticket_repo.get_ticket_trends.assert_called_once_with(period)

    @pytest.mark.asyncio
    async def test_get_sla_trends(self, reporting_service, mock_ticket_repo):
        """Test SLA compliance trends"""
        mock_sla_trends = [
            {"date": "2023-01", "sla_compliance": 0.95, "avg_resolution_time": 20.5},
            {"date": "2023-02", "sla_compliance": 0.92, "avg_resolution_time": 22.1},
            {"date": "2023-03", "sla_compliance": 0.97, "avg_resolution_time": 19.8}
        ]
        mock_ticket_repo.get_sla_trends.return_value = mock_sla_trends
        
        result = await reporting_service.get_sla_trends()
        
        assert result == mock_sla_trends
        mock_ticket_repo.get_sla_trends.assert_called_once()

    # Report Generation Tests
    @pytest.mark.asyncio
    async def test_generate_ticket_report(self, reporting_service, mock_ticket_repo):
        """Test ticket report generation"""
        filters = {
            "status": ["open", "in_progress"],
            "priority": ["high", "critical"],
            "date_from": "2023-01-01",
            "date_to": "2023-12-31"
        }
        
        mock_tickets = [
            {"id": 1, "title": "Ticket 1", "status": "open"},
            {"id": 2, "title": "Ticket 2", "status": "in_progress"}
        ]
        mock_ticket_repo.get_tickets_for_report.return_value = mock_tickets
        
        with patch.object(reporting_service, '_generate_csv_report') as mock_csv:
            mock_csv.return_value = "ticket_report.csv"
            
            result = await reporting_service.generate_ticket_report(filters, "csv")
        
        assert result == "ticket_report.csv"
        mock_csv.assert_called_once_with(mock_tickets, "tickets")

    @pytest.mark.asyncio
    async def test_generate_user_activity_report(self, reporting_service, mock_user_repo):
        """Test user activity report generation"""
        date_from = datetime.utcnow() - timedelta(days=30)
        date_to = datetime.utcnow()
        
        mock_activity = [
            {"user_id": 1, "username": "user1", "tickets_created": 15, "tickets_resolved": 12},
            {"user_id": 2, "username": "user2", "tickets_created": 20, "tickets_resolved": 18}
        ]
        mock_user_repo.get_user_activity.return_value = mock_activity
        
        with patch.object(reporting_service, '_generate_excel_report') as mock_excel:
            mock_excel.return_value = "user_activity.xlsx"
            
            result = await reporting_service.generate_user_activity_report(date_from, date_to, "excel")
        
        assert result == "user_activity.xlsx"
        mock_excel.assert_called_once_with(mock_activity, "user_activity")

    # Export Format Tests
    def test_generate_csv_report(self, reporting_service):
        """Test CSV report generation"""
        data = [
            {"id": 1, "title": "Ticket 1", "status": "open"},
            {"id": 2, "title": "Ticket 2", "status": "closed"}
        ]
        
        with patch('pandas.DataFrame.to_csv') as mock_to_csv:
            mock_to_csv.return_value = None
            
            result = reporting_service._generate_csv_report(data, "test_report")
        
        assert result.endswith(".csv")
        mock_to_csv.assert_called_once()

    def test_generate_excel_report(self, reporting_service):
        """Test Excel report generation"""
        data = [
            {"user": "user1", "count": 10},
            {"user": "user2", "count": 15}
        ]
        
        with patch('pandas.DataFrame.to_excel') as mock_to_excel:
            mock_to_excel.return_value = None
            
            result = reporting_service._generate_excel_report(data, "test_report")
        
        assert result.endswith(".xlsx")
        mock_to_excel.assert_called_once()

    def test_generate_pdf_report(self, reporting_service):
        """Test PDF report generation"""
        data = [{"field": "value"}]
        template_name = "ticket_report"
        
        with patch.object(reporting_service, '_render_pdf_template') as mock_render:
            mock_render.return_value = b"PDF content"
            
            result = reporting_service._generate_pdf_report(data, template_name)
        
        assert result.endswith(".pdf")
        mock_render.assert_called_once()

    # Advanced Analytics Tests
    @pytest.mark.asyncio
    async def test_get_predictive_analytics(self, reporting_service, mock_ticket_repo):
        """Test predictive analytics"""
        mock_predictions = {
            "predicted_volume": {
                "next_week": 45,
                "next_month": 180,
                "confidence": 0.85
            },
            "resource_requirements": {
                "additional_agents": 2,
                "peak_hours": ["09:00", "14:00"]
            }
        }
        
        with patch.object(reporting_service, '_calculate_predictions') as mock_predict:
            mock_predict.return_value = mock_predictions
            
            result = await reporting_service.get_predictive_analytics()
        
        assert result == mock_predictions

    @pytest.mark.asyncio
    async def test_get_workload_distribution(self, reporting_service, mock_user_repo):
        """Test workload distribution analysis"""
        mock_distribution = [
            {"user_id": 1, "username": "agent1", "active_tickets": 12, "workload_percentage": 75},
            {"user_id": 2, "username": "agent2", "active_tickets": 8, "workload_percentage": 50}
        ]
        mock_user_repo.get_workload_distribution.return_value = mock_distribution
        
        result = await reporting_service.get_workload_distribution()
        
        assert result == mock_distribution
        mock_user_repo.get_workload_distribution.assert_called_once()

    # Error Handling Tests
    @pytest.mark.asyncio
    async def test_report_generation_error_handling(self, reporting_service, mock_ticket_repo):
        """Test error handling in report generation"""
        mock_ticket_repo.get_tickets_for_report.side_effect = Exception("Database error")
        
        with pytest.raises(HTTPException) as exc_info:
            await reporting_service.generate_ticket_report({}, "csv")
        
        assert exc_info.value.status_code == 500
        assert "Report generation failed" in str(exc_info.value.detail)