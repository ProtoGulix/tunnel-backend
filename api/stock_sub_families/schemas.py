"""Schémas Pydantic pour les sous-familles de stock"""
from pydantic import BaseModel, Field
from uuid import UUID
from typing import Optional


class StockSubFamilyCreate(BaseModel):
    """Schéma pour créer une sous-famille (family_code + code dans le body)"""
    family_code: str = Field(..., max_length=20)
    code: str = Field(..., max_length=20)
    label: Optional[str] = Field(default=None, max_length=100)
    template_id: Optional[UUID] = Field(
        default=None, description="UUID du template à associer")

    class Config:
        from_attributes = True


class StockSubFamilyCreateInFamily(BaseModel):
    """Schéma pour créer une sous-famille avec family_code dans l'URL"""
    code: str = Field(..., max_length=20)
    label: Optional[str] = Field(default=None, max_length=100)
    template_id: Optional[UUID] = Field(
        default=None, description="UUID du template à associer")

    class Config:
        from_attributes = True


class StockSubFamilyUpdate(BaseModel):
    """Schéma pour mettre à jour une sous-famille de stock"""
    label: Optional[str] = Field(default=None, max_length=100)
    template_id: Optional[UUID] = Field(
        default=None, description="UUID du template à associer ou null pour dissocier")

    class Config:
        from_attributes = True
