from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator

from api.gamme_step_validations.schemas import GammeStepValidationOut


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
    di_code: Optional[str] = None
    di_statut: Optional[str] = None
    intervention_id: Optional[UUID] = None
    status: str
    skip_reason: Optional[str] = None
    created_at: Optional[datetime] = None
    gamme_steps: list[GammeStepValidationOut] = []

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


class RepairOccurrencesResult(BaseModel):
    """Résultat de la procédure de réparation des occurrences corrompues."""
    steps_relinked: int
    occurrences_relinked: int
    occurrences_set_in_progress: int
    occurrences_completed: int
    requests_closed: int
    details: list[str] = []
