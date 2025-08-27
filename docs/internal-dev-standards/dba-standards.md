# DBA 規範 Database Administration Standards

## 目錄 Table of Contents

1. [資料庫設計規範](#資料庫設計規範)
2. [命名慣例](#命名慣例)
3. [效能優化](#效能優化)
4. [安全性規範](#安全性規範)
5. [備份與恢復](#備份與恢復)
6. [監控與維護](#監控與維護)
7. [版本控制與遷移](#版本控制與遷移)

## 資料庫設計規範

### 技術規範
- **資料庫**: PostgreSQL 16+
- **連接池**: PgBouncer
- **ORM**: SQLAlchemy (Python), Entity Framework Core (.NET)
- **遷移工具**: Alembic (Python), EF Core Migrations (.NET)

### 表格設計原則

#### 基礎欄位標準
```sql
-- 所有表格必須包含的基礎欄位
CREATE TABLE example_table (
    id SERIAL PRIMARY KEY,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    created_by INTEGER REFERENCES users(id),
    updated_by INTEGER REFERENCES users(id),
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    version INTEGER NOT NULL DEFAULT 1,

    -- 業務欄位
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) NOT NULL DEFAULT 'active'
);

-- 自動更新 updated_at 觸發器
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    NEW.version = NEW.version + 1;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_example_table_updated_at
    BEFORE UPDATE ON example_table
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

#### 資料類型規範
```sql
-- 字串類型
name VARCHAR(255)           -- 一般名稱 (最大 255 字元)
title VARCHAR(500)          -- 標題 (最大 500 字元)
description TEXT            -- 長文本描述
code VARCHAR(50)            -- 代碼/編號
email VARCHAR(320)          -- Email 地址 (RFC 5321 標準)
phone VARCHAR(20)           -- 電話號碼

-- 數值類型
id SERIAL PRIMARY KEY       -- 主鍵 ID
amount DECIMAL(15,2)        -- 金額 (精確度要求高)
percentage DECIMAL(5,2)     -- 百分比 (0.00 ~ 999.99)
quantity INTEGER            -- 數量
weight DECIMAL(10,3)        -- 重量

-- 日期時間類型
created_at TIMESTAMP WITH TIME ZONE    -- 建立時間 (含時區)
birth_date DATE                        -- 生日 (僅日期)
start_time TIME                        -- 開始時間 (僅時間)

-- 布林類型
is_active BOOLEAN NOT NULL DEFAULT TRUE
is_deleted BOOLEAN NOT NULL DEFAULT FALSE

-- JSON 類型
metadata JSONB              -- 結構化資料
settings JSONB              -- 設定資料
```

## 命名慣例

### 表格命名
```sql
-- 表格名稱使用複數形式的 snake_case
users                       -- 使用者表
user_profiles              -- 使用者檔案表
order_items                -- 訂單項目表
product_categories         -- 產品分類表

-- 關聯表命名
user_roles                 -- 使用者角色關聯表
project_members            -- 專案成員關聯表
```

### 欄位命名
```sql
-- 欄位名稱使用 snake_case
user_id                    -- 外鍵
first_name                 -- 名字
last_name                  -- 姓氏
email_address              -- Email 地址
phone_number               -- 電話號碼
birth_date                 -- 生日
is_active                  -- 狀態標記
created_at                 -- 建立時間
updated_at                 -- 更新時間

-- 布林欄位使用 is_ 或 has_ 前綴
is_verified                -- 是否已驗證
has_permission             -- 是否有權限
can_edit                   -- 是否可編輯
```

### 索引命名
```sql
-- 索引命名格式: idx_表格名_欄位名[_欄位名]
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_first_name_last_name ON users(first_name, last_name);
CREATE INDEX idx_orders_user_id_created_at ON orders(user_id, created_at);

-- 唯一索引
CREATE UNIQUE INDEX uniq_users_email ON users(email);
CREATE UNIQUE INDEX uniq_products_code ON products(code);

-- 部分索引
CREATE INDEX idx_orders_active ON orders(created_at) WHERE is_deleted = FALSE;
```

### 約束命名
```sql
-- 主鍵約束: pk_表格名
ALTER TABLE users ADD CONSTRAINT pk_users PRIMARY KEY (id);

-- 外鍵約束: fk_表格名_參考表格名
ALTER TABLE orders ADD CONSTRAINT fk_orders_users
    FOREIGN KEY (user_id) REFERENCES users(id);

-- 檢查約束: chk_表格名_欄位名
ALTER TABLE users ADD CONSTRAINT chk_users_email
    CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$');

-- 唯一約束: uniq_表格名_欄位名
ALTER TABLE users ADD CONSTRAINT uniq_users_username UNIQUE (username);
```

## 效能優化

### 索引策略

#### 查詢優化索引
```sql
-- 單欄位索引 (高選擇性欄位)
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_orders_status ON orders(status);

-- 複合索引 (最常用的查詢組合)
CREATE INDEX idx_orders_user_id_created_at ON orders(user_id, created_at DESC);
CREATE INDEX idx_products_category_id_is_active ON products(category_id, is_active);

-- 部分索引 (條件篩選)
CREATE INDEX idx_orders_pending ON orders(created_at)
WHERE status = 'pending';

CREATE INDEX idx_users_active_email ON users(email)
WHERE is_active = TRUE AND is_deleted = FALSE;

-- 表達式索引
CREATE INDEX idx_users_lower_email ON users(LOWER(email));
CREATE INDEX idx_products_full_text ON products
USING gin(to_tsvector('english', name || ' ' || description));
```

#### 查詢最佳化
```sql
-- 使用 EXPLAIN ANALYZE 分析查詢計畫
EXPLAIN ANALYZE
SELECT u.id, u.username, COUNT(o.id) as order_count
FROM users u
LEFT JOIN orders o ON u.id = o.user_id
WHERE u.is_active = TRUE
  AND u.created_at >= '2024-01-01'
GROUP BY u.id, u.username
ORDER BY order_count DESC
LIMIT 100;

-- 避免 SELECT *，明確指定需要的欄位
SELECT u.id, u.username, u.email
FROM users u
WHERE u.is_active = TRUE;

-- 使用適當的 JOIN 類型
-- INNER JOIN (只返回匹配的記錄)
SELECT u.username, p.title
FROM users u
INNER JOIN posts p ON u.id = p.user_id;

-- LEFT JOIN (返回左表所有記錄)
SELECT u.username, COUNT(p.id) as post_count
FROM users u
LEFT JOIN posts p ON u.id = p.user_id
GROUP BY u.id, u.username;
```

### 分割策略

#### 水平分割 (Partitioning)
```sql
-- 按時間分割表格
CREATE TABLE orders (
    id SERIAL,
    user_id INTEGER NOT NULL,
    order_date DATE NOT NULL,
    amount DECIMAL(10,2),
    status VARCHAR(50)
) PARTITION BY RANGE (order_date);

-- 建立分割區
CREATE TABLE orders_2024_q1 PARTITION OF orders
    FOR VALUES FROM ('2024-01-01') TO ('2024-04-01');

CREATE TABLE orders_2024_q2 PARTITION OF orders
    FOR VALUES FROM ('2024-04-01') TO ('2024-07-01');

-- 自動建立分割區的函數
CREATE OR REPLACE FUNCTION create_monthly_partition(table_name text, start_date date)
RETURNS void AS $$
DECLARE
    partition_name text;
    end_date date;
BEGIN
    partition_name := table_name || '_' || to_char(start_date, 'YYYY_MM');
    end_date := start_date + interval '1 month';

    EXECUTE format('CREATE TABLE %I PARTITION OF %I
                    FOR VALUES FROM (%L) TO (%L)',
                    partition_name, table_name, start_date, end_date);
END;
$$ LANGUAGE plpgsql;
```

### 查詢快取策略

#### Redis 快取實作
```python
# Python - Redis 快取裝飾器
import redis
import json
from functools import wraps
from typing import Any, Optional

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def cache_result(expire_time: int = 3600):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 生成快取鍵
            cache_key = f"{func.__name__}:{hash(str(args) + str(kwargs))}"

            # 嘗試從快取獲取
            cached_result = redis_client.get(cache_key)
            if cached_result:
                return json.loads(cached_result)

            # 執行函數並快取結果
            result = await func(*args, **kwargs)
            redis_client.setex(
                cache_key,
                expire_time,
                json.dumps(result, default=str)
            )

            return result
        return wrapper
    return decorator

# 使用範例
@cache_result(expire_time=1800)  # 30 分鐘快取
async def get_user_profile(user_id: int):
    # 資料庫查詢邏輯
    pass
```

## 安全性規範

### 使用者權限管理
```sql
-- 建立專用資料庫使用者
CREATE USER app_readonly WITH PASSWORD 'secure_password';
CREATE USER app_readwrite WITH PASSWORD 'secure_password';
CREATE USER app_admin WITH PASSWORD 'secure_password';

-- 設定權限
-- 唯讀使用者
GRANT CONNECT ON DATABASE app_db TO app_readonly;
GRANT USAGE ON SCHEMA public TO app_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO app_readonly;

-- 讀寫使用者
GRANT CONNECT ON DATABASE app_db TO app_readwrite;
GRANT USAGE ON SCHEMA public TO app_readwrite;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO app_readwrite;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO app_readwrite;

-- 管理使用者
GRANT ALL PRIVILEGES ON DATABASE app_db TO app_admin;
```

### 資料加密
```sql
-- 敏感資料加密
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- 加密敏感欄位
CREATE TABLE user_sensitive_data (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    encrypted_ssn BYTEA,  -- 加密的身分證字號
    encrypted_credit_card BYTEA,  -- 加密的信用卡號
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 加密函數
CREATE OR REPLACE FUNCTION encrypt_sensitive_data(data text, key text)
RETURNS bytea AS $$
BEGIN
    RETURN pgp_sym_encrypt(data, key);
END;
$$ LANGUAGE plpgsql;

-- 解密函數
CREATE OR REPLACE FUNCTION decrypt_sensitive_data(encrypted_data bytea, key text)
RETURNS text AS $$
BEGIN
    RETURN pgp_sym_decrypt(encrypted_data, key);
END;
$$ LANGUAGE plpgsql;
```

### 稽核日誌
```sql
-- 建立稽核日誌表
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(255) NOT NULL,
    operation VARCHAR(10) NOT NULL,  -- INSERT, UPDATE, DELETE
    record_id INTEGER,
    old_values JSONB,
    new_values JSONB,
    user_id INTEGER REFERENCES users(id),
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 稽核觸發器函數
CREATE OR REPLACE FUNCTION audit_trigger_function()
RETURNS TRIGGER AS $$
DECLARE
    audit_record audit_logs%ROWTYPE;
BEGIN
    audit_record.table_name := TG_TABLE_NAME;
    audit_record.operation := TG_OP;
    audit_record.created_at := NOW();

    IF TG_OP = 'INSERT' THEN
        audit_record.record_id := NEW.id;
        audit_record.new_values := to_jsonb(NEW);
    ELSIF TG_OP = 'UPDATE' THEN
        audit_record.record_id := NEW.id;
        audit_record.old_values := to_jsonb(OLD);
        audit_record.new_values := to_jsonb(NEW);
    ELSIF TG_OP = 'DELETE' THEN
        audit_record.record_id := OLD.id;
        audit_record.old_values := to_jsonb(OLD);
    END IF;

    INSERT INTO audit_logs VALUES (audit_record.*);

    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    ELSE
        RETURN NEW;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- 為敏感表格建立稽核觸發器
CREATE TRIGGER users_audit_trigger
    AFTER INSERT OR UPDATE OR DELETE ON users
    FOR EACH ROW EXECUTE FUNCTION audit_trigger_function();
```

## 備份與恢復

### 備份策略
```bash
#!/bin/bash
# scripts/database_backup.sh

# 設定變數
DB_NAME="app_db"
DB_USER="postgres"
BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

# 建立備份目錄
mkdir -p "$BACKUP_DIR/daily"
mkdir -p "$BACKUP_DIR/weekly"
mkdir -p "$BACKUP_DIR/monthly"

# 每日完整備份
echo "Starting daily backup..."
pg_dump -h localhost -U $DB_USER -d $DB_NAME -Fc > "$BACKUP_DIR/daily/backup_$DATE.dump"

# 每週備份 (星期日)
if [ $(date +%u) -eq 7 ]; then
    echo "Creating weekly backup..."
    cp "$BACKUP_DIR/daily/backup_$DATE.dump" "$BACKUP_DIR/weekly/"
fi

# 每月備份 (每月1號)
if [ $(date +%d) -eq 01 ]; then
    echo "Creating monthly backup..."
    cp "$BACKUP_DIR/daily/backup_$DATE.dump" "$BACKUP_DIR/monthly/"
fi

# 清理過期備份
echo "Cleaning old backups..."
find "$BACKUP_DIR/daily" -name "backup_*.dump" -mtime +$RETENTION_DAYS -delete
find "$BACKUP_DIR/weekly" -name "backup_*.dump" -mtime +90 -delete
find "$BACKUP_DIR/monthly" -name "backup_*.dump" -mtime +365 -delete

# 驗證備份
echo "Verifying backup..."
pg_restore --list "$BACKUP_DIR/daily/backup_$DATE.dump" > /dev/null
if [ $? -eq 0 ]; then
    echo "✅ Backup verification successful"
else
    echo "❌ Backup verification failed"
    exit 1
fi

echo "Backup completed: backup_$DATE.dump"
```

### 恢復程序
```bash
#!/bin/bash
# scripts/database_restore.sh

BACKUP_FILE=$1
DB_NAME="app_db"
DB_USER="postgres"

if [ -z "$BACKUP_FILE" ]; then
    echo "Usage: $0 <backup_file>"
    exit 1
fi

if [ ! -f "$BACKUP_FILE" ]; then
    echo "Backup file not found: $BACKUP_FILE"
    exit 1
fi

echo "⚠️  WARNING: This will restore database '$DB_NAME' from backup"
echo "Backup file: $BACKUP_FILE"
read -p "Are you sure? (yes/no): " confirmation

if [ "$confirmation" != "yes" ]; then
    echo "Restore cancelled"
    exit 1
fi

# 停止應用程式服務
echo "Stopping application services..."
docker-compose stop backend

# 建立恢復前備份
echo "Creating pre-restore backup..."
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
pg_dump -h localhost -U $DB_USER -d $DB_NAME -Fc > "/backups/pre_restore_$TIMESTAMP.dump"

# 刪除現有連線
echo "Terminating existing connections..."
psql -h localhost -U $DB_USER -d postgres -c "
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE datname = '$DB_NAME' AND pid <> pg_backend_pid();"

# 恢復資料庫
echo "Restoring database..."
pg_restore -h localhost -U $DB_USER -d $DB_NAME --clean --if-exists --verbose "$BACKUP_FILE"

if [ $? -eq 0 ]; then
    echo "✅ Database restore completed successfully"

    # 重新啟動應用程式服務
    echo "Starting application services..."
    docker-compose start backend

    echo "✅ Restore process completed"
else
    echo "❌ Database restore failed"
    echo "Restoring from pre-restore backup..."
    pg_restore -h localhost -U $DB_USER -d $DB_NAME --clean --if-exists "/backups/pre_restore_$TIMESTAMP.dump"
    exit 1
fi
```

## 監控與維護

### 效能監控查詢
```sql
-- 監控長時間執行的查詢
SELECT
    pid,
    user,
    application_name,
    client_addr,
    query_start,
    state,
    query
FROM pg_stat_activity
WHERE state = 'active'
  AND query_start < NOW() - INTERVAL '5 minutes'
  AND query NOT LIKE '%pg_stat_activity%';

-- 監控表格大小
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
    pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) as table_size,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) - pg_relation_size(schemaname||'.'||tablename)) as index_size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- 監控索引使用情況
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan ASC;

-- 監控未使用的索引
SELECT
    schemaname,
    tablename,
    indexname,
    pg_size_pretty(pg_relation_size(indexrelid)) as size
FROM pg_stat_user_indexes
WHERE idx_scan = 0
  AND schemaname = 'public';
```

### 自動維護腳本
```sql
-- 自動 VACUUM 和 ANALYZE
-- 建議在 crontab 中設定定期執行
-- 0 2 * * * psql -d app_db -c "VACUUM ANALYZE;"

-- 重建統計資訊
ANALYZE;

-- 清理死元組
VACUUM;

-- 重建索引 (需要時)
REINDEX INDEX CONCURRENTLY idx_users_email;

-- 檢查資料庫健康狀態
SELECT
    datname,
    numbackends,
    xact_commit,
    xact_rollback,
    blks_read,
    blks_hit,
    tup_returned,
    tup_fetched,
    tup_inserted,
    tup_updated,
    tup_deleted
FROM pg_stat_database
WHERE datname = 'app_db';
```

## 版本控制與遷移

### Alembic 遷移 (Python)
```python
# migrations/env.py
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
from app.models import Base

config = context.config
fileConfig(config.config_file_name)
target_metadata = Base.metadata

def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

run_migrations_online()
```

```python
# migrations/versions/001_create_users_table.py
"""create users table

Revision ID: 001
Revises:
Create Date: 2025-01-XX 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('idx_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('idx_users_username'), 'users', ['username'], unique=True)

def downgrade():
    op.drop_index(op.f('idx_users_username'), table_name='users')
    op.drop_index(op.f('idx_users_email'), table_name='users')
    op.drop_table('users')
```

### 遷移最佳實踐
```bash
# 建立新遷移
alembic revision --autogenerate -m "add user profile table"

# 套用遷移
alembic upgrade head

# 回滾遷移
alembic downgrade -1

# 檢查當前版本
alembic current

# 檢查歷史記錄
alembic history --verbose
```

---

*最後更新: 2025-01-XX*
