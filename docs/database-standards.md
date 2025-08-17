# 資料庫設計規範

## 🏗️ 資料庫架構設計

### 命名規則

#### 表格命名

- 使用複數名詞：`users`, `orders`, `products`
- 使用 snake_case：`user_profiles`, `order_items`
- 避免縮寫：使用 `categories` 而非 `cats`

#### 欄位命名

- 使用 snake_case：`first_name`, `created_at`
- 主鍵統一使用 `id`
- 外鍵使用 `{table_name}_id`：`user_id`, `order_id`
- 布林值使用 `is_` 前綴：`is_active`, `is_deleted`
- 時間戳使用標準名稱：`created_at`, `updated_at`, `deleted_at`

#### 索引命名

```sql
-- 主鍵索引
pk_{table_name}

-- 唯一索引
uk_{table_name}_{column_name}

-- 一般索引
idx_{table_name}_{column_name}

-- 外鍵索引
fk_{table_name}_{referenced_table}
```

### 資料類型規範

#### PostgreSQL 推薦類型

```sql
-- 主鍵
id BIGSERIAL PRIMARY KEY

-- 字串
email VARCHAR(255) NOT NULL
username VARCHAR(50) NOT NULL
description TEXT

-- 數字
price DECIMAL(10,2)
quantity INTEGER
rating FLOAT

-- 時間
created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
updated_at TIMESTAMP WITH TIME ZONE
birth_date DATE

-- 布林值
is_active BOOLEAN DEFAULT TRUE

-- JSON
metadata JSONB
settings JSONB

-- UUID
uuid UUID DEFAULT gen_random_uuid()
```

## 📊 表格設計模式

### 基礎表格結構

```sql
-- 用戶表
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    uuid UUID DEFAULT gen_random_uuid() UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    last_login_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP WITH TIME ZONE
);

-- 創建索引
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_is_active ON users(is_active);
CREATE INDEX idx_users_created_at ON users(created_at);
```

### 審計欄位 (Audit Fields)

每個表格都應包含以下審計欄位：

```sql
created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
created_by BIGINT REFERENCES users(id),
updated_by BIGINT REFERENCES users(id)
```

### 軟刪除 (Soft Delete)

```sql
deleted_at TIMESTAMP WITH TIME ZONE,
deleted_by BIGINT REFERENCES users(id)

-- 創建部分索引以提升查詢性能
CREATE INDEX idx_users_active ON users(id) WHERE deleted_at IS NULL;
```

## 🔗 關聯設計

### 一對多關聯

```sql
-- 用戶和訂單 (一對多)
CREATE TABLE orders (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    order_number VARCHAR(50) UNIQUE NOT NULL,
    total_amount DECIMAL(10,2) NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_orders_user_id ON orders(user_id);
CREATE INDEX idx_orders_status ON orders(status);
```

### 多對多關聯

```sql
-- 用戶和角色 (多對多)
CREATE TABLE roles (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE user_roles (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    role_id BIGINT NOT NULL REFERENCES roles(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    assigned_by BIGINT REFERENCES users(id),

    UNIQUE(user_id, role_id)
);

CREATE INDEX idx_user_roles_user_id ON user_roles(user_id);
CREATE INDEX idx_user_roles_role_id ON user_roles(role_id);
```

## 🔒 安全性設計

### 密碼存儲

```sql
-- 永遠不要存儲明文密碼
CREATE TABLE users (
    id BIGSERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL, -- 使用 bcrypt 或 Argon2
    password_reset_token VARCHAR(255),
    password_reset_expires_at TIMESTAMP WITH TIME ZONE,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP WITH TIME ZONE
);
```

### 敏感資料加密

```sql
-- 敏感資料表
CREATE TABLE user_profiles (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id),
    phone_number_encrypted BYTEA, -- 加密存儲
    address_encrypted BYTEA,      -- 加密存儲
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### 權限控制

```sql
-- 行級安全性 (Row Level Security)
ALTER TABLE user_profiles ENABLE ROW LEVEL SECURITY;

-- 創建策略：用戶只能查看自己的資料
CREATE POLICY user_profiles_policy ON user_profiles
    FOR ALL TO authenticated_users
    USING (user_id = current_user_id());
```

## 📈 性能優化

### 索引策略

```sql
-- 複合索引 (按查詢頻率排序)
CREATE INDEX idx_orders_user_status ON orders(user_id, status);
CREATE INDEX idx_orders_created_status ON orders(created_at, status);

-- 部分索引 (只索引需要的資料)
CREATE INDEX idx_users_active_email ON users(email) WHERE is_active = TRUE;

-- 表達式索引
CREATE INDEX idx_users_lower_email ON users(LOWER(email));

-- JSONB 索引
CREATE INDEX idx_user_metadata ON users USING GIN(metadata);
```

### 分區表 (Partitioning)

```sql
-- 按時間分區的日誌表
CREATE TABLE logs (
    id BIGSERIAL,
    user_id BIGINT,
    action VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
) PARTITION BY RANGE (created_at);

-- 創建分區
CREATE TABLE logs_2024_01 PARTITION OF logs
    FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

CREATE TABLE logs_2024_02 PARTITION OF logs
    FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');
```

## 🔄 資料遷移

### Alembic 遷移腳本範例

```python
# migrations/versions/001_create_users_table.py
"""Create users table

Revision ID: 001
Revises:
Create Date: 2024-01-01 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # 創建用戶表
    op.create_table(
        'users',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('uuid', postgresql.UUID(), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('username', sa.String(50), nullable=False),
        sa.Column('first_name', sa.String(100), nullable=True),
        sa.Column('last_name', sa.String(100), nullable=True),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('is_verified', sa.Boolean(), nullable=False, default=False),
        sa.Column('last_login_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(timezone=True), nullable=False),
        sa.Column('updated_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column('deleted_at', sa.TIMESTAMP(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('username'),
        sa.UniqueConstraint('uuid')
    )

    # 創建索引
    op.create_index('idx_users_email', 'users', ['email'])
    op.create_index('idx_users_username', 'users', ['username'])
    op.create_index('idx_users_is_active', 'users', ['is_active'])
    op.create_index('idx_users_created_at', 'users', ['created_at'])

    # 創建部分索引
    op.execute(
        "CREATE INDEX idx_users_active ON users(id) WHERE deleted_at IS NULL"
    )

def downgrade():
    op.drop_table('users')
```

## 📊 資料完整性

### 約束條件

```sql
-- 檢查約束
ALTER TABLE users ADD CONSTRAINT chk_users_email_format
    CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$');

ALTER TABLE orders ADD CONSTRAINT chk_orders_total_positive
    CHECK (total_amount > 0);

ALTER TABLE users ADD CONSTRAINT chk_users_created_before_updated
    CHECK (created_at <= updated_at OR updated_at IS NULL);

-- 外鍵約束
ALTER TABLE orders ADD CONSTRAINT fk_orders_user_id
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE;
```

### 觸發器 (Triggers)

```sql
-- 自動更新 updated_at 欄位
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

## 🔍 查詢優化

### 查詢最佳實踐

```sql
-- ✅ 使用索引的查詢
SELECT * FROM users WHERE email = 'user@example.com';

-- ✅ 使用 LIMIT 限制結果
SELECT * FROM users ORDER BY created_at DESC LIMIT 10;

-- ✅ 使用 EXISTS 而非 IN (對於大資料集)
SELECT * FROM users u
WHERE EXISTS (
    SELECT 1 FROM orders o WHERE o.user_id = u.id
);

-- ❌ 避免在 WHERE 子句中使用函數
-- 錯誤
SELECT * FROM users WHERE UPPER(email) = 'USER@EXAMPLE.COM';
-- 正確
SELECT * FROM users WHERE email = LOWER('USER@EXAMPLE.COM');
```

### 查詢計劃分析

```sql
-- 分析查詢計劃
EXPLAIN ANALYZE SELECT * FROM users WHERE email = 'user@example.com';

-- 查看索引使用情況
SELECT
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;
```

## 🔄 備份與恢復

### 備份策略

```bash
# 完整備份
pg_dump -h localhost -U postgres -d myapp > backup_$(date +%Y%m%d_%H%M%S).sql

# 僅結構備份
pg_dump -h localhost -U postgres -d myapp --schema-only > schema_backup.sql

# 僅資料備份
pg_dump -h localhost -U postgres -d myapp --data-only > data_backup.sql

# 壓縮備份
pg_dump -h localhost -U postgres -d myapp | gzip > backup.sql.gz
```

### 恢復策略

```bash
# 從備份恢復
psql -h localhost -U postgres -d myapp < backup.sql

# 從壓縮備份恢復
gunzip -c backup.sql.gz | psql -h localhost -U postgres -d myapp
```

## 📊 監控與維護

### 資料庫監控

```sql
-- 查看資料庫大小
SELECT
    pg_database.datname,
    pg_size_pretty(pg_database_size(pg_database.datname)) AS size
FROM pg_database;

-- 查看表格大小
SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- 查看慢查詢
SELECT
    query,
    calls,
    total_time,
    mean_time,
    rows
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;
```

### 定期維護

```sql
-- 更新統計資訊
ANALYZE;

-- 清理死元組
VACUUM;

-- 重建索引
REINDEX INDEX idx_users_email;

-- 檢查資料庫完整性
SELECT * FROM pg_stat_database WHERE datname = 'myapp';
```
