"""Schémas Pydantic pour les services"""
from pydantic import BaseModel
from uuid import UUID


class ServiceBase(BaseModel):
    """Schéma de base pour un service"""
    code: str
    label: str


class ServiceCreate(ServiceBase):
    """Schéma pour créer un service"""
    is_active: bool = True


class ServiceUpdate(BaseModel):
    """Schéma pour mettre à jour un service"""
    label: str | None = None
    is_active: bool | None = None


class ServiceOut(ServiceBase):
    """Schéma complet d'un service"""
    id: UUID
    is_active: bool

    class Config:
        from_attributes = True
