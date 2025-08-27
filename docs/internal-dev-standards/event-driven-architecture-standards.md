# 事件驅動架構規範 Event-Driven Architecture Standards

## 目錄 Table of Contents

1. [事件驅動設計原則](#事件驅動設計原則)
2. [Kafka 配置與管理](#kafka-配置與管理)
3. [事件建模設計](#事件建模設計)
4. [事件發布與訂閱](#事件發布與訂閱)
5. [事件溯源 (Event Sourcing)](#事件溯源-event-sourcing)
6. [CQRS 模式](#cqrs-模式)
7. [事件處理保證](#事件處理保證)
8. [監控與故障排除](#監控與故障排除)

## 事件驅動設計原則

### 核心概念
```python
# 事件驅動架構的核心組件

class DomainEvent:
    """領域事件基類"""

    def __init__(self, aggregate_id: str, event_type: str):
        self.aggregate_id = aggregate_id
        self.event_type = event_type
        self.event_id = str(uuid4())
        self.timestamp = datetime.utcnow()
        self.version = 1

class EventStore:
    """事件儲存介面"""

    async def append_events(self, stream_id: str, events: List[DomainEvent]) -> None:
        pass

    async def get_events(self, stream_id: str, from_version: int = 0) -> List[DomainEvent]:
        pass

class EventPublisher:
    """事件發布器"""

    async def publish(self, event: DomainEvent) -> None:
        pass

class EventHandler:
    """事件處理器基類"""

    async def handle(self, event: DomainEvent) -> None:
        pass
```

### 事件類型分類
```python
# 不同類型的事件定義

# 1. 領域事件 (Domain Events)
class UserRegisteredEvent(DomainEvent):
    def __init__(self, user_id: str, email: str, username: str):
        super().__init__(user_id, "UserRegistered")
        self.email = email
        self.username = username

# 2. 整合事件 (Integration Events)
class OrderCompletedEvent(DomainEvent):
    def __init__(self, order_id: str, customer_id: str, total_amount: float):
        super().__init__(order_id, "OrderCompleted")
        self.customer_id = customer_id
        self.total_amount = total_amount

# 3. 系統事件 (System Events)
class PaymentProcessedEvent(DomainEvent):
    def __init__(self, payment_id: str, order_id: str, amount: float):
        super().__init__(payment_id, "PaymentProcessed")
        self.order_id = order_id
        self.amount = amount
```

## Kafka 配置與管理

### Kafka 叢集配置
```yaml
# docker-compose.kafka.yml
version: '3.8'

services:
  zookeeper:
    image: confluentinc/cp-zookeeper:7.4.0
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_TICK_TIME: 2000
    volumes:
      - zookeeper-data:/var/lib/zookeeper/data
      - zookeeper-logs:/var/lib/zookeeper/log

  kafka:
    image: confluentinc/cp-kafka:7.4.0
    depends_on:
      - zookeeper
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://localhost:9092,PLAINTEXT_DOCKER://kafka:29092
      KAFKA_LISTENER_SECURITY_PROTOCOL_MAP: PLAINTEXT:PLAINTEXT,PLAINTEXT_DOCKER:PLAINTEXT
      KAFKA_INTER_BROKER_LISTENER_NAME: PLAINTEXT_DOCKER
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
      KAFKA_AUTO_CREATE_TOPICS_ENABLE: 'false'
    ports:
      - "9092:9092"
    volumes:
      - kafka-data:/var/lib/kafka/data

  kafka-ui:
    image: provectuslabs/kafka-ui:latest
    depends_on:
      - kafka
    environment:
      KAFKA_CLUSTERS_0_NAME: local
      KAFKA_CLUSTERS_0_BOOTSTRAPSERVERS: kafka:29092
    ports:
      - "8080:8080"

volumes:
  zookeeper-data:
  zookeeper-logs:
  kafka-data:
```

### Topic 管理策略
```python
from aiokafka.admin import AIOKafkaAdminClient, NewTopic

class KafkaTopicManager:
    """Kafka Topic 管理器"""

    def __init__(self, bootstrap_servers: str):
        self.bootstrap_servers = bootstrap_servers
        self.admin_client = None

    async def initialize(self):
        """初始化 Admin 客戶端"""
        self.admin_client = AIOKafkaAdminClient(
            bootstrap_servers=self.bootstrap_servers
        )
        await self.admin_client.start()

    async def create_topics(self):
        """建立所有必要的 Topics"""
        topics = [
            # 使用者相關事件
            NewTopic(
                name="user.events",
                num_partitions=3,
                replication_factor=1
            ),
            # 訂單相關事件
            NewTopic(
                name="order.events",
                num_partitions=6,
                replication_factor=1
            ),
            # 支付相關事件
            NewTopic(
                name="payment.events",
                num_partitions=3,
                replication_factor=1
            ),
            # 通知相關事件
            NewTopic(
                name="notification.events",
                num_partitions=3,
                replication_factor=1
            ),
            # 死信佇列
            NewTopic(
                name="dead-letter-queue",
                num_partitions=1,
                replication_factor=1
            )
        ]

        try:
            await self.admin_client.create_topics(topics, validate_only=False)
        except Exception as e:
            print(f"Error creating topics: {e}")

    async def cleanup(self):
        """清理資源"""
        if self.admin_client:
            await self.admin_client.close()
```

## 事件建模設計

### 事件結構定義
```python
from dataclasses import dataclass, asdict
from typing import Dict, Any
import json

@dataclass
class EventMetadata:
    """事件元數據"""
    correlation_id: str
    causation_id: str
    user_id: str
    source_service: str

@dataclass
class EventEnvelope:
    """事件信封 - 包裝事件的標準格式"""
    event_id: str
    event_type: str
    aggregate_id: str
    aggregate_type: str
    event_version: int
    timestamp: str
    metadata: EventMetadata
    payload: Dict[str, Any]

    def to_json(self) -> str:
        """序列化為 JSON"""
        return json.dumps(asdict(self), ensure_ascii=False, default=str)

    @classmethod
    def from_json(cls, json_str: str) -> 'EventEnvelope':
        """從 JSON 反序列化"""
        data = json.loads(json_str)
        metadata = EventMetadata(**data['metadata'])
        return cls(
            event_id=data['event_id'],
            event_type=data['event_type'],
            aggregate_id=data['aggregate_id'],
            aggregate_type=data['aggregate_type'],
            event_version=data['event_version'],
            timestamp=data['timestamp'],
            metadata=metadata,
            payload=data['payload']
        )

# 具體事件實作
class OrderCreatedEvent:
    """訂單建立事件"""

    def __init__(self, order_id: str, customer_id: str, items: List[Dict], total: float):
        self.order_id = order_id
        self.customer_id = customer_id
        self.items = items
        self.total = total

    def to_envelope(self, metadata: EventMetadata) -> EventEnvelope:
        """轉換為事件信封"""
        return EventEnvelope(
            event_id=str(uuid4()),
            event_type="OrderCreated",
            aggregate_id=self.order_id,
            aggregate_type="Order",
            event_version=1,
            timestamp=datetime.utcnow().isoformat(),
            metadata=metadata,
            payload={
                "order_id": self.order_id,
                "customer_id": self.customer_id,
                "items": self.items,
                "total": self.total
            }
        )
```

## 事件發布與訂閱

### Kafka 發布器實作
```python
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
import asyncio

class KafkaEventPublisher:
    """Kafka 事件發布器"""

    def __init__(self, bootstrap_servers: str):
        self.bootstrap_servers = bootstrap_servers
        self.producer = None

    async def start(self):
        """啟動發布器"""
        self.producer = AIOKafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            value_serializer=lambda x: x.encode('utf-8') if isinstance(x, str) else x,
            compression_type='gzip',
            acks='all',  # 等待所有副本確認
            retries=3,
            max_in_flight_requests_per_connection=1  # 保證訊息順序
        )
        await self.producer.start()

    async def publish_event(self, topic: str, event_envelope: EventEnvelope):
        """發布事件"""
        try:
            # 使用 aggregate_id 作為 partition key 確保順序
            partition_key = event_envelope.aggregate_id.encode('utf-8')

            await self.producer.send_and_wait(
                topic=topic,
                key=partition_key,
                value=event_envelope.to_json()
            )

            print(f"Event published: {event_envelope.event_type} to {topic}")

        except Exception as e:
            print(f"Failed to publish event: {e}")
            raise

    async def stop(self):
        """停止發布器"""
        if self.producer:
            await self.producer.stop()

class KafkaEventConsumer:
    """Kafka 事件消費者"""

    def __init__(self, bootstrap_servers: str, group_id: str, topics: List[str]):
        self.bootstrap_servers = bootstrap_servers
        self.group_id = group_id
        self.topics = topics
        self.consumer = None
        self.event_handlers = {}

    def register_handler(self, event_type: str, handler: callable):
        """註冊事件處理器"""
        self.event_handlers[event_type] = handler

    async def start_consuming(self):
        """開始消費事件"""
        self.consumer = AIOKafkaConsumer(
            *self.topics,
            bootstrap_servers=self.bootstrap_servers,
            group_id=self.group_id,
            auto_offset_reset='earliest',
            enable_auto_commit=False,  # 手動提交 offset
            value_deserializer=lambda x: x.decode('utf-8')
        )

        await self.consumer.start()

        try:
            async for msg in self.consumer:
                await self._process_message(msg)
        finally:
            await self.consumer.stop()

    async def _process_message(self, msg):
        """處理訊息"""
        try:
            # 反序列化事件
            event_envelope = EventEnvelope.from_json(msg.value)

            # 查找對應的處理器
            handler = self.event_handlers.get(event_envelope.event_type)

            if handler:
                await handler(event_envelope)

                # 手動提交 offset
                await self.consumer.commit()

                print(f"Event processed: {event_envelope.event_type}")
            else:
                print(f"No handler found for event: {event_envelope.event_type}")

        except Exception as e:
            print(f"Error processing message: {e}")
            # 可以將失敗的訊息發送到死信佇列
            await self._send_to_dead_letter_queue(msg)

    async def _send_to_dead_letter_queue(self, msg):
        """發送到死信佇列"""
        # 實作死信佇列邏輯
        pass
```

### 事件處理器實作
```python
class OrderEventHandlers:
    """訂單事件處理器"""

    def __init__(self, notification_service, inventory_service):
        self.notification_service = notification_service
        self.inventory_service = inventory_service

    async def handle_order_created(self, event_envelope: EventEnvelope):
        """處理訂單建立事件"""
        payload = event_envelope.payload

        # 發送確認郵件
        await self.notification_service.send_order_confirmation(
            customer_id=payload['customer_id'],
            order_id=payload['order_id']
        )

        # 更新庫存
        for item in payload['items']:
            await self.inventory_service.reserve_item(
                product_id=item['product_id'],
                quantity=item['quantity']
            )

    async def handle_payment_completed(self, event_envelope: EventEnvelope):
        """處理付款完成事件"""
        payload = event_envelope.payload

        # 發送付款確認
        await self.notification_service.send_payment_confirmation(
            customer_id=payload['customer_id'],
            order_id=payload['order_id'],
            amount=payload['amount']
        )

# 註冊事件處理器
async def setup_event_consumers():
    """設定事件消費者"""

    # 通知服務消費者
    notification_consumer = KafkaEventConsumer(
        bootstrap_servers="localhost:9092",
        group_id="notification-service",
        topics=["order.events", "payment.events"]
    )

    handlers = OrderEventHandlers(notification_service, inventory_service)
    notification_consumer.register_handler("OrderCreated", handlers.handle_order_created)
    notification_consumer.register_handler("PaymentCompleted", handlers.handle_payment_completed)

    # 啟動消費者
    await notification_consumer.start_consuming()
```

## 事件溯源 (Event Sourcing)

### 事件儲存實作
```python
class PostgreSQLEventStore:
    """PostgreSQL 事件儲存實作"""

    def __init__(self, connection_pool):
        self.pool = connection_pool

    async def append_events(self, stream_id: str, expected_version: int,
                          events: List[EventEnvelope]):
        """追加事件到事件流"""

        async with self.pool.acquire() as conn:
            async with conn.transaction():
                # 檢查版本號避免並發衝突
                current_version = await self._get_current_version(conn, stream_id)

                if current_version != expected_version:
                    raise ConcurrencyError(f"Expected version {expected_version}, "
                                         f"but current version is {current_version}")

                # 插入事件
                for i, event in enumerate(events):
                    await conn.execute("""
                        INSERT INTO events (
                            stream_id, event_id, event_type, event_data,
                            event_version, created_at
                        ) VALUES ($1, $2, $3, $4, $5, $6)
                    """, stream_id, event.event_id, event.event_type,
                        event.to_json(), expected_version + i + 1,
                        datetime.utcnow())

    async def get_events(self, stream_id: str, from_version: int = 0) -> List[EventEnvelope]:
        """取得事件流中的事件"""

        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT event_data FROM events
                WHERE stream_id = $1 AND event_version > $2
                ORDER BY event_version
            """, stream_id, from_version)

            return [EventEnvelope.from_json(row['event_data']) for row in rows]

# 聚合重建
class OrderAggregate:
    """使用事件溯源的訂單聚合"""

    def __init__(self):
        self.id = None
        self.customer_id = None
        self.items = []
        self.status = "DRAFT"
        self.total = 0.0
        self.version = 0

    @classmethod
    async def load_from_history(cls, order_id: str, event_store: PostgreSQLEventStore):
        """從事件歷史重建聚合"""
        aggregate = cls()
        events = await event_store.get_events(order_id)

        for event_envelope in events:
            aggregate._apply_event(event_envelope)
            aggregate.version += 1

        return aggregate

    def _apply_event(self, event_envelope: EventEnvelope):
        """套用事件到聚合"""
        event_type = event_envelope.event_type
        payload = event_envelope.payload

        if event_type == "OrderCreated":
            self.id = payload['order_id']
            self.customer_id = payload['customer_id']
            self.items = payload['items']
            self.total = payload['total']
            self.status = "CREATED"

        elif event_type == "OrderConfirmed":
            self.status = "CONFIRMED"

        elif event_type == "OrderCancelled":
            self.status = "CANCELLED"
```

---

*最後更新: 2025-01-XX*
