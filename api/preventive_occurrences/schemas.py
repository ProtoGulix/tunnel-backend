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
    di_code: Optional[str] = None
    di_statut: Optional[str] = None
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


class RepairOccurrencesResult(BaseModel):
    """Résultat de la procédure de réparation des occurrences corrompues."""
    # Bug 1 : gamme_step_validation sans intervention_id malgré occurrence liée à une intervention
    steps_relinked: int
    # Bug 2 : occurrence encore 'generated' alors que l'intervention est fermée
    occurrences_completed: int
    # Demandes liées à une intervention fermée mais encore 'acceptee'
    requests_closed: int
    # Détail des occurrences et interventions traitées (pour audit)
    details: list[str] = []
