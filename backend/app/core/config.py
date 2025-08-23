"""
應用配置模組
"""

import os
from enum import Enum
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings


class Environment(str, Enum):
    """環境類型"""

    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TESTING = "testing"


class Settings(BaseSettings):
    """應用設定"""

    # 環境設定
    ENVIRONMENT: Environment = Environment.DEVELOPMENT

    # 資料庫設定
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/myapp"

    # 安全設定
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # 應用設定
    APP_NAME: str = "FastAPI Backend"
    APP_VERSION: str = "1.0.0"

    # CORS 設定
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ]

    # 資料庫連線池設定
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 30
    DB_POOL_RECYCLE: int = 3600

    # 日誌設定
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"

    # 資料庫日誌設定
    DB_ECHO: bool = False

    @property
    def is_development(self) -> bool:
        """是否為開發環境"""
        return self.ENVIRONMENT == Environment.DEVELOPMENT

    @property
    def is_production(self) -> bool:
        """是否為生產環境"""
        return self.ENVIRONMENT == Environment.PRODUCTION

    @property
    def is_testing(self) -> bool:
        """是否為測試環境"""
        return self.ENVIRONMENT == Environment.TESTING

    @property
    def debug(self) -> bool:
        """是否啟用調試模式"""
        return self.is_development

    @property
    def cors_origins(self) -> List[str]:
        """根據環境返回適當的 CORS 來源"""
        if self.is_production:
            # 生產環境：只允許特定域名
            return [
                "https://yourdomain.com",
                "https://www.yourdomain.com",
            ]
        else:
            # 開發/測試環境：允許本地開發
            return self.ALLOWED_ORIGINS

    @property
    def db_pool_settings(self) -> dict:
        """根據環境返回資料庫連線池設定"""
        if self.is_production:
            return {
                "pool_size": 50,
                "max_overflow": 100,
                "pool_recycle": 1800,
            }
        else:
            return {
                "pool_size": self.DB_POOL_SIZE,
                "max_overflow": self.DB_MAX_OVERFLOW,
                "pool_recycle": self.DB_POOL_RECYCLE,
            }

    @field_validator("DATABASE_URL", mode="before")
    def validate_database_url(cls, v: str) -> str:
        """驗證資料庫 URL"""
        if not v.startswith(("postgresql://", "postgresql+asyncpg://")):
            raise ValueError("DATABASE_URL must be a PostgreSQL URL")
        return v

    @field_validator("SECRET_KEY", mode="after")
    def validate_secret_key(cls, v: str, info) -> str:
        """驗證密鑰安全性"""
        environment = info.data.get("ENVIRONMENT", Environment.DEVELOPMENT)
        if (
            environment == Environment.PRODUCTION
            and v == "your-secret-key-change-in-production"
        ):
            raise ValueError("Must set a secure SECRET_KEY in production")
        if len(v) < 32:
            raise ValueError("SECRET_KEY must be at least 32 characters long")
        return v

    model_config = {"env_file": ".env", "case_sensitive": True}


def get_settings() -> Settings:
    """獲取設定實例"""
    return Settings()


# 全局設定實例
settings = get_settings()
