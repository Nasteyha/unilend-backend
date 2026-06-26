from pydantic import BaseModel
from uuid import UUID
from enum import Enum

class RiskLevel(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"

class ItemStatus(str, Enum):
    available = "available"
    borrowed = "borrowed"
    unavailable = "unavailable"

class ItemCreate(BaseModel):
    title: str
    description: str
    category: str
    risk_level: RiskLevel
    max_borrow_days: int = 14
    

class ItemResponse(BaseModel):
    id: UUID
    title: str
    description: str
    category: str
    risk_level: RiskLevel
    status: ItemStatus
    owner_id: UUID
    max_borrow_days: int

    class Config:
        from_attributes = True

class ItemUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    category: str | None = None
    risk_level: RiskLevel | None = None