from pydantic import BaseModel, ConfigDict, Field, model_validator
from typing import Optional, List
from datetime import datetime, time, date
from uuid import UUID
from api.users.schemas import UserListItem
from api.purchase_requests.schemas import PurchaseRequestListItem


class InterventionTaskRef(BaseModel):
    """Référence légère de tâche embarquée dans une action"""
    id: UUID
    label: str
    status: str
    origin: str
    optional: bool = False

    model_config = ConfigDict(from_attributes=True)


class InterventionTaskValidationRequest(BaseModel):
    """Tâche à tagger/valider/skipper lors de la création d'une action"""
    task_id: UUID
    close_task: bool = Field(
        default=False,
        description="Si true, passe la tâche à 'done' après liaison",
    )
    skip: bool = Field(
        default=False,
        description="Si true, passe la tâche à 'skipped' (close_task ignoré)",
    )
    skip_reason: Optional[str] = Field(
        default=None,
        description="Obligatoire si skip=true",
    )

    @model_validator(mode="after")
    def validate_logic(self) -> "InterventionTaskValidationRequest":
        if self.skip and not (self.skip_reason or "").strip():
            raise ValueError("skip_reason obligatoire si skip=true")
        if self.skip and self.close_task:
            raise ValueError("skip et close_task sont mutuellement exclusifs")
        return self


class InterventionActionIn(BaseModel):
    """Schéma d'entrée pour créer une action d'intervention"""
    intervention_id: UUID
    description: Optional[str] = Field(
        default=None, description="Note optionnelle sur l'action")
    time_spent: Optional[float] = Field(default=None)
    action_subcategory: int
    tech: UUID
    complexity_score: int
    complexity_factor: Optional[str] = Field(default=None)
    created_at: Optional[str] = Field(default=None)
    action_start: Optional[time] = Field(default=None)
    action_end: Optional[time] = Field(default=None)
    tasks: Optional[List[InterventionTaskValidationRequest]] = Field(
        default=None,
        description="Tâches à tagger/valider en même temps que cette action",
    )

    @model_validator(mode="after")
    def validate_tasks(self) -> "InterventionActionIn":
        if self.tasks is not None and len(self.tasks) == 0:
            raise ValueError("tasks ne peut pas être une liste vide")
        if self.tasks:
            ids = [str(t.task_id) for t in self.tasks]
            if len(ids) != len(set(ids)):
                raise ValueError("task_id en double dans le lot tasks")
        return self

    model_config = ConfigDict(from_attributes=True)


class ActionCategoryDetail(BaseModel):
    """Détail de catégorie d'action"""
    id: int
    name: str
    code: Optional[str] = Field(default=None)
    color: Optional[str] = Field(default=None)

    model_config = ConfigDict(from_attributes=True)


class ActionSubcategoryDetail(BaseModel):
    """Sous-catégorie avec catégorie parent imbriquée"""
    id: int
    name: str
    code: Optional[str] = Field(default=None)
    category: Optional[ActionCategoryDetail] = Field(default=None)

    model_config = ConfigDict(from_attributes=True)


class InterventionActionPatch(BaseModel):
    """Schéma de mise à jour partielle d'une action d'intervention"""
    description: Optional[str] = Field(default=None)
    time_spent: Optional[float] = Field(default=None)
    action_subcategory: Optional[int] = Field(default=None)
    tech: Optional[UUID] = Field(default=None)
    complexity_score: Optional[int] = Field(default=None)
    complexity_factor: Optional[str] = Field(default=None)
    action_start: Optional[time] = Field(default=None)
    action_end: Optional[time] = Field(default=None)
    created_at: Optional[str] = Field(default=None)
    tasks: Optional[List[InterventionTaskValidationRequest]] = Field(
        default=None,
        description="Tâches à tagger/valider/skipper sur cette action",
    )

    @model_validator(mode="after")
    def validate_tasks(self) -> "InterventionActionPatch":
        if self.tasks is not None and len(self.tasks) == 0:
            raise ValueError("tasks ne peut pas être une liste vide")
        if self.tasks:
            ids = [str(t.task_id) for t in self.tasks]
            if len(ids) != len(set(ids)):
                raise ValueError("task_id en double dans le lot tasks")
        return self

    model_config = ConfigDict(from_attributes=True)


class InterventionRef(BaseModel):
    """Intervention légère embarquée dans une action"""
    id: UUID
    code: Optional[str] = None
    title: Optional[str] = None
    status_actual: Optional[str] = None
    equipement_id: Optional[UUID] = None
    equipement_code: Optional[str] = None
    equipement_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class InterventionActionOut(BaseModel):
    """Schéma de sortie pour une action d'intervention"""
    id: UUID
    intervention_id: Optional[UUID] = Field(default=None)
    intervention: Optional[InterventionRef] = Field(default=None)
    description: Optional[str] = Field(default=None)
    time_spent: Optional[float] = Field(default=None)
    subcategory: Optional[ActionSubcategoryDetail] = Field(default=None)
    tech: Optional[UserListItem] = Field(default=None)
    complexity_score: Optional[int] = Field(default=None)
    complexity_factor: Optional[str] = Field(default=None)
    action_start: Optional[time] = None
    action_end: Optional[time] = None
    purchase_requests: List[PurchaseRequestListItem] = Field(
        default_factory=list)
    tasks: List[InterventionTaskRef] = Field(
        default_factory=list,
        description="Tâches taggées par cette action",
    )
    created_at: Optional[datetime] = Field(default=None)
    updated_at: Optional[datetime] = Field(default=None)

    model_config = ConfigDict(from_attributes=True)


class InterventionActionsByDate(BaseModel):
    """Actions groupées par jour — réponse de GET /intervention-actions"""
    date: date
    actions: List[InterventionActionOut]
