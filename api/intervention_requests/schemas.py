from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID

from api.equipements.schemas import EquipementListItem
from api.services.schemas import ServiceOut
from api.constants import INTERVENTION_TYPE_IDS


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
    service_id: Optional[UUID] = Field(
        default=None, description="UUID du service (optionnel)")
    description: str = Field(...,
                             description="Description de l'intervention demandée")
    is_system: bool = Field(default=False, description="DI créée par le système (ex: maintenance préventive)")
    suggested_type_inter: Optional[str] = Field(
        default=None, description="Type d'intervention suggéré (pré-remplit l'acceptation)")

    @field_validator("suggested_type_inter")
    @classmethod
    def validate_suggested_type_inter(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in INTERVENTION_TYPE_IDS:
            raise ValueError(f"Type d'intervention suggéré invalide : {v}")
        return v

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
    equipement: Optional[EquipementListItem] = None
    demandeur_nom: str
    service: Optional[ServiceOut] = None
    demandeur_service: Optional[str] = Field(
        None, alias="demandeur_service_legacy")
    description: str
    statut: str
    statut_label: Optional[str] = None
    statut_color: Optional[str] = None
    intervention_id: Optional[UUID] = None
    is_system: bool = False
    suggested_type_inter: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        populate_by_name = True


class InterventionRequestDetail(InterventionRequestListItem):
    status_log: List[StatusLogEntry] = Field(default_factory=list)


class StatusTransitionIn(BaseModel):
    status_to: str = Field(..., description="Nouveau statut cible")
    notes: Optional[str] = Field(
        default=None, description="Motif ou commentaire (obligatoire pour rejetee)")
    changed_by: Optional[UUID] = Field(
        default=None, description="UUID de l'utilisateur Directus")
    # Champs pour la création d'intervention lors de l'acceptation (status_to = acceptee)
    type_inter: Optional[str] = Field(
        default=None, description="Type d'intervention (obligatoire pour acceptee)")
    tech_id: Optional[UUID] = Field(
        default=None, description="UUID du technicien pilote (prioritaire sur tech_initials)")
    tech_initials: Optional[str] = Field(
        default=None, description="Initiales du technicien (legacy — utiliser tech_id de préférence)")
    priority: Optional[str] = Field(
        default=None, description="Priorité de l'intervention")
    reported_date: Optional[str] = Field(
        default=None, description="Date de signalement (YYYY-MM-DD)")

    @model_validator(mode="after")
    def validate_tech(self):
        if self.status_to == "acceptee":
            if not self.tech_id and not self.tech_initials:
                raise ValueError("tech_id ou tech_initials requis pour acceptee")
        return self


class RepairResult(BaseModel):
    """Résultat de la réparation des DIs orphelines liées à des interventions fermées"""
    repaired_count: int = Field(..., description="Nombre de DIs passées à 'cloturee'")
    details: List[dict] = Field(
        default_factory=list,
        description="Détail par DI réparée (id, code, machine_code)"
    )

    class Config:
        from_attributes = True
