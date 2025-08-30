"""
Legacy Item schemas for backward compatibility.
"""
from .base import BaseModel, datetime, Optional


# ============================================================================
# ITEM SCHEMAS (LEGACY)
# ============================================================================

class ItemBase(BaseModel):
    title: str
    description: Optional[str] = None


class ItemCreate(ItemBase):
    pass


class Item(ItemBase):
    id: int
    owner_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
