from datetime import datetime
from pydantic import BaseModel


class WatchlistCreate(BaseModel):
    name: str
    source_kind: str
    source_name: str
    config_json: str
    active: bool = True


class WatchlistRead(BaseModel):
    id: int
    name: str
    source_kind: str
    source_name: str
    config_json: str
    active: bool
    last_run_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class WatchlistRunResult(BaseModel):
    watchlist_id: int
    created_events: int
    generated_leads: int
    impacted_company_ids: list[int]
    detail: str
