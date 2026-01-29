from pydantic import BaseModel
from typing import Optional, Union
from datetime import datetime
from uuid import UUID


class StatusDetail(BaseModel):
    """Détail d'un statut d'intervention"""
    id: str
    code: Optional[str] = None
    label: Optional[str] = None
    color: Optional[str] = None
    value: Optional[int] = None

    class Config:
        from_attributes = True


class InterventionStatusLogIn(BaseModel):
    """Schéma d'entrée pour créer un log de changement de statut"""
    intervention_id: UUID
    status_from: Optional[str] = None  # Peut être null pour premier changement
    status_to: str
    technician_id: UUID
    date: Union[str, datetime]  # Accepte string ou datetime, validator convertira
    notes: Optional[str] = None

    class Config:
        from_attributes = True


class InterventionStatusLogOut(BaseModel):
    """Schéma de sortie pour un log de changement de statut"""
    id: UUID
    intervention_id: UUID
    status_from: Optional[str] = None
    status_to: str
    status_from_detail: Optional[StatusDetail] = None
    status_to_detail: Optional[StatusDetail] = None
    technician_id: Optional[UUID] = None
    date: datetime
    notes: Optional[str] = None

    class Config:
        from_attributes = True
