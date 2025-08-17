"""
基礎 Repository 模組
"""
from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.orm import DeclarativeBase

T = TypeVar('T', bound=DeclarativeBase)


class BaseRepository(Generic[T], ABC):
    """基礎 Repository 類別"""
    
    def __init__(self, session: AsyncSession, model_class: type[T]):
        self.session = session
        self.model_class = model_class
    
    async def get_by_id(self, id: int) -> Optional[T]:
        """根據 ID 獲取實體"""
        result = await self.session.execute(
            select(self.model_class).where(self.model_class.id == id)
        )
        return result.scalar_one_or_none()
    
    async def get_all(
        self, 
        skip: int = 0, 
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[T]:
        """獲取所有實體"""
        query = select(self.model_class)
        
        # 應用篩選條件
        if filters:
            for key, value in filters.items():
                if hasattr(self.model_class, key):
                    query = query.where(getattr(self.model_class, key) == value)
        
        query = query.offset(skip).limit(limit)
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """計算實體數量"""
        query = select(func.count(self.model_class.id))
        
        # 應用篩選條件
        if filters:
            for key, value in filters.items():
                if hasattr(self.model_class, key):
                    query = query.where(getattr(self.model_class, key) == value)
        
        result = await self.session.execute(query)
        return result.scalar()
    
    async def create(self, obj: T) -> T:
        """創建實體"""
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj
    
    async def update(self, id: int, **kwargs) -> Optional[T]:
        """更新實體"""
        await self.session.execute(
            update(self.model_class)
            .where(self.model_class.id == id)
            .values(**kwargs)
        )
        return await self.get_by_id(id)
    
    async def delete(self, id: int) -> bool:
        """刪除實體"""
        result = await self.session.execute(
            delete(self.model_class).where(self.model_class.id == id)
        )
        return result.rowcount > 0