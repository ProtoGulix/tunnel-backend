from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, date
from uuid import UUID

from api.supplier_order_lines.schemas import SupplierOrderLineListItem
from api.suppliers.schemas import SupplierListItem


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
    supplier: Optional[SupplierListItem] = Field(
        default=None, description="Informations fournisseur enrichies")
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
    line_count: int = Field(default=0, description="Nombre de lignes")
    age_days: int = Field(default=0, description="Âge en jours depuis création")
    age_color: str = Field(default="gray", description="Couleur indicateur âge (gray, orange, red)")
    is_blocking: bool = Field(default=False, description="Commande bloquante (en attente trop longtemps)")
    created_at: Optional[datetime] = Field(default=None)
    updated_at: Optional[datetime] = Field(default=None)

    class Config:
        from_attributes = True


class SupplierOrderListItem(BaseModel):
    """Schéma léger pour la liste"""
    id: UUID
    order_number: str
    supplier_id: UUID
    supplier: Optional[SupplierListItem] = Field(
        default=None, description="Informations fournisseur enrichies")
    status: str
    total_amount: Optional[float] = Field(default=0)
    ordered_at: Optional[datetime] = Field(default=None)
    expected_delivery_date: Optional[date] = Field(default=None)
    line_count: int = Field(default=0, description="Nombre de lignes")
    age_days: int = Field(default=0, description="Âge en jours depuis création")
    age_color: str = Field(default="gray", description="Couleur indicateur âge (gray, orange, red)")
    is_blocking: bool = Field(default=False, description="Commande bloquante (en attente trop longtemps)")
    created_at: Optional[datetime] = Field(default=None)
    updated_at: Optional[datetime] = Field(default=None)

    class Config:
        from_attributes = True


class EmailExportOut(BaseModel):
    """Schéma de sortie pour l'export email"""
    subject: str = Field(..., description="Sujet de l'email")
    body_text: str = Field(..., description="Corps de l'email en texte brut")
    body_html: str = Field(..., description="Corps de l'email en HTML")
    supplier_email: Optional[str] = Field(default=None, description="Email du fournisseur")

    class Config:
        from_attributes = True
