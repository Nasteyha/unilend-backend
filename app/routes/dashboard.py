from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.item import Item, ItemStatus
from app.models.borrow_request import BorrowRequest, RequestStatus
from app.schemas.dashboard import DashboardStats
from app.routes.auth import get_current_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])

@router.get("/stats", response_model=DashboardStats)
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    items_listed = db.query(Item).filter(
        Item.owner_id == current_user.id
    ).count()

    items_currently_borrowed = db.query(Item).filter(
        Item.owner_id == current_user.id,
        Item.status != ItemStatus.available,
    ).count()

    requests_sent = db.query(BorrowRequest).filter(
        BorrowRequest.borrower_id == current_user.id
    ).count()

    requests_received_pending = (
        db.query(BorrowRequest)
        .join(Item, BorrowRequest.item_id == Item.id)
        .filter(
            Item.owner_id == current_user.id,
            BorrowRequest.status == RequestStatus.pending,
        )
        .count()
    )

    requests_approved = db.query(BorrowRequest).filter(
        BorrowRequest.borrower_id == current_user.id,
        BorrowRequest.status == RequestStatus.approved,
    ).count()

    return DashboardStats(
        items_listed=items_listed,
        items_currently_borrowed=items_currently_borrowed,
        requests_sent=requests_sent,
        requests_received_pending=requests_received_pending,
        requests_approved=requests_approved,
        trust_score=current_user.trust_score,
    )