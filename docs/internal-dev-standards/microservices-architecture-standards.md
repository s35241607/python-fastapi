# 微服務架構規範 Microservices Architecture Standards

## 目錄 Table of Contents

1. [微服務設計原則](#微服務設計原則)
2. [服務拆分策略](#服務拆分策略)
3. [領域驅動設計 (DDD)](#領域驅動設計-ddd)
4. [API Gateway 設計](#api-gateway-設計)
5. [服務間通訊](#服務間通訊)
6. [資料管理策略](#資料管理策略)
7. [監控與觀測](#監控與觀測)
8. [部署策略](#部署策略)

## 微服務設計原則

### 核心原則
1. **單一職責**: 每個服務專注於特定的業務功能
2. **自主性**: 服務可獨立開發、部署和擴展
3. **去中心化**: 避免共享數據庫和緊耦合
4. **容錯性**: 服務應能優雅地處理故障
5. **可觀測性**: 完整的日誌、監控和追蹤

### 微服務邊界定義
```python
# 基於業務能力的服務劃分範例

# 使用者服務 (User Service)
class UserService:
    """負責使用者管理的所有功能"""
    - 使用者註冊/登入
    - 使用者資料管理
    - 權限驗證

# 產品服務 (Product Service)
class ProductService:
    """負責產品目錄管理"""
    - 產品資訊管理
    - 庫存管理
    - 產品分類

# 訂單服務 (Order Service)
class OrderService:
    """負責訂單處理流程"""
    - 訂單建立
    - 訂單狀態管理
    - 付款處理

# 通知服務 (Notification Service)
class NotificationService:
    """負責所有通知功能"""
    - 電子郵件通知
    - 簡訊通知
    - 推播通知
```

## 服務拆分策略

### 基於領域的拆分
```mermaid
graph TB
    A[企業應用程式] --> B[使用者管理領域]
    A --> C[產品管理領域]
    A --> D[訂單處理領域]
    A --> E[支付處理領域]

    B --> F[User Service]
    B --> G[Auth Service]

    C --> H[Product Service]
    C --> I[Inventory Service]

    D --> J[Order Service]
    D --> K[Cart Service]

    E --> L[Payment Service]
    E --> M[Billing Service]
```

### 服務大小指導原則
```python
# 微服務規模評估標準

class ServiceSizeGuidelines:
    """微服務規模指導原則"""

    # 團隊規模: 2-8 人 (Amazon Two-Pizza Rule)
    TEAM_SIZE = "2-8 people"

    # 程式碼行數: 建議 < 10,000 行
    MAX_LINES_OF_CODE = 10000

    # 資料庫表格數: 建議 < 10 個
    MAX_DATABASE_TABLES = 10

    # 部署時間: 建議 < 15 分鐘
    MAX_DEPLOYMENT_TIME = "15 minutes"

    # 啟動時間: 建議 < 60 秒
    MAX_STARTUP_TIME = "60 seconds"

    # 責任邊界: 單一業務能力
    RESPONSIBILITY = "Single business capability"
```

## 領域驅動設計 (DDD)

### 限界上下文 (Bounded Context)
```python
# 使用者管理限界上下文
class UserManagementContext:
    """使用者管理的限界上下文"""

    # 聚合根
    class User:
        def __init__(self, user_id: UserId, email: Email):
            self.user_id = user_id
            self.email = email
            self.profile = UserProfile()

    # 值物件
    class Email:
        def __init__(self, value: str):
            self._validate(value)
            self.value = value

    # 領域服務
    class UserDomainService:
        async def is_email_unique(self, email: Email) -> bool:
            # 檢查電子郵件唯一性
            pass

# 訂單處理限界上下文
class OrderProcessingContext:
    """訂單處理的限界上下文"""

    class Order:
        def __init__(self, order_id: OrderId, customer_id: CustomerId):
            self.order_id = order_id
            self.customer_id = customer_id
            self.items = []
            self.status = OrderStatus.PENDING

    class OrderItem:
        def __init__(self, product_id: ProductId, quantity: int, price: Money):
            self.product_id = product_id
            self.quantity = quantity
            self.price = price
```

### 聚合設計原則
```python
from dataclasses import dataclass
from typing import List
from datetime import datetime

@dataclass
class OrderAggregate:
    """訂單聚合 - 確保業務不變性"""

    order_id: str
    customer_id: str
    items: List['OrderItem']
    status: str
    total_amount: float
    created_at: datetime

    def add_item(self, product_id: str, quantity: int, price: float):
        """新增訂單項目 - 保持聚合一致性"""
        if self.status != "DRAFT":
            raise DomainException("Cannot modify confirmed order")

        item = OrderItem(product_id, quantity, price)
        self.items.append(item)
        self._recalculate_total()

    def confirm(self):
        """確認訂單 - 領域業務規則"""
        if not self.items:
            raise DomainException("Cannot confirm empty order")

        if self.total_amount <= 0:
            raise DomainException("Order total must be positive")

        self.status = "CONFIRMED"

        # 發布領域事件
        self._publish_event(OrderConfirmedEvent(self.order_id, self.customer_id))

    def _recalculate_total(self):
        """重新計算總金額"""
        self.total_amount = sum(item.quantity * item.price for item in self.items)

    def _publish_event(self, event):
        """發布領域事件到事件總線"""
        EventBus.publish(event)
```

## API Gateway 設計

### Kong API Gateway 配置
```yaml
# kong.yml - API Gateway 配置
_format_version: "3.0"

services:
  - name: user-service
    url: http://user-service:8001
    routes:
      - name: user-routes
        paths:
          - /api/v1/users
        methods:
          - GET
          - POST
          - PUT
          - DELETE

  - name: product-service
    url: http://product-service:8002
    routes:
      - name: product-routes
        paths:
          - /api/v1/products
        methods:
          - GET
          - POST
          - PUT
          - DELETE

  - name: order-service
    url: http://order-service:8003
    routes:
      - name: order-routes
        paths:
          - /api/v1/orders
        methods:
          - GET
          - POST
          - PUT
          - DELETE

# JWT 認證插件
plugins:
  - name: jwt
    config:
      key_claim_name: iss
      secret_is_base64: false

  - name: cors
    config:
      origins:
        - http://localhost:5173
        - https://app.company.com
      methods:
        - GET
        - POST
        - PUT
        - DELETE
        - OPTIONS
      headers:
        - Accept
        - Accept-Version
        - Content-Length
        - Content-MD5
        - Content-Type
        - Date
        - Authorization
```

### 請求路由策略
```python
# API Gateway 路由規則
class APIGatewayRouting:
    """API Gateway 路由配置"""

    ROUTES = {
        # 使用者相關路由
        "/api/v1/users/**": "user-service:8001",
        "/api/v1/auth/**": "user-service:8001",
        "/api/v1/profiles/**": "user-service:8001",

        # 產品相關路由
        "/api/v1/products/**": "product-service:8002",
        "/api/v1/categories/**": "product-service:8002",
        "/api/v1/inventory/**": "product-service:8002",

        # 訂單相關路由
        "/api/v1/orders/**": "order-service:8003",
        "/api/v1/cart/**": "order-service:8003",

        # 支付相關路由
        "/api/v1/payments/**": "payment-service:8004",
        "/api/v1/billing/**": "payment-service:8004",

        # 通知相關路由
        "/api/v1/notifications/**": "notification-service:8005",
    }

    # 負載均衡策略
    LOAD_BALANCING = {
        "algorithm": "round-robin",
        "health_checks": True,
        "timeout": 30,
        "retries": 3
    }
```

## 服務間通訊

### 同步通訊 (HTTP/REST)
```python
import httpx
from typing import Optional

class UserServiceClient:
    """使用者服務客戶端"""

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)

    async def get_user_by_id(self, user_id: str) -> Optional[dict]:
        """取得使用者資訊 - 同步呼叫"""
        try:
            response = await self.client.get(f"{self.base_url}/users/{user_id}")
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None
            raise ServiceCommunicationError(f"Failed to get user: {e}")
        except httpx.RequestError as e:
            raise ServiceCommunicationError(f"Request failed: {e}")

    async def validate_user_exists(self, user_id: str) -> bool:
        """驗證使用者是否存在"""
        user = await self.get_user_by_id(user_id)
        return user is not None

# 在訂單服務中使用
class OrderApplicationService:
    def __init__(self, user_service_client: UserServiceClient):
        self.user_service_client = user_service_client

    async def create_order(self, create_order_request: CreateOrderRequest):
        # 驗證使用者存在 - 同步服務間呼叫
        user_exists = await self.user_service_client.validate_user_exists(
            create_order_request.customer_id
        )

        if not user_exists:
            raise ValidationError("Customer does not exist")

        # 建立訂單...
```

### 斷路器模式 (Circuit Breaker)
```python
import asyncio
from enum import Enum
from datetime import datetime, timedelta

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    """斷路器實作"""

    def __init__(self,
                 failure_threshold: int = 5,
                 timeout: int = 60,
                 recovery_timeout: int = 30):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED

    async def call(self, func, *args, **kwargs):
        """包裝服務呼叫的斷路器"""

        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
            else:
                raise CircuitBreakerOpenError("Circuit breaker is open")

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result

        except Exception as e:
            self._on_failure()
            raise e

    def _should_attempt_reset(self) -> bool:
        """檢查是否應該嘗試重置斷路器"""
        if self.last_failure_time is None:
            return False

        time_since_failure = datetime.now() - self.last_failure_time
        return time_since_failure.total_seconds() > self.recovery_timeout

    def _on_success(self):
        """成功時重置斷路器"""
        self.failure_count = 0
        self.state = CircuitState.CLOSED

    def _on_failure(self):
        """失敗時更新斷路器狀態"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN

# 使用斷路器的服務客戶端
class ResilientUserServiceClient:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client = httpx.AsyncClient()
        self.circuit_breaker = CircuitBreaker()

    async def get_user_by_id(self, user_id: str) -> Optional[dict]:
        """使用斷路器保護的服務呼叫"""
        return await self.circuit_breaker.call(
            self._get_user_by_id_internal, user_id
        )

    async def _get_user_by_id_internal(self, user_id: str) -> Optional[dict]:
        response = await self.client.get(f"{self.base_url}/users/{user_id}")
        response.raise_for_status()
        return response.json()
```

## 資料管理策略

### Database Per Service 模式
```yaml
# 每個服務獨立的資料庫配置
# docker-compose.microservices.yml

version: '3.8'

services:
  # 使用者服務資料庫
  user-db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: user_service_db
      POSTGRES_USER: user_service
      POSTGRES_PASSWORD: ${USER_DB_PASSWORD}
    volumes:
      - user_db_data:/var/lib/postgresql/data
    networks:
      - user-network

  # 產品服務資料庫
  product-db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: product_service_db
      POSTGRES_USER: product_service
      POSTGRES_PASSWORD: ${PRODUCT_DB_PASSWORD}
    volumes:
      - product_db_data:/var/lib/postgresql/data
    networks:
      - product-network

  # 訂單服務資料庫
  order-db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: order_service_db
      POSTGRES_USER: order_service
      POSTGRES_PASSWORD: ${ORDER_DB_PASSWORD}
    volumes:
      - order_db_data:/var/lib/postgresql/data
    networks:
      - order-network

volumes:
  user_db_data:
  product_db_data:
  order_db_data:

networks:
  user-network:
  product-network:
  order-network:
```

### 資料一致性策略
```python
# Saga 模式實作 - 分散式事務管理
from enum import Enum
from typing import List, Dict, Any

class SagaStep:
    """Saga 步驟定義"""

    def __init__(self, service: str, action: str, compensation: str):
        self.service = service
        self.action = action
        self.compensation = compensation
        self.data = {}

class SagaStatus(Enum):
    STARTED = "started"
    COMPENSATING = "compensating"
    COMPLETED = "completed"
    FAILED = "failed"

class OrderProcessingSaga:
    """訂單處理 Saga"""

    def __init__(self):
        self.steps = [
            SagaStep("inventory-service", "reserve_items", "release_items"),
            SagaStep("payment-service", "process_payment", "refund_payment"),
            SagaStep("shipping-service", "schedule_delivery", "cancel_delivery"),
            SagaStep("notification-service", "send_confirmation", "send_cancellation")
        ]
        self.status = SagaStatus.STARTED
        self.completed_steps = []
        self.current_step = 0

    async def execute(self, order_data: Dict[str, Any]):
        """執行 Saga 流程"""
        try:
            for step in self.steps:
                await self._execute_step(step, order_data)
                self.completed_steps.append(step)
                self.current_step += 1

            self.status = SagaStatus.COMPLETED

        except Exception as e:
            self.status = SagaStatus.COMPENSATING
            await self._compensate()
            self.status = SagaStatus.FAILED
            raise SagaExecutionError(f"Saga failed: {e}")

    async def _execute_step(self, step: SagaStep, data: Dict[str, Any]):
        """執行單一 Saga 步驟"""
        service_client = self._get_service_client(step.service)
        await service_client.execute_action(step.action, data)

    async def _compensate(self):
        """執行補償動作"""
        # 反向執行已完成的步驟
        for step in reversed(self.completed_steps):
            try:
                service_client = self._get_service_client(step.service)
                await service_client.execute_action(step.compensation, step.data)
            except Exception as e:
                # 記錄補償失敗，但繼續執行其他補償
                logger.error(f"Compensation failed for {step.service}: {e}")
```

## 監控與觀測

### 分散式追蹤
```python
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

# OpenTelemetry 設定
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer(__name__)

jaeger_exporter = JaegerExporter(
    agent_host_name="localhost",
    agent_port=14268,
)

span_processor = BatchSpanProcessor(jaeger_exporter)
trace.get_tracer_provider().add_span_processor(span_processor)

# 服務中使用追蹤
class OrderService:
    def __init__(self):
        self.tracer = trace.get_tracer(__name__)

    async def create_order(self, order_data: dict):
        with self.tracer.start_as_current_span("create_order") as span:
            span.set_attribute("order.customer_id", order_data["customer_id"])
            span.set_attribute("order.item_count", len(order_data["items"]))

            # 驗證使用者
            with self.tracer.start_as_current_span("validate_customer"):
                customer_valid = await self._validate_customer(order_data["customer_id"])
                span.set_attribute("validation.result", customer_valid)

            # 處理訂單
            with self.tracer.start_as_current_span("process_order"):
                order = await self._process_order(order_data)
                span.set_attribute("order.id", order.id)

            return order
```

### 服務健康檢查
```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

health_router = APIRouter()

@health_router.get("/health")
async def health_check():
    """基本健康檢查"""
    return {"status": "healthy", "service": "order-service"}

@health_router.get("/health/detailed")
async def detailed_health_check(db: AsyncSession = Depends(get_db)):
    """詳細健康檢查"""
    checks = {
        "database": await _check_database(db),
        "external_services": await _check_external_services(),
        "memory_usage": _check_memory_usage(),
        "disk_space": _check_disk_space()
    }

    overall_status = "healthy" if all(checks.values()) else "unhealthy"

    return {
        "status": overall_status,
        "service": "order-service",
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat()
    }

async def _check_database(db: AsyncSession) -> bool:
    """檢查資料庫連線"""
    try:
        await db.execute(text("SELECT 1"))
        return True
    except Exception:
        return False

async def _check_external_services() -> bool:
    """檢查外部服務連線"""
    services_to_check = [
        "user-service:8001/health",
        "payment-service:8004/health"
    ]

    for service_url in services_to_check:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"http://{service_url}", timeout=5.0)
                if response.status_code != 200:
                    return False
        except Exception:
            return False

    return True
```

## 部署策略

### Docker Compose 微服務編排
```yaml
# docker-compose.microservices.yml
version: '3.8'

services:
  # API Gateway
  kong:
    image: kong:latest
    environment:
      KONG_DATABASE: "off"
      KONG_DECLARATIVE_CONFIG: /kong/declarative/kong.yml
      KONG_PROXY_ACCESS_LOG: /dev/stdout
      KONG_ADMIN_ACCESS_LOG: /dev/stdout
      KONG_PROXY_ERROR_LOG: /dev/stderr
      KONG_ADMIN_ERROR_LOG: /dev/stderr
      KONG_ADMIN_LISTEN: 0.0.0.0:8001
    volumes:
      - ./kong.yml:/kong/declarative/kong.yml
    ports:
      - "8000:8000"
      - "8001:8001"
    networks:
      - microservices-network

  # 使用者服務
  user-service:
    build:
      context: ./services/user-service
      dockerfile: Dockerfile
    environment:
      DATABASE_URL: postgresql+asyncpg://user_service:${USER_DB_PASSWORD}@user-db:5432/user_service_db
      KAFKA_BOOTSTRAP_SERVERS: kafka:9092
    depends_on:
      - user-db
      - kafka
    networks:
      - microservices-network
      - user-network
    deploy:
      replicas: 2

  # 產品服務
  product-service:
    build:
      context: ./services/product-service
      dockerfile: Dockerfile
    environment:
      DATABASE_URL: postgresql+asyncpg://product_service:${PRODUCT_DB_PASSWORD}@product-db:5432/product_service_db
      KAFKA_BOOTSTRAP_SERVERS: kafka:9092
    depends_on:
      - product-db
      - kafka
    networks:
      - microservices-network
      - product-network
    deploy:
      replicas: 2

  # 訂單服務
  order-service:
    build:
      context: ./services/order-service
      dockerfile: Dockerfile
    environment:
      DATABASE_URL: postgresql+asyncpg://order_service:${ORDER_DB_PASSWORD}@order-db:5432/order_service_db
      KAFKA_BOOTSTRAP_SERVERS: kafka:9092
      USER_SERVICE_URL: http://user-service:8000
      PRODUCT_SERVICE_URL: http://product-service:8000
    depends_on:
      - order-db
      - kafka
    networks:
      - microservices-network
      - order-network
    deploy:
      replicas: 3

networks:
  microservices-network:
    driver: bridge
  user-network:
    driver: bridge
  product-network:
    driver: bridge
  order-network:
    driver: bridge
```

---

*最後更新: 2025-01-XX*
