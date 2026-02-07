"""Schémas Pydantic pour les classes d'équipement"""
from pydantic import BaseModel
from uuid import UUID


class EquipementClassBase(BaseModel):
    """Schéma de base pour classe d'équipement"""
    code: str
    label: str
    description: str | None = None


class EquipementClassCreate(EquipementClassBase):
    """Schéma pour créer une classe d'équipement"""
    pass


class EquipementClassUpdate(BaseModel):
    """Schéma pour mettre à jour une classe d'équipement"""
    code: str | None = None
    label: str | None = None
    description: str | None = None


class EquipementClass(EquipementClassBase):
    """Schéma complet d'une classe d'équipement"""
    id: UUID

    class Config:
        from_attributes = True


class EquipementClassRef(BaseModel):
    """Référence légère à une classe d'équipement"""
    id: UUID
    code: str
    label: str

    class Config:
        from_attributes = True
