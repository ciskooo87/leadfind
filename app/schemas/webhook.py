from datetime import datetime
from pydantic import BaseModel, HttpUrl


class WebhookTargetCreate(BaseModel):
    name: str
    target_url: HttpUrl
    active: bool = True
    min_score: float = 60
    lead_tiers: str = "A,B"


class WebhookTargetRead(BaseModel):
    id: int
    name: str
    target_url: str
    active: bool
    min_score: float
    lead_tiers: str
    created_at: datetime

    model_config = {"from_attributes": True}


class WebhookDeliveryRead(BaseModel):
    id: int
    webhook_target_id: int
    company_id: int
    status: str
    response_status: int | None = None
    response_body: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
