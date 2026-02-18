"""Schémas Pydantic pour les sous-familles de stock"""
from pydantic import BaseModel, Field
from uuid import UUID
from typing import Optional


class StockSubFamilyUpdate(BaseModel):
    """Schéma pour mettre à jour une sous-famille de stock"""
    label: Optional[str] = Field(default=None, max_length=100)
    template_id: Optional[UUID] = Field(
        default=None, description="UUID du template à associer ou null pour dissocier")

    class Config:
        from_attributes = True
