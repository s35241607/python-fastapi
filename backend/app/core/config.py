"""
應用配置模組
"""
import os
from typing import Optional
from pydantic import BaseSettings, validator


class Settings(BaseSettings):
    """應用設定"""
    
    # 資料庫設定
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/myapp"
    
    # 安全設定
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # 應用設定
    APP_NAME: str = "FastAPI Backend"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # CORS 設定
    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000"
    ]
    
    # 資料庫連線池設定
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 30
    DB_POOL_RECYCLE: int = 3600
    
    # 日誌設定
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "logs/app.log"
    
    @validator("DATABASE_URL", pre=True)
    def validate_database_url(cls, v: str) -> str:
        """驗證資料庫 URL"""
        if not v.startswith(("postgresql://", "postgresql+asyncpg://")):
            raise ValueError("DATABASE_URL must be a PostgreSQL URL")
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# 全局設定實例
settings = Settings()