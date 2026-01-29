from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID

from api.stock_items.schemas import StockItemListItem


class LinkedPurchaseRequest(BaseModel):
    """Demande d'achat liée à la ligne de commande"""
    id: UUID
    purchase_request_id: UUID
    quantity: int
    item_label: Optional[str] = Field(default=None)
    requester_name: Optional[str] = Field(default=None)
    intervention_id: Optional[UUID] = Field(default=None)
    created_at: Optional[datetime] = Field(default=None)

    class Config:
        from_attributes = True


class PurchaseRequestLink(BaseModel):
    """Schéma pour lier une demande d'achat à une ligne"""
    purchase_request_id: UUID
    quantity: int = Field(..., gt=0, description="Quantité allouée à cette demande")

    class Config:
        from_attributes = True


class SupplierOrderLineIn(BaseModel):
    """Schéma d'entrée pour créer une ligne de commande fournisseur"""
    supplier_order_id: UUID = Field(..., description="ID de la commande fournisseur")
    stock_item_id: UUID = Field(..., description="ID de l'article en stock")
    supplier_ref_snapshot: Optional[str] = Field(default=None, description="Référence fournisseur snapshot")
    quantity: int = Field(..., gt=0, description="Quantité commandée")
    unit_price: Optional[float] = Field(default=None, description="Prix unitaire")
    notes: Optional[str] = Field(default=None, description="Notes")
    quote_received: Optional[bool] = Field(default=None, description="Devis reçu")
    is_selected: Optional[bool] = Field(default=None, description="Ligne sélectionnée")
    quote_price: Optional[float] = Field(default=None, description="Prix du devis")
    manufacturer: Optional[str] = Field(default=None, description="Fabricant")
    manufacturer_ref: Optional[str] = Field(default=None, description="Référence fabricant")
    quote_received_at: Optional[datetime] = Field(default=None, description="Date réception devis")
    rejected_reason: Optional[str] = Field(default=None, description="Raison du rejet")
    lead_time_days: Optional[int] = Field(default=None, description="Délai de livraison en jours")
    purchase_requests: Optional[List[PurchaseRequestLink]] = Field(
        default=None,
        description="Demandes d'achat à lier"
    )

    class Config:
        from_attributes = True


class SupplierOrderLineOut(BaseModel):
    """Schéma de sortie pour une ligne de commande fournisseur"""
    id: UUID
    supplier_order_id: UUID
    stock_item_id: UUID
    stock_item: Optional[StockItemListItem] = Field(default=None, description="Détail de l'article")
    supplier_ref_snapshot: Optional[str] = Field(default=None)
    quantity: int
    unit_price: Optional[float] = Field(default=None)
    total_price: Optional[float] = Field(default=None, description="Calculé automatiquement")
    quantity_received: Optional[int] = Field(default=0)
    notes: Optional[str] = Field(default=None)
    quote_received: Optional[bool] = Field(default=None)
    is_selected: Optional[bool] = Field(default=None)
    quote_price: Optional[float] = Field(default=None)
    manufacturer: Optional[str] = Field(default=None)
    manufacturer_ref: Optional[str] = Field(default=None)
    quote_received_at: Optional[datetime] = Field(default=None)
    rejected_reason: Optional[str] = Field(default=None)
    lead_time_days: Optional[int] = Field(default=None)
    purchase_requests: Optional[List[LinkedPurchaseRequest]] = Field(
        default=None,
        description="Demandes d'achat liées"
    )
    created_at: Optional[datetime] = Field(default=None)
    updated_at: Optional[datetime] = Field(default=None)

    class Config:
        from_attributes = True


class SupplierOrderLineListItem(BaseModel):
    """Schéma léger pour la liste"""
    id: UUID
    supplier_order_id: UUID
    stock_item_id: UUID
    stock_item_name: Optional[str] = Field(default=None)
    stock_item_ref: Optional[str] = Field(default=None)
    quantity: int
    unit_price: Optional[float] = Field(default=None)
    total_price: Optional[float] = Field(default=None)
    quantity_received: Optional[int] = Field(default=0)
    is_selected: Optional[bool] = Field(default=None)
    purchase_request_count: Optional[int] = Field(default=0)

    class Config:
        from_attributes = True
