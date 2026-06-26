import uuid
from sqlalchemy import Column, String, Integer, ForeignKey, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base
import enum

class RiskLevel(enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"

class ItemStatus(enum.Enum):
    available = "available"
    borrowed = "borrowed"
    unavailable = "unavailable"

class Item(Base):
    __tablename__ = "items"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    category = Column(String, nullable=False)
    risk_level = Column(SAEnum(RiskLevel), nullable=False)
    status = Column(SAEnum(ItemStatus), nullable=False, default=ItemStatus.available)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    max_borrow_days = Column(Integer, nullable=False, default=14)
    
    owner = relationship("User", back_populates="items")