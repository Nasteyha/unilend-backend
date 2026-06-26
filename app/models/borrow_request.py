import uuid
from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.database import Base
import enum

class RequestStatus(enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"

class BorrowRequest(Base):
    __tablename__ = "borrow_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    item_id = Column(UUID(as_uuid=True), ForeignKey("items.id"), nullable=False)
    borrower_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    status = Column(SAEnum(RequestStatus), nullable=False, default=RequestStatus.pending)
    requested_at = Column(DateTime, default=datetime.utcnow)
    return_deadline = Column(DateTime, nullable=True)

    item = relationship("Item")
    borrower = relationship("User")