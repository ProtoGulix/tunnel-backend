from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import date, datetime
from uuid import UUID


class EquipementHealth(BaseModel):
    """Santé d'un équipement"""
    level: str
    reason: str
    rules_triggered: Optional[List[str]] = None


class EquipementParent(BaseModel):
    """Équipement parent"""
    id: UUID
    code: Optional[str] = None
    name: str


class EquipementListItem(BaseModel):
    """Équipement pour liste - vue légère avec health"""
    id: UUID
    code: Optional[str] = None
    name: str
    health: EquipementHealth
    parent_id: Optional[UUID] = None

    class Config:
        from_attributes = True


class EquipementDetail(BaseModel):
    """Équipement détaillé avec health et children"""
    id: UUID
    code: Optional[str] = None
    name: str
    health: EquipementHealth
    parent_id: Optional[UUID] = None
    children_ids: List[UUID] = []

    class Config:
        from_attributes = True


class InterventionsStats(BaseModel):
    """Statistiques interventions pour endpoint /stats"""
    open: int
    closed: int
    by_status: Dict[str, int]
    by_priority: Dict[str, int]


class EquipementStatsDetailed(BaseModel):
    """Stats détaillées pour GET /equipements/{id}/stats"""
    interventions: InterventionsStats


class EquipementHealthOnly(BaseModel):
    """Health uniquement pour endpoint ultra-léger"""
    level: str
    reason: str
