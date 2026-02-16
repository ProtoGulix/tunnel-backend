from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from uuid import UUID


class StockItemIn(BaseModel):
    """Schéma d'entrée pour créer un article en stock"""
    name: str = Field(..., description="Nom de l'article")
    family_code: str = Field(..., max_length=20, description="Code famille")
    sub_family_code: str = Field(..., max_length=20,
                                 description="Code sous-famille")
    spec: Optional[str] = Field(
        default=None, max_length=50, description="Spécification")
    dimension: Optional[str] = Field(
        default=None, description="Dimension (auto pour items template)")
    quantity: Optional[int] = Field(
        default=0, ge=0, description="Quantité en stock")
    unit: Optional[str] = Field(
        default=None, max_length=50, description="Unité")
    location: Optional[str] = Field(default=None, description="Emplacement")
    standars_spec: Optional[UUID] = Field(
        default=None, description="ID spec standard")
    manufacturer_item_id: Optional[UUID] = Field(
        default=None, description="ID article fabricant")
    characteristics: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="Caractéristiques (obligatoire si template)")

    class Config:
        from_attributes = True


class StockItemOut(BaseModel):
    """Schéma de sortie pour un article en stock"""
    id: UUID
    name: str
    family_code: str
    sub_family_code: str
    spec: Optional[str] = Field(default=None)
    dimension: str
    ref: Optional[str] = Field(
        default=None, description="Référence générée automatiquement")
    quantity: Optional[int] = Field(default=0)
    unit: Optional[str] = Field(default=None)
    location: Optional[str] = Field(default=None)
    standars_spec: Optional[UUID] = Field(default=None)
    supplier_refs_count: Optional[int] = Field(
        default=0, description="Nombre de références fournisseurs")
    manufacturer_item_id: Optional[UUID] = Field(default=None)

    class Config:
        from_attributes = True


class StockItemListItem(BaseModel):
    """Schéma léger pour la liste des articles"""
    id: UUID
    name: str
    ref: Optional[str] = Field(default=None)
    family_code: str
    sub_family_code: str
    quantity: Optional[int] = Field(default=0)
    unit: Optional[str] = Field(default=None)
    location: Optional[str] = Field(default=None)

    class Config:
        from_attributes = True
