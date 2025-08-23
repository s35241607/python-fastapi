import os
import sys
import pytest
import asyncio
from typing import AsyncGenerator, Generator
from unittest.mock import Mock, AsyncMock
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from httpx import AsyncClient

# Add the app directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.main import app
from app.database import get_db, Base
from app.models import User, Ticket, Department, ApprovalWorkflow
from app.core.config import settings


# Test Database Configuration
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"
TEST_SYNC_DATABASE_URL = "sqlite:///./test.db"

# Async test engine
test_async_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,
    future=True
)

# Sync test engine for setup/teardown
test_sync_engine = create_engine(TEST_SYNC_DATABASE_URL, echo=False)

# Session makers
TestAsyncSessionLocal = async_sessionmaker(
    test_async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

TestSyncSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_sync_engine
)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
async def setup_test_database():
    """Set up test database before running tests."""
    # Create all tables
    async with test_async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield
    
    # Clean up after tests
    async with test_async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh database session for each test."""
    async with TestAsyncSessionLocal() as session:
        yield session
        await session.rollback()


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create test client with database dependency override."""
    
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest.fixture
def sync_client() -> Generator[TestClient, None, None]:
    """Create synchronous test client for simple tests."""
    with TestClient(app) as client:
        yield client


# Mock Data Fixtures
@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "email": "test@example.com",
        "username": "testuser",
        "first_name": "Test",
        "last_name": "User",
        "password": "testpassword123",
        "department_id": 1
    }


@pytest.fixture
def sample_ticket_data():
    """Sample ticket data for testing."""
    return {
        "title": "Test Ticket",
        "description": "This is a test ticket",
        "priority": "medium",
        "ticket_type": "incident",
        "department_id": 1,
        "tags": ["test", "example"]
    }


@pytest.fixture
def sample_department_data():
    """Sample department data for testing."""
    return {
        "name": "IT Department",
        "manager_id": 1,
        "budget_limit": 100000.00,
        "approval_rules": {
            "auto_approve_limit": 1000,
            "require_manager_approval": True
        }
    }


@pytest.fixture
async def test_user(db_session: AsyncSession) -> User:
    """Create a test user in the database."""
    from app.services.auth_service import get_password_hash
    
    user = User(
        email="testuser@example.com",
        username="testuser",
        first_name="Test",
        last_name="User",
        hashed_password=get_password_hash("testpassword123"),
        department_id=1,
        is_active=True
    )
    
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    return user


@pytest.fixture
async def test_admin_user(db_session: AsyncSession) -> User:
    """Create a test admin user in the database."""
    from app.services.auth_service import get_password_hash
    
    admin_user = User(
        email="admin@example.com",
        username="admin",
        first_name="Admin",
        last_name="User",
        hashed_password=get_password_hash("adminpassword123"),
        department_id=1,
        is_active=True,
        role="admin"
    )
    
    db_session.add(admin_user)
    await db_session.commit()
    await db_session.refresh(admin_user)
    
    return admin_user


@pytest.fixture
async def test_department(db_session: AsyncSession) -> Department:
    """Create a test department in the database."""
    department = Department(
        name="Test Department",
        manager_id=1,
        budget_limit=50000.00,
        approval_rules={
            "auto_approve_limit": 500,
            "require_manager_approval": True
        }
    )
    
    db_session.add(department)
    await db_session.commit()
    await db_session.refresh(department)
    
    return department


@pytest.fixture
async def test_ticket(db_session: AsyncSession, test_user: User, test_department: Department) -> Ticket:
    """Create a test ticket in the database."""
    from app.enums import TicketStatus, Priority, TicketType
    
    ticket = Ticket(
        ticket_number="TEST-001",
        title="Test Ticket",
        description="This is a test ticket for testing purposes",
        status=TicketStatus.OPEN,
        priority=Priority.MEDIUM,
        ticket_type=TicketType.INCIDENT,
        created_by_id=test_user.id,
        department_id=test_department.id,
        tags=["test", "automated"]
    )
    
    db_session.add(ticket)
    await db_session.commit()
    await db_session.refresh(ticket)
    
    return ticket


@pytest.fixture
async def authenticated_headers(client: AsyncClient, test_user: User) -> dict:
    """Get authentication headers for API requests."""
    # Login to get token
    login_data = {
        "username": test_user.username,
        "password": "testpassword123"
    }
    
    response = await client.post("/auth/login", json=login_data)
    assert response.status_code == 200
    
    token_data = response.json()
    access_token = token_data["access_token"]
    
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
async def admin_headers(client: AsyncClient, test_admin_user: User) -> dict:
    """Get admin authentication headers for API requests."""
    login_data = {
        "username": test_admin_user.username,
        "password": "adminpassword123"
    }
    
    response = await client.post("/auth/login", json=login_data)
    assert response.status_code == 200
    
    token_data = response.json()
    access_token = token_data["access_token"]
    
    return {"Authorization": f"Bearer {access_token}"}


# Mock Service Fixtures
@pytest.fixture
def mock_notification_service():
    """Mock notification service for testing."""
    mock_service = Mock()
    mock_service.send_email = AsyncMock()
    mock_service.send_teams_notification = AsyncMock()
    mock_service.send_slack_notification = AsyncMock()
    mock_service.send_ticket_created_notification = AsyncMock()
    mock_service.send_ticket_updated_notification = AsyncMock()
    mock_service.send_ticket_assigned_notification = AsyncMock()
    mock_service.send_approval_requested_notification = AsyncMock()
    mock_service.send_approval_processed_notification = AsyncMock()
    return mock_service


@pytest.fixture
def mock_file_service():
    """Mock file service for testing."""
    mock_service = Mock()
    mock_service.upload_file = AsyncMock()
    mock_service.download_file = AsyncMock()
    mock_service.delete_file = AsyncMock()
    mock_service.validate_file = Mock(return_value=True)
    return mock_service


@pytest.fixture
def mock_search_service():
    """Mock search service for testing."""
    mock_service = Mock()
    mock_service.index_document = AsyncMock()
    mock_service.search_documents = AsyncMock()
    mock_service.delete_document = AsyncMock()
    mock_service.update_document = AsyncMock()
    return mock_service


# Utility Functions
class TestUtilities:
    """Utility functions for testing."""
    
    @staticmethod
    async def create_test_users(db_session: AsyncSession, count: int = 5) -> list[User]:
        """Create multiple test users."""
        from app.services.auth_service import get_password_hash
        
        users = []
        for i in range(count):
            user = User(
                email=f"user{i}@example.com",
                username=f"user{i}",
                first_name=f"User",
                last_name=f"{i}",
                hashed_password=get_password_hash("password123"),
                department_id=1,
                is_active=True
            )
            db_session.add(user)
            users.append(user)
        
        await db_session.commit()
        
        for user in users:
            await db_session.refresh(user)
        
        return users
    
    @staticmethod
    async def create_test_tickets(db_session: AsyncSession, user_id: int, count: int = 10) -> list[Ticket]:
        """Create multiple test tickets."""
        from app.enums import TicketStatus, Priority, TicketType
        import random
        
        tickets = []
        statuses = list(TicketStatus)
        priorities = list(Priority)
        types = list(TicketType)
        
        for i in range(count):
            ticket = Ticket(
                ticket_number=f"TEST-{i:03d}",
                title=f"Test Ticket {i}",
                description=f"Description for test ticket {i}",
                status=random.choice(statuses),
                priority=random.choice(priorities),
                ticket_type=random.choice(types),
                created_by_id=user_id,
                department_id=1,
                tags=[f"tag{i}", "test"]
            )
            db_session.add(ticket)
            tickets.append(ticket)
        
        await db_session.commit()
        
        for ticket in tickets:
            await db_session.refresh(ticket)
        
        return tickets
    
    @staticmethod
    def assert_response_structure(response_data: dict, expected_keys: list[str]):
        """Assert that response contains expected keys."""
        for key in expected_keys:
            assert key in response_data, f"Missing key: {key}"
    
    @staticmethod
    def assert_pagination_structure(response_data: dict):
        """Assert that response has proper pagination structure."""
        expected_keys = ["items", "total", "page", "size", "pages"]
        for key in expected_keys:
            assert key in response_data, f"Missing pagination key: {key}"


@pytest.fixture
def test_utils():
    """Provide test utilities."""
    return TestUtilities


# Test Configuration
class TestConfig:
    """Test configuration settings."""
    
    # Database settings
    DATABASE_URL = TEST_DATABASE_URL
    TEST_DATABASE_URL = TEST_DATABASE_URL
    
    # JWT settings for testing
    SECRET_KEY = "test-secret-key-for-testing-only"
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 30
    
    # File upload settings for testing
    UPLOAD_DIR = "./test_uploads"
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS = [".txt", ".pdf", ".jpg", ".png"]
    
    # Notification settings for testing
    ENABLE_EMAIL_NOTIFICATIONS = False
    ENABLE_TEAMS_NOTIFICATIONS = False
    ENABLE_SLACK_NOTIFICATIONS = False
    
    # Search settings for testing
    ENABLE_SEARCH_INDEXING = False
    
    # Testing flags
    TESTING = True
    DEBUG = True


@pytest.fixture
def test_config():
    """Provide test configuration."""
    return TestConfig


# Performance Testing Utilities
@pytest.fixture
def performance_timer():
    """Timer utility for performance testing."""
    import time
    
    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None
        
        def start(self):
            self.start_time = time.time()
        
        def stop(self):
            self.end_time = time.time()
            return self.elapsed
        
        @property
        def elapsed(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return None
    
    return Timer()


# Custom Pytest Markers
pytest_markers = [
    "unit: marks tests as unit tests",
    "integration: marks tests as integration tests",
    "e2e: marks tests as end-to-end tests",
    "slow: marks tests as slow running",
    "requires_db: marks tests that require database",
    "requires_auth: marks tests that require authentication",
    "performance: marks tests as performance tests"
]


# Test Data Generators
class DataGenerator:
    """Generate test data for various entities."""
    
    @staticmethod
    def user_data(**overrides):
        """Generate user test data."""
        import uuid
        base_data = {
            "email": f"user_{uuid.uuid4().hex[:8]}@example.com",
            "username": f"user_{uuid.uuid4().hex[:8]}",
            "first_name": "Test",
            "last_name": "User",
            "password": "testpassword123",
            "department_id": 1
        }
        base_data.update(overrides)
        return base_data
    
    @staticmethod
    def ticket_data(**overrides):
        """Generate ticket test data."""
        import uuid
        base_data = {
            "title": f"Test Ticket {uuid.uuid4().hex[:8]}",
            "description": "This is a test ticket created for testing purposes",
            "priority": "medium",
            "ticket_type": "incident",
            "department_id": 1,
            "tags": ["test", "automated"]
        }
        base_data.update(overrides)
        return base_data
    
    @staticmethod
    def department_data(**overrides):
        """Generate department test data."""
        import uuid
        base_data = {
            "name": f"Test Department {uuid.uuid4().hex[:8]}",
            "manager_id": 1,
            "budget_limit": 50000.00,
            "approval_rules": {
                "auto_approve_limit": 1000,
                "require_manager_approval": True
            }
        }
        base_data.update(overrides)
        return base_data


@pytest.fixture
def data_generator():
    """Provide data generator utilities."""
    return DataGenerator


# Async Test Helpers
class AsyncTestHelper:
    """Helper functions for async testing."""
    
    @staticmethod
    async def wait_for_condition(condition_func, timeout=5.0, interval=0.1):
        """Wait for a condition to become true."""
        import asyncio
        
        end_time = asyncio.get_event_loop().time() + timeout
        
        while asyncio.get_event_loop().time() < end_time:
            if await condition_func():
                return True
            await asyncio.sleep(interval)
        
        return False
    
    @staticmethod
    async def run_with_timeout(coro, timeout=10.0):
        """Run coroutine with timeout."""
        import asyncio
        
        try:
            return await asyncio.wait_for(coro, timeout=timeout)
        except asyncio.TimeoutError:
            pytest.fail(f"Operation timed out after {timeout} seconds")


@pytest.fixture
def async_helper():
    """Provide async testing helpers."""
    return AsyncTestHelper