"""Schémas Pydantic pour le domaine équipements"""
from datetime import date
from typing import Any
from uuid import UUID

from pydantic import BaseModel

from api.utils.pagination import PaginationMeta


class EquipmentClassRef(BaseModel):
    """Référence à une classe d'équipement"""
    id: UUID
    code: str
    label: str


class EquipementHealth(BaseModel):
    """Santé d'un équipement"""
    level: str
    reason: str
    open_interventions_count: int = 0
    urgent_count: int = 0
    rules_triggered: list[str] | None = None


class EquipementParent(BaseModel):
    """Équipement parent"""
    id: UUID
    code: str | None = None
    name: str


class EquipementListItem(BaseModel):
    """Équipement pour liste - vue légère avec health"""
    id: UUID
    code: str | None = None
    name: str
    health: EquipementHealth
    parent_id: UUID | None = None
    equipment_class: EquipmentClassRef | None = None

    class Config:
        from_attributes = True


class TypeInterventionRef(BaseModel):
    """Référence à un type d'intervention avec code et label"""
    code: str | None = None
    label: str | None = None


class InterventionListItem(BaseModel):
    """Intervention légère pour inclusion dans le détail équipement"""
    id: UUID
    code: str | None = None
    title: str | None = None
    type_inter: TypeInterventionRef | None = None
    status_actual: str | None = None
    priority: str | None = None
    reported_date: date | None = None

    class Config:
        from_attributes = True


class InterventionsPaginated(BaseModel):
    """Interventions paginées pour inclusion dans le détail équipement"""
    total: int
    page: int
    page_size: int
    total_pages: int
    items: list[InterventionListItem]


class EquipementChildItem(BaseModel):
    """Enfant d'un équipement - vue légère avec health"""
    id: UUID
    code: str | None = None
    name: str
    health: EquipementHealth

    class Config:
        from_attributes = True


class EquipementDetail(BaseModel):
    """Équipement détaillé avec tous les champs, children_count et interventions paginées"""
    id: UUID
    code: str | None = None
    name: str
    no_machine: str | None = None
    affectation: str | None = None
    is_mere: bool | None = None
    fabricant: str | None = None
    numero_serie: str | None = None
    date_mise_service: date | None = None
    notes: str | None = None
    health: EquipementHealth
    parent_id: UUID | None = None
    equipement_class: EquipmentClassRef | None = None
    children_count: int = 0
    interventions: InterventionsPaginated

    class Config:
        from_attributes = True


class EquipementCreate(BaseModel):
    """Schéma pour créer un équipement"""
    code: str | None = None
    name: str
    parent_id: UUID | None = None
    equipment_class_id: UUID | None = None


class EquipementUpdate(BaseModel):
    """Schéma pour mettre à jour un équipement"""
    code: str | None = None
    name: str | None = None
    parent_id: UUID | None = None
    equipment_class_id: UUID | None = None


class InterventionsStats(BaseModel):
    """Statistiques interventions pour endpoint /stats"""
    open: int
    closed: int
    by_status: dict[str, int]
    by_priority: dict[str, int]


class EquipementStatsDetailed(BaseModel):
    """Stats détaillées pour GET /equipements/{id}/stats"""
    interventions: InterventionsStats


class EquipementHealthOnly(BaseModel):
    """Health uniquement pour endpoint ultra-léger"""
    level: str
    reason: str
    open_interventions_count: int = 0
    urgent_count: int = 0


class EquipementClassFacetItem(BaseModel):
    """Facette par classe d'équipement"""
    code: str | None = None
    label: str | None = None
    count: int


class EquipementListPaginated(BaseModel):
    """Réponse paginée de la liste des équipements avec facettes"""
    items: list[EquipementListItem]
    pagination: PaginationMeta
    facets: dict[str, list[EquipementClassFacetItem]]
