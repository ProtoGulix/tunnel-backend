"""Schémas pour l'endpoint unifié /tasks/workspace."""
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from uuid import UUID


class UserRef(BaseModel):
    """Utilisateur léger (pour created_by, assigned_to, tech)."""
    id: UUID
    initials: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class InterventionRef(BaseModel):
    """Intervention légère pour les options de filtrage."""
    id: UUID
    code: Optional[str] = None
    title: Optional[str] = None
    status: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class EquipementRef(BaseModel):
    """Équipement léger embarqué dans une intervention."""
    id: UUID
    name: Optional[str] = None
    code: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ActionRef(BaseModel):
    """Action liée à une tâche (si include_actions=true)."""
    id: UUID
    created_at: Optional[datetime] = None
    description: Optional[str] = None
    time_spent: Optional[float] = None
    tech: Optional[UserRef] = None

    model_config = ConfigDict(from_attributes=True)


class TaskDetail(BaseModel):
    """Tâche enrichie prête UI pour la page Tasks."""
    id: UUID
    label: str
    status: str
    origin: Optional[str] = None
    optional: bool = False
    due_date: Optional[date] = None
    skip_reason: Optional[str] = None
    time_spent_total: Optional[float] = None
    created_at: Optional[datetime] = None
    created_by: Optional[UserRef] = None
    assigned_to: Optional[UserRef] = None
    actions: List[ActionRef] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class InterventionGroup(BaseModel):
    """Intervention avec ses tâches agrégées — unité de premier niveau dans la réponse."""
    id: UUID
    code: Optional[str] = None
    title: Optional[str] = None
    status: Optional[str] = None
    equipement: Optional[EquipementRef] = None
    tasks: List[TaskDetail] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class TasksCounter(BaseModel):
    """Compteurs pour la page Tasks."""
    total: int = 0
    todo: int = 0
    in_progress: int = 0
    done: int = 0
    skipped: int = 0
    backlog_unassigned_todo: int = 0


class TasksOptions(BaseModel):
    """Listes de filtres pour les dropdown UI."""
    users: List[UserRef] = Field(default_factory=list)
    interventions: List[InterventionRef] = Field(default_factory=list)


class TasksPagination(BaseModel):
    """Pagination offset standard."""
    total: int
    page: int
    page_size: int
    total_pages: int
    offset: int
    count: int


class TasksMetadata(BaseModel):
    """Métadonnées de réponse."""
    generated_at: datetime
    etag: Optional[str] = None


class TasksWorkspaceResponse(BaseModel):
    """Réponse unifiée pour /tasks/workspace."""
    items: List[InterventionGroup]
    pagination: TasksPagination
    counters: Optional[TasksCounter] = None
    options: Optional[TasksOptions] = None
    meta: TasksMetadata
    errors: Optional[List[Dict[str, Any]]] = None

    model_config = ConfigDict(from_attributes=True)
