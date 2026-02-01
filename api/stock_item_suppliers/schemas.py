from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID


class StockItemSupplierIn(BaseModel):
    """Schéma d'entrée pour créer/modifier une référence fournisseur"""
    stock_item_id: UUID = Field(..., description="ID de l'article en stock")
    supplier_id: UUID = Field(..., description="ID du fournisseur")
    supplier_ref: str = Field(..., description="Référence fournisseur")
    unit_price: Optional[float] = Field(default=None, description="Prix unitaire")
    min_order_quantity: Optional[int] = Field(default=1, description="Quantité minimum de commande")
    delivery_time_days: Optional[int] = Field(default=None, description="Délai de livraison en jours")
    is_preferred: Optional[bool] = Field(default=False, description="Fournisseur préféré")
    manufacturer_item_id: Optional[UUID] = Field(default=None, description="ID de l'article fabricant")

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
    # Enrichissement
    stock_item_name: Optional[str] = Field(default=None, description="Nom de l'article")
    stock_item_ref: Optional[str] = Field(default=None, description="Référence interne de l'article")
    supplier_name: Optional[str] = Field(default=None, description="Nom du fournisseur")
    supplier_code: Optional[str] = Field(default=None, description="Code du fournisseur")
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
    stock_item_name: Optional[str] = Field(default=None)
    stock_item_ref: Optional[str] = Field(default=None)
    supplier_name: Optional[str] = Field(default=None)
    supplier_code: Optional[str] = Field(default=None)

    class Config:
        from_attributes = True
