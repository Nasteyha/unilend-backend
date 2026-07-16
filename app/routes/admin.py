from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.item import Item
from app.models.borrow_request import BorrowRequest, RequestStatus
from app.models.transaction import Transaction, TransactionStatus
from app.routes.auth import get_current_user

router = APIRouter(prefix="/admin", tags=["Admin"])

def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Authorization gate: the caller must be authenticated AND an admin."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

@router.get("/stats")
def get_platform_stats(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    return {
        "total_users": db.query(User).count(),
        "total_items": db.query(Item).count(),
        "requests_pending": db.query(BorrowRequest).filter(BorrowRequest.status == RequestStatus.pending).count(),
        "requests_approved": db.query(BorrowRequest).filter(BorrowRequest.status == RequestStatus.approved).count(),
        "requests_rejected": db.query(BorrowRequest).filter(BorrowRequest.status == RequestStatus.rejected).count(),
        "requests_returned": db.query(BorrowRequest).filter(BorrowRequest.status == RequestStatus.returned).count(),
        "transactions_active": db.query(Transaction).filter(Transaction.status == TransactionStatus.active).count(),
        "returns_on_time": db.query(Transaction).filter(Transaction.status == TransactionStatus.returned).count(),
        "returns_late": db.query(Transaction).filter(Transaction.status == TransactionStatus.returned_late).count(),
    }

@router.get("/users")
def get_all_users(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    users = db.query(User).all()
    return [
        {
            "id": str(u.id),
            "full_name": u.full_name,
            "email": u.email,
            "role": u.role,
            "trust_score": u.trust_score,
            "created_at": u.created_at,
        }
        for u in users
    ]

@router.get("/transactions")
def get_all_transactions(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
):
    transactions = db.query(Transaction).order_by(Transaction.borrowed_at.desc()).all()
    return [
        {
            "id": str(t.id),
            "status": t.status.value,
            "borrowed_at": t.borrowed_at,
            "returned_at": t.returned_at,
            "item_title": t.borrow_request.item.title,
            "borrower_name": t.borrow_request.borrower.full_name,
        }
        for t in transactions
    ]