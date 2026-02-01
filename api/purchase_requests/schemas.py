from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID

from api.stock_items.schemas import StockItemListItem


class LinkedOrderLine(BaseModel):
    """Ligne de commande fournisseur liée à une demande d'achat"""
    id: UUID
    supplier_order_line_id: UUID
    quantity_allocated: int = Field(..., description="Quantité allouée à cette demande")
    supplier_order_id: UUID
    supplier_order_status: Optional[str] = Field(default=None, description="Statut de la commande fournisseur")
    supplier_order_number: Optional[str] = Field(default=None, description="Numéro de la commande fournisseur")
    stock_item_id: UUID
    stock_item_name: Optional[str] = Field(default=None)
    stock_item_ref: Optional[str] = Field(default=None)
    quantity: int = Field(..., description="Quantité totale de la ligne")
    unit_price: Optional[float] = Field(default=None)
    total_price: Optional[float] = Field(default=None)
    quote_received: Optional[bool] = Field(default=None, description="Devis reçu")
    quote_price: Optional[float] = Field(default=None, description="Prix du devis")
    quantity_received: Optional[int] = Field(default=0)
    is_selected: Optional[bool] = Field(default=None, description="Ligne sélectionnée pour commande")
    created_at: Optional[datetime] = Field(default=None)

    class Config:
        from_attributes = True


class PurchaseRequestIn(BaseModel):
    """Schéma d'entrée pour créer une demande d'achat"""
    stock_item_id: Optional[UUID] = Field(default=None, description="ID de l'item en stock (optionnel)")
    item_label: str = Field(..., description="Libellé de l'article demandé")
    quantity: int = Field(..., gt=0, description="Quantité demandée")
    unit: Optional[str] = Field(default=None, max_length=50, description="Unité (pièce, kg, etc.)")
    requested_by: Optional[str] = Field(default=None, description="Demandeur (identifiant)")
    urgency: Optional[str] = Field(default="normal", description="Niveau d'urgence (normal, high, critical)")
    reason: Optional[str] = Field(default=None, description="Raison de la demande")
    notes: Optional[str] = Field(default=None, description="Notes complémentaires")
    workshop: Optional[str] = Field(default=None, max_length=255, description="Atelier concerné")
    intervention_id: Optional[UUID] = Field(default=None, description="ID de l'intervention associée (si liée à une action)")
    quantity_requested: Optional[int] = Field(default=None, description="Quantité demandée (détail)")
    urgent: Optional[bool] = Field(default=False, description="Flag urgence")
    requester_name: Optional[str] = Field(default=None, description="Nom du demandeur")

    class Config:
        from_attributes = True


class PurchaseRequestOut(BaseModel):
    """Schéma de sortie pour une demande d'achat"""
    id: UUID
    status: str = Field(default="open", description="Statut de la demande")
    stock_item_id: Optional[UUID] = Field(default=None)
    stock_item: Optional[StockItemListItem] = Field(default=None, description="Détail de l'article en stock")
    item_label: str
    quantity: int
    unit: Optional[str] = Field(default=None)
    requested_by: Optional[str] = Field(default=None)
    urgency: Optional[str] = Field(default=None)
    reason: Optional[str] = Field(default=None)
    notes: Optional[str] = Field(default=None)
    workshop: Optional[str] = Field(default=None)
    intervention_id: Optional[UUID] = Field(default=None)
    quantity_requested: Optional[int] = Field(default=None)
    quantity_approved: Optional[int] = Field(default=None)
    urgent: Optional[bool] = Field(default=None)
    requester_name: Optional[str] = Field(default=None)
    approver_name: Optional[str] = Field(default=None)
    approved_at: Optional[datetime] = Field(default=None)
    order_lines: Optional[List[LinkedOrderLine]] = Field(
        default=None,
        description="Lignes de commande fournisseur liées"
    )
    created_at: Optional[datetime] = Field(default=None)
    updated_at: Optional[datetime] = Field(default=None)

    class Config:
        from_attributes = True
