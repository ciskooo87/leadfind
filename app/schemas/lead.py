from datetime import datetime
from pydantic import BaseModel


class LeadRead(BaseModel):
    company_id: int
    score: float
    conversion_probability: str
    lead_tier: str
    summary: str
    hypothesis_of_pain: str
    best_approach: str
    recommended_product: str
    timing: str
    risk: str
    score_explanation: str
    created_at: datetime

    model_config = {"from_attributes": True}
