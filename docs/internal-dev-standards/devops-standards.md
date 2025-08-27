# DevOps 規範 DevOps Standards

## 目錄 Table of Contents

1. [基礎設施規範](#基礎設施規範)
2. [容器化規範](#容器化規範)
3. [CI/CD 流程](#cicd-流程)
4. [部署策略](#部署策略)
5. [監控與日誌](#監控與日誌)
6. [安全性規範](#安全性規範)
7. [災難恢復](#災難恢復)

## 基礎設施規範

### 技術棧
- **容器平台**: Docker + Docker Compose
- **反向代理**: Nginx
- **API Gateway**: Kong (JWT 驗證)
- **版本控制**: Git + GitLab
- **CI/CD**: GitLab CI
- **監控**: Prometheus + Grafana
- **日誌**: ELK Stack (Elasticsearch + Logstash + Kibana)

### 環境配置

#### 環境分層
```yaml
# 環境層級
environments:
  development:
    description: "本地開發環境"
    resources: "最小資源配置"
    data: "模擬資料"

  testing:
    description: "測試環境"
    resources: "中等資源配置"
    data: "測試資料集"

  production:
    description: "生產環境"
    resources: "完整資源配置"
    data: "真實資料"
```

### 網路架構
```yaml
# 網路配置
networks:
  frontend_network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16

  backend_network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.21.0.0/16
```

## 容器化規範

### Docker 最佳實踐

#### 多階段構建
```dockerfile
# backend/Dockerfile
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
COPY . .

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

#### 前端 Dockerfile
```dockerfile
# frontend/Dockerfile
FROM node:22-alpine as builder

WORKDIR /app

# 複製依賴文件
COPY package*.json ./

# 安裝依賴
RUN npm ci --only=production

# 複製源代碼
COPY . .

# 構建應用
RUN npm run build

# 生產階段
FROM nginx:alpine as production

# 複製自定義 Nginx 配置
COPY default.conf /etc/nginx/conf.d/default.conf

# 複製構建好的靜態文件
COPY --from=builder /app/dist /usr/share/nginx/html

# 建立非 root 使用者
RUN addgroup -g 1001 -S nginx && \
    adduser -S -D -H -u 1001 -h /var/cache/nginx -s /sbin/nologin -G nginx -g nginx nginx

# 健康檢查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:80/health || exit 1

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

### Docker Compose 配置

#### 開發環境
```yaml
# docker-compose.yml
version: '3.8'

services:
  database:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: ${POSTGRES_DB:-app_dev}
      POSTGRES_USER: ${POSTGRES_USER:-postgres}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-password}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - backend_network
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-postgres}"]
      interval: 30s
      timeout: 10s
      retries: 5

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
      target: development
    environment:
      DATABASE_URL: postgresql+asyncpg://${POSTGRES_USER:-postgres}:${POSTGRES_PASSWORD:-password}@database:5432/${POSTGRES_DB:-app_dev}
      REDIS_URL: redis://redis:6379
    volumes:
      - ./backend:/app
    depends_on:
      database:
        condition: service_healthy
    networks:
      - backend_network
      - frontend_network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      target: development
    environment:
      VITE_API_GATEWAY_URL: http://localhost:8000
    volumes:
      - ./frontend:/app
      - /app/node_modules
    depends_on:
      - backend
    networks:
      - frontend_network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5173"]
      interval: 30s
      timeout: 10s
      retries: 3

  redis:
    image: redis:7-alpine
    networks:
      - backend_network
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  postgres_data:

networks:
  frontend_network:
    driver: bridge
  backend_network:
    driver: bridge
```

#### 生產環境
```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - static_files:/usr/share/nginx/html/static
    depends_on:
      - frontend
      - backend
    networks:
      - frontend_network
    restart: unless-stopped

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      target: production
    environment:
      VITE_API_GATEWAY_URL: https://api.yourdomain.com
    networks:
      - frontend_network
    restart: unless-stopped

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
      target: production
    environment:
      DATABASE_URL: ${DATABASE_URL}
      REDIS_URL: ${REDIS_URL}
      SECRET_KEY: ${SECRET_KEY}
    networks:
      - backend_network
      - frontend_network
    restart: unless-stopped

  database:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./backups:/backups
    networks:
      - backend_network
    restart: unless-stopped

volumes:
  postgres_data:
  static_files:

networks:
  frontend_network:
  backend_network:
```

## CI/CD 流程

### GitLab CI 配置

#### 完整 CI/CD Pipeline
```yaml
# .gitlab-ci.yml
stages:
  - lint
  - test
  - build
  - deploy
  - notify

variables:
  DOCKER_DRIVER: overlay2
  DOCKER_TLS_CERTDIR: "/certs"

# 代碼品質檢查
frontend:lint:
  stage: lint
  image: node:22-alpine
  script:
    - cd frontend
    - npm ci
    - npm run lint:check
    - npm run format:check
  only:
    - merge_requests
    - main
  artifacts:
    reports:
      junit: frontend/lint-results.xml

backend:lint:
  stage: lint
  image: python:3.13-slim
  script:
    - cd backend
    - pip install uv
    - uv sync
    - uv run black --check .
    - uv run flake8 . --format=junit-xml --output-file=flake8-results.xml
  only:
    - merge_requests
    - main
  artifacts:
    reports:
      junit: backend/flake8-results.xml

# 測試階段
frontend:test:
  stage: test
  image: node:22-alpine
  script:
    - cd frontend
    - npm ci
    - npm run test:unit
    - npm run test:coverage
  coverage: '/Lines\s*:\s*(\d+\.?\d*)%/'
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: frontend/coverage/cobertura-coverage.xml
      junit: frontend/test-results.xml

backend:test:
  stage: test
  image: python:3.13-slim
  services:
    - postgres:16-alpine
  variables:
    POSTGRES_DB: test_db
    POSTGRES_USER: test_user
    POSTGRES_PASSWORD: test_password
    DATABASE_URL: postgresql+asyncpg://test_user:test_password@postgres:5432/test_db
  script:
    - cd backend
    - pip install uv
    - uv sync
    - uv run pytest --cov=app --cov-report=xml --junit-xml=test-results.xml tests/
  coverage: '/TOTAL.*\s+(\d+%)$/'
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: backend/coverage.xml
      junit: backend/test-results.xml

# 構建階段
build:images:
  stage: build
  image: docker:24-dind
  services:
    - docker:24-dind
  before_script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
  script:
    - docker build -t $CI_REGISTRY_IMAGE/frontend:$CI_COMMIT_SHA ./frontend
    - docker build -t $CI_REGISTRY_IMAGE/backend:$CI_COMMIT_SHA ./backend
    - docker push $CI_REGISTRY_IMAGE/frontend:$CI_COMMIT_SHA
    - docker push $CI_REGISTRY_IMAGE/backend:$CI_COMMIT_SHA
  only:
    - main
    - develop

# 部署階段
deploy:staging:
  stage: deploy
  image: alpine:latest
  before_script:
    - apk add --no-cache openssh-client
    - eval $(ssh-agent -s)
    - echo "$SSH_PRIVATE_KEY" | tr -d '\r' | ssh-add -
    - mkdir -p ~/.ssh
    - chmod 700 ~/.ssh
    - ssh-keyscan $STAGING_SERVER >> ~/.ssh/known_hosts
    - chmod 644 ~/.ssh/known_hosts
  script:
    - ssh $STAGING_USER@$STAGING_SERVER "
        cd /opt/app &&
        export IMAGE_TAG=$CI_COMMIT_SHA &&
        docker-compose -f docker-compose.staging.yml pull &&
        docker-compose -f docker-compose.staging.yml up -d"
  environment:
    name: staging
    url: https://staging.yourdomain.com
  only:
    - develop

deploy:production:
  stage: deploy
  image: alpine:latest
  before_script:
    - apk add --no-cache openssh-client
    - eval $(ssh-agent -s)
    - echo "$SSH_PRIVATE_KEY" | tr -d '\r' | ssh-add -
  script:
    - ssh $PRODUCTION_USER@$PRODUCTION_SERVER "
        cd /opt/app &&
        export IMAGE_TAG=$CI_COMMIT_SHA &&
        docker-compose -f docker-compose.prod.yml pull &&
        docker-compose -f docker-compose.prod.yml up -d"
  environment:
    name: production
    url: https://yourdomain.com
  when: manual
  only:
    - main

# 通知階段
notify:success:
  stage: notify
  image: alpine:latest
  script:
    - apk add --no-cache curl
    - 'curl -X POST -H "Content-type: application/json" --data "{\"text\":\"✅ Deployment to $CI_ENVIRONMENT_NAME successful: $CI_PIPELINE_URL\"}" $SLACK_WEBHOOK_URL'
  when: on_success

notify:failure:
  stage: notify
  image: alpine:latest
  script:
    - apk add --no-cache curl
    - 'curl -X POST -H "Content-type: application/json" --data "{\"text\":\"❌ Deployment to $CI_ENVIRONMENT_NAME failed: $CI_PIPELINE_URL\"}" $SLACK_WEBHOOK_URL'
  when: on_failure
```

### 部署腳本

#### 零停機部署腳本
```bash
#!/bin/bash
# scripts/deploy.sh

set -e

ENVIRONMENT=${1:-staging}
IMAGE_TAG=${2:-latest}

echo "🚀 Starting deployment to $ENVIRONMENT environment..."
echo "📦 Using image tag: $IMAGE_TAG"

# 驗證環境
if [[ ! "$ENVIRONMENT" =~ ^(staging|production)$ ]]; then
    echo "❌ Invalid environment. Use 'staging' or 'production'"
    exit 1
fi

# 設置變數
COMPOSE_FILE="docker-compose.$ENVIRONMENT.yml"
BACKUP_DIR="/backups/$(date +%Y%m%d_%H%M%S)"

# 檢查必要檔案
if [ ! -f "$COMPOSE_FILE" ]; then
    echo "❌ Compose file $COMPOSE_FILE not found"
    exit 1
fi

# 建立備份目錄
mkdir -p "$BACKUP_DIR"

# 資料庫備份
echo "📂 Creating database backup..."
docker-compose -f "$COMPOSE_FILE" exec -T database pg_dump -U $POSTGRES_USER $POSTGRES_DB > "$BACKUP_DIR/database.sql"

# 拉取新映像
echo "📥 Pulling new images..."
export IMAGE_TAG=$IMAGE_TAG
docker-compose -f "$COMPOSE_FILE" pull

# 滾動更新
echo "🔄 Performing rolling update..."

# 更新後端 (先更新一個實例)
docker-compose -f "$COMPOSE_FILE" up -d --no-deps --scale backend=2 backend
sleep 30

# 健康檢查
echo "🏥 Performing health check..."
BACKEND_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health)
if [ "$BACKEND_HEALTH" != "200" ]; then
    echo "❌ Backend health check failed. Rolling back..."
    docker-compose -f "$COMPOSE_FILE" down
    exit 1
fi

# 更新前端
docker-compose -f "$COMPOSE_FILE" up -d --no-deps frontend

# 最終健康檢查
sleep 30
FRONTEND_HEALTH=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:80/health)
if [ "$FRONTEND_HEALTH" != "200" ]; then
    echo "❌ Frontend health check failed. Rolling back..."
    docker-compose -f "$COMPOSE_FILE" down
    exit 1
fi

# 清理舊映像
echo "🧹 Cleaning up old images..."
docker image prune -f

echo "✅ Deployment completed successfully!"
echo "📊 Application status:"
docker-compose -f "$COMPOSE_FILE" ps
```

## 監控與日誌

### Prometheus 配置
```yaml
# monitoring/prometheus/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alert_rules.yml"

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'backend'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'
    scrape_interval: 10s

  - job_name: 'frontend'
    static_configs:
      - targets: ['frontend:80']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093
```

### 告警規則
```yaml
# monitoring/prometheus/alert_rules.yml
groups:
  - name: application_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} errors per second"

      - alert: HighResponseTime
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High response time detected"
          description: "95th percentile response time is {{ $value }}s"

      - alert: DatabaseDown
        expr: up{job="postgres"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Database is down"
          description: "PostgreSQL database is not responding"
```

### ELK Stack 配置
```yaml
# monitoring/elk/logstash/pipeline/logstash.conf
input {
  beats {
    port => 5044
  }
}

filter {
  if [fields][service] == "backend" {
    grok {
      match => { "message" => "%{TIMESTAMP_ISO8601:timestamp} %{LOGLEVEL:level} %{GREEDYDATA:message}" }
    }

    date {
      match => [ "timestamp", "ISO8601" ]
    }
  }

  if [fields][service] == "frontend" {
    grok {
      match => { "message" => "%{COMBINEDAPACHELOG}" }
    }
  }
}

output {
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "logs-%{[fields][service]}-%{+YYYY.MM.dd}"
  }
}
```

## 安全性規範

### SSL/TLS 配置
```nginx
# nginx/ssl.conf
server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;

    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;

    add_header Strict-Transport-Security "max-age=63072000" always;
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
}
```

### 環境變數管理
```bash
# .env.template
# 資料庫配置
POSTGRES_DB=your_database
POSTGRES_USER=your_user
POSTGRES_PASSWORD=your_secure_password

# 應用程式配置
SECRET_KEY=your_secret_key_here
DEBUG=false
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# 第三方服務
REDIS_URL=redis://redis:6379
SMTP_HOST=smtp.yourdomain.com
SMTP_PORT=587
```

## 災難恢復

### 備份策略
```bash
#!/bin/bash
# scripts/backup.sh

# 資料庫備份
docker-compose exec database pg_dump -U $POSTGRES_USER $POSTGRES_DB | gzip > "backup_$(date +%Y%m%d_%H%M%S).sql.gz"

# 檔案備份
tar -czf "files_backup_$(date +%Y%m%d_%H%M%S).tar.gz" /opt/app/uploads

# 上傳到雲端儲存
aws s3 cp backup_*.sql.gz s3://your-backup-bucket/database/
aws s3 cp files_backup_*.tar.gz s3://your-backup-bucket/files/

# 清理本地備份 (保留 7 天)
find . -name "backup_*.sql.gz" -mtime +7 -delete
find . -name "files_backup_*.tar.gz" -mtime +7 -delete
```

### 恢復程序
```bash
#!/bin/bash
# scripts/restore.sh

BACKUP_FILE=$1

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file>"
    exit 1
fi

# 停止應用程式
docker-compose down

# 恢復資料庫
gunzip -c "$BACKUP_FILE" | docker-compose exec -T database psql -U $POSTGRES_USER $POSTGRES_DB

# 重新啟動應用程式
docker-compose up -d

echo "✅ Restore completed successfully!"
```

---

*最後更新: 2025-01-XX*
