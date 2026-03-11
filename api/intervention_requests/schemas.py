from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID


class RequestStatusRef(BaseModel):
    code: str
    label: str
    color: str
    sort_order: int

    class Config:
        from_attributes = True


class InterventionRequestIn(BaseModel):
    machine_id: UUID = Field(..., description="Machine concernée")
    demandeur_nom: str = Field(..., description="Nom du demandeur")
    demandeur_service: Optional[str] = Field(default=None, description="Service du demandeur")
    description: str = Field(..., description="Description de l'intervention demandée")

    class Config:
        from_attributes = True


class StatusLogEntry(BaseModel):
    id: UUID
    status_from: Optional[str] = None
    status_to: str
    status_from_label: Optional[str] = None
    status_to_label: Optional[str] = None
    status_to_color: Optional[str] = None
    changed_by: Optional[UUID] = None
    notes: Optional[str] = None
    date: datetime

    class Config:
        from_attributes = True


class InterventionRequestListItem(BaseModel):
    id: UUID
    code: str
    machine_id: UUID
    machine_name: Optional[str] = None
    demandeur_nom: str
    demandeur_service: Optional[str] = None
    description: str
    statut: str
    statut_label: Optional[str] = None
    statut_color: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class InterventionRequestDetail(InterventionRequestListItem):
    status_log: List[StatusLogEntry] = Field(default_factory=list)


class StatusTransitionIn(BaseModel):
    status_to: str = Field(..., description="Nouveau statut cible")
    notes: Optional[str] = Field(default=None, description="Motif ou commentaire (obligatoire pour rejetee)")
    changed_by: Optional[UUID] = Field(default=None, description="UUID de l'utilisateur Directus")
