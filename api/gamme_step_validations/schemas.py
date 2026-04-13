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
    intervention_id: UUID
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
        if self.status == "skipped" and not (self.skip_reason or "").strip():
            raise ValueError("skip_reason est obligatoire quand status = 'skipped'")
        return self


class GammeProgressOut(BaseModel):
    total: int
    validated: int
    skipped: int
    pending: int
    is_complete: bool = False

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="after")
    def compute_is_complete(self) -> "GammeProgressOut":
        self.is_complete = self.pending == 0 and self.total > 0
        return self
