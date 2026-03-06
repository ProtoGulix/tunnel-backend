from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID


class ManufacturerItemIn(BaseModel):
    """Schéma d'entrée pour créer/modifier une référence fabricant"""
    manufacturer_name: str = Field(...,
                                   description="Nom du fabricant/constructeur")
    manufacturer_ref: Optional[str] = Field(
        default=None, description="Référence catalogue fabricant")

    class Config:
        from_attributes = True


class ManufacturerItemOut(BaseModel):
    """Schéma de sortie pour une référence fabricant"""
    id: UUID
    manufacturer_name: str
    manufacturer_ref: Optional[str] = Field(default=None)

    class Config:
        from_attributes = True


class SupplierItemLink(BaseModel):
    """Référence fournisseur liée à un fabricant (schéma léger)"""
    id: UUID
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


class ManufacturerItemDetail(ManufacturerItemOut):
    """Référence fabricant avec ses références fournisseurs liées"""
    supplier_items: List[SupplierItemLink] = Field(
        default_factory=list,
        description="Références fournisseurs utilisant ce fabricant"
    )
