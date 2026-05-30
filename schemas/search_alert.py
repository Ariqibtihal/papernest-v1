from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SearchAlertCreate(BaseModel):
    query: str
    filters_json: str | None = None
    email: str | None = None
    frequency: str = "daily"


class SearchAlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    query: str
    filters_json: str | None
    email: str | None
    frequency: str
    is_active: bool
    created_at: datetime
    last_run_at: datetime | None


class SearchAlertList(BaseModel):
    total: int
    items: list[SearchAlertOut]
