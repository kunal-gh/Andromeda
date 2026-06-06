"""Human-in-the-loop review system for escalated decisions."""
from datetime import datetime
from enum import Enum
from pydantic import BaseModel
from typing import Literal

class ReviewStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    NEEDS_INFO = "needs_info"

class HumanReviewRequest(BaseModel):
    conversation_id: str
    order_id: str | None
    original_decision: Literal["APPROVED", "DENIED", "ESCALATED"]
    reason: str
    customer_email: str
    risk_flags: list[str]
    created_at: datetime = datetime.utcnow()
    status: ReviewStatus = ReviewStatus.PENDING
    reviewer_notes: str | None = None
    reviewed_by: str | None = None
    reviewed_at: datetime | None = None

class HumanReviewService:
    def __init__(self, db_session):
        self.db = db_session
    
    async def create_review_request(self, request: HumanReviewRequest) -> str:
        try:
            from app.db.models import Escalation
            escalation = Escalation(
                conversation_id=request.conversation_id,
                order_id=request.order_id,
                reason=request.reason,
                status="pending",
            )
            self.db.add(escalation)
            self.db.commit()
            return str(escalation.id)
        except ImportError:
            return "mock-escalation-id"
    
    async def get_pending_reviews(self, limit: int = 50) -> list[dict]:
        try:
            from app.db.models import Escalation
            return self.db.query(Escalation).filter(Escalation.status == "pending").order_by(Escalation.created_at.desc()).limit(limit).all()
        except ImportError:
            return []
    
    async def resolve_review(self, review_id: str, reviewer: str, decision: ReviewStatus, notes: str | None = None) -> dict:
        try:
            from app.db.models import Escalation
            escalation = self.db.get(Escalation, review_id)
            if not escalation:
                raise ValueError(f"Review {review_id} not found")
            escalation.status = decision.value
            escalation.reviewer = reviewer
            escalation.reviewed_at = datetime.utcnow()
            escalation.notes = notes
            self.db.commit()
            return {"id": review_id, "status": decision.value, "reviewer": reviewer}
        except ImportError:
            return {"id": review_id, "status": decision.value, "reviewer": reviewer}
