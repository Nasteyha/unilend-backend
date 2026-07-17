from pydantic import BaseModel
from uuid import UUID
from datetime import datetime
from enum import Enum

class RequestStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    returned = "returned"

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

class ReceivedRequestResponse(BaseModel):
    id: UUID
    status: RequestStatus
    requested_at: datetime
    return_deadline: datetime | None
    item_id: UUID
    item_title: str
    borrower_id: UUID
    borrower_name: str
    borrower_trust_score: int
    borrower_email: str

class MyRequestResponse(BaseModel):
    id: UUID
    status: RequestStatus
    requested_at: datetime
    return_deadline: datetime | None
    item_id: UUID
    item_title: str
    lender_name: str
    lender_email: str

    class Config:
        from_attributes = True
