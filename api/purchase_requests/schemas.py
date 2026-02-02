from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date
from uuid import UUID

from api.stock_items.schemas import StockItemListItem


# ========== Schémas optimisés v1.2.0 ==========

class DerivedStatus(BaseModel):
    """Statut dérivé calculé côté backend"""
    code: str = Field(..., description="Code statut (OPEN, QUOTED, ORDERED, PARTIAL, RECEIVED, REJECTED)")
    label: str = Field(..., description="Label lisible")
    color: str = Field(..., description="Couleur hexadécimale")

    class Config:
        from_attributes = True


class PurchaseRequestListItem(BaseModel):
    """Schéma léger pour liste (tableau, pagination)"""
    id: UUID
    item_label: str
    quantity: int
    unit: Optional[str] = Field(default=None)

    # Statut dérivé (calculé en SQL)
    derived_status: DerivedStatus

    # Infos essentielles sans objets imbriqués
    stock_item_ref: Optional[str] = Field(
        default=None, description="Référence article")
    stock_item_name: Optional[str] = Field(
        default=None, description="Nom article")
    intervention_code: Optional[str] = Field(
        default=None, description="Code intervention")
    requester_name: Optional[str] = Field(default=None)
    urgency: Optional[str] = Field(default=None)
    urgent: Optional[bool] = Field(default=False)

    # Compteurs agrégés (évite de charger order_lines)
    quotes_count: int = Field(default=0, description="Nombre de devis reçus")
    selected_count: int = Field(
        default=0, description="Nombre de lignes sélectionnées")
    suppliers_count: int = Field(
        default=0, description="Nombre de fournisseurs différents")

    # Métadonnées
    created_at: Optional[datetime] = Field(default=None)
    updated_at: Optional[datetime] = Field(default=None)

    class Config:
        from_attributes = True


class SupplierInfo(BaseModel):
    """Informations fournisseur enrichies"""
    id: UUID
    name: str
    code: Optional[str] = Field(default=None)
    contact_name: Optional[str] = Field(default=None)
    email: Optional[str] = Field(default=None)
    phone: Optional[str] = Field(default=None)

    class Config:
        from_attributes = True


class LinkedOrderLineDetail(BaseModel):
    """Ligne de commande avec fournisseur enrichi (pour détails complets)"""
    id: UUID
    supplier_order_line_id: UUID
    quantity_allocated: int

    # Commande fournisseur
    supplier_order_id: UUID
    supplier_order_number: Optional[str] = Field(default=None)
    supplier_order_status: Optional[str] = Field(default=None)

    # Fournisseur enrichi
    supplier: Optional[SupplierInfo] = Field(default=None)

    # Détails ligne
    unit_price: Optional[float] = Field(default=None)
    total_price: Optional[float] = Field(default=None)
    quote_received: Optional[bool] = Field(default=None)
    quote_price: Optional[float] = Field(default=None)
    quote_received_at: Optional[datetime] = Field(default=None)
    is_selected: Optional[bool] = Field(default=None)
    quantity_received: Optional[int] = Field(default=None)
    manufacturer: Optional[str] = Field(default=None)
    manufacturer_ref: Optional[str] = Field(default=None)
    lead_time_days: Optional[int] = Field(default=None)
    notes: Optional[str] = Field(default=None)
    created_at: Optional[datetime] = Field(default=None)

    class Config:
        from_attributes = True


class EquipementInfo(BaseModel):
    """Informations équipement pour contexte intervention"""
    id: UUID
    code: Optional[str] = Field(default=None)
    name: str

    class Config:
        from_attributes = True


class InterventionInfo(BaseModel):
    """Informations intervention complètes"""
    id: UUID
    code: Optional[str] = Field(default=None)
    title: str
    priority: Optional[str] = Field(default=None)
    status_actual: Optional[str] = Field(default=None)
    equipement: Optional[EquipementInfo] = Field(default=None)

    class Config:
        from_attributes = True


class StockItemDetail(BaseModel):
    """Article stock complet (pour édition)"""
    id: UUID
    name: str
    ref: Optional[str] = Field(default=None)
    family_code: str
    sub_family_code: str
    quantity: Optional[int] = Field(default=0)
    unit: Optional[str] = Field(default=None)
    location: Optional[str] = Field(default=None)
    supplier_refs_count: Optional[int] = Field(default=0)

    class Config:
        from_attributes = True


class PurchaseRequestDetail(BaseModel):
    """Schéma complet pour détails (modal, édition)"""
    id: UUID
    item_label: str
    quantity: int
    unit: Optional[str] = Field(default=None)

    # Statut dérivé
    derived_status: DerivedStatus

    # Relations complètes
    stock_item: Optional[StockItemDetail] = Field(
        default=None, description="Article stock complet")
    intervention: Optional[InterventionInfo] = Field(
        default=None, description="Intervention complète")
    order_lines: List[LinkedOrderLineDetail] = Field(
        default_factory=list, description="Lignes avec fournisseurs")

    # Métadonnées demande
    requested_by: Optional[str] = Field(default=None)
    requester_name: Optional[str] = Field(default=None)
    approver_name: Optional[str] = Field(default=None)
    approved_at: Optional[datetime] = Field(default=None)
    urgency: Optional[str] = Field(default=None)
    urgent: Optional[bool] = Field(default=False)
    reason: Optional[str] = Field(default=None)
    notes: Optional[str] = Field(default=None)
    workshop: Optional[str] = Field(default=None)
    quantity_requested: Optional[int] = Field(default=None)
    quantity_approved: Optional[int] = Field(default=None)
    created_at: Optional[datetime] = Field(default=None)
    updated_at: Optional[datetime] = Field(default=None)

    class Config:
        from_attributes = True


class PurchaseRequestStats(BaseModel):
    """Statistiques agrégées"""
    period: dict = Field(..., description="Période analysée")
    totals: dict = Field(..., description="Totaux généraux")
    by_status: List[dict] = Field(default_factory=list)
    by_urgency: List[dict] = Field(default_factory=list)
    top_items: List[dict] = Field(default_factory=list)

    class Config:
        from_attributes = True


# ========== Schémas legacy (à déprécier) ==========

class LinkedOrderLine(BaseModel):
    """Ligne de commande fournisseur liée à une demande d'achat"""
    id: UUID
    supplier_order_line_id: UUID
    quantity_allocated: int = Field(...,
                                    description="Quantité allouée à cette demande")
    supplier_order_id: UUID
    supplier_order_status: Optional[str] = Field(
        default=None, description="Statut de la commande fournisseur")
    supplier_order_number: Optional[str] = Field(
        default=None, description="Numéro de la commande fournisseur")
    stock_item_id: UUID
    stock_item_name: Optional[str] = Field(default=None)
    stock_item_ref: Optional[str] = Field(default=None)
    quantity: int = Field(..., description="Quantité totale de la ligne")
    unit_price: Optional[float] = Field(default=None)
    total_price: Optional[float] = Field(default=None)
    quote_received: Optional[bool] = Field(
        default=None, description="Devis reçu")
    quote_price: Optional[float] = Field(
        default=None, description="Prix du devis")
    quantity_received: Optional[int] = Field(default=0)
    is_selected: Optional[bool] = Field(
        default=None, description="Ligne sélectionnée pour commande")
    created_at: Optional[datetime] = Field(default=None)

    class Config:
        from_attributes = True


class PurchaseRequestIn(BaseModel):
    """Schéma d'entrée pour créer une demande d'achat"""
    stock_item_id: Optional[UUID] = Field(
        default=None, description="ID de l'item en stock (optionnel)")
    item_label: str = Field(..., description="Libellé de l'article demandé")
    quantity: int = Field(..., gt=0, description="Quantité demandée")
    unit: Optional[str] = Field(
        default=None, max_length=50, description="Unité (pièce, kg, etc.)")
    requested_by: Optional[str] = Field(
        default=None, description="Demandeur (identifiant)")
    urgency: Optional[str] = Field(
        default="normal", description="Niveau d'urgence (normal, high, critical)")
    reason: Optional[str] = Field(
        default=None, description="Raison de la demande")
    notes: Optional[str] = Field(
        default=None, description="Notes complémentaires")
    workshop: Optional[str] = Field(
        default=None, max_length=255, description="Atelier concerné")
    intervention_id: Optional[UUID] = Field(
        default=None, description="ID de l'intervention associée (si liée à une action)")
    quantity_requested: Optional[int] = Field(
        default=None, description="Quantité demandée (détail)")
    urgent: Optional[bool] = Field(default=False, description="Flag urgence")
    requester_name: Optional[str] = Field(
        default=None, description="Nom du demandeur")

    class Config:
        from_attributes = True


class PurchaseRequestOut(BaseModel):
    """Schéma de sortie pour une demande d'achat"""
    id: UUID
    status: str = Field(default="open", description="Statut de la demande")
    stock_item_id: Optional[UUID] = Field(default=None)
    stock_item: Optional[StockItemListItem] = Field(
        default=None, description="Détail de l'article en stock")
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
