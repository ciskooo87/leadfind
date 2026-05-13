from datetime import datetime
from pydantic import BaseModel


class WatchlistCreate(BaseModel):
    name: str
    source_kind: str
    source_name: str
    config_json: str
    active: bool = True
    schedule_minutes: int | None = None


class WatchlistRead(BaseModel):
    id: int
    name: str
    source_kind: str
    source_name: str
    config_json: str
    active: bool
    schedule_minutes: int | None = None
    last_run_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class WatchlistRunResult(BaseModel):
    watchlist_id: int
    created_events: int
    generated_leads: int
    impacted_company_ids: list[int]
    detail: str


class WatchlistRunLogRead(BaseModel):
    id: int
    watchlist_id: int
    status: str
    created_events: int
    generated_leads: int
    impacted_company_ids_json: str
    detail: str
    started_at: datetime
    finished_at: datetime | None = None

    model_config = {"from_attributes": True}


class WatchlistSchedulerRunResponse(BaseModel):
    executed_watchlists: int
    skipped_watchlists: int
    results: list[WatchlistRunResult]
