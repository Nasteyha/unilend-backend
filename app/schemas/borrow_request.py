from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from enum import Enum

class RequestStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"

class BorrowRequestCreate(BaseModel):
    item_id: UUID
    return_deadline: datetime

class BorrowRequestResponse(BaseModel):
    id: UUID
    item_id: UUID
    borrower_id: UUID
    status: RequestStatus
    requested_at: datetime
    return_deadline: datetime | None

    class Config:
        from_attributes = True