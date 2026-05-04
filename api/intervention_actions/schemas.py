from pydantic import BaseModel, ConfigDict, Field, model_validator
from typing import Optional, List
from datetime import datetime, time, date
from uuid import UUID
from api.users.schemas import UserListItem
from api.purchase_requests.schemas import PurchaseRequestListItem
from api.equipements.schemas import EquipementDetail
from api.intervention_requests.schemas import InterventionRequestListItem
from api.intervention_tasks.schemas import TaskProgressOut, InterventionTaskOut
from api.intervention_status_log.schemas import InterventionStatusLogOut


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
    """Intervention légère embarquée dans une action (utilisée dans get_all)"""
    id: UUID
    code: Optional[str] = None
    title: Optional[str] = None
    status_actual: Optional[str] = None
    equipement_id: Optional[UUID] = None
    equipement_code: Optional[str] = None
    equipement_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class InterventionStats(BaseModel):
    """Stats calculées pour une intervention"""
    action_count: int = 0
    total_time: float = 0
    avg_complexity: Optional[float] = None
    purchase_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class InterventionDetail(BaseModel):
    """Détail complet d'une intervention embarqué dans une action (endpoint GET /action/{id})"""
    id: UUID
    code: Optional[str] = None
    title: Optional[str] = None
    status_actual: Optional[str] = None
    type_inter: Optional[str] = None
    priority: Optional[str] = None
    reported_by: Optional[str] = None
    tech_initials: Optional[str] = None
    tech_id: Optional[UUID] = None
    reported_date: Optional[date] = None
    equipements: Optional[EquipementDetail] = None
    request: Optional[InterventionRequestListItem] = None
    stats: Optional[InterventionStats] = None
    tasks: List[InterventionTaskOut] = Field(default_factory=list)
    task_progress: Optional[TaskProgressOut] = None
    status_logs: List[InterventionStatusLogOut] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class InterventionActionOut(BaseModel):
    """Schéma de sortie pour une action d'intervention"""
    id: UUID
    intervention_id: Optional[UUID] = Field(default=None)
    intervention: Optional[InterventionRef] = Field(
        default=None,
        description="Référence légère (liste) ou détail complet (GET /{id})",
    )
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
    tasks: List[InterventionTaskOut] = Field(
        default_factory=list,
        description="Tâches taggées par cette action",
    )
    created_at: Optional[datetime] = Field(default=None)
    updated_at: Optional[datetime] = Field(default=None)

    model_config = ConfigDict(from_attributes=True)


class InterventionActionDetail(BaseModel):
    """Schéma de sortie enrichi pour GET /intervention-actions/{id} — contexte complet pour analyse IA"""
    id: UUID
    intervention_id: Optional[UUID] = Field(default=None)
    intervention: Optional[InterventionDetail] = Field(
        default=None,
        description="Détail complet de l'intervention parente (équipement, request, stats, tâches, logs)",
    )
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
    tasks: List[InterventionTaskOut] = Field(
        default_factory=list,
        description="Tâches traitées par cette action — détail complet avec statut, assigned_to, skip_reason, temps passé",
    )
    created_at: Optional[datetime] = Field(default=None)
    updated_at: Optional[datetime] = Field(default=None)

    model_config = ConfigDict(from_attributes=True)


class InterventionActionsByDate(BaseModel):
    """Actions groupées par jour — réponse de GET /intervention-actions"""
    date: date
    actions: List[InterventionActionOut]
