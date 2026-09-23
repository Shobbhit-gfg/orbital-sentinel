from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field


RiskTier = Literal["LOW", "MEDIUM", "HIGH"]


class ScreenRequest(BaseModel):
    window_hours: float = Field(default=3.0, ge=0.25, le=24)
    coarse_step_seconds: int = Field(default=60, ge=10, le=300)
    refine_step_seconds: int = Field(default=1, ge=1, le=5)
    max_objects: int = Field(default=80, ge=2, le=500)
    broadphase_distance_km: float | None = Field(default=None, ge=10, le=5000)


class ExplainResponse(BaseModel):
    event_id: str
    explanation: str
    source: str


class ObjectResponse(BaseModel):
    norad_id: str
    name: str
    epoch: datetime | None
    retrieved_at: datetime
    source_url: str
    samples: list[dict]


class EventResponse(BaseModel):
    id: str
    object_a: dict
    object_b: dict
    tca: datetime
    miss_distance_m: float
    relative_speed_mps: float
    screening_risk: RiskTier
    window_start: datetime
    window_end: datetime
    data_retrieved_at: datetime
    explanation: str | None = None
