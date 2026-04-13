from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator


class PreventiveOccurrenceOut(BaseModel):
    id: UUID
    plan_id: UUID
    plan_label: str
    machine_id: UUID
    machine_code: str
    machine_name: str
    scheduled_date: Optional[date] = None
    triggered_at: Optional[datetime] = None
    hours_at_trigger: Optional[float] = None
    di_id: Optional[UUID] = None
    intervention_id: Optional[UUID] = None
    status: str
    skip_reason: Optional[str] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class OccurrenceSkipIn(BaseModel):
    skip_reason: str

    @field_validator("skip_reason")
    @classmethod
    def skip_reason_not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("skip_reason ne peut pas être vide")
        return v.strip()


class GenerateOccurrencesResult(BaseModel):
    generated: int
    skipped_conflicts: int
    errors: list[str] = []
