"""Schémas Pydantic pour les statuts d'équipement"""
from pydantic import BaseModel


class EquipementStatut(BaseModel):
    """Statut d'équipement (référentiel)"""
    id: int
    code: str
    label: str
    interventions: bool
    couleur: str | None = None

    class Config:
        from_attributes = True
