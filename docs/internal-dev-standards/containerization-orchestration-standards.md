# 容器化與編排規範 Containerization & Orchestration Standards

## 目錄 Table of Contents

1. [Docker 容器化策略](#docker-容器化策略)
2. [微服務 Docker 配置](#微服務-docker-配置)
3. [Docker Compose 編排](#docker-compose-編排)
4. [環境變數管理](#環境變數管理)
5. [網路配置](#網路配置)
6. [資料持久化](#資料持久化)
7. [監控與日誌](#監控與日誌)
8. [CI/CD 整合](#cicd-整合)

## Docker 容器化策略

### 微服務 Dockerfile 範例
```dockerfile
# services/user-service/Dockerfile
FROM python:3.13-slim as builder

WORKDIR /app

# 安裝 uv
RUN pip install uv

# 複製依賴文件
COPY pyproject.toml uv.lock ./

# 安裝依賴
RUN uv sync --frozen

# 生產階段
FROM python:3.13-slim as production

WORKDIR /app

# 複製已安裝的依賴
COPY --from=builder /app/.venv /app/.venv

# 設置 PATH
ENV PATH="/app/.venv/bin:$PATH"

# 複製應用程式代碼
COPY ./app ./app

# 建立非 root 使用者
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /app
USER appuser

# 健康檢查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 多階段建構優化
```dockerfile
# services/order-service/Dockerfile
FROM python:3.13-slim as base

# 設定基礎環境變數
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 建構階段
FROM base as builder

WORKDIR /app

# 安裝系統依賴
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 安裝 uv
RUN pip install uv

# 複製並安裝 Python 依賴
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# 測試階段
FROM builder as test

# 安裝測試依賴
RUN uv sync --frozen

# 複製原始碼
COPY . .

# 執行測試
RUN uv run pytest tests/ --cov=app --cov-report=html

# 生產階段
FROM base as production

WORKDIR /app

# 只複製生產依賴
COPY --from=builder /app/.venv /app/.venv

# 設置 PATH
ENV PATH="/app/.venv/bin:$PATH"

# 複製應用程式
COPY ./app ./app

# 建立使用者
RUN groupadd -r appuser && useradd -r -g appuser appuser \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 微服務 Docker 配置

### .dockerignore 配置
```
# .dockerignore - 微服務通用配置
**/__pycache__
**/*.pyc
**/*.pyo
**/*.pyd
**/*.pytest_cache
**/node_modules
**/coverage
**/htmlcov
**/.git
**/.gitignore
**/README.md
**/Dockerfile
**/docker-compose*.yml
**/.vscode
**/.idea
**/tests/
**/.coverage
**/*.log
**/temp/
**/tmp/
```

### 服務特定 Docker Compose
```yaml
# services/user-service/docker-compose.service.yml
version: '3.8'

services:
  user-service:
    build:
      context: .
      dockerfile: Dockerfile
      target: production
    environment:
      - DATABASE_URL=postgresql+asyncpg://user_service:${USER_DB_PASSWORD}@user-db:5432/user_service_db
      - KAFKA_BOOTSTRAP_SERVERS=kafka:29092
      - REDIS_URL=redis://redis:6379/0
      - LOG_LEVEL=INFO
    depends_on:
      user-db:
        condition: service_healthy
      kafka:
        condition: service_started
    networks:
      - user-network
      - kafka-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M

  user-db:
    image: postgres:16-alpine
    environment:
      - POSTGRES_DB=user_service_db
      - POSTGRES_USER=user_service
      - POSTGRES_PASSWORD=${USER_DB_PASSWORD}
    volumes:
      - user_db_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql:ro
    networks:
      - user-network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user_service"]
      interval: 30s
      timeout: 10s
      retries: 5
    deploy:
      resources:
        limits:
          memory: 256M

volumes:
  user_db_data:

networks:
  user-network:
    driver: bridge
  kafka-network:
    external: true
```

## Docker Compose 編排

### 主編排文件
```yaml
# docker-compose.microservices.yml
version: '3.8'

x-common-variables: &common-variables
  KAFKA_BOOTSTRAP_SERVERS: kafka:29092
  REDIS_URL: redis://redis:6379
  LOG_LEVEL: ${LOG_LEVEL:-INFO}
  ENVIRONMENT: ${ENVIRONMENT:-development}

services:
  # API Gateway
  kong:
    image: kong:3.4-alpine
    environment:
      KONG_DATABASE: "off"
      KONG_DECLARATIVE_CONFIG: /kong/declarative/kong.yml
      KONG_PROXY_ACCESS_LOG: /dev/stdout
      KONG_ADMIN_ACCESS_LOG: /dev/stdout
      KONG_PROXY_ERROR_LOG: /dev/stderr
      KONG_ADMIN_ERROR_LOG: /dev/stderr
      KONG_ADMIN_LISTEN: 0.0.0.0:8001
    volumes:
      - ./infrastructure/kong/kong.yml:/kong/declarative/kong.yml:ro
    ports:
      - "${KONG_PROXY_PORT:-8000}:8000"
      - "${KONG_ADMIN_PORT:-8001}:8001"
    networks:
      - kong-network
    healthcheck:
      test: ["CMD", "kong", "health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # 基礎設施服務
  zookeeper:
    image: confluentinc/cp-zookeeper:7.4.0
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181
      ZOOKEEPER_TICK_TIME: 2000
    volumes:
      - zookeeper_data:/var/lib/zookeeper/data
      - zookeeper_logs:/var/lib/zookeeper/log
    networks:
      - kafka-network

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
    ports:
      - "9092:9092"
    volumes:
      - kafka_data:/var/lib/kafka/data
    networks:
      - kafka-network
    healthcheck:
      test: ["CMD", "kafka-broker-api-versions", "--bootstrap-server", "localhost:9092"]
      interval: 30s
      timeout: 10s
      retries: 3

  redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    networks:
      - redis-network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

  # 業務服務
  user-service:
    build:
      context: ./services/user-service
      dockerfile: Dockerfile
      target: production
    environment:
      <<: *common-variables
      DATABASE_URL: postgresql+asyncpg://user_service:${USER_DB_PASSWORD}@user-db:5432/user_service_db
      SERVICE_NAME: user-service
    depends_on:
      user-db:
        condition: service_healthy
      kafka:
        condition: service_healthy
      redis:
        condition: service_healthy
    networks:
      - user-network
      - kafka-network
      - redis-network
      - kong-network
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '1.0'
          memory: 1G

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
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user_service"]
      interval: 30s
      timeout: 10s
      retries: 5

volumes:
  zookeeper_data:
  zookeeper_logs:
  kafka_data:
  redis_data:
  user_db_data:
  product_db_data:
  order_db_data:

networks:
  kong-network:
    driver: bridge
  kafka-network:
    driver: bridge
  redis-network:
    driver: bridge
  user-network:
    driver: bridge
  product-network:
    driver: bridge
  order-network:
    driver: bridge
```

## 環境變數管理

### 環境配置模板
```bash
# .env.template
# 複製此文件為 .env 並填入實際值

# 環境設定
ENVIRONMENT=development
LOG_LEVEL=INFO

# 資料庫密碼
USER_DB_PASSWORD=secure_user_password
PRODUCT_DB_PASSWORD=secure_product_password
ORDER_DB_PASSWORD=secure_order_password
PAYMENT_DB_PASSWORD=secure_payment_password

# Kong Gateway
KONG_PROXY_PORT=8000
KONG_ADMIN_PORT=8001

# JWT Secret
JWT_SECRET_KEY=your-super-secret-jwt-key
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=30

# 外部服務
PAYMENT_GATEWAY_URL=https://api.payment-provider.com
NOTIFICATION_SERVICE_API_KEY=your-notification-api-key

# 監控
JAEGER_AGENT_HOST=jaeger
JAEGER_AGENT_PORT=14268
PROMETHEUS_GATEWAY=prometheus:9091
```

### 開發與生產環境分離
```yaml
# docker-compose.override.yml (開發環境)
version: '3.8'

services:
  user-service:
    environment:
      - DEBUG=true
      - RELOAD=true
    volumes:
      - ./services/user-service:/app:cached
    ports:
      - "8001:8000"
    command: ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

  product-service:
    volumes:
      - ./services/product-service:/app:cached
    ports:
      - "8002:8000"
    command: ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

  # 開發工具
  kafka-ui:
    image: provectuslabs/kafka-ui:latest
    environment:
      KAFKA_CLUSTERS_0_NAME: local
      KAFKA_CLUSTERS_0_BOOTSTRAPSERVERS: kafka:29092
    ports:
      - "8080:8080"
    networks:
      - kafka-network

  redis-commander:
    image: rediscommander/redis-commander:latest
    environment:
      REDIS_HOSTS: local:redis:6379
    ports:
      - "8081:8081"
    networks:
      - redis-network
```

```yaml
# docker-compose.prod.yml (生產環境)
version: '3.8'

services:
  user-service:
    environment:
      - DEBUG=false
      - RELOAD=false
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '1.0'
          memory: 1G
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"
```

## 網路配置

### 網路隔離策略
```yaml
# networks/networks.yml
version: '3.8'

networks:
  # 前端網路 - 對外暴露
  frontend-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16

  # API Gateway 網路
  gateway-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.21.0.0/16

  # 業務服務網路
  services-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.22.0.0/16

  # 資料庫網路 - 內部隔離
  database-network:
    driver: bridge
    internal: true
    ipam:
      config:
        - subnet: 172.23.0.0/16

  # 快取網路
  cache-network:
    driver: bridge
    internal: true
    ipam:
      config:
        - subnet: 172.24.0.0/16

  # 訊息佇列網路
  messaging-network:
    driver: bridge
    internal: true
    ipam:
      config:
        - subnet: 172.25.0.0/16
```

## 監控與日誌

### 監控堆疊配置
```yaml
# monitoring/docker-compose.monitoring.yml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml:ro
      - prometheus_data:/prometheus
    ports:
      - "9090:9090"
    networks:
      - monitoring

  grafana:
    image: grafana/grafana:latest
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning:ro
    ports:
      - "3000:3000"
    networks:
      - monitoring

  jaeger:
    image: jaegertracing/all-in-one:latest
    environment:
      - COLLECTOR_OTLP_ENABLED=true
    ports:
      - "16686:16686"
      - "14268:14268"
    networks:
      - monitoring

  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:8.11.0
    environment:
      - discovery.type=single-node
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
      - xpack.security.enabled=false
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data
    ports:
      - "9200:9200"
    networks:
      - monitoring

  kibana:
    image: docker.elastic.co/kibana/kibana:8.11.0
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
    ports:
      - "5601:5601"
    depends_on:
      - elasticsearch
    networks:
      - monitoring

volumes:
  prometheus_data:
  grafana_data:
  elasticsearch_data:

networks:
  monitoring:
    driver: bridge
```

### 日誌配置
```yaml
# logging/docker-compose.logging.yml
version: '3.8'

x-logging: &default-logging
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"

services:
  user-service:
    logging: *default-logging
    environment:
      - LOG_FORMAT=json
      - LOG_LEVEL=INFO
    labels:
      - "logging=true"
      - "service=user-service"

  # Fluentd 日誌收集器
  fluentd:
    image: fluent/fluentd:v1.16-debian-1
    volumes:
      - ./fluentd/fluent.conf:/fluentd/etc/fluent.conf:ro
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
    ports:
      - "24224:24224"
    networks:
      - monitoring
```

## CI/CD 整合

### GitLab CI 配置
```yaml
# .gitlab-ci.yml
stages:
  - test
  - build
  - deploy

variables:
  DOCKER_DRIVER: overlay2
  DOCKER_TLS_CERTDIR: "/certs"

# 測試階段
test:microservices:
  stage: test
  image: docker:20.10.16
  services:
    - docker:20.10.16-dind
  script:
    - docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit
    - docker-compose -f docker-compose.test.yml down
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml

# 建構階段
build:images:
  stage: build
  image: docker:20.10.16
  services:
    - docker:20.10.16-dind
  before_script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
  script:
    - |
      for service in user-service product-service order-service; do
        docker build -t $CI_REGISTRY_IMAGE/$service:$CI_COMMIT_SHA ./services/$service
        docker push $CI_REGISTRY_IMAGE/$service:$CI_COMMIT_SHA
      done
  only:
    - main
    - develop

# 部署階段
deploy:staging:
  stage: deploy
  image: alpine:latest
  before_script:
    - apk add --no-cache openssh-client docker-compose
  script:
    - ssh $DEPLOY_USER@$STAGING_SERVER "
        cd /opt/microservices &&
        export IMAGE_TAG=$CI_COMMIT_SHA &&
        docker-compose -f docker-compose.prod.yml pull &&
        docker-compose -f docker-compose.prod.yml up -d"
  environment:
    name: staging
    url: https://staging.yourdomain.com
  only:
    - develop

deploy:production:
  stage: deploy
  script:
    - ssh $DEPLOY_USER@$PRODUCTION_SERVER "
        cd /opt/microservices &&
        export IMAGE_TAG=$CI_COMMIT_SHA &&
        docker-compose -f docker-compose.prod.yml pull &&
        docker-compose -f docker-compose.prod.yml up -d"
  environment:
    name: production
    url: https://yourdomain.com
  when: manual
  only:
    - main
```

### 部署腳本
```bash
#!/bin/bash
# scripts/deploy.sh

set -e

ENVIRONMENT=${1:-staging}
IMAGE_TAG=${2:-latest}

echo "🚀 Deploying microservices to $ENVIRONMENT..."

# 設定環境變數
export IMAGE_TAG=$IMAGE_TAG
export ENVIRONMENT=$ENVIRONMENT

# 拉取最新映像
echo "📥 Pulling latest images..."
docker-compose -f docker-compose.prod.yml pull

# 執行資料庫遷移
echo "🗄️ Running database migrations..."
docker-compose -f docker-compose.prod.yml run --rm user-service uv run alembic upgrade head
docker-compose -f docker-compose.prod.yml run --rm product-service uv run alembic upgrade head
docker-compose -f docker-compose.prod.yml run --rm order-service uv run alembic upgrade head

# 部署服務
echo "🐳 Starting services..."
docker-compose -f docker-compose.prod.yml up -d

# 等待服務啟動
echo "⏳ Waiting for services to be ready..."
./scripts/wait-for-services.sh

# 執行健康檢查
echo "🏥 Running health checks..."
./scripts/health-check.sh

echo "✅ Deployment completed successfully!"
```

---

*最後更新: 2025-01-XX*
