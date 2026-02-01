from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


class SupplierIn(BaseModel):
    """Schéma d'entrée pour créer/modifier un fournisseur"""
    name: str = Field(..., description="Nom du fournisseur")
    code: Optional[str] = Field(default=None, description="Code fournisseur")
    contact_name: Optional[str] = Field(default=None, description="Nom du contact")
    email: Optional[str] = Field(default=None, description="Email")
    phone: Optional[str] = Field(default=None, description="Téléphone")
    address: Optional[str] = Field(default=None, description="Adresse")
    notes: Optional[str] = Field(default=None, description="Notes")
    is_active: Optional[bool] = Field(default=True, description="Fournisseur actif")

    class Config:
        from_attributes = True


class SupplierOut(BaseModel):
    """Schéma de sortie pour un fournisseur"""
    id: UUID
    name: str
    code: Optional[str] = Field(default=None)
    contact_name: Optional[str] = Field(default=None)
    email: Optional[str] = Field(default=None)
    phone: Optional[str] = Field(default=None)
    address: Optional[str] = Field(default=None)
    notes: Optional[str] = Field(default=None)
    is_active: Optional[bool] = Field(default=True)
    created_at: Optional[datetime] = Field(default=None)
    updated_at: Optional[datetime] = Field(default=None)

    class Config:
        from_attributes = True


class SupplierListItem(BaseModel):
    """Schéma léger pour la liste"""
    id: UUID
    name: str
    code: Optional[str] = Field(default=None)
    contact_name: Optional[str] = Field(default=None)
    email: Optional[str] = Field(default=None)
    phone: Optional[str] = Field(default=None)
    is_active: Optional[bool] = Field(default=True)

    class Config:
        from_attributes = True
