from datetime import datetime

from pydantic import BaseModel, Field


class ExternalMarketSignalCreate(BaseModel):
    signal_key: str = Field(min_length=1, max_length=100)
    title: str = Field(min_length=1, max_length=255)
    source_name: str = Field(min_length=1, max_length=100)
    source_url: str | None = None
    summary: str = Field(min_length=1)
    relevance_weight: int = Field(default=1, ge=1, le=10)
    active: bool = True


class ExternalMarketSignalRead(BaseModel):
    id: int
    signal_key: str
    title: str
    source_name: str
    source_url: str | None
    summary: str
    relevance_weight: int
    active: bool
    created_at: datetime
