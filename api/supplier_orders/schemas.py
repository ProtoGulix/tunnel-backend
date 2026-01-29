from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date
from uuid import UUID

from api.supplier_order_lines.schemas import SupplierOrderLineListItem


class SupplierOrderIn(BaseModel):
    """Schéma d'entrée pour créer une commande fournisseur"""
    supplier_id: UUID = Field(..., description="ID du fournisseur")
    status: Optional[str] = Field(default="OPEN", max_length=50, description="Statut de la commande")
    ordered_at: Optional[datetime] = Field(default=None, description="Date de commande")
    expected_delivery_date: Optional[date] = Field(default=None, description="Date de livraison prévue")
    notes: Optional[str] = Field(default=None, description="Notes")
    currency: Optional[float] = Field(default=None, description="Devise/taux")

    class Config:
        from_attributes = True


class SupplierOrderOut(BaseModel):
    """Schéma de sortie pour une commande fournisseur"""
    id: UUID
    order_number: str = Field(..., description="Numéro de commande (généré automatiquement)")
    supplier_id: UUID
    status: str
    total_amount: Optional[float] = Field(default=0, description="Montant total")
    ordered_at: Optional[datetime] = Field(default=None)
    expected_delivery_date: Optional[date] = Field(default=None)
    received_at: Optional[datetime] = Field(default=None)
    notes: Optional[str] = Field(default=None)
    currency: Optional[float] = Field(default=None)
    lines: Optional[List[SupplierOrderLineListItem]] = Field(
        default=None,
        description="Lignes de la commande"
    )
    created_at: Optional[datetime] = Field(default=None)
    updated_at: Optional[datetime] = Field(default=None)

    class Config:
        from_attributes = True


class SupplierOrderListItem(BaseModel):
    """Schéma léger pour la liste"""
    id: UUID
    order_number: str
    supplier_id: UUID
    status: str
    total_amount: Optional[float] = Field(default=0)
    ordered_at: Optional[datetime] = Field(default=None)
    expected_delivery_date: Optional[date] = Field(default=None)
    line_count: Optional[int] = Field(default=0, description="Nombre de lignes")

    class Config:
        from_attributes = True
