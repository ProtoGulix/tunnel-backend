from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import date, datetime
from uuid import UUID


class EquipementParent(BaseModel):
    """Équipement parent"""
    id: UUID
    code: Optional[str] = None
    name: str


class EquipementOut(BaseModel):
    """Schéma de sortie pour un équipement (simple)"""
    id: UUID
    code: Optional[str] = None
    name: str
    no_machine: Optional[int] = None
    affectation: Optional[str] = None
    marque: Optional[str] = None
    model: Optional[str] = None
    no_serie: Optional[str] = None
    equipement_mere: Optional[UUID] = None
    is_mere: bool = False
    type_equipement: Optional[str] = None
    fabricant: Optional[str] = None
    numero_serie: Optional[str] = None
    date_mise_service: Optional[date] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class InterventionTypeStats(BaseModel):
    """Stats d'interventions pour un type (CUR/PRE)"""
    total: int
    open: int
    in_progress: int
class EquipementStats(BaseModel):
    """Stats des équipements"""
    interventions: Dict[str, InterventionTypeStats]




class EquipementListItem(BaseModel):
    """Équipement avec statistiques pour liste"""
    id: UUID
    code: Optional[str] = None
    name: str
    status: str
    status_color: str
    open_interventions_count: int
    stats: EquipementStats
    parent: Optional[EquipementParent] = None
    equipement_mere: Optional[UUID] = None
    is_mere: bool

    class Config:
        from_attributes = True


class InterventionSummary(BaseModel):
    """Intervention simplifiée pour détail équipement"""
    id: UUID
    code: str
    title: str
    status: str
    priority: str
    reported_date: date
    type_inter: str
    closed_date: Optional[datetime] = None


class ActionSummary(BaseModel):
    """Action simplifiée pour calcul temps"""
    id: UUID
    intervention_id: UUID
    time_spent: Optional[float] = None
    created_at: Optional[datetime] = None


class EquipementDetail(BaseModel):
    """Équipement avec détails complets et interventions décisionnelles"""
    id: UUID
    code: Optional[str] = None
    name: str
    status: str
    status_color: str
    equipement_mere: Optional[UUID] = None
    is_mere: bool
    parent: Optional[EquipementParent] = None
    interventions: List[InterventionSummary]
    actions: List[ActionSummary]
    time_spent_period_hours: float
    period_days: int
    # Champs optionnels équipement
    no_machine: Optional[int] = None
    affectation: Optional[str] = None
    marque: Optional[str] = None
    model: Optional[str] = None
    no_serie: Optional[str] = None
    type_equipement: Optional[str] = None
    fabricant: Optional[str] = None
    numero_serie: Optional[str] = None
    date_mise_service: Optional[date] = None
    notes: Optional[str] = None

    class Config:
        from_attributes = True
