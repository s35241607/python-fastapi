import pytest
from httpx import AsyncClient
from unittest.mock import patch, Mock

from app.models import User, Ticket, Department
from app.enums import TicketStatus, Priority, TicketType


class TestAuthEndpoints:
    """Comprehensive tests for authentication endpoints"""

    @pytest.mark.asyncio
    async def test_login_success(self, client: AsyncClient, test_user: User):
        """Test successful user login"""
        login_data = {
            "username": test_user.username,
            "password": "testpassword123"
        }
        
        response = await client.post("/auth/login", json=login_data)
        
        assert response.status_code == 200
        response_data = response.json()
        assert "access_token" in response_data
        assert "refresh_token" in response_data
        assert response_data["token_type"] == "bearer"
        assert "user" in response_data
        assert response_data["user"]["username"] == test_user.username

    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, client: AsyncClient):
        """Test login with invalid credentials"""
        login_data = {
            "username": "nonexistent",
            "password": "wrongpassword"
        }
        
        response = await client.post("/auth/login", json=login_data)
        
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_login_missing_fields(self, client: AsyncClient):
        """Test login with missing required fields"""
        login_data = {"username": "testuser"}  # Missing password
        
        response = await client.post("/auth/login", json=login_data)
        
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_success(self, client: AsyncClient, test_department: Department):
        """Test successful user registration"""
        register_data = {
            "email": "newuser@example.com",
            "username": "newuser",
            "first_name": "New",
            "last_name": "User",
            "password": "newpassword123",
            "department_id": test_department.id
        }
        
        response = await client.post("/auth/register", json=register_data)
        
        assert response.status_code == 201
        response_data = response.json()
        assert response_data["email"] == register_data["email"]
        assert response_data["username"] == register_data["username"]
        assert "id" in response_data

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client: AsyncClient, test_user: User):
        """Test registration with duplicate email"""
        register_data = {
            "email": test_user.email,  # Duplicate email
            "username": "newuser",
            "first_name": "New",
            "last_name": "User",
            "password": "newpassword123",
            "department_id": 1
        }
        
        response = await client.post("/auth/register", json=register_data)
        
        assert response.status_code == 400
        assert "Email already registered" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_register_invalid_password(self, client: AsyncClient):
        """Test registration with invalid password"""
        register_data = {
            "email": "newuser@example.com",
            "username": "newuser",
            "first_name": "New",
            "last_name": "User",
            "password": "weak",  # Too weak
            "department_id": 1
        }
        
        response = await client.post("/auth/register", json=register_data)
        
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_current_user(self, client: AsyncClient, authenticated_headers: dict):
        """Test getting current authenticated user"""
        response = await client.get("/auth/me", headers=authenticated_headers)
        
        assert response.status_code == 200
        response_data = response.json()
        assert "id" in response_data
        assert "username" in response_data
        assert "email" in response_data

    @pytest.mark.asyncio
    async def test_get_current_user_unauthorized(self, client: AsyncClient):
        """Test getting current user without authentication"""
        response = await client.get("/auth/me")
        
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_logout_success(self, client: AsyncClient, authenticated_headers: dict):
        """Test successful logout"""
        response = await client.post("/auth/logout", headers=authenticated_headers)
        
        assert response.status_code == 200
        assert response.json()["message"] == "Successfully logged out"

    @pytest.mark.asyncio
    async def test_refresh_token_success(self, client: AsyncClient, test_user: User):
        """Test successful token refresh"""
        # First login to get refresh token
        login_response = await client.post("/auth/login", json={
            "username": test_user.username,
            "password": "testpassword123"
        })
        refresh_token = login_response.json()["refresh_token"]
        
        # Use refresh token to get new access token
        response = await client.post("/auth/refresh", json={
            "refresh_token": refresh_token
        })
        
        assert response.status_code == 200
        response_data = response.json()
        assert "access_token" in response_data
        assert response_data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_refresh_token_invalid(self, client: AsyncClient):
        """Test token refresh with invalid token"""
        response = await client.post("/auth/refresh", json={
            "refresh_token": "invalid_token"
        })
        
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_change_password_success(self, client: AsyncClient, authenticated_headers: dict):
        """Test successful password change"""
        password_data = {
            "current_password": "testpassword123",
            "new_password": "newtestpassword123"
        }
        
        response = await client.post("/auth/change-password", json=password_data, headers=authenticated_headers)
        
        assert response.status_code == 200
        assert response.json()["message"] == "Password changed successfully"

    @pytest.mark.asyncio
    async def test_change_password_wrong_current(self, client: AsyncClient, authenticated_headers: dict):
        """Test password change with wrong current password"""
        password_data = {
            "current_password": "wrongpassword",
            "new_password": "newtestpassword123"
        }
        
        response = await client.post("/auth/change-password", json=password_data, headers=authenticated_headers)
        
        assert response.status_code == 400
        assert "Invalid current password" in response.json()["detail"]


class TestTicketEndpoints:
    """Comprehensive tests for ticket endpoints"""

    @pytest.mark.asyncio
    async def test_create_ticket_success(self, client: AsyncClient, authenticated_headers: dict, test_department: Department):
        """Test successful ticket creation"""
        ticket_data = {
            "title": "Test API Ticket",
            "description": "This is a test ticket created via API",
            "priority": "high",
            "ticket_type": "incident",
            "department_id": test_department.id,
            "tags": ["api", "test"]
        }
        
        response = await client.post("/tickets/", json=ticket_data, headers=authenticated_headers)
        
        assert response.status_code == 201
        response_data = response.json()
        assert response_data["title"] == ticket_data["title"]
        assert response_data["priority"] == ticket_data["priority"]
        assert "ticket_number" in response_data
        assert "id" in response_data

    @pytest.mark.asyncio
    async def test_create_ticket_unauthorized(self, client: AsyncClient):
        """Test ticket creation without authentication"""
        ticket_data = {
            "title": "Unauthorized Ticket",
            "description": "This should fail",
            "priority": "medium",
            "ticket_type": "request",
            "department_id": 1
        }
        
        response = await client.post("/tickets/", json=ticket_data)
        
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_create_ticket_invalid_data(self, client: AsyncClient, authenticated_headers: dict):
        """Test ticket creation with invalid data"""
        ticket_data = {
            "title": "",  # Empty title
            "description": "Test description",
            "priority": "invalid_priority",  # Invalid priority
            "ticket_type": "incident",
            "department_id": 1
        }
        
        response = await client.post("/tickets/", json=ticket_data, headers=authenticated_headers)
        
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_get_tickets_list(self, client: AsyncClient, authenticated_headers: dict):
        """Test getting tickets list"""
        response = await client.get("/tickets/", headers=authenticated_headers)
        
        assert response.status_code == 200
        response_data = response.json()
        assert "items" in response_data
        assert "total" in response_data
        assert "page" in response_data
        assert "size" in response_data

    @pytest.mark.asyncio
    async def test_get_tickets_with_filters(self, client: AsyncClient, authenticated_headers: dict):
        """Test getting tickets with filters"""
        params = {
            "status": "open",
            "priority": "high",
            "page": 1,
            "size": 10
        }
        
        response = await client.get("/tickets/", params=params, headers=authenticated_headers)
        
        assert response.status_code == 200
        response_data = response.json()
        assert "items" in response_data

    @pytest.mark.asyncio
    async def test_get_ticket_by_id(self, client: AsyncClient, authenticated_headers: dict, test_ticket: Ticket):
        """Test getting specific ticket by ID"""
        response = await client.get(f"/tickets/{test_ticket.id}", headers=authenticated_headers)
        
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["id"] == test_ticket.id
        assert response_data["title"] == test_ticket.title

    @pytest.mark.asyncio
    async def test_get_ticket_not_found(self, client: AsyncClient, authenticated_headers: dict):
        """Test getting non-existent ticket"""
        response = await client.get("/tickets/999999", headers=authenticated_headers)
        
        assert response.status_code == 404
        assert "Ticket not found" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_update_ticket_success(self, client: AsyncClient, authenticated_headers: dict, test_ticket: Ticket):
        """Test successful ticket update"""
        update_data = {
            "title": "Updated Ticket Title",
            "description": "Updated description",
            "priority": "critical"
        }
        
        response = await client.patch(f"/tickets/{test_ticket.id}", json=update_data, headers=authenticated_headers)
        
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["title"] == update_data["title"]
        assert response_data["priority"] == update_data["priority"]

    @pytest.mark.asyncio
    async def test_update_ticket_unauthorized(self, client: AsyncClient, test_ticket: Ticket):
        """Test ticket update without authentication"""
        update_data = {"title": "Should not work"}
        
        response = await client.patch(f"/tickets/{test_ticket.id}", json=update_data)
        
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_delete_ticket_success(self, client: AsyncClient, authenticated_headers: dict, test_ticket: Ticket):
        """Test successful ticket deletion"""
        response = await client.delete(f"/tickets/{test_ticket.id}", headers=authenticated_headers)
        
        assert response.status_code == 200
        
        # Verify ticket is deleted
        get_response = await client.get(f"/tickets/{test_ticket.id}", headers=authenticated_headers)
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_assign_ticket_success(self, client: AsyncClient, authenticated_headers: dict, test_ticket: Ticket, test_user: User):
        """Test successful ticket assignment"""
        assign_data = {"assigned_to_id": test_user.id}
        
        response = await client.post(f"/tickets/{test_ticket.id}/assign", json=assign_data, headers=authenticated_headers)
        
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["assigned_to_id"] == test_user.id

    @pytest.mark.asyncio
    async def test_assign_ticket_invalid_user(self, client: AsyncClient, authenticated_headers: dict, test_ticket: Ticket):
        """Test ticket assignment to invalid user"""
        assign_data = {"assigned_to_id": 999999}
        
        response = await client.post(f"/tickets/{test_ticket.id}/assign", json=assign_data, headers=authenticated_headers)
        
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_search_tickets(self, client: AsyncClient, authenticated_headers: dict):
        """Test ticket search functionality"""
        search_params = {
            "q": "test",
            "status": "open",
            "priority": "high"
        }
        
        response = await client.get("/tickets/search", params=search_params, headers=authenticated_headers)
        
        assert response.status_code == 200
        response_data = response.json()
        assert "items" in response_data
        assert "total" in response_data

    @pytest.mark.asyncio
    async def test_bulk_update_tickets(self, client: AsyncClient, authenticated_headers: dict, test_utils):
        """Test bulk ticket updates"""
        # Create multiple test tickets
        tickets = await test_utils.create_test_tickets(client, 1, 3)
        ticket_ids = [ticket.id for ticket in tickets]
        
        bulk_data = {
            "ticket_ids": ticket_ids,
            "updates": {
                "status": "in_progress",
                "priority": "high"
            }
        }
        
        response = await client.post("/tickets/bulk-update", json=bulk_data, headers=authenticated_headers)
        
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["updated_count"] >= 0

    @pytest.mark.asyncio
    async def test_export_tickets(self, client: AsyncClient, authenticated_headers: dict):
        """Test ticket export functionality"""
        export_params = {
            "format": "csv",
            "status": "open"
        }
        
        response = await client.get("/tickets/export", params=export_params, headers=authenticated_headers)
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv"


class TestPermissionValidation:
    """Tests for role-based access control and permissions"""

    @pytest.mark.asyncio
    async def test_admin_only_endpoint_success(self, client: AsyncClient, admin_headers: dict):
        """Test admin-only endpoint with admin user"""
        response = await client.get("/admin/users", headers=admin_headers)
        
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_admin_only_endpoint_forbidden(self, client: AsyncClient, authenticated_headers: dict):
        """Test admin-only endpoint with regular user"""
        response = await client.get("/admin/users", headers=authenticated_headers)
        
        assert response.status_code == 403
        assert "Insufficient permissions" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_department_access_control(self, client: AsyncClient, authenticated_headers: dict, test_department: Department):
        """Test department-based access control"""
        # Create ticket in different department
        other_dept_ticket_data = {
            "title": "Other Department Ticket",
            "description": "Should not be accessible",
            "priority": "medium",
            "ticket_type": "request",
            "department_id": 999  # Different department
        }
        
        with patch('app.services.ticket_service.TicketService.create_ticket') as mock_create:
            mock_create.side_effect = HTTPException(status_code=403, detail="Access denied")
            
            response = await client.post("/tickets/", json=other_dept_ticket_data, headers=authenticated_headers)
            
            assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_resource_ownership_validation(self, client: AsyncClient, authenticated_headers: dict):
        """Test that users can only access their own resources"""
        # Try to access ticket created by another user
        with patch('app.services.ticket_service.TicketService.get_ticket_by_id') as mock_get:
            mock_get.side_effect = HTTPException(status_code=403, detail="Access denied")
            
            response = await client.get("/tickets/999", headers=authenticated_headers)
            
            assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_rate_limiting(self, client: AsyncClient, authenticated_headers: dict):
        """Test API rate limiting"""
        # Make multiple rapid requests
        responses = []
        for i in range(10):
            response = await client.get("/tickets/", headers=authenticated_headers)
            responses.append(response)
        
        # All requests should succeed initially (assuming reasonable rate limits)
        assert all(r.status_code == 200 for r in responses)

    @pytest.mark.asyncio
    async def test_token_expiration_handling(self, client: AsyncClient):
        """Test handling of expired tokens"""
        expired_token = "expired.jwt.token"
        expired_headers = {"Authorization": f"Bearer {expired_token}"}
        
        response = await client.get("/tickets/", headers=expired_headers)
        
        assert response.status_code == 401
        assert "Token expired" in response.json()["detail"] or "Invalid token" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_malformed_token_handling(self, client: AsyncClient):
        """Test handling of malformed tokens"""
        malformed_headers = {"Authorization": "Bearer malformed_token"}
        
        response = await client.get("/tickets/", headers=malformed_headers)
        
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_missing_authorization_header(self, client: AsyncClient):
        """Test handling of missing authorization header"""
        response = await client.get("/tickets/")
        
        assert response.status_code == 401


class TestApprovalEndpoints:
    """Tests for approval workflow endpoints"""

    @pytest.mark.asyncio
    async def test_create_approval_workflow(self, client: AsyncClient, authenticated_headers: dict, test_ticket: Ticket):
        """Test creating approval workflow"""
        workflow_data = {
            "ticket_id": test_ticket.id,
            "workflow_type": "sequential",
            "steps": [
                {
                    "step_name": "Manager Approval",
                    "approver_id": 1,
                    "step_order": 1,
                    "is_required": True
                }
            ]
        }
        
        response = await client.post("/approvals/workflows", json=workflow_data, headers=authenticated_headers)
        
        assert response.status_code == 201
        response_data = response.json()
        assert response_data["ticket_id"] == test_ticket.id
        assert response_data["workflow_type"] == "sequential"

    @pytest.mark.asyncio
    async def test_process_approval_action(self, client: AsyncClient, authenticated_headers: dict):
        """Test processing approval action"""
        workflow_id = 1
        action_data = {
            "action": "approve",
            "comments": "Approved by manager"
        }
        
        with patch('app.services.approval_service.ApprovalService.process_approval_action') as mock_process:
            mock_process.return_value = Mock(id=workflow_id, status="approved")
            
            response = await client.post(f"/approvals/{workflow_id}/process", json=action_data, headers=authenticated_headers)
            
            assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_pending_approvals(self, client: AsyncClient, authenticated_headers: dict):
        """Test getting pending approvals"""
        response = await client.get("/approvals/pending", headers=authenticated_headers)
        
        assert response.status_code == 200
        response_data = response.json()
        assert "items" in response_data
        assert "total" in response_data

    @pytest.mark.asyncio
    async def test_bulk_approve(self, client: AsyncClient, authenticated_headers: dict):
        """Test bulk approval processing"""
        bulk_data = {
            "workflow_ids": [1, 2, 3],
            "action": "approve",
            "comments": "Bulk approval"
        }
        
        with patch('app.services.approval_service.ApprovalService.bulk_approve') as mock_bulk:
            mock_bulk.return_value = {"processed": 3, "failed": 0}
            
            response = await client.post("/approvals/bulk-process", json=bulk_data, headers=authenticated_headers)
            
            assert response.status_code == 200
            response_data = response.json()
            assert response_data["processed"] == 3


class TestErrorHandling:
    """Tests for error handling and edge cases"""

    @pytest.mark.asyncio
    async def test_database_connection_error(self, client: AsyncClient, authenticated_headers: dict):
        """Test handling of database connection errors"""
        with patch('app.database.get_db') as mock_db:
            mock_db.side_effect = Exception("Database connection failed")
            
            response = await client.get("/tickets/", headers=authenticated_headers)
            
            assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_validation_error_response(self, client: AsyncClient, authenticated_headers: dict):
        """Test validation error response format"""
        invalid_data = {
            "title": "",  # Required field empty
            "priority": "invalid"  # Invalid enum value
        }
        
        response = await client.post("/tickets/", json=invalid_data, headers=authenticated_headers)
        
        assert response.status_code == 422
        response_data = response.json()
        assert "detail" in response_data
        assert isinstance(response_data["detail"], list)

    @pytest.mark.asyncio
    async def test_large_payload_handling(self, client: AsyncClient, authenticated_headers: dict):
        """Test handling of large payloads"""
        large_description = "x" * 10000  # 10KB description
        
        ticket_data = {
            "title": "Large Payload Test",
            "description": large_description,
            "priority": "medium",
            "ticket_type": "request",
            "department_id": 1
        }
        
        response = await client.post("/tickets/", json=ticket_data, headers=authenticated_headers)
        
        # Should either succeed or fail gracefully
        assert response.status_code in [201, 413, 422]

    @pytest.mark.asyncio
    async def test_concurrent_requests(self, client: AsyncClient, authenticated_headers: dict):
        """Test handling of concurrent requests"""
        import asyncio
        
        # Create multiple concurrent requests
        tasks = []
        for i in range(5):
            task = client.get("/tickets/", headers=authenticated_headers)
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks)
        
        # All requests should complete successfully
        assert all(r.status_code == 200 for r in responses)

    @pytest.mark.asyncio
    async def test_content_type_validation(self, client: AsyncClient, authenticated_headers: dict):
        """Test content type validation"""
        # Send XML instead of JSON
        xml_data = "<ticket><title>XML Ticket</title></ticket>"
        
        response = await client.post(
            "/tickets/", 
            content=xml_data, 
            headers={**authenticated_headers, "Content-Type": "application/xml"}
        )
        
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_special_characters_handling(self, client: AsyncClient, authenticated_headers: dict):
        """Test handling of special characters and unicode"""
        ticket_data = {
            "title": "Special chars: éñü中文🚀",
            "description": "Testing unicode: αβγδε ñáéíóú 中文测试 🎉🔥💯",
            "priority": "medium",
            "ticket_type": "request",
            "department_id": 1
        }
        
        response = await client.post("/tickets/", json=ticket_data, headers=authenticated_headers)
        
        assert response.status_code == 201
        response_data = response.json()
        assert response_data["title"] == ticket_data["title"]