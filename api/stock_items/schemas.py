from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from uuid import UUID


class PreferredSupplierInfo(BaseModel):
    """Fournisseur préféré embarqué dans la liste des articles"""
    supplier_id: UUID
    supplier_name: Optional[str] = Field(default=None)
    supplier_ref: str
    unit_price: Optional[float] = Field(default=None)
    delivery_time_days: Optional[int] = Field(default=None)

    class Config:
        from_attributes = True


class EmbeddedSupplier(BaseModel):
    """Fournisseur embarqué dans le détail d'un article"""
    id: UUID
    supplier_id: UUID
    supplier_name: Optional[str] = Field(default=None)
    supplier_ref: str
    unit_price: Optional[float] = Field(default=None)
    min_order_quantity: Optional[int] = Field(default=None)
    delivery_time_days: Optional[int] = Field(default=None)
    is_preferred: bool = Field(default=False)
    manufacturer_item_id: Optional[UUID] = Field(
        default=None,
        description="Ref fabricant telle que référencée par ce fournisseur"
    )

    class Config:
        from_attributes = True


class SubFamilyTemplate(BaseModel):
    """Template de sous-famille embarqué dans le détail d'un article"""
    id: UUID
    code: str
    version: int
    pattern: Optional[str] = Field(default=None)

    class Config:
        from_attributes = True


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
    characteristics: Optional[List[Dict[str, Any]]] = Field(
        default=None, description="Caractéristiques (obligatoire si template)")

    class Config:
        from_attributes = True


class StockItemOut(BaseModel):
    """Schéma de sortie pour un article en stock (détail)"""
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
    suppliers: List[EmbeddedSupplier] = Field(
        default_factory=list,
        description="Fournisseurs triés préféré en premier"
    )
    sub_family_template: Optional[SubFamilyTemplate] = Field(
        default=None,
        description="Template de la sous-famille (null si legacy)"
    )

    class Config:
        from_attributes = True


class StockItemListItem(BaseModel):
    """Schéma léger pour la liste des articles"""
    id: UUID
    name: str
    ref: Optional[str] = Field(default=None)
    family_code: str
    sub_family_code: str
    spec: Optional[str] = Field(default=None)
    dimension: Optional[str] = Field(default=None)
    quantity: Optional[int] = Field(default=0)
    unit: Optional[str] = Field(default=None)
    location: Optional[str] = Field(default=None)
    supplier_refs_count: Optional[int] = Field(default=0)
    preferred_supplier: Optional[PreferredSupplierInfo] = Field(
        default=None,
        description="Fournisseur préféré (null si aucun)"
    )

    class Config:
        from_attributes = True


class FamilyFacetSubFamily(BaseModel):
    """Sous-famille avec compteur pour les facettes"""
    code: str
    label: Optional[str] = Field(default=None)
    count: int

    class Config:
        from_attributes = True


class FamilyFacet(BaseModel):
    """Famille avec compteur et sous-familles pour les facettes"""
    code: str
    label: Optional[str] = Field(default=None)
    count: int
    sub_families: List[FamilyFacetSubFamily] = Field(default_factory=list)

    class Config:
        from_attributes = True


class StockItemFacets(BaseModel):
    """Facettes pour filtres famille/sous-famille"""
    families: List[FamilyFacet] = Field(default_factory=list)

    class Config:
        from_attributes = True
