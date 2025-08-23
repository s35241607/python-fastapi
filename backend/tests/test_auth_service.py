import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from jose import jwt

from app.services.auth_service import AuthService
from app.models import User, UserSession, ApiKey
from app.schemas import UserCreate, LoginRequest, PasswordChangeRequest
from app.core.config import settings


class TestAuthService:
    """Comprehensive unit tests for AuthService"""

    @pytest.fixture
    def mock_db_session(self):
        """Mock database session"""
        session = Mock(spec=AsyncSession)
        session.add = Mock()
        session.commit = AsyncMock()
        session.refresh = AsyncMock()
        session.execute = AsyncMock()
        session.scalar = AsyncMock()
        return session

    @pytest.fixture
    def auth_service(self, mock_db_session):
        """Create AuthService instance with mocked dependencies"""
        return AuthService(mock_db_session)

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
            is_active=True,
            hashed_password="$2b$12$test_hashed_password",
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )

    @pytest.fixture
    def valid_login_request(self):
        """Valid login request data"""
        return LoginRequest(
            username="testuser",
            password="testpassword123"
        )

    @pytest.fixture
    def valid_user_create(self):
        """Valid user creation data"""
        return UserCreate(
            email="newuser@example.com",
            username="newuser",
            first_name="New",
            last_name="User",
            password="newpassword123",
            department_id=1
        )

    # Authentication Tests
    @pytest.mark.asyncio
    async def test_authenticate_user_success(self, auth_service, mock_user, mock_db_session):
        """Test successful user authentication"""
        # Mock database query
        mock_db_session.scalar.return_value = mock_user
        
        # Mock password verification
        with patch('app.services.auth_service.verify_password', return_value=True):
            result = await auth_service.authenticate_user("testuser", "testpassword123")
        
        assert result == mock_user
        mock_db_session.scalar.assert_called_once()

    @pytest.mark.asyncio
    async def test_authenticate_user_invalid_username(self, auth_service, mock_db_session):
        """Test authentication with invalid username"""
        # Mock user not found
        mock_db_session.scalar.return_value = None
        
        result = await auth_service.authenticate_user("invaliduser", "password")
        
        assert result is False
        mock_db_session.scalar.assert_called_once()

    @pytest.mark.asyncio
    async def test_authenticate_user_invalid_password(self, auth_service, mock_user, mock_db_session):
        """Test authentication with invalid password"""
        # Mock database query
        mock_db_session.scalar.return_value = mock_user
        
        # Mock password verification failure
        with patch('app.services.auth_service.verify_password', return_value=False):
            result = await auth_service.authenticate_user("testuser", "wrongpassword")
        
        assert result is False

    @pytest.mark.asyncio
    async def test_authenticate_inactive_user(self, auth_service, mock_user, mock_db_session):
        """Test authentication with inactive user"""
        # Set user as inactive
        mock_user.is_active = False
        mock_db_session.scalar.return_value = mock_user
        
        with patch('app.services.auth_service.verify_password', return_value=True):
            result = await auth_service.authenticate_user("testuser", "testpassword123")
        
        assert result is False

    # Login Tests
    @pytest.mark.asyncio
    async def test_login_success(self, auth_service, mock_user, valid_login_request, mock_db_session):
        """Test successful login"""
        # Mock authenticate_user
        with patch.object(auth_service, 'authenticate_user', return_value=mock_user):
            # Mock create_user_session
            mock_session = UserSession(
                id=1,
                user_id=1,
                session_token="mock_session_token",
                expires_at=datetime.utcnow() + timedelta(hours=24),
                is_active=True
            )
            with patch.object(auth_service, 'create_user_session', return_value=mock_session):
                # Mock token creation
                with patch.object(auth_service, 'create_access_token', return_value="mock_access_token"):
                    with patch.object(auth_service, 'create_refresh_token', return_value="mock_refresh_token"):
                        result = await auth_service.login(valid_login_request)
        
        assert result["access_token"] == "mock_access_token"
        assert result["refresh_token"] == "mock_refresh_token"
        assert result["token_type"] == "bearer"
        assert result["user"]["id"] == 1

    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, auth_service, valid_login_request):
        """Test login with invalid credentials"""
        # Mock authenticate_user failure
        with patch.object(auth_service, 'authenticate_user', return_value=False):
            with pytest.raises(HTTPException) as exc_info:
                await auth_service.login(valid_login_request)
        
        assert exc_info.value.status_code == 401
        assert "Invalid credentials" in str(exc_info.value.detail)

    # Token Creation Tests
    def test_create_access_token(self, auth_service):
        """Test access token creation"""
        user_data = {"sub": "1", "username": "testuser"}
        
        with patch('app.services.auth_service.jwt.encode') as mock_encode:
            mock_encode.return_value = "mock_token"
            token = auth_service.create_access_token(user_data)
        
        assert token == "mock_token"
        mock_encode.assert_called_once()

    def test_create_access_token_with_expiry(self, auth_service):
        """Test access token creation with custom expiry"""
        user_data = {"sub": "1", "username": "testuser"}
        expires_delta = timedelta(minutes=30)
        
        with patch('app.services.auth_service.jwt.encode') as mock_encode:
            mock_encode.return_value = "mock_token"
            token = auth_service.create_access_token(user_data, expires_delta)
        
        assert token == "mock_token"
        # Verify the payload includes the custom expiry
        call_args = mock_encode.call_args[0]
        payload = call_args[0]
        assert "exp" in payload

    def test_create_refresh_token(self, auth_service):
        """Test refresh token creation"""
        user_data = {"sub": "1", "username": "testuser"}
        
        with patch('app.services.auth_service.jwt.encode') as mock_encode:
            mock_encode.return_value = "mock_refresh_token"
            token = auth_service.create_refresh_token(user_data)
        
        assert token == "mock_refresh_token"
        mock_encode.assert_called_once()

    # Token Verification Tests
    @pytest.mark.asyncio
    async def test_verify_token_valid(self, auth_service, mock_user, mock_db_session):
        """Test valid token verification"""
        token = "valid_token"
        payload = {"sub": "1", "username": "testuser", "exp": datetime.utcnow() + timedelta(hours=1)}
        
        with patch('app.services.auth_service.jwt.decode', return_value=payload):
            mock_db_session.scalar.return_value = mock_user
            result = await auth_service.verify_token(token)
        
        assert result == mock_user

    @pytest.mark.asyncio
    async def test_verify_token_expired(self, auth_service):
        """Test expired token verification"""
        token = "expired_token"
        
        with patch('app.services.auth_service.jwt.decode', side_effect=jwt.ExpiredSignatureError()):
            with pytest.raises(HTTPException) as exc_info:
                await auth_service.verify_token(token)
        
        assert exc_info.value.status_code == 401
        assert "Token expired" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_verify_token_invalid(self, auth_service):
        """Test invalid token verification"""
        token = "invalid_token"
        
        with patch('app.services.auth_service.jwt.decode', side_effect=jwt.JWTError()):
            with pytest.raises(HTTPException) as exc_info:
                await auth_service.verify_token(token)
        
        assert exc_info.value.status_code == 401
        assert "Invalid token" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_verify_token_user_not_found(self, auth_service, mock_db_session):
        """Test token verification when user not found"""
        token = "valid_token"
        payload = {"sub": "999", "username": "nonexistent", "exp": datetime.utcnow() + timedelta(hours=1)}
        
        with patch('app.services.auth_service.jwt.decode', return_value=payload):
            mock_db_session.scalar.return_value = None
            with pytest.raises(HTTPException) as exc_info:
                await auth_service.verify_token(token)
        
        assert exc_info.value.status_code == 401
        assert "User not found" in str(exc_info.value.detail)

    # User Registration Tests
    @pytest.mark.asyncio
    async def test_register_user_success(self, auth_service, valid_user_create, mock_db_session):
        """Test successful user registration"""
        # Mock user doesn't exist
        mock_db_session.scalar.return_value = None
        
        with patch('app.services.auth_service.get_password_hash', return_value="hashed_password"):
            new_user = User(
                id=1,
                email=valid_user_create.email,
                username=valid_user_create.username,
                first_name=valid_user_create.first_name,
                last_name=valid_user_create.last_name,
                department_id=valid_user_create.department_id,
                hashed_password="hashed_password",
                is_active=True
            )
            mock_db_session.refresh.return_value = new_user
            
            result = await auth_service.register_user(valid_user_create)
        
        assert result.email == valid_user_create.email
        assert result.username == valid_user_create.username
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_register_user_email_exists(self, auth_service, valid_user_create, mock_user, mock_db_session):
        """Test registration with existing email"""
        # Mock user exists
        mock_db_session.scalar.return_value = mock_user
        
        with pytest.raises(HTTPException) as exc_info:
            await auth_service.register_user(valid_user_create)
        
        assert exc_info.value.status_code == 400
        assert "Email already registered" in str(exc_info.value.detail)

    # Password Management Tests
    @pytest.mark.asyncio
    async def test_change_password_success(self, auth_service, mock_user, mock_db_session):
        """Test successful password change"""
        password_request = PasswordChangeRequest(
            current_password="oldpassword",
            new_password="newpassword123"
        )
        
        with patch('app.services.auth_service.verify_password', return_value=True):
            with patch('app.services.auth_service.get_password_hash', return_value="new_hashed_password"):
                result = await auth_service.change_password(mock_user, password_request)
        
        assert result is True
        assert mock_user.hashed_password == "new_hashed_password"
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_change_password_invalid_current(self, auth_service, mock_user, mock_db_session):
        """Test password change with invalid current password"""
        password_request = PasswordChangeRequest(
            current_password="wrongpassword",
            new_password="newpassword123"
        )
        
        with patch('app.services.auth_service.verify_password', return_value=False):
            with pytest.raises(HTTPException) as exc_info:
                await auth_service.change_password(mock_user, password_request)
        
        assert exc_info.value.status_code == 400
        assert "Invalid current password" in str(exc_info.value.detail)

    # Session Management Tests
    @pytest.mark.asyncio
    async def test_create_user_session(self, auth_service, mock_user, mock_db_session):
        """Test user session creation"""
        with patch('uuid.uuid4') as mock_uuid:
            mock_uuid.return_value.hex = "mock_session_token"
            
            session = await auth_service.create_user_session(mock_user.id, "192.168.1.1", "Test Agent")
        
        assert session.user_id == mock_user.id
        assert session.session_token == "mock_session_token"
        assert session.is_active is True
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_invalidate_user_session(self, auth_service, mock_db_session):
        """Test user session invalidation"""
        session_token = "test_session_token"
        mock_session = UserSession(
            id=1,
            user_id=1,
            session_token=session_token,
            is_active=True
        )
        mock_db_session.scalar.return_value = mock_session
        
        result = await auth_service.invalidate_user_session(session_token)
        
        assert result is True
        assert mock_session.is_active is False
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_invalidate_user_session_not_found(self, auth_service, mock_db_session):
        """Test invalidation of non-existent session"""
        session_token = "nonexistent_token"
        mock_db_session.scalar.return_value = None
        
        result = await auth_service.invalidate_user_session(session_token)
        
        assert result is False

    # Refresh Token Tests
    @pytest.mark.asyncio
    async def test_refresh_access_token_success(self, auth_service, mock_user, mock_db_session):
        """Test successful access token refresh"""
        refresh_token = "valid_refresh_token"
        payload = {
            "sub": "1",
            "username": "testuser",
            "type": "refresh",
            "exp": datetime.utcnow() + timedelta(days=7)
        }
        
        with patch('app.services.auth_service.jwt.decode', return_value=payload):
            mock_db_session.scalar.return_value = mock_user
            with patch.object(auth_service, 'create_access_token', return_value="new_access_token"):
                result = await auth_service.refresh_access_token(refresh_token)
        
        assert result["access_token"] == "new_access_token"
        assert result["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_refresh_access_token_invalid_type(self, auth_service):
        """Test refresh with invalid token type"""
        refresh_token = "invalid_type_token"
        payload = {
            "sub": "1",
            "username": "testuser",
            "type": "access",  # Wrong type
            "exp": datetime.utcnow() + timedelta(days=7)
        }
        
        with patch('app.services.auth_service.jwt.decode', return_value=payload):
            with pytest.raises(HTTPException) as exc_info:
                await auth_service.refresh_access_token(refresh_token)
        
        assert exc_info.value.status_code == 401
        assert "Invalid token type" in str(exc_info.value.detail)

    # API Key Tests
    @pytest.mark.asyncio
    async def test_create_api_key(self, auth_service, mock_user, mock_db_session):
        """Test API key creation"""
        key_name = "Test API Key"
        
        with patch('secrets.token_urlsafe', return_value="test_api_key"):
            api_key = await auth_service.create_api_key(mock_user.id, key_name)
        
        assert api_key.user_id == mock_user.id
        assert api_key.name == key_name
        assert api_key.key_hash is not None
        assert api_key.is_active is True
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_verify_api_key_valid(self, auth_service, mock_user, mock_db_session):
        """Test valid API key verification"""
        api_key = "test_api_key"
        mock_api_key = ApiKey(
            id=1,
            user_id=1,
            name="Test Key",
            key_hash="hashed_key",
            is_active=True,
            user=mock_user
        )
        
        with patch('app.services.auth_service.verify_password', return_value=True):
            mock_db_session.scalar.return_value = mock_api_key
            result = await auth_service.verify_api_key(api_key)
        
        assert result == mock_user

    @pytest.mark.asyncio
    async def test_verify_api_key_invalid(self, auth_service, mock_db_session):
        """Test invalid API key verification"""
        api_key = "invalid_api_key"
        mock_db_session.scalar.return_value = None
        
        result = await auth_service.verify_api_key(api_key)
        
        assert result is None

    # Logout Tests
    @pytest.mark.asyncio
    async def test_logout_success(self, auth_service, mock_db_session):
        """Test successful logout"""
        session_token = "test_session_token"
        
        with patch.object(auth_service, 'invalidate_user_session', return_value=True):
            result = await auth_service.logout(session_token)
        
        assert result is True

    @pytest.mark.asyncio
    async def test_logout_invalid_session(self, auth_service):
        """Test logout with invalid session"""
        session_token = "invalid_session_token"
        
        with patch.object(auth_service, 'invalidate_user_session', return_value=False):
            result = await auth_service.logout(session_token)
        
        assert result is False

    # Edge Cases and Error Handling
    @pytest.mark.asyncio
    async def test_database_error_handling(self, auth_service, valid_user_create, mock_db_session):
        """Test database error handling during user registration"""
        mock_db_session.scalar.return_value = None
        mock_db_session.commit.side_effect = Exception("Database error")
        
        with patch('app.services.auth_service.get_password_hash', return_value="hashed_password"):
            with pytest.raises(Exception):
                await auth_service.register_user(valid_user_create)

    def test_token_payload_validation(self, auth_service):
        """Test token payload validation"""
        # Test with missing required fields
        incomplete_payload = {"username": "testuser"}  # Missing 'sub'
        
        with patch('app.services.auth_service.jwt.encode') as mock_encode:
            mock_encode.return_value = "token"
            token = auth_service.create_access_token(incomplete_payload)
            
            # Verify the service adds required fields
            call_args = mock_encode.call_args[0]
            payload = call_args[0]
            assert "exp" in payload
            assert "iat" in payload

    @pytest.mark.asyncio
    async def test_concurrent_login_attempts(self, auth_service, mock_user, valid_login_request):
        """Test handling of concurrent login attempts"""
        # Mock successful authentication
        with patch.object(auth_service, 'authenticate_user', return_value=mock_user):
            with patch.object(auth_service, 'create_user_session') as mock_create_session:
                with patch.object(auth_service, 'create_access_token', return_value="token"):
                    with patch.object(auth_service, 'create_refresh_token', return_value="refresh"):
                        
                        # Simulate concurrent login attempts
                        tasks = []
                        for _ in range(5):
                            task = auth_service.login(valid_login_request)
                            tasks.append(task)
                        
                        results = await asyncio.gather(*tasks)
                        
                        # All should succeed
                        assert len(results) == 5
                        assert all(result["access_token"] == "token" for result in results)