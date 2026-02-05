from datetime import date
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel
from api.intervention_actions.schemas import InterventionActionOut
from api.intervention_status_log.schemas import InterventionStatusLogOut
from api.equipements.schemas import EquipementDetail


class InterventionIn(BaseModel):
    """Schéma d'entrée pour créer/modifier une intervention"""
    title: Optional[str] = None
    machine_id: Optional[UUID] = None
    type_inter: Optional[str] = None
    priority: Optional[str] = None
    reported_by: Optional[str] = None
    tech_initials: Optional[str] = None
    status_actual: Optional[str] = None
    printed_fiche: Optional[bool] = None
    reported_date: Optional[date] = None

    class Config:
        from_attributes = True


class InterventionStats(BaseModel):
    """Stats calculées pour une intervention"""
    action_count: int = 0
    total_time: float = 0
    avg_complexity: Optional[float] = None

    class Config:
        from_attributes = True


class InterventionOut(BaseModel):
    """Schéma pour une intervention avec ses actions et équipement"""
    id: UUID
    code: Optional[str] = None
    title: Optional[str] = None
    equipements: Optional[EquipementDetail] = None
    type_inter: Optional[str] = None
    priority: Optional[str] = None
    reported_by: Optional[str] = None
    tech_initials: Optional[str] = None
    status_actual: Optional[str] = None
    updated_by: Optional[UUID] = None
    printed_fiche: Optional[bool] = None
    reported_date: Optional[date] = None

    stats: InterventionStats
    actions: List[InterventionActionOut] = []
    status_logs: List[InterventionStatusLogOut] = []

    class Config:
        from_attributes = True
