from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.borrow_request import BorrowRequest, RequestStatus
from app.models.item import Item, ItemStatus, RiskLevel
from app.models.user import User
from app.schemas.borrow_request import BorrowRequestCreate, BorrowRequestResponse, ReceivedRequestResponse, MyRequestResponse
from app.routes.auth import get_current_user
from datetime import datetime, timedelta
from uuid import UUID
from typing import List
from app.models.transaction import Transaction, TransactionStatus
from app.services.trust import update_trust_score

router = APIRouter(prefix="/borrow-requests", tags=["borrow requests"])

# minimum trust score required for each risk level
RISK_THRESHOLDS = {
    RiskLevel.low: 0,
    RiskLevel.medium: 50,
    RiskLevel.high: 70,
}

@router.post("/", response_model=BorrowRequestResponse)
def create_borrow_request(
    request: BorrowRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # 1. find the item
    item = db.query(Item).filter(Item.id == request.item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    # 2. guard: can't request your own item
    if item.owner_id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot request your own item")

    # 3. item must be available
    if item.status != ItemStatus.available:
        raise HTTPException(status_code=400, detail="This item is not available for borrowing")

    # 4. eligibility check: trust score vs risk level
    required_score = RISK_THRESHOLDS[item.risk_level]
    if current_user.trust_score < required_score:
        raise HTTPException(
            status_code=403,
            detail=f"Your trust score is too low to borrow this item. A score of {required_score} is required.",
        )

    # 5. guard: no duplicate pending request for the same item
    existing = db.query(BorrowRequest).filter(
        BorrowRequest.item_id == request.item_id,
        BorrowRequest.borrower_id == current_user.id,
        BorrowRequest.status == RequestStatus.pending,
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="You already have a pending request for this item")

# 6. validate the proposed return date
    now = datetime.utcnow()
    if request.return_deadline <= now:
        raise HTTPException(status_code=400, detail="Return date must be in the future")

    latest_allowed = now + timedelta(days=item.max_borrow_days)
    if request.return_deadline > latest_allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Return date is too far out. This item can be borrowed for a maximum of {item.max_borrow_days} days.",
        )
# 7. all checks passed: create the request as pending with the proposed return date
    new_request = BorrowRequest(
        item_id=request.item_id,
        borrower_id=current_user.id,
        status=RequestStatus.pending,
        return_deadline=request.return_deadline
    )
    db.add(new_request)
    db.commit()
    db.refresh(new_request)
    return new_request

@router.get("/mine", response_model=List[MyRequestResponse])
def get_my_requests(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    requests = db.query(BorrowRequest).filter(
        BorrowRequest.borrower_id == current_user.id
    ).all()

    result = []
    for r in requests:
        result.append(MyRequestResponse(
            id=r.id,
            status=r.status,
            requested_at=r.requested_at,
            return_deadline=r.return_deadline,
            item_id=r.item_id,
            item_title=r.item.title,
            lender_name=r.item.owner.full_name,
            lender_email=r.item.owner.email,
        ))
    return result

@router.put("/{request_id}/approve", response_model=BorrowRequestResponse)
def approve_request(request_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # find the request
    borrow_request = db.query(BorrowRequest).filter(BorrowRequest.id == request_id).first()
    if not borrow_request:
        raise HTTPException(status_code=404, detail="Request not found")

    # must still be pending
    if borrow_request.status != RequestStatus.pending:
        raise HTTPException(status_code=400, detail="This request has already been decided")

    # only the item's owner can approve
    item = db.query(Item).filter(Item.id == borrow_request.item_id).first()
    if item.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only approve requests for your own items")

    # approve: update request status and flip the item to borrowed
    borrow_request.status = RequestStatus.approved
    item.status = ItemStatus.borrowed

    # the approval is the handover moment: open a transaction
    new_transaction = Transaction(
        borrow_request_id=borrow_request.id,
        status=TransactionStatus.active,
    )
    db.add(new_transaction)

    db.commit()
    db.refresh(borrow_request)
    return borrow_request


@router.put("/{request_id}/reject", response_model=BorrowRequestResponse)
def reject_request(request_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # find the request
    borrow_request = db.query(BorrowRequest).filter(BorrowRequest.id == request_id).first()
    if not borrow_request:
        raise HTTPException(status_code=404, detail="Request not found")

    # must still be pending
    if borrow_request.status != RequestStatus.pending:
        raise HTTPException(status_code=400, detail="This request has already been decided")

    # only the item's owner can reject
    item = db.query(Item).filter(Item.id == borrow_request.item_id).first()
    if item.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only reject requests for your own items")

    # reject: just update the request status, item stays available
    borrow_request.status = RequestStatus.rejected

    db.commit()
    db.refresh(borrow_request)
    return borrow_request

@router.get("/received", response_model=List[ReceivedRequestResponse])
def get_received_requests(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # find all items owned by the current user
    my_item_ids = [item.id for item in db.query(Item).filter(Item.owner_id == current_user.id).all()]

    # find all pending requests for those items
    requests = db.query(BorrowRequest).filter(
        BorrowRequest.item_id.in_(my_item_ids),
        BorrowRequest.status.in_([RequestStatus.pending, RequestStatus.approved]),
    ).all()

    # build the enriched response for each request
    result = []
    for r in requests:
        result.append(ReceivedRequestResponse(
            id=r.id,
            status=r.status,
            requested_at=r.requested_at,
            return_deadline=r.return_deadline,
            item_id=r.item_id,
            item_title=r.item.title,
            borrower_id=r.borrower_id,
            borrower_name=r.borrower.full_name,
            borrower_trust_score=r.borrower.trust_score,
            borrower_email=r.borrower.email,
        ))
    return result

@router.put("/{request_id}/return", response_model=BorrowRequestResponse)
def mark_returned(request_id: UUID, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # find the request
    borrow_request = db.query(BorrowRequest).filter(BorrowRequest.id == request_id).first()
    if not borrow_request:
        raise HTTPException(status_code=404, detail="Request not found")

    # only approved requests can be returned
    if borrow_request.status != RequestStatus.approved:
        raise HTTPException(status_code=400, detail="Only approved requests can be marked as returned")

    # only the item's owner can confirm the return
    item = db.query(Item).filter(Item.id == borrow_request.item_id).first()
    if item.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only confirm returns for your own items")

    # find the open transaction for this request
    transaction = db.query(Transaction).filter(
        Transaction.borrow_request_id == borrow_request.id,
        Transaction.status == TransactionStatus.active,
    ).first()
    if not transaction:
        raise HTTPException(status_code=404, detail="No active transaction found for this request")

    # record the return and decide: on time or late?
    now = datetime.utcnow()
    transaction.returned_at = now
    if borrow_request.return_deadline and now > borrow_request.return_deadline:
        transaction.status = TransactionStatus.returned_late
    else:
        transaction.status = TransactionStatus.returned

    # the item goes back on the shelf
    item.status = ItemStatus.available

    borrow_request.status = RequestStatus.returned
    
    # the trust engine reacts to the outcome
    borrower = db.query(User).filter(User.id == borrow_request.borrower_id).first()
    update_trust_score(borrower, transaction)

    db.commit()

    db.commit()
    db.refresh(borrow_request)
    return borrow_request