"""Schémas Pydantic pour le domaine équipements"""
from uuid import UUID

from pydantic import BaseModel


class EquipmentClassRef(BaseModel):
    """Référence à une classe d'équipement"""
    id: UUID
    code: str
    label: str


class EquipementHealth(BaseModel):
    """Santé d'un équipement"""
    level: str
    reason: str
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


class EquipementDetail(BaseModel):
    """Équipement détaillé avec health et children"""
    id: UUID
    code: str | None = None
    name: str
    health: EquipementHealth
    parent_id: UUID | None = None
    equipment_class: EquipmentClassRef | None = None
    children_ids: list[UUID] = []

    class Config:
        from_attributes = True


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
