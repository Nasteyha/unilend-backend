from sqlalchemy import Column, String, Integer, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base
import uuid
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    trust_score = Column(Integer, nullable=False, default=50)
    role = Column(String, nullable=False, default="borrower")
    created_at = Column(DateTime, default=datetime.utcnow)
    items = relationship("Item", back_populates="owner")