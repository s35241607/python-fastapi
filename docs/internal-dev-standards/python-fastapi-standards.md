# Python FastAPI 後端開發規範 Python FastAPI Backend Standards

## 目錄 Table of Contents

1. [技術棧規範](#技術棧規範)
2. [專案結構](#專案結構)
3. [Clean Code 原則](#clean-code-原則)
4. [Code First 開發](#code-first-開發)
5. [API 開發規範](#api-開發規範)
6. [資料模型設計](#資料模型設計)
7. [測試規範](#測試規範)
8. [效能與安全](#效能與安全)

## 技術棧規範

### 核心技術
- **Python**: 3.13+
- **Web 框架**: FastAPI (最新穩定版)
- **ORM**: SQLAlchemy 2.0+ (非同步)
- **資料庫驅動**: asyncpg (PostgreSQL)
- **套件管理**: uv
- **ASGI 伺服器**: Uvicorn
- **遷移工具**: Alembic

### 程式碼品質工具
```toml
# pyproject.toml
[tool.black]
line-length = 88
target-version = ['py313']

[tool.ruff]
line-length = 88
target-version = "py313"
select = ["E", "F", "W", "C", "B", "I"]

[tool.mypy]
python_version = "3.13"
strict = true
warn_return_any = true
```

## 專案結構

### Code First 架構
```
backend/
├── app/
│   ├── core/               # 核心配置與基礎設施
│   │   ├── __init__.py
│   │   ├── config.py      # 應用程式配置
│   │   ├── database.py    # 資料庫連線設定
│   │   ├── security.py    # 安全相關設定
│   │   └── exceptions.py  # 自定義例外
│   ├── domain/            # 領域層 (業務邏輯核心)
│   │   ├── __init__.py
│   │   ├── entities/      # 領域實體
│   │   ├── value_objects/ # 值物件
│   │   ├── services/      # 領域服務
│   │   └── repositories/  # 抽象儲存庫介面
│   ├── infrastructure/    # 基礎設施層
│   │   ├── __init__.py
│   │   ├── database/      # 資料庫實作
│   │   │   ├── models/    # SQLAlchemy 模型
│   │   │   └── repositories/ # 儲存庫實作
│   │   ├── external/      # 外部服務整合
│   │   └── middleware/    # 中介軟體
│   ├── application/       # 應用層
│   │   ├── __init__.py
│   │   ├── schemas/       # Pydantic 模式
│   │   ├── services/      # 應用服務
│   │   └── use_cases/     # 使用案例
│   ├── presentation/      # 展示層
│   │   ├── __init__.py
│   │   ├── api/          # API 路由
│   │   │   ├── v1/       # API 版本 1
│   │   │   └── v2/       # API 版本 2
│   │   └── dependencies/ # FastAPI 依賴注入
│   └── main.py           # 應用程式入口點
├── tests/                # 測試目錄
├── migrations/           # Alembic 遷移
└── pyproject.toml       # 專案配置
```

## Clean Code 原則

### 命名規範
```python
# 類別名稱 - PascalCase
class UserService:
    """處理使用者相關業務邏輯的服務類別"""
    pass

class PaymentProcessor:
    """處理付款流程的處理器"""
    pass

# 函數名稱 - snake_case，使用動詞開頭
def calculate_user_total_amount(user_id: int) -> Decimal:
    """計算使用者的總金額"""
    pass

def validate_email_format(email: str) -> bool:
    """驗證電子郵件格式是否正確"""
    pass

# 變數名稱 - snake_case，具描述性
user_profile_data = {"name": "John", "age": 30}
is_email_verified = True
total_order_count = 0

# 常數 - UPPER_SNAKE_CASE
MAX_RETRY_ATTEMPTS = 3
DEFAULT_PAGE_SIZE = 20
API_VERSION = "v1"
```

### 函數設計原則
```python
from typing import List, Optional
from decimal import Decimal
from dataclasses import dataclass

# 單一職責原則 - 一個函數只做一件事
def calculate_tax_amount(base_amount: Decimal, tax_rate: Decimal) -> Decimal:
    """計算稅額，職責單一且明確"""
    return base_amount * tax_rate

def format_currency(amount: Decimal, currency_code: str = "USD") -> str:
    """格式化貨幣顯示"""
    return f"{currency_code} {amount:.2f}"

# 純函數 - 無副作用，相同輸入產生相同輸出
def get_discount_rate(user_tier: str) -> Decimal:
    """根據使用者等級獲取折扣率"""
    discount_mapping = {
        "bronze": Decimal("0.05"),
        "silver": Decimal("0.10"),
        "gold": Decimal("0.15"),
        "platinum": Decimal("0.20")
    }
    return discount_mapping.get(user_tier.lower(), Decimal("0.00"))

# 小函數原則 - 保持函數簡短
def is_valid_email(email: str) -> bool:
    """檢查電子郵件格式是否有效"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

# 參數數量控制 - 最多3-4個參數，使用 dataclass 整合複雜參數
@dataclass
class OrderCalculationParams:
    base_amount: Decimal
    tax_rate: Decimal
    discount_rate: Decimal
    shipping_cost: Decimal

def calculate_order_total(params: OrderCalculationParams) -> Decimal:
    """計算訂單總額"""
    subtotal = params.base_amount - (params.base_amount * params.discount_rate)
    tax_amount = subtotal * params.tax_rate
    return subtotal + tax_amount + params.shipping_cost
```

### 類別設計原則
```python
from abc import ABC, abstractmethod
from typing import Protocol

# 單一職責原則
class EmailValidator:
    """專門負責電子郵件驗證的類別"""

    def __init__(self, allowed_domains: List[str] = None):
        self.allowed_domains = allowed_domains or []

    def is_valid_format(self, email: str) -> bool:
        """檢查電子郵件格式"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    def is_allowed_domain(self, email: str) -> bool:
        """檢查電子郵件網域是否被允許"""
        if not self.allowed_domains:
            return True
        domain = email.split('@')[1].lower()
        return domain in self.allowed_domains

# 開放封閉原則 - 使用抽象基類
class NotificationSender(ABC):
    """通知發送者抽象基類"""

    @abstractmethod
    async def send_notification(self, recipient: str, message: str) -> bool:
        """發送通知的抽象方法"""
        pass

class EmailNotificationSender(NotificationSender):
    """電子郵件通知發送者"""

    async def send_notification(self, recipient: str, message: str) -> bool:
        # 電子郵件發送實作
        print(f"Sending email to {recipient}: {message}")
        return True

class SMSNotificationSender(NotificationSender):
    """簡訊通知發送者"""

    async def send_notification(self, recipient: str, message: str) -> bool:
        # 簡訊發送實作
        print(f"Sending SMS to {recipient}: {message}")
        return True

# 依賴反轉原則 - 使用 Protocol
class EmailServiceProtocol(Protocol):
    async def send_email(self, to: str, subject: str, body: str) -> bool:
        ...

class UserNotificationService:
    """使用者通知服務"""

    def __init__(self, email_service: EmailServiceProtocol):
        self._email_service = email_service

    async def notify_user_registration(self, user_email: str, username: str) -> bool:
        subject = "歡迎註冊"
        body = f"歡迎 {username}，您已成功註冊！"
        return await self._email_service.send_email(user_email, subject, body)
```

## Code First 開發

### 領域驅動設計
```python
# domain/entities/user.py
from dataclasses import dataclass
from typing import Optional
from datetime import datetime
from uuid import UUID, uuid4

@dataclass
class User:
    """使用者領域實體"""
    id: UUID
    username: str
    email: str
    created_at: datetime
    updated_at: datetime
    is_active: bool = True

    @classmethod
    def create_new_user(cls, username: str, email: str) -> "User":
        """建立新使用者的工廠方法"""
        now = datetime.utcnow()
        return cls(
            id=uuid4(),
            username=username,
            email=email,
            created_at=now,
            updated_at=now,
            is_active=True
        )

    def deactivate(self) -> None:
        """停用使用者"""
        self.is_active = False
        self.updated_at = datetime.utcnow()

    def update_email(self, new_email: str) -> None:
        """更新電子郵件"""
        self.email = new_email
        self.updated_at = datetime.utcnow()

# domain/value_objects/email.py
from dataclasses import dataclass
import re

@dataclass(frozen=True)
class Email:
    """電子郵件值物件"""
    value: str

    def __post_init__(self):
        if not self._is_valid_email(self.value):
            raise ValueError(f"Invalid email format: {self.value}")

    @staticmethod
    def _is_valid_email(email: str) -> bool:
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    @property
    def domain(self) -> str:
        """取得電子郵件網域"""
        return self.value.split('@')[1]

# domain/services/user_domain_service.py
class UserDomainService:
    """使用者領域服務"""

    def __init__(self, user_repository: "UserRepositoryProtocol"):
        self._user_repository = user_repository

    async def is_username_available(self, username: str) -> bool:
        """檢查使用者名稱是否可用"""
        existing_user = await self._user_repository.find_by_username(username)
        return existing_user is None

    async def is_email_registered(self, email: Email) -> bool:
        """檢查電子郵件是否已註冊"""
        existing_user = await self._user_repository.find_by_email(email.value)
        return existing_user is not None
```

### 儲存庫模式
```python
# domain/repositories/user_repository.py
from abc import ABC, abstractmethod
from typing import Optional, List
from uuid import UUID
from ..entities.user import User

class UserRepositoryProtocol(ABC):
    """使用者儲存庫抽象介面"""

    @abstractmethod
    async def save(self, user: User) -> User:
        """儲存使用者"""
        pass

    @abstractmethod
    async def find_by_id(self, user_id: UUID) -> Optional[User]:
        """根據 ID 查找使用者"""
        pass

    @abstractmethod
    async def find_by_username(self, username: str) -> Optional[User]:
        """根據使用者名稱查找使用者"""
        pass

    @abstractmethod
    async def find_by_email(self, email: str) -> Optional[User]:
        """根據電子郵件查找使用者"""
        pass

    @abstractmethod
    async def find_all_active(self, skip: int = 0, limit: int = 100) -> List[User]:
        """查找所有啟用的使用者"""
        pass

# infrastructure/database/repositories/user_repository.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List
from uuid import UUID

from ....domain.repositories.user_repository import UserRepositoryProtocol
from ....domain.entities.user import User
from ..models.user_model import UserModel

class SQLAlchemyUserRepository(UserRepositoryProtocol):
    """SQLAlchemy 使用者儲存庫實作"""

    def __init__(self, session: AsyncSession):
        self._session = session

    async def save(self, user: User) -> User:
        """儲存使用者"""
        user_model = UserModel.from_entity(user)
        self._session.add(user_model)
        await self._session.commit()
        await self._session.refresh(user_model)
        return user_model.to_entity()

    async def find_by_id(self, user_id: UUID) -> Optional[User]:
        """根據 ID 查找使用者"""
        result = await self._session.execute(
            select(UserModel).where(UserModel.id == user_id)
        )
        user_model = result.scalar_one_or_none()
        return user_model.to_entity() if user_model else None

    async def find_by_username(self, username: str) -> Optional[User]:
        """根據使用者名稱查找使用者"""
        result = await self._session.execute(
            select(UserModel).where(UserModel.username == username)
        )
        user_model = result.scalar_one_or_none()
        return user_model.to_entity() if user_model else None
```

### SQLAlchemy 模型映射
```python
# infrastructure/database/models/user_model.py
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
from uuid import uuid4
from datetime import datetime

from ....domain.entities.user import User

Base = declarative_base()

class UserModel(Base):
    """使用者資料庫模型"""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    @classmethod
    def from_entity(cls, user: User) -> "UserModel":
        """從領域實體建立資料庫模型"""
        return cls(
            id=user.id,
            username=user.username,
            email=user.email,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at
        )

    def to_entity(self) -> User:
        """轉換為領域實體"""
        return User(
            id=self.id,
            username=self.username,
            email=self.email,
            is_active=self.is_active,
            created_at=self.created_at,
            updated_at=self.updated_at
        )
```

## API 開發規範

### FastAPI 路由設計
```python
# presentation/api/v1/users.py
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from uuid import UUID

from ....application.schemas.user_schemas import UserCreateSchema, UserResponseSchema
from ....application.services.user_application_service import UserApplicationService
from ...dependencies.auth import get_current_user
from ...dependencies.database import get_user_service

router = APIRouter(prefix="/api/v1/users", tags=["users"])

@router.post(
    "/",
    response_model=UserResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="建立新使用者",
    description="建立一個新的使用者帳戶"
)
async def create_user(
    user_data: UserCreateSchema,
    user_service: UserApplicationService = Depends(get_user_service)
) -> UserResponseSchema:
    """建立新使用者"""
    try:
        user = await user_service.create_user(user_data)
        return UserResponseSchema.from_entity(user)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get(
    "/{user_id}",
    response_model=UserResponseSchema,
    summary="取得使用者資料",
    description="根據使用者 ID 取得使用者詳細資料"
)
async def get_user(
    user_id: UUID,
    user_service: UserApplicationService = Depends(get_user_service),
    current_user: User = Depends(get_current_user)
) -> UserResponseSchema:
    """取得使用者資料"""
    user = await user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return UserResponseSchema.from_entity(user)
```

### 應用服務層
```python
# application/services/user_application_service.py
from typing import Optional, List
from uuid import UUID

from ...domain.entities.user import User
from ...domain.value_objects.email import Email
from ...domain.services.user_domain_service import UserDomainService
from ...domain.repositories.user_repository import UserRepositoryProtocol
from ..schemas.user_schemas import UserCreateSchema

class UserApplicationService:
    """使用者應用服務"""

    def __init__(
        self,
        user_repository: UserRepositoryProtocol,
        user_domain_service: UserDomainService
    ):
        self._user_repository = user_repository
        self._user_domain_service = user_domain_service

    async def create_user(self, user_data: UserCreateSchema) -> User:
        """建立新使用者"""
        # 驗證電子郵件格式
        email = Email(user_data.email)

        # 檢查使用者名稱是否可用
        if not await self._user_domain_service.is_username_available(user_data.username):
            raise ValueError("Username is already taken")

        # 檢查電子郵件是否已註冊
        if await self._user_domain_service.is_email_registered(email):
            raise ValueError("Email is already registered")

        # 建立新使用者
        user = User.create_new_user(
            username=user_data.username,
            email=email.value
        )

        # 儲存使用者
        return await self._user_repository.save(user)

    async def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """根據 ID 取得使用者"""
        return await self._user_repository.find_by_id(user_id)
```

## 測試規範

### 單元測試
```python
# tests/unit/domain/test_user_entity.py
import pytest
from datetime import datetime
from uuid import uuid4

from app.domain.entities.user import User

class TestUserEntity:
    """使用者實體測試"""

    def test_create_new_user_should_set_correct_attributes(self):
        """測試建立新使用者應設定正確的屬性"""
        # Arrange
        username = "john_doe"
        email = "john@example.com"

        # Act
        user = User.create_new_user(username, email)

        # Assert
        assert user.username == username
        assert user.email == email
        assert user.is_active is True
        assert isinstance(user.id, UUID)
        assert isinstance(user.created_at, datetime)
        assert isinstance(user.updated_at, datetime)

    def test_deactivate_should_set_is_active_false(self):
        """測試停用使用者應將 is_active 設為 False"""
        # Arrange
        user = User.create_new_user("test_user", "test@example.com")
        original_updated_at = user.updated_at

        # Act
        user.deactivate()

        # Assert
        assert user.is_active is False
        assert user.updated_at > original_updated_at

# tests/unit/application/test_user_application_service.py
import pytest
from unittest.mock import AsyncMock, Mock
from uuid import uuid4

from app.application.services.user_application_service import UserApplicationService
from app.application.schemas.user_schemas import UserCreateSchema
from app.domain.entities.user import User

@pytest.mark.asyncio
class TestUserApplicationService:
    """使用者應用服務測試"""

    @pytest.fixture
    def mock_user_repository(self):
        return AsyncMock()

    @pytest.fixture
    def mock_user_domain_service(self):
        return Mock()

    @pytest.fixture
    def user_service(self, mock_user_repository, mock_user_domain_service):
        return UserApplicationService(mock_user_repository, mock_user_domain_service)

    async def test_create_user_success(self, user_service, mock_user_repository, mock_user_domain_service):
        """測試成功建立使用者"""
        # Arrange
        user_data = UserCreateSchema(username="john_doe", email="john@example.com")
        mock_user_domain_service.is_username_available.return_value = True
        mock_user_domain_service.is_email_registered.return_value = False

        expected_user = User.create_new_user(user_data.username, user_data.email)
        mock_user_repository.save.return_value = expected_user

        # Act
        result = await user_service.create_user(user_data)

        # Assert
        assert result.username == user_data.username
        assert result.email == user_data.email
        mock_user_repository.save.assert_called_once()

    async def test_create_user_username_taken_should_raise_error(self, user_service, mock_user_domain_service):
        """測試使用者名稱已被使用應拋出錯誤"""
        # Arrange
        user_data = UserCreateSchema(username="taken_user", email="test@example.com")
        mock_user_domain_service.is_username_available.return_value = False

        # Act & Assert
        with pytest.raises(ValueError, match="Username is already taken"):
            await user_service.create_user(user_data)
```

### 整合測試
```python
# tests/integration/test_user_api.py
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.main import app
from app.core.database import get_db

@pytest.mark.asyncio
class TestUserAPI:
    """使用者 API 整合測試"""

    async def test_create_user_success(self, client: AsyncClient, db_session: AsyncSession):
        """測試成功建立使用者 API"""
        # Arrange
        user_data = {
            "username": "integration_test_user",
            "email": "integration@example.com"
        }

        # Act
        response = await client.post("/api/v1/users/", json=user_data)

        # Assert
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == user_data["username"]
        assert data["email"] == user_data["email"]
        assert data["is_active"] is True
        assert "id" in data
        assert "created_at" in data

    async def test_create_user_duplicate_username_should_return_400(self, client: AsyncClient):
        """測試重複使用者名稱應返回 400 錯誤"""
        # Arrange
        user_data = {
            "username": "duplicate_user",
            "email": "test1@example.com"
        }

        # 先建立一個使用者
        await client.post("/api/v1/users/", json=user_data)

        # 嘗試建立相同使用者名稱的使用者
        duplicate_data = {
            "username": "duplicate_user",
            "email": "test2@example.com"
        }

        # Act
        response = await client.post("/api/v1/users/", json=duplicate_data)

        # Assert
        assert response.status_code == 400
        data = response.json()
        assert "Username is already taken" in data["detail"]
```

## 效能與安全

### 非同步最佳實踐
```python
# 正確的非同步模式
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

async def get_users_with_orders(db: AsyncSession, user_ids: List[UUID]) -> List[User]:
    """正確的批次查詢，避免 N+1 問題"""
    result = await db.execute(
        select(UserModel)
        .options(selectinload(UserModel.orders))
        .where(UserModel.id.in_(user_ids))
    )
    return [user_model.to_entity() for user_model in result.scalars()]

async def process_users_concurrently(user_service: UserApplicationService, user_ids: List[UUID]):
    """併發處理使用者，但控制並發數量"""
    semaphore = asyncio.Semaphore(10)  # 限制併發數量

    async def process_user(user_id: UUID):
        async with semaphore:
            return await user_service.process_user(user_id)

    tasks = [process_user(user_id) for user_id in user_ids]
    return await asyncio.gather(*tasks)
```

### 安全性最佳實踐
```python
# 輸入驗證
from pydantic import BaseModel, Field, field_validator
import re

class UserCreateSchema(BaseModel):
    """使用者建立模式"""
    username: str = Field(..., min_length=3, max_length=50, pattern=r'^[a-zA-Z0-9_]+$')
    email: str = Field(..., max_length=255)
    password: str = Field(..., min_length=8, max_length=128)

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, v):
            raise ValueError('Invalid email format')
        return v.lower()

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        return v

# 密碼處理
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class PasswordService:
    """密碼服務"""

    @staticmethod
    def hash_password(password: str) -> str:
        """雜湊密碼"""
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """驗證密碼"""
        return pwd_context.verify(plain_password, hashed_password)
```

---

*最後更新: 2025-01-XX*
