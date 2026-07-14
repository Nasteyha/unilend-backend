from pydantic import BaseModel

class DashboardStats(BaseModel):
    items_listed: int
    items_currently_borrowed: int
    requests_sent: int
    requests_received_pending: int
    requests_approved: int
    trust_score: int