"""
Enterprise Ticket Management System - Load Testing
Simulates 1000+ concurrent users with realistic behavior patterns
"""

import random
import json
from datetime import datetime, timedelta
from locust import HttpUser, task, between, events, tag
from locust.contrib.fasthttp import FastHttpUser
import logging


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TicketManagementUser(FastHttpUser):
    """
    Simulates a real user of the ticket management system
    with realistic behavior patterns and timing
    """
    
    # Realistic user behavior timing - between 1-5 seconds between actions
    wait_time = between(1, 5)
    
    # User session data
    user_token = None
    user_id = None
    user_role = None
    created_tickets = []
    
    def on_start(self):
        """Called when a user starts - perform login"""
        self.login()
        
    def on_stop(self):
        """Called when a user stops - perform logout"""
        if self.user_token:
            self.logout()
    
    def login(self):
        """Authenticate user and get token"""
        # Create different user types for realistic testing
        user_types = [
            {"role": "user", "username": f"user_{random.randint(1, 1000)}", "password": "testpass123"},
            {"role": "manager", "username": f"manager_{random.randint(1, 100)}", "password": "testpass123"},
            {"role": "admin", "username": f"admin_{random.randint(1, 10)}", "password": "testpass123"}
        ]
        
        user_data = random.choice(user_types)
        self.user_role = user_data["role"]
        
        login_data = {
            "username": user_data["username"],
            "password": user_data["password"]
        }
        
        with self.client.post("/auth/login", json=login_data, catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                self.user_token = data.get("access_token")
                self.user_id = data.get("user", {}).get("id")
                response.success()
                logger.info(f"User {user_data['username']} logged in successfully")
            else:
                # Create user if doesn't exist
                self.register_user(user_data)
                response.failure("Login failed, attempting registration")
    
    def register_user(self, user_data):
        """Register a new user if login fails"""
        register_data = {
            "username": user_data["username"],
            "password": user_data["password"],
            "email": f"{user_data['username']}@loadtest.com",
            "first_name": "Load",
            "last_name": "Test",
            "department_id": random.randint(1, 5)
        }
        
        with self.client.post("/auth/register", json=register_data, catch_response=True) as response:
            if response.status_code == 201:
                # Try login again
                self.login()
                response.success()
            else:
                response.failure("Registration failed")
    
    def logout(self):
        """Logout user"""
        if self.user_token:
            headers = {"Authorization": f"Bearer {self.user_token}"}
            with self.client.post("/auth/logout", headers=headers, catch_response=True) as response:
                if response.status_code == 200:
                    response.success()
                else:
                    response.failure("Logout failed")
    
    def get_auth_headers(self):
        """Get authorization headers"""
        return {"Authorization": f"Bearer {self.user_token}"} if self.user_token else {}
    
    @task(20)
    @tag('dashboard')
    def view_dashboard(self):
        """View dashboard - most common action"""
        headers = self.get_auth_headers()
        with self.client.get("/reports/dashboard", headers=headers, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Dashboard load failed: {response.status_code}")
    
    @task(15)
    @tag('tickets')
    def list_tickets(self):
        """List tickets with various filters"""
        headers = self.get_auth_headers()
        
        # Simulate different search patterns
        search_params = [
            {},  # No filters
            {"status": "open"},
            {"priority": "high"},
            {"status": "in_progress", "priority": "medium"},
            {"search": "test"},
            {"created_by_id": self.user_id} if self.user_id else {},
            {"page": random.randint(1, 5), "size": 20}
        ]
        
        params = random.choice(search_params)
        
        with self.client.get("/tickets/", params=params, headers=headers, catch_response=True) as response:
            if response.status_code == 200:
                data = response.json()
                response.success()
                logger.debug(f"Retrieved {len(data.get('items', []))} tickets")
            else:
                response.failure(f"Ticket list failed: {response.status_code}")
    
    @task(10)
    @tag('tickets')
    def create_ticket(self):
        """Create new tickets"""
        headers = self.get_auth_headers()
        
        ticket_data = {
            "title": f"Load Test Ticket {random.randint(1000, 9999)}",
            "description": f"This is a load test ticket created at {datetime.utcnow()}",
            "priority": random.choice(["low", "medium", "high", "critical"]),
            "ticket_type": random.choice(["incident", "request", "problem", "change"]),
            "department_id": random.randint(1, 5),
            "tags": [f"loadtest", f"tag{random.randint(1, 10)}"]
        }
        
        with self.client.post("/tickets/", json=ticket_data, headers=headers, catch_response=True) as response:
            if response.status_code == 201:
                ticket = response.json()
                self.created_tickets.append(ticket["id"])
                response.success()
                logger.info(f"Created ticket {ticket['id']}")
            else:
                response.failure(f"Ticket creation failed: {response.status_code}")
    
    @task(8)
    @tag('tickets')
    def view_ticket_detail(self):
        """View ticket details"""
        headers = self.get_auth_headers()
        
        # Use created tickets or random ID
        if self.created_tickets:
            ticket_id = random.choice(self.created_tickets)
        else:
            ticket_id = random.randint(1, 100)
        
        with self.client.get(f"/tickets/{ticket_id}", headers=headers, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                response.success()  # Expected for random IDs
            else:
                response.failure(f"Ticket detail failed: {response.status_code}")
    
    @task(6)
    @tag('tickets')
    def update_ticket(self):
        """Update existing tickets"""
        if not self.created_tickets:
            return
        
        headers = self.get_auth_headers()
        ticket_id = random.choice(self.created_tickets)
        
        update_data = {
            "status": random.choice(["open", "in_progress", "resolved"]),
            "priority": random.choice(["low", "medium", "high"])
        }
        
        with self.client.patch(f"/tickets/{ticket_id}", json=update_data, headers=headers, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Ticket update failed: {response.status_code}")
    
    @task(5)
    @tag('comments')
    def add_comment(self):
        """Add comments to tickets"""
        if not self.created_tickets:
            return
        
        headers = self.get_auth_headers()
        ticket_id = random.choice(self.created_tickets)
        
        comment_data = {
            "content": f"Load test comment added at {datetime.utcnow()}",
            "is_internal": random.choice([True, False])
        }
        
        with self.client.post(f"/comments/ticket/{ticket_id}", json=comment_data, headers=headers, catch_response=True) as response:
            if response.status_code == 201:
                response.success()
            else:
                response.failure(f"Comment creation failed: {response.status_code}")
    
    @task(4)
    @tag('search')
    def search_tickets(self):
        """Perform search operations"""
        headers = self.get_auth_headers()
        
        search_terms = [
            "test", "urgent", "system", "error", "request", 
            "network", "software", "hardware", "issue", "problem"
        ]
        
        search_query = {
            "search": random.choice(search_terms),
            "page": 1,
            "size": 10
        }
        
        with self.client.get("/tickets/search", params=search_query, headers=headers, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Search failed: {response.status_code}")
    
    @task(3)
    @tag('approvals')
    def view_approvals(self):
        """View approval queue (manager/admin only)"""
        if self.user_role not in ["manager", "admin"]:
            return
        
        headers = self.get_auth_headers()
        
        with self.client.get("/approvals/pending", headers=headers, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 403:
                response.success()  # Expected for insufficient permissions
            else:
                response.failure(f"Approvals view failed: {response.status_code}")
    
    @task(2)
    @tag('reports')
    def view_reports(self):
        """View various reports"""
        headers = self.get_auth_headers()
        
        report_endpoints = [
            "/reports/metrics",
            "/reports/ticket-statistics",
            "/reports/sla-compliance",
            "/reports/user-performance"
        ]
        
        endpoint = random.choice(report_endpoints)
        
        with self.client.get(endpoint, headers=headers, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 403:
                response.success()  # Expected for permission restrictions
            else:
                response.failure(f"Report {endpoint} failed: {response.status_code}")
    
    @task(1)
    @tag('files')
    def upload_file(self):
        """Simulate file uploads"""
        if not self.created_tickets:
            return
        
        headers = self.get_auth_headers()
        ticket_id = random.choice(self.created_tickets)
        
        # Simulate small file upload
        files = {
            'file': ('test_file.txt', b'This is a test file for load testing', 'text/plain')
        }
        
        with self.client.post(f"/attachments/ticket/{ticket_id}/upload", 
                            files=files, headers=headers, catch_response=True) as response:
            if response.status_code in [200, 201]:
                response.success()
            else:
                response.failure(f"File upload failed: {response.status_code}")


class AdminUser(TicketManagementUser):
    """
    Specialized user type for admin operations
    Performs more administrative tasks
    """
    
    wait_time = between(2, 8)  # Admins tend to be more deliberate
    
    @task(5)
    @tag('admin')
    def manage_users(self):
        """Admin user management tasks"""
        if self.user_role != "admin":
            return
        
        headers = self.get_auth_headers()
        
        with self.client.get("/auth/users", headers=headers, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"User management failed: {response.status_code}")
    
    @task(3)
    @tag('admin')
    def bulk_operations(self):
        """Perform bulk operations"""
        if self.user_role != "admin":
            return
        
        headers = self.get_auth_headers()
        
        # Simulate bulk ticket updates
        bulk_data = {
            "ticket_ids": [random.randint(1, 100) for _ in range(5)],
            "updates": {"priority": "low"}
        }
        
        with self.client.patch("/tickets/bulk-update", json=bulk_data, headers=headers, catch_response=True) as response:
            if response.status_code in [200, 207]:  # 207 for partial success
                response.success()
            else:
                response.failure(f"Bulk operation failed: {response.status_code}")


# Load testing event handlers
@events.init.add_listener
def on_locust_init(environment, **kwargs):
    """Initialize load test environment"""
    logger.info("Initializing load test environment...")
    logger.info("Target: Enterprise Ticket Management System")
    logger.info("Goal: Simulate 1000+ concurrent users")


@events.test_start.add_listener  
def on_test_start(environment, **kwargs):
    """Called when test starts"""
    logger.info("Load test started!")
    logger.info(f"Target host: {environment.host}")
    logger.info("Simulating enterprise-grade concurrent usage...")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when test stops - generate performance report"""
    logger.info("Load test completed!")
    
    stats = environment.stats
    total_rps = stats.total.current_rps
    avg_response_time = stats.total.avg_response_time
    max_response_time = stats.total.max_response_time
    failure_ratio = stats.total.fail_ratio
    
    logger.info("=== LOAD TEST RESULTS ===")
    logger.info(f"Total Requests: {stats.total.num_requests}")
    logger.info(f"Requests per Second: {total_rps:.2f}")
    logger.info(f"Average Response Time: {avg_response_time:.2f}ms")
    logger.info(f"Max Response Time: {max_response_time:.2f}ms")
    logger.info(f"Failure Rate: {failure_ratio*100:.2f}%")
    
    # Performance benchmarks for enterprise system
    if total_rps >= 100:
        logger.info("✓ RPS benchmark met (>100 RPS)")
    else:
        logger.warning("⚠ RPS benchmark not met (<100 RPS)")
    
    if avg_response_time <= 2000:  # 2 seconds
        logger.info("✓ Response time benchmark met (<2000ms)")
    else:
        logger.warning("⚠ Response time benchmark not met (>2000ms)")
    
    if failure_ratio <= 0.01:  # 1% failure rate
        logger.info("✓ Reliability benchmark met (<1% failures)")
    else:
        logger.warning("⚠ Reliability benchmark not met (>1% failures)")


# Custom user classes for different load patterns
class ManagerUser(TicketManagementUser):
    """Manager-specific user behavior"""
    weight = 2  # Managers are less common than regular users
    
    @task(10)
    @tag('management')
    def review_team_tickets(self):
        """Managers review team tickets more frequently"""
        headers = self.get_auth_headers()
        
        params = {
            "department_id": random.randint(1, 5),
            "status": "pending_approval"
        }
        
        with self.client.get("/tickets/", params=params, headers=headers, catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Team ticket review failed: {response.status_code}")


# Performance testing scenarios
class HighVolumeUser(FastHttpUser):
    """
    High-volume user for stress testing
    Simulates peak usage periods
    """
    
    wait_time = between(0.1, 0.5)  # Very fast interactions
    user_token = None
    
    def on_start(self):
        # Quick authentication
        login_data = {
            "username": f"stress_user_{random.randint(1, 10000)}",
            "password": "testpass123"
        }
        
        response = self.client.post("/auth/login", json=login_data)
        if response.status_code == 200:
            self.user_token = response.json().get("access_token")
    
    @task
    def rapid_dashboard_access(self):
        """Rapid dashboard access to test caching and performance"""
        if not self.user_token:
            return
        
        headers = {"Authorization": f"Bearer {self.user_token}"}
        self.client.get("/reports/dashboard", headers=headers)
    
    @task  
    def rapid_ticket_list(self):
        """Rapid ticket listing to test database performance"""
        if not self.user_token:
            return
        
        headers = {"Authorization": f"Bearer {self.user_token}"}
        params = {"page": random.randint(1, 10), "size": 20}
        self.client.get("/tickets/", params=params, headers=headers)


if __name__ == "__main__":
    # This allows running the load test directly
    import os
    os.system("locust -f locustfile.py --host=http://localhost:8000")