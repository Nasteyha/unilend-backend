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
    result = []
    for u in users:
        # every transaction where this user was the borrower, regardless of rating
        borrower_transactions = (
            db.query(Transaction)
            .join(BorrowRequest, Transaction.borrow_request_id == BorrowRequest.id)
            .filter(BorrowRequest.borrower_id == u.id)
            .all()
        )
        completed_loans = sum(
            1 for t in borrower_transactions
            if t.status in (TransactionStatus.returned, TransactionStatus.returned_late)
        )

        rated_transactions = [t for t in borrower_transactions if t.lender_rating is not None]
        if rated_transactions:
            average_rating = sum(t.lender_rating for t in rated_transactions) / len(rated_transactions)
        else:
            average_rating = None

        result.append({
            "id": str(u.id),
            "full_name": u.full_name,
            "email": u.email,
            "role": u.role,
            "trust_score": u.trust_score,
            "average_rating": average_rating,
            "completed_loans": completed_loans,
            "created_at": u.created_at,
        })
    return result

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
            "return_note": t.return_note,
        }
        for t in transactions
    ]