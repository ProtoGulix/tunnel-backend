from typing import List, Optional
from pydantic import BaseModel


class StatusLabel(BaseModel):
    color: str
    text: str


class Breakdown(BaseModel):
    prod_hours: float
    dep_hours: float
    pilot_hours: float
    frag_hours: float
    total_hours: float


class Capacity(BaseModel):
    total_hours: float
    capacity_hours: float
    charge_percent: float
    status: StatusLabel


class TopCause(BaseModel):
    name: str
    total_hours: float
    action_count: int
    percent: float


class Fragmentation(BaseModel):
    action_count: int
    short_action_count: int
    short_action_percent: float
    frag_percent: float
    status: StatusLabel
    top_causes: List[TopCause]


class Pilotage(BaseModel):
    pilot_hours: float
    pilot_percent: float
    status: StatusLabel


class SiteConsumption(BaseModel):
    site_name: str
    total_hours: float
    frag_hours: float
    percent_total: float
    percent_frag: float


class Period(BaseModel):
    start_date: str
    end_date: str
    days: int


class ServiceStatusResponse(BaseModel):
    period: Period
    capacity: Capacity
    breakdown: Breakdown
    fragmentation: Fragmentation
    pilotage: Pilotage
    site_consumption: List[SiteConsumption]

    class Config:
        from_attributes = True
