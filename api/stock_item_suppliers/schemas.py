from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID
from api.manufacturer_items.schemas import ManufacturerItemOut


class StockItemSupplierIn(BaseModel):
    """Schéma d'entrée pour créer une référence fournisseur"""
    stock_item_id: UUID = Field(..., description="ID de l'article en stock")
    supplier_id: UUID = Field(..., description="ID du fournisseur")
    supplier_ref: str = Field(..., description="Référence fournisseur")
    unit_price: Optional[float] = Field(
        default=None, description="Prix unitaire")
    min_order_quantity: Optional[int] = Field(
        default=1, description="Quantité minimum de commande")
    delivery_time_days: Optional[int] = Field(
        default=None, description="Délai de livraison en jours")
    is_preferred: Optional[bool] = Field(
        default=False, description="Fournisseur préféré")
    manufacturer_item_id: Optional[UUID] = Field(
        default=None, description="ID de l'article fabricant")
    product_url: Optional[str] = Field(
        default=None, description="URL fiche produit chez le fournisseur")

    class Config:
        from_attributes = True


class StockItemSupplierUpdate(BaseModel):
    """Schéma d'entrée pour modifier une référence fournisseur (stock_item_id et supplier_id immutables)"""
    supplier_ref: Optional[str] = Field(
        default=None, description="Référence fournisseur")
    unit_price: Optional[float] = Field(
        default=None, description="Prix unitaire")
    min_order_quantity: Optional[int] = Field(
        default=None, description="Quantité minimum de commande")
    delivery_time_days: Optional[int] = Field(
        default=None, description="Délai de livraison en jours")
    is_preferred: Optional[bool] = Field(
        default=None, description="Fournisseur préféré")
    manufacturer_item_id: Optional[UUID] = Field(
        default=None, description="ID de l'article fabricant")
    product_url: Optional[str] = Field(
        default=None, description="URL fiche produit chez le fournisseur")

    class Config:
        from_attributes = True


class StockItemSupplierOut(BaseModel):
    """Schéma de sortie pour une référence fournisseur"""
    id: UUID
    stock_item_id: UUID
    supplier_id: UUID
    supplier_ref: str
    unit_price: Optional[float] = Field(default=None)
    min_order_quantity: Optional[int] = Field(default=1)
    delivery_time_days: Optional[int] = Field(default=None)
    is_preferred: Optional[bool] = Field(default=False)
    manufacturer_item_id: Optional[UUID] = Field(default=None)
    manufacturer_item: Optional[ManufacturerItemOut] = Field(
        default=None, description="Détail référence fabricant")
    product_url: Optional[str] = Field(
        default=None, description="URL fiche produit chez le fournisseur")
    # Enrichissement
    stock_item_name: Optional[str] = Field(
        default=None, description="Nom de l'article")
    stock_item_ref: Optional[str] = Field(
        default=None, description="Référence interne de l'article")
    supplier_name: Optional[str] = Field(
        default=None, description="Nom du fournisseur")
    supplier_code: Optional[str] = Field(
        default=None, description="Code du fournisseur")
    created_at: Optional[datetime] = Field(default=None)
    updated_at: Optional[datetime] = Field(default=None)

    class Config:
        from_attributes = True


class StockItemSupplierListItem(BaseModel):
    """Schéma léger pour la liste"""
    id: UUID
    stock_item_id: UUID
    supplier_id: UUID
    supplier_ref: str
    unit_price: Optional[float] = Field(default=None)
    min_order_quantity: Optional[int] = Field(default=1)
    delivery_time_days: Optional[int] = Field(default=None)
    is_preferred: Optional[bool] = Field(default=False)
    manufacturer_item: Optional[ManufacturerItemOut] = Field(default=None)
    product_url: Optional[str] = Field(default=None)
    stock_item_name: Optional[str] = Field(default=None)
    stock_item_ref: Optional[str] = Field(default=None)
    supplier_name: Optional[str] = Field(default=None)
    supplier_code: Optional[str] = Field(default=None)

    class Config:
        from_attributes = True
