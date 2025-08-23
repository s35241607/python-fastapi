"""
資料庫連接模組 - 異步版本
"""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.declarative import declarative_base

from app.core.config import settings

# 創建異步引擎
pool_settings = settings.db_pool_settings
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=pool_settings["pool_size"],
    max_overflow=pool_settings["max_overflow"],
    pool_pre_ping=True,
    pool_recycle=pool_settings["pool_recycle"],
    echo=settings.DB_ECHO,
)

# 創建異步會話工廠
AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# 資料庫模型基類
Base = declarative_base()


async def get_db():
    """
    獲取資料庫會話

    Yields:
        AsyncSession: 資料庫會話
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
