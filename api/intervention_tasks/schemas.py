from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from api.users.schemas import UserListItem


class InterventionTaskOut(BaseModel):
    id: UUID
    intervention_id: Optional[UUID] = None
    label: str
    origin: str = "plan"
    status: str
    optional: bool
    assigned_to: Optional[UserListItem] = None
    due_date: Optional[date] = None
    sort_order: int
    skip_reason: Optional[str] = None
    gamme_step_id: Optional[UUID] = None
    occurrence_id: Optional[UUID] = None
    closed_by: Optional[UUID] = None
    created_by: Optional[UUID] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    action_count: int = 0
    time_spent: float = 0.0

    model_config = ConfigDict(from_attributes=True)


class InterventionTaskIn(BaseModel):
    intervention_id: UUID
    label: str
    origin: str = Field(default="tech", pattern="^(plan|resp|tech)$")
    optional: bool = False
    assigned_to: Optional[UUID] = None
    due_date: Optional[date] = None
    sort_order: int = 0

    model_config = ConfigDict(from_attributes=True)


class InterventionTaskPatch(BaseModel):
    label: Optional[str] = None
    status: Optional[str] = Field(
        default=None,
        pattern="^skipped$",
        description="Seule la transition vers 'skipped' est autorisée via PATCH direct",
    )
    skip_reason: Optional[str] = None
    assigned_to: Optional[UUID] = None
    due_date: Optional[date] = None
    sort_order: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="after")
    def validate_status_rules(self) -> "InterventionTaskPatch":
        if self.status == "skipped" and not (self.skip_reason or "").strip():
            raise ValueError("skip_reason obligatoire si status=skipped")
        return self


class TaskProgressOut(BaseModel):
    total: int
    todo: int
    in_progress: int
    done: int
    skipped: int
    blocking_pending: int = 0
    is_complete: bool = False

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="after")
    def compute_is_complete(self) -> "TaskProgressOut":
        self.is_complete = self.blocking_pending == 0 and self.total > 0
        return self
