from datetime import datetime
from typing import List, Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, model_validator


class GammeStepIn(BaseModel):
    label: str
    sort_order: int
    optional: bool = False


class GammeStepOut(BaseModel):
    id: UUID
    plan_id: UUID
    label: str
    sort_order: int
    optional: bool

    model_config = ConfigDict(from_attributes=True)


class PreventivePlanIn(BaseModel):
    code: str
    label: str
    equipement_class_id: UUID
    trigger_type: Literal["periodicity", "hours"]
    periodicity_days: Optional[int] = None
    hours_threshold: Optional[int] = None
    auto_accept: bool = False
    steps: List[GammeStepIn] = []

    @model_validator(mode="after")
    def validate_trigger_fields(self) -> "PreventivePlanIn":
        if self.trigger_type == "periodicity" and self.periodicity_days is None:
            raise ValueError("periodicity_days est requis quand trigger_type = 'periodicity'")
        if self.trigger_type == "hours" and self.hours_threshold is None:
            raise ValueError("hours_threshold est requis quand trigger_type = 'hours'")
        return self


class PreventivePlanOut(BaseModel):
    id: UUID
    code: str
    label: str
    equipement_class_id: UUID
    equipement_class_label: Optional[str] = None
    trigger_type: str
    periodicity_days: Optional[int] = None
    hours_threshold: Optional[int] = None
    auto_accept: bool
    active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    steps: List[GammeStepOut] = []

    model_config = ConfigDict(from_attributes=True)


class PreventivePlanUpdate(BaseModel):
    label: Optional[str] = None
    equipement_class_id: Optional[UUID] = None
    trigger_type: Optional[Literal["periodicity", "hours"]] = None
    periodicity_days: Optional[int] = None
    hours_threshold: Optional[int] = None
    auto_accept: Optional[bool] = None
    steps: Optional[List[GammeStepIn]] = None

    @model_validator(mode="after")
    def validate_trigger_fields(self) -> "PreventivePlanUpdate":
        if self.trigger_type == "periodicity" and self.periodicity_days is None:
            raise ValueError("periodicity_days est requis quand trigger_type = 'periodicity'")
        if self.trigger_type == "hours" and self.hours_threshold is None:
            raise ValueError("hours_threshold est requis quand trigger_type = 'hours'")
        return self
