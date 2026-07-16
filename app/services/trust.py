from app.models.user import User
from app.models.transaction import Transaction, TransactionStatus

# trust score rules: how much each outcome changes the borrower's score
TRUST_REWARD_ON_TIME = 5
TRUST_PENALTY_LATE = -10

# the score is always kept within these bounds
TRUST_MIN = 0
TRUST_MAX = 100

def update_trust_score(borrower: User, transaction: Transaction) -> None:
    """Adjust the borrower's trust score based on how a transaction ended."""
    if transaction.status == TransactionStatus.returned:
        change = TRUST_REWARD_ON_TIME
    elif transaction.status == TransactionStatus.returned_late:
        change = TRUST_PENALTY_LATE
    else:
        return  # transaction still active: no score change

    new_score = borrower.trust_score + change
    borrower.trust_score = max(TRUST_MIN, min(TRUST_MAX, new_score))