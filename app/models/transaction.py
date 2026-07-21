import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Boolean, Enum as SAEnum, String, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base
import enum

class TransactionStatus(enum.Enum):
    active = "active"
    returned = "returned"
    returned_late = "returned_late"

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    borrow_request_id = Column(UUID(as_uuid=True), ForeignKey("borrow_requests.id"), nullable=False)
    status = Column(SAEnum(TransactionStatus), nullable=False, default=TransactionStatus.active)
    borrowed_at = Column(DateTime, default=datetime.utcnow)
    returned_at = Column(DateTime, nullable=True)
    condition_verified = Column(Boolean, nullable=False, default=False)
    return_note = Column(String, nullable=True)
    lender_rating = Column(Integer, nullable=True)

    borrow_request = relationship("BorrowRequest")