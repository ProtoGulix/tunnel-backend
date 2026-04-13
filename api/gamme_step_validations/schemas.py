from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, model_validator


class GammeStepValidationOut(BaseModel):
    id: UUID
    step_id: UUID
    step_label: str
    step_sort_order: int
    step_optional: bool
    occurrence_id: Optional[UUID] = None
    intervention_id: Optional[UUID] = None
    action_id: Optional[UUID] = None
    status: str
    skip_reason: Optional[str] = None
    validated_at: Optional[datetime] = None
    validated_by: Optional[UUID] = None

    model_config = ConfigDict(from_attributes=True)


class GammeStepValidationPatch(BaseModel):
    status: str
    action_id: Optional[UUID] = None
    skip_reason: Optional[str] = None
    validated_by: UUID

    @model_validator(mode="after")
    def validate_status_rules(self) -> "GammeStepValidationPatch":
        if self.status not in ("validated", "skipped"):
            raise ValueError("status doit être 'validated' ou 'skipped'")

        # Si validé, action_id est OBLIGATOIRE
        if self.status == "validated" and self.action_id is None:
            raise ValueError("action_id est obligatoire quand status = 'validated'")

        # Si skippé, skip_reason est OBLIGATOIRE (pas d'action)
        if self.status == "skipped" and not (self.skip_reason or "").strip():
            raise ValueError("skip_reason est obligatoire quand status = 'skipped'")

        # Si skippé, action_id doit être NULL
        if self.status == "skipped" and self.action_id is not None:
            raise ValueError("action_id doit être null quand status = 'skipped'")

        return self


class GammeProgressOut(BaseModel):
    total: int
    validated: int
    skipped: int
    pending: int
    blocking_pending: int = 0
    is_complete: bool = False

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="after")
    def compute_is_complete(self) -> "GammeProgressOut":
        self.is_complete = self.blocking_pending == 0 and self.total > 0
        return self
