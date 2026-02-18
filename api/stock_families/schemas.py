"""Schémas Pydantic pour les familles de stock"""
from pydantic import BaseModel, Field
from typing import List

from api.stock_items.template_schemas import StockSubFamily


class StockFamilyListItem(BaseModel):
    """Schéma léger pour la liste des familles"""
    family_code: str = Field(..., max_length=20, description="Code famille")
    sub_family_count: int = Field(..., description="Nombre de sous-familles")

    class Config:
        from_attributes = True


class StockFamilyDetail(BaseModel):
    """Schéma détaillé d'une famille avec ses sous-familles"""
    family_code: str = Field(..., max_length=20, description="Code famille")
    sub_families: List[StockSubFamily] = Field(
        ..., description="Liste des sous-familles avec templates")
    sub_family_count: int = Field(..., description="Nombre de sous-familles")

    class Config:
        from_attributes = True
